"""Bounded unique-key preflight routing, accounting and no-tool controls."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

from tests.support import ROOT
from beyond_consensus.experiments import rr_unique_preflight as probe
from beyond_consensus.experiments.manifest import validate_manifest
from beyond_consensus.models.base import Generation
from beyond_consensus.util import BCError, digest


class Backend:
    def __init__(self, error=None, text=None):self.calls=[];self.error=error;self.text=text
    def count_input(self, messages):return 100 + messages[-1]['content'].count('record ')*10
    def generate(self, messages, cap, seed):
        self.calls.append((deepcopy(messages),cap,seed))
        if self.error:raise self.error
        text = messages[0]['content'].split('no Markdown: ',1)[1] if self.text is None else self.text
        return Generation(text, 100, 20, 0, dict(finish_reason='eos',constraint_complete=True,constraint_cpu_seconds=.2))


def manifest():
    m=dict(schema=probe.SCHEMA,protocol=probe.PROTOCOL,model=asdict(probe.model()),
        cases=probe.cases(),maximum_calls=3,maximum_logical_tokens=49152,cpu_cap_per_call=1200,
        shards=1,episodes=[],planned_episodes=0,task_inputs_used=False,task_execution_allowed=False,
        worst_case_fit_established=False,source_revision='test',controls={},model_lock_sha256=digest({}))
    m['experiment_id']=digest(m)
    return m


class UniquePreflight(unittest.TestCase):
    def test_frozen_bounds_cannot_expand_even_when_rehashed(self):
        self.assertEqual(validate_manifest(manifest()).model.action_constraint,probe.MODE)
        for key,value in [('maximum_calls',4),('task_inputs_used',True),('episodes',[{}]),('maximum_logical_tokens',99999),('cases',[])]:
            m=manifest();m[key]=value;m['experiment_id']=digest({k:v for k,v in m.items() if k!='experiment_id'})
            with self.subTest(key=key), self.assertRaises(BCError):probe.validate(m)

    def test_three_calls_long_input_and_accounting_without_action_execution(self):
        backend=Backend();saved=[]
        rows=probe.sequence(backend,lambda reset:dict(reset=reset),lambda rows:saved.append(deepcopy(rows)))
        self.assertEqual(len(backend.calls),3)
        self.assertTrue(all(r['passed'] for r in rows))
        self.assertTrue(14080<=rows[-1]['input_tokens']<=14336)
        self.assertTrue(all(cap==2048 and seed==0 for _,cap,seed in backend.calls))
        for row in rows:
            r=row['resources']
            self.assertEqual(r['actual_tokens'],row['input_tokens']+100)
            self.assertEqual(r['reserved_tokens'],0)
            self.assertEqual(r['uncertain_tokens'],0)
        self.assertTrue(any(s and s[-1]['resources']['reserved_tokens'] for s in saved))

    def test_generation_error_retains_unknown_tokens_and_stops(self):
        backend=Backend(error=RuntimeError('synthetic'))
        rows=probe.sequence(backend,lambda reset:{},lambda rows:None)
        self.assertEqual(len(backend.calls),1)
        self.assertEqual(rows[0]['status'],'error')
        self.assertEqual(rows[0]['failure_stage'],'generation')
        self.assertEqual(rows[0]['error_message'],'synthetic')
        self.assertEqual(rows[0]['error_frames'][-1]['function'],'generate')
        self.assertGreater(rows[0]['resources']['uncertain_tokens'],0)
        self.assertFalse(rows[0]['passed'])

    def test_interrupt_retains_checkpoint(self):
        saved=[]
        with self.assertRaises(KeyboardInterrupt):
            probe.sequence(Backend(error=KeyboardInterrupt()),lambda reset:{},lambda rows:saved.append(deepcopy(rows)))
        self.assertGreater(saved[-1][0]['resources']['uncertain_tokens'],0)
        self.assertEqual(saved[-1][0]['error_type'],'KeyboardInterrupt')

    def test_duplicate_response_fails_despite_completion_metadata(self):
        rows=probe.sequence(Backend(text='{"tool":"finish","tool":"finish"}'),lambda reset:{},lambda rows:None)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r['status']=='not_attempted' for r in rows[1:]))
        self.assertFalse(rows[0]['passed'])
        self.assertEqual(rows[0]['resources']['uncertain_tokens'],0)

    def test_wrong_valid_response_is_not_success(self):
        rows=probe.sequence(Backend(text='{"tool":"finish"}'),lambda reset:{},lambda rows:None)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(not r['passed'] for r in rows))

    def test_submission_preflight_only_and_single_use(self):
        with TemporaryDirectory() as tmp, patch.object(probe,'check'):
            for mode,n in [('run',1),('preflight',2)]:
                with self.assertRaises(BCError):probe.submission(manifest(),ROOT,{},mode,n,tmp)
            probe.submission(manifest(),ROOT,{},'preflight',1,tmp)
            (Path(tmp)/'unique-preflight-started.json').write_text('{}')
            with self.assertRaises(BCError):probe.submission(manifest(),ROOT,{},'preflight',1,tmp)

    def test_loader_failure_is_saved_blocks_retry_and_aggregates(self):
        from beyond_consensus.evaluation.aggregate import aggregate
        with TemporaryDirectory() as tmp, patch.object(probe,'check'):
            root=Path(tmp);lock=root/'lock.json';lock.write_text('{}')
            output=root/'preflight.json';m=manifest()
            with patch('beyond_consensus.models.transformers_backend.TransformersBackend', side_effect=RuntimeError('load')) as loader:
                with self.assertRaises(RuntimeError):probe.run(m,lock,ROOT,output)
                report=aggregate(m,root)
                self.assertEqual(report['status'],'error')
                self.assertEqual(report['failure_stage'],'model_load')
                self.assertEqual(report['error_message'],'load')
                self.assertEqual(report['calls'],[])
                self.assertFalse(report['model_executed'])
                with self.assertRaises(BCError):probe.run(m,lock,ROOT,output)
                self.assertEqual(loader.call_count,1)
            report['manifest_hash']='changed';output.write_text(json.dumps(report))
            with self.assertRaises(BCError):aggregate(m,root)

    def test_changed_source_lock_and_missing_native_controls_rejected(self):
        m=manifest()
        with patch.object(probe,'source_revision',return_value='changed'), self.assertRaises(BCError):probe.check(m,ROOT,{})
        with patch.object(probe,'source_revision',return_value='test'),patch.object(probe,'check_controls'),patch.object(probe,'require_qualification'):
            with self.assertRaises(BCError):probe.check(m,ROOT,{'different':True})
            lock={'decoder_qualification':{}};m['model_lock_sha256']=digest(lock)
            m['experiment_id']=digest({k:v for k,v in m.items() if k!='experiment_id'})
            with self.assertRaises(BCError):probe.check(m,ROOT,lock)

    def test_error_capture_is_bounded_and_has_no_locals(self):
        rows=probe.sequence(Backend(error=RuntimeError('x'*5000)),lambda reset:{},lambda rows:None)
        row=rows[0]
        self.assertEqual(len(row['error_message']),4096)
        self.assertTrue(row['error_message_truncated'])
        self.assertLessEqual(len(row['error_frames']),12)
        self.assertTrue(all(set(f)=={'file','line','function'} for f in row['error_frames']))

    def test_post_generation_memory_error_preserves_known_usage_and_response(self):
        calls=[]
        def memory(reset):
            calls.append(reset)
            if not reset:raise RuntimeError('synthetic device failure')
            return {}
        backend=Backend()
        rows=probe.sequence(backend,memory,lambda rows:None)
        self.assertEqual(calls,[True,False])
        self.assertEqual(len(backend.calls),1)
        self.assertEqual(rows[0]['failure_stage'],'memory_after')
        self.assertEqual(rows[0]['generation']['output_tokens'],100)
        self.assertEqual(rows[0]['resources']['uncertain_tokens'],0)
        self.assertGreater(rows[0]['resources']['actual_tokens'],0)
