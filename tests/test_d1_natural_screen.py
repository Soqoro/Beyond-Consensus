"""Small synthetic batch; zero dataset/model/tokenizer/native solver access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bc_phase2 import d1_natural_screen as n
from bc_phase2.model import Invalid
from test_phase2_planner_qwen import Tokenizer,Model,Torch


def response(count=2,source='mock:0'):
    return {'schema':n.VERSION,'source_id':source,'status':'single_task' if count==1 else 'decomposed',
            'tasks':[{'id':f'T{i}','responsibility':f'Derive symbolic intermediate {i}',
                      'required_inputs':['problem_statement' if i==1 else f'T{i-1}'],
                      'produces':f'Symbolic relation {i}'} for i in range(1,count+1)],
            'final_assembly':f'Use [T{count}] to answer the question; no value supplied.'}


class Parser(unittest.TestCase):
    def test_counts_one_two_three_and_more(self):
        for count in (1,2,3,4,8,12):
            r=n.parse_response(json.dumps(response(count)),'mock:0')
            self.assertEqual(r['proposed_task_count'],count);self.assertIsNone(r['meaningful_task_count'])
        r=n.parse_response(json.dumps(dict(schema=n.VERSION,source_id='mock:0',status='unsupported',tasks=[],reason='No justified task')),'mock:0')
        self.assertEqual(r['proposed_task_count'],0)

    def test_invalid_cycle_dangling_unused_duplicate_status_and_extra(self):
        mutations=[lambda r:r['tasks'][0]['required_inputs'].__setitem__(0,'T2'),
                   lambda r:r['tasks'][1]['required_inputs'].__setitem__(0,'T9'),
                   lambda r:r.update(final_assembly='Use [T1].'),
                   lambda r:r['tasks'][1].update(id='T1'),lambda r:r.update(status='single_task'),
                   lambda r:r.update(answer='42'),lambda r:r['tasks'][0].update(cost=7),
                   lambda r:r.update(final_assembly='Use [T99].')]
        for mutate in mutations:
            r=response();mutate(r)
            self.assertEqual(n.review_response(json.dumps(r),'mock:0')['status'],'invalid')
        raw=json.dumps(response()).replace('"schema":', '"schema":"duplicate","schema":',1)
        self.assertEqual(n.review_response(raw,'mock:0')['status'],'invalid')

    def test_source_and_protected_input_isolation(self):
        for key in ('answer','solution','reviewer_decomposition','costs'):
            with self.assertRaises(Invalid):n.request({'id':'mock:0','problem':'x',key:'protected'})
        r=n.request({'id':'mock:0','problem':'x'})
        self.assertEqual(set(r['payload']['source']),{'id','problem'})
        self.assertNotIn('joint-domain-v1',json.dumps(r))
        self.assertEqual(n.review_response(json.dumps(response()),'mock:other')['status'],'invalid')


class Ledger(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.records=[{'id':f'mock:{i}','problem':'Synthetic problem'} for i in range(3)]
        self.tok=Tokenizer();self.model=Model();self.model.generated=[7,9]
        self.transport=n.NaturalTransport(self.tok,self.model,Torch())
        self.path=Path(self.tmp.name)/'run';self.session=n.NaturalMockSession(self.path,self.records,self.transport)

    def test_three_terminal_calls_counts_raw_and_no_correction(self):
        for i,count in enumerate((1,2,3)):
            raw=json.dumps(response(count,source=f'mock:{i}'));self.tok.final=raw
            row=self.session.advance(f'mock:{i}')
            self.assertEqual(row['review']['proposed_task_count'],count)
            self.assertEqual(row['raw_response'],raw);self.assertEqual(row['actual_tokens'],7)
            self.assertEqual(row['reservation_tokens'],3077)
            self.assertEqual(self.model.calls[-1]['max_new_tokens'],3072)
        self.assertEqual(self.session.snapshot()['totals']['simulated_actual_tokens'],21)
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(len(self.model.calls),3)

    def test_invalid_response_continues_to_next_without_retry(self):
        self.tok.final='{}';r=self.session.advance('mock:0');self.assertEqual(r['state'],'invalid_response')
        again=n.NaturalMockSession(self.path,self.records,self.transport)
        with self.assertRaises(Invalid):again.advance('mock:0')
        self.tok.final=json.dumps(response(source='mock:1'))
        self.assertEqual(again.advance('mock:1')['state'],'completed')

    def test_crash_keeps_reservation(self):
        def crash():raise RuntimeError('possible dispatch')
        self.model.before=crash
        with self.assertRaises(RuntimeError):self.session.advance('mock:0')
        again=n.NaturalMockSession(self.path,self.records,self.transport)
        self.assertEqual(again.snapshot()['totals']['simulated_reserved_tokens'],3077)
        with self.assertRaises(Invalid):again.advance('mock:0')

    def test_unknown_usage_stops_but_reliable_truncation_continues(self):
        for index,usage in enumerate((None,3072)):
            session=n.NaturalMockSession(Path(self.tmp.name)/str(index),self.records,self.transport)
            obs={'input_tokens':5,'output_tokens':usage,'final_text':'{}','raw_decoded':'{}',
                 'finish_reason':'length_limit','boundary_error':None}
            with patch.object(self.transport,'generate',return_value=obs):r=session.advance('mock:0')
            self.assertEqual(r['state'],'uncertain' if usage is None else 'response_boundary_error')
            if usage is None:
                with self.assertRaises(Invalid):session.advance('mock:1')
            else:
                self.tok.final=json.dumps(response(source='mock:1'))
                self.assertEqual(session.advance('mock:1')['state'],'completed')

    def test_non_thinking_is_verified_no_silent_fallback(self):
        self.model.generated=[6,8,7,9];self.tok.final=json.dumps(response())
        r=self.session.advance('mock:0');self.assertEqual(r['state'],'response_boundary_error')
        self.assertEqual(r['observation']['boundary_error'],'unexpected_generated_thinking')
        with patch.object(self.tok,'apply_chat_template',return_value='same <think>'):
            with self.assertRaises(Exception):n.NaturalTransport(self.tok,self.model,Torch())

    def test_order_input_overflow_and_real_ids_blocked(self):
        with self.assertRaises(Invalid):self.session.advance('mock:1')
        self.tok.input_length=13313
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(self.session.snapshot()['attempts'],[])
        real=[dict(r,id=s) for r,s in zip(self.records,n.SMOKE)]
        with self.assertRaises(Invalid):n.NaturalMockSession(Path(self.tmp.name)/'real',real,self.transport)

    def test_unknown_finish_resource_breach_and_unresolved_reservation_halt(self):
        for i,(out,finish) in enumerate(((2,'unknown'),(3073,'eos'),(2,'length_limit'))):
            session=n.NaturalMockSession(Path(self.tmp.name)/('halt'+str(i)),self.records,self.transport)
            obs={'input_tokens':5,'output_tokens':out,'finish_reason':finish,
                 'final_text':'{}','raw_decoded':'{}','boundary_error':None}
            with patch.object(self.transport,'generate',return_value=obs):session.advance('mock:0')
            with self.assertRaises(Invalid):session.advance('mock:1')

    def test_unsupported_and_semantic_quality_do_not_gate_next(self):
        self.tok.final=json.dumps(dict(schema=n.VERSION,source_id='mock:0',status='unsupported',tasks=[],reason='No decomposition'))
        first=self.session.advance('mock:0')
        self.assertTrue(n.reliable_terminal(first))
        self.tok.final=json.dumps(response(source='mock:1'))
        second=self.session.advance('mock:1')
        self.assertEqual(second['review']['semantic_review'],'pending')
        self.tok.final=json.dumps(response(source='mock:2'))
        self.assertEqual(self.session.advance('mock:2')['state'],'completed')
        with self.assertRaises(Invalid):self.session.advance('mock:0')

    def test_disabled_preflight_rejects_old_approval_or_flag(self):
        manifest=n.disabled_manifest();p=n.preflight(manifest)
        self.assertEqual([r['source_id'] for r in p['rows']],list(n.SMOKE))
        self.assertFalse(p['execution_allowed']);self.assertEqual(p['model_calls'],0)
        with self.assertRaises(Invalid):n.open_live(manifest,approval={'decision':'approved'})
        manifest['execution_allowed']=True
        with self.assertRaises(Invalid):n.preflight(manifest)

if __name__=='__main__':unittest.main()
