"""Offline audit controls; generated observations here are CPU doubles only."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from tests.test_rr_unique_preflight import Backend, manifest
from beyond_consensus.experiments import rr_unique_preflight as probe, rr_unique_review as audit
from beyond_consensus.models.action_schema import contract
from beyond_consensus.util import BCError, digest, file_hash


def fixture():
    lock = dict(revision='revision', tokenizer_revision='revision', decoder_qualification=dict(
        status='passed', model_executed=False, sql_executed=False, context_limit=16384, output_cap=2048,
        contract=contract(probe.MODE), qualification_key='cpu-double', packages={'torch':'double'},
        effective_generation_tokens=dict(eos_token_id=[9], pad_token_id=9),
        thinking_template=dict(template_hash='double')))
    runtime = dict(model_lock_hash=digest(lock), settings=asdict(probe.model()),
        qualification_key='cpu-double', checkpoint_revision='revision', tokenizer_revision='revision',
        dependencies={'torch':'double'}, generation_tokens=dict(eos_token_id=[9], pad_token_id=9),
        chat_template=dict(template_hash='double'), vram_total_bytes=80_000_000_000, snapshot_id='a'*64)
    class Double(Backend):
        config = probe.model()
        def generate(self, messages, cap, seed):
            g = super().generate(messages, cap, seed)
            g.diagnostics.update(rendered_input_tokens=self.count_input(messages),
                action_constraint=contract(probe.MODE), eos_token_id=[9], last_generated_token_id=9,
                constraint_cpu_seconds=0)
            return g
    backend = Double(); backend.runtime = runtime
    mem = dict(peak_allocated_bytes=10, peak_reserved_bytes=20, total_bytes=80_000_000_000)
    rows = probe.sequence(backend, lambda reset:mem, lambda rows:None)
    m = manifest(); m['model_lock_sha256'] = digest(lock)
    m['experiment_id'] = digest({k:v for k,v in m.items() if k!='experiment_id'})
    r = dict(schema='rr-unique-preflight-report-v1', protocol=probe.PROTOCOL,
        status='passed_observed_cases', command_failed=False, experiment_id=m['experiment_id'],
        manifest_hash=digest(m), source_revision=m['source_revision'], runtime=runtime,
        model_executed=True, model_instances=1, maximum_calls=3, calls=rows,
        actual_tokens=sum(x['resources']['actual_tokens'] for x in rows), uncertain_tokens=0,
        **{k:False for k in ('task_inputs_used','sql_executed','task_execution_allowed',
            'worst_case_fit_established','task_competence_measured')})
    return m, r, lock


class NormalAudit(unittest.TestCase):
    def check(self, m, r, lock):
        # Separate tests already cover diagnostic review approvals; this fixture
        # has no real approval or model and must not be used as qualification.
        with patch.object(probe, 'normal_gate'):
            audit.check_report(m, r, lock)

    def test_complete_observations_and_no_generation_or_scoring(self):
        m, r, lock = fixture()
        with patch.object(probe, 'sequence', side_effect=AssertionError('must not generate')):
            self.check(m, r, lock)
        self.assertNotIn('text', r['calls'][0]['generation'])

    def test_pending_diagnostic_review_is_not_bypassed(self):
        m, r, lock = fixture()
        with self.assertRaises(BCError):audit.check_report(m, r, lock)

    def test_missing_failed_changed_contract_and_accounting_rejected(self):
        m, r, lock = fixture()
        changes = [lambda x:x['calls'].pop(), lambda x:x.update(actual_tokens=0),
            lambda x:x.update(task_execution_allowed=True),
            lambda x:x['calls'][0].update(strict_parser_valid=False),
            lambda x:x['calls'][0]['pre_dispatch'].update(guard_enabled=False),
            lambda x:x['calls'][0]['generation']['diagnostics'].update(constraint_complete=False),
            lambda x:x['calls'][0]['resources'].update(uncertain_tokens=1),
            lambda x:x['calls'][0]['resources']['events'][2].update(output_tokens=1),
            lambda x:x['calls'][0]['resources'].update(cpu_cap_debit=float('nan')),
            lambda x:x['calls'][0]['generation'].update(text_sha256=''),
            lambda x:x['runtime'].update(settings={})]
        for change in changes:
            bad = deepcopy(r); change(bad)
            with self.subTest(change=change), self.assertRaises((BCError, KeyError)):
                self.check(m, bad, lock)

    def test_snapshot_and_compatibility_are_separate_from_observation_success(self):
        m, r, lock = fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); run=root/'run'; run.mkdir(); snapshots=root/'snapshots'
            snap=snapshots/('a'*64); (snap/'resolved').mkdir(parents=True)
            r['runtime']['import_path']=str(snap/'src/beyond_consensus/models/transformers_backend.py')
            for row in r['calls']:row['pre_dispatch']['runtime']=deepcopy(r['runtime'])
            for path, obj in ((run/'manifest.json',m),(run/'preflight.json',r),
                (snap/'resolved/manifest.json',m),(snap/'resolved/model-lock.json',lock),(snap/'resolved/cluster.json',{})):
                path.write_text(json.dumps(obj))
            marker=dict(manifest_hash=digest(m), source_revision=m['source_revision'], cluster_hash=digest({}),
                files={str(p.relative_to(snap)):file_hash(p) for p in snap.rglob('*') if p.is_file()})
            (snap/'snapshot.json').write_text(json.dumps(marker))
            with patch.object(probe,'normal_gate'),patch.object(audit,'require_qualification'):
                before=file_hash(run/'preflight.json')
                result=audit.inspect(run,snapshots,ROOT)
                self.assertEqual(result['status'],'verified_internal_bindings_review_pending')
                self.assertEqual(result['current_compatibility']['status'],'blocked')
                self.assertFalse(result['task_execution_allowed'])
                self.assertFalse(result['scheduler_completion_verified'])
                self.assertEqual(before,file_hash(run/'preflight.json'))
                # Add the complete current contract to the synthetic snapshot:
                # unchanged code is reusable without a new model call.
                for name in result['current_compatibility']['changed_files']:
                    path=snap/name;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes((ROOT/name).read_bytes())
                marker['files']={str(p.relative_to(snap)):file_hash(p)
                    for p in snap.rglob('*') if p.is_file() and p.name!='snapshot.json'}
                (snap/'snapshot.json').write_text(json.dumps(marker))
                compatible=audit.inspect(run,snapshots,ROOT)
                self.assertEqual(compatible['current_compatibility']['status'],'compatible')
                self.assertFalse(compatible['task_execution_allowed'])
                (snap/'extra.txt').write_text('changed')
                with self.assertRaises(BCError):audit.inspect(run,snapshots,ROOT)

    def test_unsafe_snapshot_is_rejected_before_access(self):
        m,r,_=fixture();r['runtime']['snapshot_id']='../outside'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,obj in (('manifest.json',m),('preflight.json',r)):
                (root/name).write_text(json.dumps(obj))
            with self.assertRaisesRegex(BCError,'Unsafe snapshot'):
                audit.inspect(root,root,ROOT)
