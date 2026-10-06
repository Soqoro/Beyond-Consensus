"""Offline provenance controls use fabricated test records, never research evidence."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from beyond_consensus.experiments import rr_v2_preflight as probe
from beyond_consensus.experiments.rr_v2_evidence import audit, audit_normal
from beyond_consensus.util import digest, file_hash


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.snapshots = self.root/'snapshots'
        self.normal = self.make('normal', False)
        self.stress = self.make('stress', True)

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def make(self, label, stress, scoped=False, wrong_grammar=False):
        suffix = 'scoped-v1' if scoped and not wrong_grammar else 'v2'
        locks = {}
        for role in ('json', 'plan'):
            locks[role] = dict(checkpoint='Qwen/Qwen3.5-27B',
                revision='fc05daec18b0a78c049392ed2e771dde82bdf654',
                tokenizer_revision='fc05daec18b0a78c049392ed2e771dde82bdf654',
                model_path='/test/model', tokenizer_path='/test/tokenizer',
                metadata_hashes={'config.json': 'fake'}, weight_hashes={'weights': 'fake'},
                decoder_qualification=dict(status='passed', model_executed=False, sql_executed=False,
                    context_limit=16384, contract={'mode': f'reporecourse-{role}-{suffix}-pool-7'},
                    qualification_key=role, packages={'torch': 'test'},
                    effective_generation_tokens={'eos_token_id': [1], 'pad_token_id': 1},
                    thinking_template={'template_hash': 'test'}))
        with patch.object(probe, 'check_locks'), patch.object(probe, 'source_revision', return_value='test-source'):
            m = probe.build(Path('.'), locks['json'], locks['plan'], 7, full_budget_stress=stress, plan_scoped=scoped)
        snapshot_id = digest(label); snapshot = self.snapshots/snapshot_id
        self.write(snapshot/'resolved/manifest.json', m)
        self.write(snapshot/'resolved/model-lock.json', locks['json'])
        self.write(snapshot/'src/example.json', {'test_only': label})
        files = {str(p.relative_to(snapshot)): file_hash(p) for p in snapshot.rglob('*') if p.is_file()}
        marker = dict(files=files, source_revision=m['source_revision'], manifest_hash=digest(m))
        self.write(snapshot/'snapshot.json', marker)
        runtime = dict(snapshot_id=snapshot_id, settings=m['model'],
            model_lock_hash=digest(locks['json']), checkpoint_revision=m['model']['revision'],
            tokenizer_revision=m['model']['tokenizer_revision'], dependencies={'torch': 'test'},
            qualification_key='json', generation_tokens={'eos_token_id': [1], 'pad_token_id': 1},
            chat_template={'template_hash': 'test'}, hardware='test-only H100',
            compute_capability=[9, 0], torch_cuda='test', vram_total_bytes=100)
        rows=[]
        for round_index in range(2):
            for identity in [f'w{i}' for i in range(7)]+['planner']:
                d = dict(rendered_input_tokens=14336, rendered_input_ids_hash=digest(identity),
                    constraint_complete=True, finish_reason='eos')
                output = 2048 if stress else 10
                if stress:
                    d.update(observed_cache_sequence_length=16383, forced_token_verified=True,
                        force_mask_calls=2048, stress_protocol=probe.STRESS_PROTOCOL, normal_decoder_applied=False)
                rows.append(dict(identity=identity, round=round_index, passed=True, uncertain_tokens=0,
                    input_tokens=14336, output_tokens=output, output_cap=2048, prompt_hash=digest(identity),
                    generation=dict(output_tokens=output, diagnostics=d,
                        text=json.dumps({'tool': 'read_source', 'name': 'probe_'+identity})),
                    memory=dict(peak_allocated_bytes=60, peak_reserved_bytes=70, total_bytes=100)))
        report = dict(runtime=runtime, experiment_id=m['experiment_id'], manifest_hash=digest(m),
            source_revision=m['source_revision'], qualification_keys={'json':'json','plan':'plan'},
            pool=7, model_instances=1, model_executed=True, sql_executed=False, task_inputs_used=False,
            task_execution_allowed=False, worst_case_fit_established=False, command_failed=False,
            status='passed_full_budget_geometry' if stress else 'passed_observed_sequence',
            full_budget_geometry_passed=stress, normal_decoding=not stress, calls=rows,
            actual_tokens=sum(r['input_tokens']+r['output_tokens'] for r in rows), uncertain_tokens=0)
        run=self.root/label
        self.write(run/'manifest.json', m); self.write(run/'preflight.json', report)
        return run

    def check(self): return audit(self.normal, self.stress, self.snapshots)

    def mutate(self, fn):
        path=self.stress/'preflight.json'; report=json.loads(path.read_text()); fn(report); self.write(path,report)

    def test_linked_pair_passes_but_never_grants_execution(self):
        result=self.check()
        self.assertEqual(result['status'], 'verified_internal_bindings_review_pending')
        self.assertFalse(result['task_execution_allowed'])
        self.assertFalse(result['model_executed'])
        self.assertFalse(result['historical_grammar_key_recomputed'])
        self.assertEqual(result['changed_source_files'], ['src/example.json'])
        self.assertEqual(result['evidence'][1]['actual_tokens'], 262144)

    def test_missing_and_modified_snapshot_fail(self):
        snapshot=self.snapshots/digest('stress')
        (snapshot/'src/example.json').write_text('tampered')
        self.assertEqual(self.check()['status'], 'failed')
        (self.normal/'preflight.json').unlink()
        self.assertEqual(len(self.check()['errors']), 2)

    def test_false_success_wrong_cache_or_accounting_fail(self):
        original=(self.stress/'preflight.json').read_text()
        mutations=[lambda r:r.update(actual_tokens=1),
            lambda r:r.update(experiment_id='other'),
            lambda r:r['calls'][0]['generation']['diagnostics'].update(observed_cache_sequence_length=None),
            lambda r:r['calls'][0].update(identity='w6'),
            lambda r:r['calls'][0].update(uncertain_tokens=1),
            lambda r:r['runtime'].update(settings={}),
            lambda r:r['qualification_keys'].update(plan='wrong')]
        for mutate in mutations:
            (self.stress/'preflight.json').write_text(original)
            self.mutate(mutate)
            self.assertEqual(self.check()['status'], 'failed')

    def test_runtime_pair_mismatch_is_not_silently_pooled(self):
        self.mutate(lambda r:r['runtime'].update(hardware='different device'))
        result=self.check()
        self.assertEqual(result['status'], 'binding_mismatch')
        self.assertEqual(result['cross_run_binding_differences'], ['hardware'])

    def test_unsafe_snapshot_reference_rejected(self):
        self.mutate(lambda r:r['runtime'].update(snapshot_id='../escape'))
        self.assertEqual(self.check()['status'], 'failed')


    def test_single_scoped_sequence_is_not_paired_qualification(self):
        normal = self.make('scoped', False, scoped=True)
        result = audit_normal(normal, self.snapshots)
        self.assertEqual(result['status'], 'verified_internal_bindings_review_pending')
        self.assertEqual(result['schema'], 'rr-v2-preflight-single-audit-v1')
        for key in ('task_execution_allowed', 'stress_evidence_verified',
                    'worst_case_fit_established', 'model_executed', 'sql_executed'):
            self.assertFalse(result[key])
        self.assertEqual(len(result['evidence']), 1)
        self.assertEqual(audit(normal, self.stress, self.snapshots)['status'], 'binding_mismatch')

    def test_single_wrong_grammar_missing_and_stress_reports_fail(self):
        wrong = self.make('wrong-grammar', False, scoped=True, wrong_grammar=True)
        self.assertEqual(audit_normal(wrong, self.snapshots)['status'], 'failed')
        self.assertEqual(audit_normal(self.stress, self.snapshots)['status'], 'failed')
        (self.normal/'preflight.json').unlink()
        self.assertEqual(audit_normal(self.normal, self.snapshots)['status'], 'failed')
