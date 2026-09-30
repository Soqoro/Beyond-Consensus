"""Synthetic-only probe boundaries, isolation and conservative failure accounting."""
from pathlib import Path
import copy
import json
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from unittest.mock import patch

from beyond_consensus.experiments import rr_v2_preflight as probe
from beyond_consensus.models.base import Generation
from beyond_consensus.util import BCError, digest


class Backend:
    def __init__(self): self.prompts = []; self.fail = False
    def count_input(self, messages):
        return 100 + messages[1]['content'].count('record ') * 25
    def generate(self, messages, cap, seed):
        self.prompts.append(copy.deepcopy(messages))
        if self.fail: raise RuntimeError('unknown usage')
        action = messages[0]['content'].split('no Markdown: ')[1]
        messages[0]['content'] = 'mutated copy'
        return Generation(action, 12, 4, .1, {'constraint_complete': True, 'finish_reason': 'eos'})


class ProbeTests(unittest.TestCase):
    def manifest(self):
        with patch.object(probe, 'check_locks'), patch.object(probe, 'source_revision', return_value='source'):
            return probe.build(Path('.'), {'lock': 'worker'}, {'lock': 'planner'}, 7)

    def test_sequence_isolated_and_revisited_all_pools(self):
        for pool in range(2, 9):
            backend = Backend(); roles = []
            rows = probe.sequence(backend, pool, roles.append, lambda **kw: {'peak': 1})
            self.assertEqual(len(rows), 2*(pool+1))
            self.assertTrue(all(r['passed'] for r in rows))
            self.assertEqual(len({r['prompt_hash'] for r in rows}), pool+1)
            self.assertEqual(backend.prompts[:pool+1], backend.prompts[pool+1:])
            self.assertEqual(roles.count('plan'), 2)
            self.assertTrue(all(14080 <= r['input_tokens'] <= 14336 for r in rows))

    def test_failure_stops_and_reserves_unknown_tokens(self):
        backend = Backend(); backend.fail = True
        rows = probe.sequence(backend, 7, lambda _: None, lambda **kw: {})
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]['passed'])
        self.assertEqual(rows[0]['uncertain_tokens'], rows[0]['input_tokens']+2048)

    def test_wrong_action_and_truncation_not_passed(self):
        for text, diagnostics in [('{}', {'constraint_complete': True, 'finish_reason': 'eos'}),
                                 ('{}', {'constraint_complete': False, 'finish_reason': 'length_limit'})]:
            backend = Backend()
            backend.generate = lambda *args: Generation(text, 2048, None, 0, diagnostics)
            rows = probe.sequence(backend, 2, lambda _: None, lambda **kw: {})
            self.assertFalse(any(r['passed'] for r in rows))

    def test_manifest_preflight_only_and_source_bound(self):
        m = self.manifest()
        self.assertEqual(probe.validate(m).shards, 1)
        with patch.object(probe, 'source_revision', return_value='source'), patch.object(probe, 'check_locks'):
            probe.check_submission(m, {}, Path('.'), 'preflight', 1)
            for mode, concurrency in [('run', 1), ('preflight', 2)]:
                with self.assertRaises(BCError): probe.check_submission(m, {}, Path('.'), mode, concurrency)
        with patch.object(probe, 'source_revision', return_value='changed'):
            with self.assertRaises(BCError): probe.check_submission(m, {}, Path('.'), 'preflight', 1)
        m['pool'] = 8
        with self.assertRaises(BCError): probe.validate(m)

    def test_task_runner_rejects_without_loading(self):
        from beyond_consensus.experiments.runner import run_manifest
        with self.assertRaisesRegex(BCError, "cannot run task"):
            run_manifest(self.manifest(), Path("/unused"), Path("."))

    def test_lock_pair_and_hash(self):
        lock = {k: 'same' for k in ('checkpoint','revision','tokenizer_revision','model_path',
                                   'tokenizer_path','metadata_hashes','weight_hashes')}
        m = self.manifest(); m.update(model_lock_sha256=digest(lock), planner_lock=copy.deepcopy(lock))
        with patch('beyond_consensus.models.competence.require_qualification') as qualify:
            probe.check_locks(m, lock)
            self.assertEqual(qualify.call_count, 2)
            m['planner_lock']['weight_hashes'] = 'different'
            with self.assertRaises(BCError): probe.check_locks(m, lock)
        with self.assertRaises(BCError): probe.check_locks(m, {})


class StressTests(unittest.TestCase):
    def test_full_budget_requires_all_geometry_evidence(self):
        from beyond_consensus.models.rr_memory_stress import verified
        good = dict(rendered_input_tokens=14336, observed_cache_sequence_length=16383,
                    forced_token_verified=True, force_mask_calls=2048)
        self.assertTrue(verified(good, 2048))
        self.assertFalse(verified(good, 2047))
        for key in good:
            bad = dict(good); bad.pop(key)
            self.assertFalse(verified(bad, 2048))
        for key, value in [('rendered_input_tokens', 14324),
                           ('observed_cache_sequence_length', 16382),
                           ('forced_token_verified', False), ('force_mask_calls', 2047)]:
            self.assertFalse(verified(dict(good, **{key: value}), 2048))

    def test_stress_sequence_separate_from_normal_generation(self):
        from beyond_consensus.models.rr_memory_stress import PROTOCOL
        backend = Backend(); roles = []; prompts = []
        def generate(b, messages, cap, seed):
            self.assertIs(b, backend)
            prompts.append(copy.deepcopy(messages))
            return Generation('', 2048, None, 1, dict(stress_protocol=PROTOCOL,
                rendered_input_tokens=14336, observed_cache_sequence_length=16383,
                forced_token_verified=True, force_mask_calls=2048))
        with patch('beyond_consensus.models.rr_memory_stress.generate', side_effect=generate):
            rows = probe.sequence(backend, 7, roles.append, lambda **kw: {}, full_budget_stress=True)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(r['passed'] for r in rows))
        self.assertEqual(sum(r['input_tokens']+r['output_tokens'] for r in rows), 262144)
        self.assertEqual(backend.prompts, [])
        self.assertEqual(prompts[:8], prompts[8:])
        self.assertEqual(roles.count('plan'), 2)
        with patch('beyond_consensus.models.rr_memory_stress.generate', side_effect=RuntimeError('OOM')):
            rows = probe.sequence(backend, 7, roles.append, lambda **kw: {}, full_budget_stress=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['uncertain_tokens'], 16384)
        self.assertFalse(rows[0]['passed'])

    def test_stress_has_new_manifest_identity_and_no_task_permission(self):
        with patch.object(probe, 'check_locks'), patch.object(probe, 'source_revision', return_value='source'):
            normal = probe.build(Path('.'), {'a': 1}, {'a': 2}, 7)
            stress = probe.build(Path('.'), {'a': 1}, {'a': 2}, 7, full_budget_stress=True)
        self.assertNotEqual(normal['experiment_id'], stress['experiment_id'])
        self.assertNotEqual(normal['protocol'], stress['protocol'])
        self.assertFalse(stress['task_execution_allowed'])
        probe.validate(stress)
        with self.assertRaises(BCError):
            probe.check_submission(stress, {}, Path('.'), 'run', 1)

    def test_force_processor_preserves_only_inert_token(self):
        from beyond_consensus.models.rr_memory_stress import ForceInertToken
        class Scores:
            def __init__(self): self.values = [[1, 9, 3], [4, 8, 6]]
            def fill_(self, value): self.values = [[value]*3 for _ in range(2)]
            def __setitem__(self, key, value):
                for row in self.values: row[key[1]] = value
        scores = Scores(); processor = ForceInertToken(2)
        self.assertIs(processor(None, scores), scores)
        self.assertEqual(scores.values, [[float('-inf'), float('-inf'), 0]]*2)
        self.assertEqual(processor.calls, 1)
