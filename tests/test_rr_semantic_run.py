"""Bounded adapter controls; model doubles never claim GPU competence."""
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from tests.support import ROOT
from beyond_consensus.experiments import rr_semantic_run as run
from beyond_consensus.experiments import rr_semantic_diagnostic as design
from beyond_consensus.experiments.rr_open_clean import seal
from beyond_consensus.util import BCError, digest


def manifest():
    m = dict(schema=run.SCHEMA, source_revision='test', model=run.model_settings(),
        model_lock_sha256='lock', implementation_hashes={}, evidence={}, cases=list(run.CASES),
        maximum_calls=3, model_planner_calls=0, seed=0, pool=7, context_limit=16384,
        output_cap=2048, token_cap=16384, cpu_cap=1200, evaluator_cpu_cap=1200,
        shards=1, episodes=[], planned_episodes=0, task_execution_allowed=False, approval=None,
        limitations=run.LIMITATIONS, historical_scores_changed=False, confirmatory=False)
    seal(m)
    return m


def measured():
    return {'cases': [dict(id=i, messages_hash=digest(run.messages(i)), input_tokens=100) for i in run.CASES]}


class Backend:
    def __init__(self, mode='correct'):
        self.calls = 0
        self.mode = mode
        self.prompts = []

    def count_input(self, prompt):
        self.prompts.append(copy.deepcopy(prompt))
        return 100

    def generate(self, prompt, cap, seed):
        case = run.CASES[self.calls]
        self.calls += 1
        if self.mode == 'crash':
            raise RuntimeError('synthetic device error')
        if self.mode == 'interrupt':
            raise KeyboardInterrupt()
        action = design.authored_action(case)
        text = json.dumps(action)
        if self.mode == 'malformed':
            text = '{'
        if self.mode == 'wrong_tool':
            text = '{"tool":"list_sources"}'
        if self.mode == 'duplicate':
            text = '{"tool":"publish","tool":"finish"}'
        return SimpleNamespace(text=text, output_tokens=30, reasoning_tokens=5, device_seconds=0,
            diagnostics={'finish_reason': 'length_limit' if self.mode == 'length' else 'eos',
                         'constraint_complete': self.mode != 'length'})


def fake_environment(case, resources=None):
    env = REAL_ENV(case, resources)
    def action(worker, value):
        env.bound['report'] = 'synthetic-version'
        return {'version': 'synthetic-version'}
    env.action = action
    env.check_public = lambda: {'report': True}
    if case == 'mapping_keys':
        env.execute = lambda *a: {'status': 'ok', 'output': {'labels': ['alpha'], 'size_bytes': {'X': 4}}}
    else:
        indices = [0, 1, 2, 3] if case == 'order_grain' else [0, 4, 5]
        env.execute = lambda *a: {'status': 'ok', 'outputs': [{
            'columns': env.public['required_outputs'][0]['columns'],
            'rows': [[r[i] for i in indices] for r in design.reference(design.fixtures())]}]}
    return env

REAL_ENV = design.environment


class Scope(unittest.TestCase):
    def test_exact_approval_and_changed_caps(self):
        m = manifest()
        receipt = run.approval_template(m)
        receipt.update(decision='approved', reviewer='test', reviewed_at='2026-10-16')
        with patch.object(run, 'verify'):
            approved = run.authorize(m, receipt, ROOT, {})
        self.assertTrue(approved['task_execution_allowed'])
        self.assertNotEqual(approved['experiment_id'], m['experiment_id'])
        run.validate(approved)
        for key, value in [('maximum_calls',4), ('output_cap',4096), ('seed',True)]:
            changed = copy.deepcopy(approved); changed[key] = value; seal(changed)
            with self.assertRaises(BCError):
                run.validate(changed)
        changed = copy.deepcopy(approved); changed['approval']['maximum_calls'] = 4; seal(changed)
        with self.assertRaises(BCError):
            run.validate(changed)

    def test_started_attempt_and_pending_approval(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(run, 'verify'):
            m = manifest()
            with self.assertRaisesRegex(BCError, 'approval'):
                run.submission(m, {}, ROOT, 'run', 1, tmp)
            m['task_execution_allowed'] = True
            Path(tmp, 'semantic-started.json').write_text('started')
            with self.assertRaisesRegex(BCError, 'no retry'):
                run.submission(m, {}, ROOT, 'run', 1, tmp)
            with self.assertRaises(BCError):
                run.submission(m, {}, ROOT, 'preflight', 1, tmp)
            with self.assertRaises(BCError):
                run.submission(m, {}, ROOT, 'run', 2, tmp)

    def test_runtime_rejects_retry_before_loading(self):
        with self.assertRaisesRegex(BCError, 'retry'):
            run.run({}, Path('/unused'), ROOT, model_lock=None, retry_failures=True)
        with patch.dict(os.environ, {'CUDA_LAUNCH_BLOCKING':'1'}):
            with self.assertRaisesRegex(BCError, 'asynchronous'):
                run.run({}, Path('/unused'), ROOT, model_lock=None)

    def test_backend_injection_and_preflight_routes(self):
        from beyond_consensus.experiments.runner import run_manifest
        from beyond_consensus.experiments.manifest import validate_manifest
        with self.assertRaisesRegex(BCError, 'injected'):
            run_manifest({'schema':run.SCHEMA}, Path('/unused'), ROOT, backend=object())
        self.assertEqual(validate_manifest(manifest()).shards, 1)

    def test_public_messages_are_deterministic_and_reference_free(self):
        for case in run.CASES:
            first = run.messages(case)
            self.assertEqual(first, run.messages(case))
            text = json.dumps(first)
            self.assertNotIn('COUNT(DISTINCT', text)
            self.assertNotIn('semantic_correct', text)
            self.assertNotIn('wrong_keys', text)
            self.assertIn('synthetic_sources', text)
            self.assertIn('diagnostic_caps', text)

    def test_production_report_missing_and_tampered_fail_closed(self):
        with self.assertRaises(BCError):
            run.check_production({'schema':'rr-semantic-production-controls-v1', 'status':'passed'})

    def test_aggregate_preserves_unrun_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = manifest()
            self.assertEqual(run.aggregate(m,tmp)['missing_cases'], list(run.CASES))
            path = Path(tmp)/'semantic-report.json'
            path.write_text(json.dumps(dict(experiment_id=m['experiment_id'], manifest_hash=digest(m), calls=[])))
            self.assertEqual(run.aggregate(m,tmp)['calls'], [])
            path.write_text(json.dumps(dict(experiment_id='changed', manifest_hash=digest(m), calls=[])))
            with self.assertRaises(BCError):
                run.aggregate(m,tmp)


class Sequence(unittest.TestCase):
    def execute(self, mode='correct'):
        backend = Backend(mode); saved=[]; f=measured()
        with patch.object(design, 'environment', side_effect=fake_environment):
            rows = run.sequence(backend, f, saved.append)
        return backend, rows, saved

    def test_three_calls_and_separate_ledgers(self):
        backend, rows, saved = self.execute()
        self.assertEqual(backend.calls, 3)
        self.assertTrue(all(r['complete_in_budget'] for r in rows))
        self.assertTrue(any(r['dispatched'] and 'generation' not in r for s in saved for r in s))
        for row in rows:
            self.assertEqual(row['resources']['actual_tokens'], 130)
            self.assertEqual(row['resources']['uncertain_tokens'], 0)
            self.assertEqual(row['evaluator_resources']['actual_tokens'], 0)
            self.assertGreater(row['evaluator_resources']['cpu_cap_debit'], 0)
            self.assertEqual(row['status'], 'completed')
        for prompt in backend.prompts:
            self.assertNotIn('semantic_correct', json.dumps(prompt))

    def test_malformed_and_duplicate_responses_are_not_repaired(self):
        for mode in ('malformed','duplicate'):
            backend, rows, saved = self.execute(mode)
            self.assertEqual(backend.calls, 3)
            self.assertTrue(all(r['status']=='rejected' for r in rows))
            self.assertTrue(all(r['resources']['actual_tokens']==130 for r in rows))
            self.assertTrue(all(r['semantic_correct'] is None for r in rows))

    def test_device_error_retains_uncertainty_and_stops(self):
        backend, rows, saved = self.execute('crash')
        self.assertEqual(backend.calls, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'infrastructure_failed')
        self.assertGreater(rows[0]['resources']['uncertain_tokens'], 0)

    def test_interruption_retains_inflight_usage(self):
        saved=[]; backend=Backend('interrupt'); f=measured()
        with patch.object(design, 'environment', side_effect=fake_environment):
            with self.assertRaises(KeyboardInterrupt):
                run.sequence(backend, f, saved.append)
        self.assertEqual(saved[-1][0]['status'], 'interrupted')
        self.assertGreater(saved[-1][0]['resources']['uncertain_tokens'], 0)

    def test_prompt_mismatch_prevents_dispatch(self):
        backend=Backend(); f=measured(); f['cases'][0]['messages_hash']='wrong'
        with patch.object(design, 'environment', side_effect=fake_environment):
            rows=run.sequence(backend,f,lambda r:None)
        self.assertEqual(backend.calls,0)
        self.assertEqual(rows[0]['status'],'infrastructure_failed')

    def test_length_limit_is_an_observation_not_a_retry(self):
        backend, rows, _ = self.execute('length')
        self.assertEqual(backend.calls, 3)
        self.assertTrue(all(r['status']=='rejected' and r['error_category']=='incomplete_generated_response' for r in rows))
        self.assertTrue(all(r['resources']['actual_tokens']==130 for r in rows))

    def test_actual_model_double_to_production_executor(self):
        from tests.test_reporecourse import optional
        if not optional():
            self.skipTest('pinned SQLGlot/jsonschema/referencing required')
        backend = Backend()
        rows = run.sequence(backend, measured(), lambda r:None)
        self.assertEqual(backend.calls, 3)
        self.assertTrue(all(r['complete_in_budget'] for r in rows), rows)
        self.assertTrue(all(r['public_monitor_passed'] for r in rows))

    def test_wrong_tool_never_executed(self):
        backend,rows,_=self.execute('wrong_tool')
        self.assertFalse(any(r['complete_in_budget'] for r in rows))
        self.assertTrue(all(r['semantic_correct'] is None for r in rows))

    def test_completed_wrong_semantics_are_distinct_from_public_pass(self):
        backend=Backend(); f=measured()
        with patch.object(design,'environment',side_effect=fake_environment), patch.object(design,'semantic_check',return_value=False):
            rows=run.sequence(backend,f,lambda r:None)
        self.assertTrue(all(r['status']=='completed' and r['public_monitor_passed'] for r in rows))
        self.assertFalse(any(r['complete_in_budget'] for r in rows))


if __name__=='__main__':
    unittest.main()
