"""Reconstructed response diagnostic controls; no model or task execution."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments import rr_response_probe as P
from beyond_consensus.util import BCError,digest


def export():
    x=dict(experiment_id=P.HISTORICAL,public_planner_inputs=[],future_outcome_labels=[])
    for i,(planner,track) in enumerate(P.SELECTION):
        obs=dict(assignment={'outputs':['repository_summary']},worker_history=[])
        row=dict(observation=obs,tool_result={'error':'malformed_json'},actor='w0',stage='primary',unit='mapping',
                 costs=[dict(kind='model_usage',finish_reason='eos',input_tokens=10,output_tokens=8)])
        x['public_planner_inputs'].append(dict(configuration_id=str(i),task=P.TASK,planner=planner))
        b=dict(track=track,branch_id=str(i),trajectories=[row,deepcopy(row)],
               checkpoint={'engine':{'v2_config':{'seeds':{'execution':123}}}},evaluation={'SECRET_GOLD':1})
        x['future_outcome_labels'].append(dict(configuration_id=str(i),result={'branches':[b]}))
    return x


class ResponseProbe(unittest.TestCase):
    def test_selection_first_only_no_gold_no_mutation(self):
        x=export();original=deepcopy(x);cases=P.select(x)
        self.assertEqual(len(cases),3);self.assertTrue(all(c['trajectory_index']==0 for c in cases))
        self.assertNotIn('SECRET_GOLD',json.dumps(cases));self.assertEqual(x,original)
        self.assertNotIn('worker_history',cases[0]['observation'])
        x['future_outcome_labels'][0]['result']['branches'][0]['trajectories'][0]['costs'][0]['finish_reason']='length_limit'
        self.assertEqual(P.select(x)[0]['trajectory_index'],1)

    def test_missing_and_duplicate_selection_rejected(self):
        x=export();x['future_outcome_labels'].pop()
        with self.assertRaises(BCError):P.select(x)
        x=export();x['future_outcome_labels'].append(x['future_outcome_labels'][0])
        with self.assertRaises(BCError):P.select(x)

    def test_three_calls_no_tools_and_separate_accounting(self):
        class Backend:
            calls=[]
            def count_input(self,m):return 10
            def generate(self,m,cap,seed):
                self.calls.append((m,cap,seed))
                return SimpleNamespace(text='{"x":1,"x":2}',output_tokens=8,reasoning_tokens=2,
                    device_seconds=0,diagnostics={'finish_reason':'eos','constraint_complete':True})
        b=Backend();saved=[];rows=P.sequence({'cases':P.select(export())},b,lambda r:saved.append(deepcopy(r)))
        self.assertEqual(len(b.calls),3)
        self.assertTrue(all(c[1:]==(2048,123) for c in b.calls))
        self.assertTrue(all(r['response_diagnostic']['parse_failure']=='duplicate_object_key' for r in rows))
        self.assertEqual(sum(r['resources']['actual_tokens'] for r in rows),54)
        self.assertTrue(any(r[0]['resources']['reserved_tokens']>0 for r in saved))

    def test_parsed_actions_are_never_executed_or_scored(self):
        class Backend:
            def count_input(self,m):return 10
            def generate(self,*a):return SimpleNamespace(text='{"tool":"publish"}',output_tokens=8,
                reasoning_tokens=0,device_seconds=0,diagnostics={})
        with patch('reporecourse.engine.Environment',side_effect=AssertionError('no environment')):
            rows=P.sequence({'cases':P.select(export())},Backend(),lambda r:None)
        self.assertTrue(all(r['parse_accepted'] for r in rows))
        self.assertTrue(all('success' not in r for r in rows))

    def test_context_failure_does_not_dispatch(self):
        class Backend:
            def count_input(self,m):return 15000
            def generate(self,*a):raise AssertionError('must not dispatch')
        rows=P.sequence({'cases':P.select(export())},Backend(),lambda r:None)
        self.assertTrue(all(r['error_category']=='context_limit' for r in rows))
        self.assertEqual(sum(r['resources']['actual_tokens'] for r in rows),0)

    def test_runtime_error_stops_remaining_calls(self):
        class Backend:
            def count_input(self,m):return 10
            def generate(self,*a):raise RuntimeError('private error')
        rows=P.sequence({'cases':P.select(export())},Backend(),lambda r:None)
        self.assertEqual(len(rows),1);self.assertNotIn('private error',json.dumps(rows))
        self.assertEqual(rows[0]['resources']['uncertain_tokens'],2058)

    def test_submission_is_run_only_single_use_and_verified(self):
        m=dict(controls={},base_manifest={'planner_lock':{}},preflight_evidence={'run':'run','snapshots':'snapshots'})
        with TemporaryDirectory() as d,patch.object(P,'check_controls'),patch.object(P,'validate'),patch.object(P.base,'check_submission'),patch.object(P,'preflight_evidence',return_value=m['preflight_evidence']):
            P.submission(m,{},'.','run',1,d)
            for mode,n in [('preflight',1),('run',2)]:
                with self.assertRaises(BCError):P.submission(m,{},'.',mode,n,d)
            (Path(d)/'response-probe-started.json').write_text('{}')
            with self.assertRaises(BCError):P.submission(m,{},'.','run',1,d)

    def test_manifest_rehash_cannot_expand_calls_or_caps(self):
        profile=dict(model={},source_revision='test',model_lock_sha256=digest({}))
        with patch.object(P,'check_controls'),patch.object(P.base,'build',return_value=profile),patch.object(P.base,'validate'),patch.object(P,'source_revision',return_value='test'),patch.object(P,'preflight_evidence',return_value={}):
            m=P.build('.',export(),{},{},'run','snapshots',{})
            P.validate(m)
            for key,value in [('maximum_calls',4),('output_cap',4096),('task_execution_allowed',True),('declared_cpu_caps_total',4000)]:
                bad=deepcopy(m);bad[key]=value
                bad['experiment_id']=digest({k:v for k,v in bad.items() if k!='experiment_id'})
                with self.assertRaises(BCError):P.validate(bad)

    def test_aggregate_routes_and_verifies_saved_report(self):
        from beyond_consensus.evaluation.aggregate import aggregate
        m=dict(schema=P.SCHEMA,experiment_id='test')
        with TemporaryDirectory() as d,patch.object(P,'validate'):
            self.assertEqual(aggregate(m,Path(d))['status'],'missing')
            report=dict(experiment_id='test',manifest_hash=digest(m),status='completed',calls=[])
            (Path(d)/'response-diagnostic.json').write_text(json.dumps(report))
            self.assertEqual(aggregate(m,Path(d)),report)
            report['manifest_hash']='changed'
            (Path(d)/'response-diagnostic.json').write_text(json.dumps(report))
            with self.assertRaises(BCError):aggregate(m,Path(d))

if __name__=='__main__':unittest.main()
