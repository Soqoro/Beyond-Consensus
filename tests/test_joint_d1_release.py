"""Synthetic final-scope binding and gated orchestration; no actual data/model."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack

from bc_phase2 import joint_d1_release as release
from bc_phase2 import joint_d1_local as local
from bc_phase2.joint_d1_qwen import settings,limits
from bc_phase2.model import Invalid,digest
from bc_phase2.planner_qwen import QwenTransport
from test_phase2_planner_qwen import Tokenizer,Model,Torch
from test_joint_d1_local import receipt
from test_joint_d1_qwen import plan,UNSUPPORTED

ROOT=Path(__file__).resolve().parents[1]


class FrozenD1(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.records=[{'id':f'mock:{i}','problem':'synthetic fixture only'} for i in range(3)]
        self.path=self.root/'statements.json';self.path.write_text(json.dumps(self.records))
        self.ids=tuple(r['id'] for r in self.records)
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(release,'SMOKE',self.ids))
        self.stack.enter_context(patch.object(local,'SMOKE',self.ids))
        self.stack.enter_context(patch.object(local,'STATEMENTS_HASH',local.file_hash(self.path)))
        self.stack.enter_context(patch.object(local,'STATEMENT_HASHES',{r['id']:hashlib.sha256(r['problem'].encode()).hexdigest() for r in self.records}))
        self.receipt=receipt()
        shards=[f'mock-{i}.safetensors' for i in range(11)]
        files={**local.METADATA,**{s:'1'*64 for s in shards}}
        self.requests=[{'source_id':r['id'],'payload_digest':release._request(r)['payload_digest'],
                        'rendered_ids_digest':digest([1]*5),'input_tokens':5,'output_reservation_tokens':6144} for r in self.records]
        self.report={'schema':'joint-d1-local-verification-v1','status':'local_inventory_and_initial_tokenization_observed',
            'receipt_digest':digest(self.receipt),'source_ids':list(self.ids),'statements_file_sha256':local.STATEMENTS_HASH,
            'statement_hashes':dict(local.STATEMENT_HASHES),'implementation':dict(release.VERIFIED_BASE_IMPLEMENTATION),
            'accounting':{'ledger':'offline_preparation_not_model_usage','cpu_seconds':0.25,'wall_seconds':0.5},
            'local_path':self.receipt['model_path'],'checkpoint':release.CHECKPOINT,'revision':release.REVISION,
            'inventory':{'files':files,'weight_shards':shards,'weight_bytes':11,'weight_hashes_observed':True,'trusted_weight_reference_compared':False},
            'template':{'template_hash':local.TEMPLATE_HASH,'reasoning_requested':True,'reasoning_support_verified':True,'probe_on_hash':'2'*64,'probe_off_hash':'3'*64},
            'generation_tokens':{'eos_token_id':[248046,248044],'pad_token_id':248044},'packages':dict(local.VERSIONS),
            'initial_requests':deepcopy(self.requests),'correction_fit':'checked_at_dispatch_not_worst_case_qualified',
            'model_executed':False,'execution_allowed':False,'gpu_used':False,'worst_case_fit_established':False}

    def freeze(self):return release.freeze(ROOT,self.receipt,self.report,self.path)

    def session(self):
        self.tokenizer=Tokenizer();self.model=Model();self.tokenizer.final=UNSUPPORTED
        transport=QwenTransport(self.tokenizer,self.model,Torch())
        scope={'source_ids':list(self.ids),'model':settings(),'limits':limits(),
               'verification':{'initial_requests':deepcopy(self.requests)}}
        return release.BoundD1Session(self.root/'run',scope,self.records,transport)

    def test_freeze_report_consumes_full_evidence_and_stays_disabled(self):
        manifest=self.freeze();r=release.review(ROOT,manifest)
        self.assertFalse(r['execution_allowed']);self.assertFalse(r['approval_matches'])
        self.assertEqual(r['source_ids'],list(self.ids))
        self.assertEqual(manifest['scope']['verification'],self.report)
        self.assertNotIn('problem',json.dumps(manifest))

    def test_incomplete_summary_wrong_inventory_or_binding_rejected(self):
        for key,value in [('inventory',{}),('implementation',{}),('receipt_digest','0'*64),
            ('source_ids',list(reversed(self.ids))),('generation_tokens',{}),('model_executed',True),
            ('packages',{}),('statement_hashes',{}),('initial_requests',[])]:
            report=deepcopy(self.report);report[key]=value
            with self.subTest(key=key),self.assertRaises(Invalid):release.freeze(ROOT,self.receipt,report,self.path)
        self.report['initial_requests'][0]['payload_digest']='a'*64
        with self.assertRaises(Invalid):self.freeze()

    def test_verified_source_mutation_or_protected_field_rejected(self):
        self.path.write_text(json.dumps([dict(self.records[0],answer='hidden')]+self.records[1:]))
        with self.assertRaises(Invalid):self.freeze()

    def test_approval_is_nonrecursive_scoped_and_cannot_open_gate(self):
        m=self.freeze();h=m['scope_digest']
        approval={'schema':'joint-d1-frozen-approval-v1','stage':'D1','decision':'approved',
                  'scope_digest':h,'reviewer':'fixture','reviewed_at':'fixture','statement_transmission_authorized':True}
        m['approval']=approval
        self.assertTrue(release.approval_matches(ROOT,m,approval));self.assertEqual(m['scope_digest'],h)
        self.assertFalse(release.review(ROOT,m)['execution_allowed'])
        for key,value in [('stage','D2'),('scope_digest','0'*64),('statement_transmission_authorized',False)]:
            bad=dict(approval,**{key:value});self.assertFalse(release.approval_matches(ROOT,m,bad))
        with patch.object(release,'open_local',side_effect=AssertionError('loader reached')):
            with self.assertRaises(Invalid):release.dispatch_live(ROOT,m,self.path,self.root/'live')
        self.assertFalse((self.root/'live').exists())

    def test_scope_mutation_rehashed_still_rejected(self):
        for key,value in [('stage','D2'),('policy',{}),('model',{}),('limits',{}),('runtime_implementation',{})]:
            m=self.freeze();m['scope'][key]=value;m['scope_digest']=digest(m['scope'])
            with self.subTest(key=key),self.assertRaises(Invalid):release.review(ROOT,m)

    def test_mock_controller_three_terminal_outputs_and_frozen_order(self):
        s=self.session()
        with self.assertRaises(Invalid):s.advance('mock:1')
        result=release.drive_session(s)
        self.assertEqual([r['status'] for r in result['sources']],['unsupported']*3)
        self.assertEqual(len(self.model.calls),3);self.assertFalse(result['model_executed'])
        self.assertEqual(result['ledger']['totals']['actual_tokens'],27)
        self.assertFalse(result['halted'])

    def test_controller_only_structural_correction_and_preserves_invalid(self):
        s=self.session();self.tokenizer.final='{}'
        result=release.drive_session(s)
        self.assertEqual(len(self.model.calls),6)
        self.assertEqual([r['status'] for r in result['sources']],['invalid']*3)
        self.assertEqual([r['request_count'] for r in result['sources']],[2]*3)
        self.assertTrue(all(not r['admitted'] for r in result['sources']))

    def test_crash_preserves_reserved_and_unrun_and_no_resume(self):
        s=self.session()
        def crash():raise RuntimeError('interrupted')
        self.model.before=crash
        result=release.drive_session(s)
        self.assertTrue(result['halted']);self.assertEqual([r['status'] for r in result['sources']],['stopped','unrun','unrun'])
        self.assertEqual(result['ledger']['totals']['reserved_tokens'],6149)
        again=release.BoundD1Session(self.root/'run',s.binding['execution_scope'],self.records,s.transport)
        with self.assertRaises(Invalid):again.advance('mock:0')

    def test_initial_render_binding_mismatch_stops_before_request(self):
        s=self.session();self.tokenizer.input_length=6
        result=release.drive_session(s)
        self.assertTrue(result['halted']);self.assertEqual(self.model.calls,[])
        self.assertEqual(result['ledger']['attempts'],[])

    def test_fake_transport_cannot_accept_benchmark_ids(self):
        s=self.session();rows=deepcopy(self.records);rows[0]['id']='test/algebra/2743.json'
        with self.assertRaises(Invalid):release.BoundD1Session(self.root/'other',s.binding['execution_scope'],rows,s.transport)

    def test_prepared_job_body_with_injected_loader_and_watchdog_only(self):
        # Both the release switch and loader are patched only inside this synthetic test.
        from types import SimpleNamespace
        tokenizer=Tokenizer();tokenizer.eos_token_id=248046;tokenizer.pad_token_id=248044
        original=tokenizer.convert_tokens_to_ids
        tokenizer.convert_tokens_to_ids=lambda x:248046 if x=='<eos>' else original(x)
        tokenizer.final=UNSUPPORTED
        model=Model();model.generated=[6,8,7,248046]
        model.generation_config=SimpleNamespace(eos_token_id=[248046,248044],pad_token_id=248044)
        torch=Torch();torch.cuda=SimpleNamespace(synchronize=lambda:None,
            get_device_properties=lambda i:SimpleNamespace(total_memory=85_000_000_000))
        transport=QwenTransport(tokenizer,model,torch,evidence='local_runtime_unqualified')
        self.report['template']=transport.template
        timers=[]
        class Timer:
            def __init__(self,seconds,callback):self.seconds=seconds;self.cancelled=False;timers.append(self)
            def start(self):pass
            def cancel(self):self.cancelled=True
        with patch.object(local,'TEMPLATE_HASH',digest(tokenizer.chat_template)):
            m=self.freeze();m['approval']={'schema':'joint-d1-frozen-approval-v1','stage':'D1','decision':'approved',
                'scope_digest':m['scope_digest'],'reviewer':'fixture','reviewed_at':'fixture','statement_transmission_authorized':True}
            with patch.object(release,'LIVE_RELEASED',True),patch.object(release,'open_local',return_value=transport) as loader,\
                 patch.object(release.threading,'Timer',Timer),\
                 patch('beyond_consensus.models.transformers_backend.require_allocation'):
                result=release.dispatch_live(ROOT,m,self.path,self.root/'job')
                self.assertEqual([r['status'] for r in result['sources']],['unsupported']*3)
                self.assertEqual(len(model.calls),3);self.assertEqual(loader.call_count,1)
                self.assertEqual(timers[0].seconds,3600);self.assertTrue(timers[0].cancelled)
                self.assertTrue((self.root/'job/startup.json').exists())
                with self.assertRaises(FileExistsError):release.dispatch_live(ROOT,m,self.path,self.root/'job')
                self.assertEqual(loader.call_count,1)
        self.assertFalse(release.LIVE_RELEASED)

    def test_evidence_floats_not_blueprint_floats_and_nonfinite_duplicate_rejected(self):
        p=self.root/'evidence.json';p.write_text(json.dumps(self.report))
        self.assertEqual(release.read_evidence(p)['accounting']['cpu_seconds'],0.25)
        for value in ('{"x":1,"x":2}','{"x":NaN}','{"x":1e400}'):
            p.write_text(value)
            with self.assertRaises(Invalid):release.read_evidence(p)
        from bc_phase2.joint_schema import decode
        with self.assertRaises(Invalid):decode('{"x":0.25}')

if __name__=='__main__':unittest.main()
