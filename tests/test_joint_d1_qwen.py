"""Synthetic D1 joint adapter tests; no dataset, native solver or real model."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bc_phase2.model import Invalid, digest
from bc_phase2.joint_fixtures import graph_fixture
from bc_phase2.joint_pipeline_contracts import blueprint_wire
from bc_phase2.joint_d1_qwen import (JointQwenSession, configuration, preflight,
    approval_matches, open_live, mock_request, CORRECTION_PROMPT, NEUTRAL_PROMPT)
from bc_phase2.planner_qwen import QwenTransport
from test_phase2_planner_qwen import Tokenizer, Model, Torch

ROOT=Path(__file__).resolve().parents[1]
UNSUPPORTED=json.dumps(dict(schema='joint-blueprint-v1',status='unsupported',reason='synthetic'))


def plan(source='mock:0',m=4):
    domain=graph_fixture(4,m,2);domain['source']['id']=source
    for s in domain['sources']:s['value']=None
    return json.dumps(dict(schema='joint-blueprint-v1',status='plan',blueprint=blueprint_wire(domain)))


class JointD1Qwen(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'run'
        self.records=[dict(id=f'mock:{i}',problem='Synthetic independent responsibilities.') for i in range(3)]
        self.tokenizer=Tokenizer();self.model=Model()
        self.transport=QwenTransport(self.tokenizer,self.model,Torch())
        self.tokenizer.final=plan()
        self.session=JointQwenSession(self.path,self.records,self.transport)

    def test_valid_joint_plan_frozen_prompt_and_reasoning_usage(self):
        row=self.session.advance('mock:0')
        self.assertEqual(row['review']['status'],'structurally_valid')
        self.assertEqual(row['actual_tokens'],9) # five input + reasoning/close/final/EOS
        self.assertEqual(row['observation']['reasoning_tokens'],2)
        self.assertEqual(row['outbound_payload']['prompt'],NEUTRAL_PROMPT)
        self.assertFalse(row['admitted']);self.assertFalse(row['model_executed'])
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(len(self.model.calls),1)

    def test_correction_uses_frozen_prompt_and_only_structural_error(self):
        self.tokenizer.final='{}';first=self.session.advance('mock:0')
        self.assertEqual(first['review']['status'],'invalid')
        self.tokenizer.final=plan();row=self.session.advance('mock:0')
        self.assertEqual(row['review']['status'],'structurally_valid')
        self.assertEqual(row['outbound_payload']['correction_prompt'],CORRECTION_PROMPT)
        self.assertEqual(row['outbound_payload']['first_response'],'{}')
        with self.assertRaises(Invalid):self.session.advance('mock:0')

    def test_second_invalid_terminal_and_global_six_call_bound(self):
        self.tokenizer.final='{}'
        for record in self.records:
            for _ in range(2):self.session.advance(record['id'])
        self.assertEqual(len(self.model.calls),6)
        with self.assertRaises(Invalid):self.session.advance('mock:0')

    def test_unsupported_terminal_after_restart(self):
        self.tokenizer.final=UNSUPPORTED;self.session.advance('mock:0')
        again=JointQwenSession(self.path,self.records,self.transport)
        with self.assertRaises(Invalid):again.advance('mock:0')
        self.assertEqual(len(self.model.calls),1)

    def test_reserved_before_generate_crash_blocks_every_source_on_restart(self):
        def crash():
            saved=json.loads(self.session.path.read_text())['state']
            self.assertEqual(saved['attempts'][0]['state'],'reserved')
            raise RuntimeError('interrupted after possible dispatch')
        self.model.before=crash
        with self.assertRaises(RuntimeError):self.session.advance('mock:0')
        again=JointQwenSession(self.path,self.records,self.transport)
        self.assertEqual(again.snapshot()['totals']['simulated_reserved_tokens'],6149)
        for record in self.records:
            with self.assertRaises(Invalid):again.advance(record['id'])

    def test_uncertain_and_excess_usage_halt(self):
        for index,usage in enumerate((None,True,-1,6145)):
            session=JointQwenSession(Path(self.temp.name)/str(index),self.records,self.transport)
            observation=dict(input_tokens=5,output_tokens=usage,final_text=UNSUPPORTED,
                             raw_decoded=UNSUPPORTED,boundary_error=None,finish_reason='eos')
            with patch.object(self.transport,'generate',return_value=observation):session.advance('mock:0')
            with self.assertRaises(Invalid):session.advance('mock:1')
            if usage==6145:self.assertEqual(session.snapshot()['totals']['simulated_actual_tokens'],6150)
            else:self.assertEqual(session.snapshot()['totals']['simulated_reserved_tokens'],6149)

    def test_input_overflow_before_reservation(self):
        self.tokenizer.input_length=10241
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(self.session.snapshot()['attempts'],[])
        self.assertEqual(self.model.calls,[])

    def test_protected_fields_and_benchmark_ids_rejected(self):
        for field in ('answer','solution','reviewer_material','future_replay_bills'):
            with self.assertRaises(Invalid):mock_request(dict(self.records[0],**{field:'PRIVATE'}))
        with self.assertRaises(Invalid):mock_request(dict(id='test/algebra/2743.json',problem='invented'))
        row=self.session.advance('mock:0')
        self.assertNotIn('PRIVATE',json.dumps(row['outbound_payload']))

    def test_generated_trusted_values_and_wrong_source_rejected(self):
        d=json.loads(plan());d['blueprint']['sources'][0]['value']='solved value'
        self.tokenizer.final=json.dumps(d)
        self.assertEqual(self.session.advance('mock:0')['review']['status'],'invalid')
        self.tokenizer.final=plan(source='mock:other')
        self.assertEqual(self.session.advance('mock:0')['review']['status'],'invalid')

    def test_length_or_reasoning_boundary_does_not_authorize_correction(self):
        self.model.generated=[6,7,9] # missing thinking close
        self.session.advance('mock:0')
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        with self.assertRaises(Invalid):self.session.advance('mock:1')

    def test_binding_change_and_corrupt_ledger_no_reset(self):
        records=copy.deepcopy(self.records);records[0]['problem']='changed'
        with self.assertRaises(Invalid):JointQwenSession(self.path,records,self.transport)
        self.session.path.write_text('{}')
        with self.assertRaises(Invalid):JointQwenSession(self.path,self.records,self.transport)

    def test_global_wall_limit(self):
        with self.session._locked():
            state=self.session._read();state['started_at']-=3601;self.session._save(state)
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(self.model.calls,[])

    def test_scope_approval_nonrecursive_and_no_live_dispatch(self):
        cfg=configuration(ROOT);old=cfg['scope_digest']
        approval=dict(schema='joint-d1-qwen-approval-v1',stage='D1',decision='approved',
                      scope_digest=old,reviewer='offline-test-only',reviewed_at='fixture-time')
        cfg['approval']=approval
        self.assertEqual(cfg['scope_digest'],old)
        self.assertTrue(approval_matches(cfg,approval,ROOT))
        self.assertFalse(preflight(cfg,ROOT)['execution_allowed'])
        with self.assertRaises(Invalid):open_live(cfg)
        for key,value in [('stage','D2'),('scope_digest','wrong'),('decision','pending')]:
            bad=dict(approval,**{key:value});self.assertFalse(approval_matches(cfg,bad,ROOT))
        for key,value in [('model',{}),('limits',{}),('source_ids',[]),('identities',{})]:
            bad=copy.deepcopy(cfg);bad['scope'][key]=value;bad['scope_digest']=digest(bad['scope'])
            with self.assertRaises(Invalid):preflight(bad,ROOT)
        cfg['enabled']=True
        with self.assertRaises(Invalid):preflight(cfg,ROOT)

    def test_transport_mismatch_rejected_at_construction(self):
        self.transport.binding['revision']='other'
        with self.assertRaises(Invalid):JointQwenSession(Path(self.temp.name)/'new',self.records,self.transport)

    def test_campaign_token_admission_preserves_prior_accounting(self):
        with self.session._locked():
            state=self.session._read()
            state['attempts']=[dict(state='completed',source_id='mock:1',actual_tokens=98300,
                                    reservation_tokens=98300)]
            self.session._save(state)
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.assertEqual(self.model.calls,[])
        self.assertEqual(self.session.snapshot()['totals']['simulated_actual_tokens'],98300)

    def test_transport_evidence_or_revision_change_blocked(self):
        self.transport.binding['revision']='different'
        with self.assertRaises(Invalid):self.session.advance('mock:0')
        self.transport.evidence='local_runtime_unqualified'
        with self.assertRaises(Invalid):JointQwenSession(Path(self.temp.name)/'new',self.records,self.transport)

if __name__=='__main__':unittest.main()
