"""No torch/model imports: deterministic tokenizer/tensor/generation doubles."""
import builtins
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.model import Invalid
from bc_phase2.planner_first import make_request
from bc_phase2.planner_qwen import (QwenTransport, QwenPlannerSession, open_local,
    verify_local_inventory, CHECKPOINT, REVISION, OUTPUT)

UNSUPPORTED = json.dumps({'schema_version':'1.0','status':'unsupported',
    'requested_agents':4,'reason':'Synthetic source does not justify four tasks.'})


class Tokenizer:
    chat_template = 'enable_thinking <think> </think> <eos>'
    eos_token = '<eos>'
    eos_token_id = 9
    pad_token_id = 0
    unk_token_id = 999
    def __init__(self):
        self.messages = []
        self.input_length = 5
        self.final = UNSUPPORTED
    def convert_tokens_to_ids(self, token):
        return {'</think>':8,'<eos>':9}.get(token,999)
    def encode(self, text, **kwargs):
        return [8] if text == '</think>' else [1]*self.input_length
    def apply_chat_template(self, messages, *, tokenize, enable_thinking, **kwargs):
        self.messages.append(messages)
        if not tokenize: return 'fixture <think>\n' if enable_thinking else 'fixture no reasoning'
        return {'input_ids':[1]*self.input_length}
    def decode(self, ids, **kwargs):
        assert kwargs == {'skip_special_tokens':False,'clean_up_tokenization_spaces':False}
        if ids == [7]: return self.final
        return ''.join({6:'reason',8:'</think>',7:self.final,9:'<eos>',0:'<pad>'}.get(i,'x') for i in ids)


class Tensor:
    def __init__(self, data): self.data = data
    def tolist(self): return self.data


class Model:
    generation_config = SimpleNamespace(eos_token_id=9, pad_token_id=0)
    def __init__(self): self.calls=[]; self.generated=[6,8,7,9]; self.before=None
    def generate(self, **kwargs):
        if self.before: self.before()
        self.calls.append(kwargs)
        return SimpleNamespace(sequences=Tensor([kwargs['input_ids'].data[0]+self.generated]))


class Torch:
    long = 'fake-long'
    cuda = SimpleNamespace(synchronize=lambda: None)
    inference_mode = staticmethod(nullcontext)
    tensor = staticmethod(lambda data, **kwargs: Tensor(data))
    ones_like = staticmethod(lambda tensor: Tensor([[1]*len(tensor.data[0])]))


class QwenTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name in ('socket.socket.connect','socket.create_connection','subprocess.Popen',
                     'bc_phase2.runtime.MockWorker.invoke','bc_phase2.allocation.solve'):
            guard=patch(name,side_effect=AssertionError('offline boundary'));guard.start();self.addCleanup(guard.stop)
        self.tokenizer=Tokenizer();self.model=Model()
        self.transport=QwenTransport(self.tokenizer,self.model,Torch())
        self.requests=[make_request({'id':f'synthetic:{i}','problem':'Synthetic problem.',
            'answer':'SECRET','solution':'SECRET'},'private-binding') for i in range(3)]
        self.session=QwenPlannerSession(self.root/'run',self.requests,self.transport)

    def test_public_load_fails_before_any_optional_import(self):
        original=builtins.__import__
        def guard(name,*args,**kwargs):
            if name.split('.')[0] in ('torch','transformers'):raise AssertionError('GPU import')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guard):
            with self.assertRaisesRegex(Invalid,'disabled'):open_local({'execution_allowed':True})
        self.assertEqual(self.model.calls,[])

    def test_actual_sequence_counts_include_reasoning_and_eos(self):
        result=self.session.advance('synthetic:0')
        self.assertEqual(result['actual_tokens'],9)
        observed=result['observation']
        self.assertEqual(observed['output_tokens'],4)
        self.assertEqual(observed['reasoning_tokens'],2)
        self.assertEqual(observed['raw_decoded'],'reason</think>'+UNSUPPORTED+'<eos>')
        self.assertEqual(observed['final_text'],UNSUPPORTED)
        self.assertEqual(result['review']['mechanical_status'],'UNSUPPORTED')
        self.assertEqual(result['totals']['real_model_calls'],0)
        options=self.model.calls[0]
        self.assertFalse(options['do_sample'])
        self.assertEqual(options['max_new_tokens'],6144)
        self.assertNotIn('temperature',options)
        self.assertNotIn('logits_processor',options)
        self.assertEqual(options['attention_mask'].data,[[1]*5])

    def test_reservation_durable_before_generate(self):
        def check():
            saved=json.loads(self.session.path.read_text())['state']['attempts'][-1]
            self.assertEqual(saved['state'],'reserved')
            self.assertEqual(saved['reservation_tokens'],5+OUTPUT)
        self.model.before=check
        self.session.advance('synthetic:0')

    def test_failure_leaves_reservation_no_replay(self):
        self.model.before=lambda: (_ for _ in ()).throw(RuntimeError('inference double failure'))
        with self.assertRaises(RuntimeError):self.session.advance('synthetic:0')
        resumed=QwenPlannerSession(self.root/'run',self.requests,self.transport)
        self.assertEqual(resumed.snapshot()['totals']['simulated_reserved_tokens'],5+OUTPUT)
        with self.assertRaises(Invalid):resumed.advance('synthetic:1')

    def test_prefix_mismatch_keeps_uncertain_usage(self):
        with patch.object(self.model,'generate',return_value=SimpleNamespace(sequences=Tensor([[2,8,7,9]]))):
            with self.assertRaisesRegex(Invalid,'prefix'):self.session.advance('synthetic:0')
        self.assertEqual(self.session.snapshot()['attempts'][0]['state'],'reserved')

    def test_missing_reasoning_boundary_not_silently_decoded_as_json(self):
        self.model.generated=[7,9]
        result=self.session.advance('synthetic:0')
        self.assertIsNone(result['raw'])
        self.assertEqual(result['actual_tokens'],7)
        self.assertIsNotNone(result['boundary_error'])
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')

    def test_duplicate_close_and_interior_eos_fail_closed(self):
        for source,ids in [('synthetic:0',[8,8,7,9]),('synthetic:1',[8,9,7,9])]:
            self.model.generated=ids
            result=self.session.advance(source)
            self.assertIsNotNone(result['boundary_error'])
            self.assertIsNone(result['raw'])

    def test_only_terminal_eos_removed_no_general_token_stripping(self):
        self.model.generated=[6,8,0,7,9]
        result=self.session.advance('synthetic:0')
        self.assertTrue(result['raw'].startswith('<pad>'))
        self.assertEqual(result['review']['mechanical_status'],'PLAN_INVALID')

    def test_correction_once_payload_and_tokens_rerendered(self):
        self.tokenizer.final='{'
        self.session.advance('synthetic:0')
        self.tokenizer.final=UNSUPPORTED;self.tokenizer.input_length=7
        row=self.session.advance('synthetic:0')
        self.assertEqual(row['actual_tokens'],11)
        self.assertIn('structural_correction',row['outbound_payload']['planning_instructions'])
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')
        self.assertEqual(len(self.model.calls),2)

    def test_context_overflow_never_generates(self):
        self.tokenizer.input_length=10241
        with self.assertRaisesRegex(Invalid,'overflow'):self.session.advance('synthetic:0')
        self.assertEqual(self.model.calls,[])
        self.assertEqual(self.session.snapshot()['attempts'],[])

    def test_overrun_actual_charge_and_global_stop(self):
        self.model.generated=[6]*OUTPUT+[8,7,9]
        row=self.session.advance('synthetic:0')
        self.assertEqual(row['state'],'usage_violation')
        self.assertEqual(row['actual_tokens'],5+OUTPUT+3)
        with self.assertRaises(Invalid):self.session.advance('synthetic:1')

    def test_secrets_and_provenance_not_in_messages(self):
        self.session.advance('synthetic:0')
        message=json.dumps(self.tokenizer.messages)
        for forbidden in ('SECRET','private-binding','synthetic:0'):
            self.assertNotIn(forbidden,message)

    def test_unexpected_template_or_ids_rejected(self):
        with patch.object(self.tokenizer,'encode',return_value=[2]):
            with self.assertRaisesRegex(Invalid,'binding'):self.session.advance('synthetic:0')
        self.assertEqual(self.model.calls,[])
        with patch.object(self.tokenizer,'apply_chat_template',return_value='no reasoning prefix'):
            with self.assertRaises(Invalid):self.session.advance('synthetic:0')

    def test_template_binding_change_resume_rejected(self):
        self.transport.binding={**self.transport.binding,'do_sample':True}
        with self.assertRaises(Invalid):QwenPlannerSession(self.root/'run',self.requests,self.transport)

    def test_raw_oversize_retention_bounded(self):
        self.tokenizer.final='x'*65537
        result=self.session.advance('synthetic:0')
        self.assertIsNone(result['raw'])
        self.assertIsNone(result['observation']['raw_decoded'])
        self.assertIn('raw_decoded_digest',result['observation'])
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')

    def test_valid_plan_survives_transport_without_extra_call(self):
        self.tokenizer.final=json.dumps({'schema_version':'1.0','status':'plan',
            'requested_agents':4,'tasks':[{'task_id':f't{i}',
                'instruction':f'Derive fixture claim {i}.','expected_artifact':'A justified claim.',
                'parent_task_ids':[f't{i-1}'] if i else [],
                'immutable_inputs':['problem_statement']} for i in range(4)],
            'ownership':[{'agent_id':f'agent_{i}','task_ids':[f't{i}']} for i in range(4)],
            'final_task_id':'t3','rationale':'Sequential fixture.'})
        result=self.session.advance('synthetic:0')
        self.assertEqual(result['review']['mechanical_status'],'PLAN_VALID')
        self.assertEqual(result['review']['qualitative_status'],'NOT_REVIEWED')
        self.assertEqual(result['raw'],self.tokenizer.final)
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')
        self.assertEqual(len(self.model.calls),1)

    def test_length_limit_keeps_all_tokens_charged(self):
        self.model.generated=[6]*OUTPUT
        row=self.session.advance('synthetic:0')
        self.assertEqual(row['observation']['finish_reason'],'length_limit')
        self.assertEqual(row['actual_tokens'],5+OUTPUT)
        self.assertIsNone(row['raw'])
        self.assertEqual(row['state'],'completed')
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')

    def test_template_change_before_call_rejected(self):
        self.tokenizer.chat_template += ' changed'
        with self.assertRaisesRegex(Invalid,'template changed'):self.session.advance('synthetic:0')
        self.assertEqual(self.model.calls,[])

    def test_six_call_and_two_invalid_boundaries(self):
        self.tokenizer.final='{' 
        for i in range(3):
            self.session.advance(f'synthetic:{i}')
            self.session.advance(f'synthetic:{i}')
        self.assertEqual(len(self.model.calls),6)
        with self.assertRaises(Invalid):self.session.advance('synthetic:0')
        self.assertEqual(len(self.model.calls),6)

    def test_reconciliation_write_interruption_blocks_restart(self):
        original=self.session._save
        def interrupt(state):
            if state['attempts'][-1]['state']=='completed':raise KeyboardInterrupt()
            return original(state)
        with patch.object(self.session,'_save',side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):self.session.advance('synthetic:0')
        resumed=QwenPlannerSession(self.root/'run',self.requests,self.transport)
        with self.assertRaises(Invalid):resumed.advance('synthetic:0')
        self.assertEqual(len(self.model.calls),1)

    def inventory(self):
        root=self.root/REVISION;root.mkdir()
        records={'config.json':{'architectures':['Qwen3_5ForConditionalGeneration']},
            'generation_config.json':{},'tokenizer.json':{},'tokenizer_config.json':{},
            'model.safetensors.index.json':{'weight_map':{'weight':'model-01.safetensors'}}}
        for name,value in records.items():(root/name).write_text(json.dumps(value))
        (root/'model-01.safetensors').write_bytes(b'synthetic bytes, not a loadable model')
        return {'checkpoint':CHECKPOINT,'revision':REVISION,'local_path':str(root),
            'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}}

    def test_inventory_hashes_full_shards_and_optional_files(self):
        lock=self.inventory();root=verify_local_inventory(lock)
        (root/'model-01.safetensors').write_bytes(b'changed')
        with self.assertRaises(Invalid):verify_local_inventory(lock)

    def test_inventory_unbound_files_and_path_traversal(self):
        lock=self.inventory();root=Path(lock['local_path'])
        (root/'added_tokens.json').write_text('{}')
        with self.assertRaises(Invalid):verify_local_inventory(lock)
        (root/'added_tokens.json').unlink()
        lock['files']['../escape']='0'*64
        with self.assertRaises(Invalid):verify_local_inventory(lock)

    def test_live_label_or_duplicate_scope_cannot_enable_session(self):
        self.transport.evidence='local_runtime_unqualified'
        with self.assertRaises(Invalid):QwenPlannerSession(self.root/'other',self.requests,self.transport)
        self.transport.evidence='injected_offline_double'
        with self.assertRaises(Invalid):QwenPlannerSession(self.root/'other',[self.requests[0]]*3,self.transport)


if __name__=='__main__':unittest.main()
