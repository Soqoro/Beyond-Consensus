"""Synthetic read-only failure reconciliation; no scheduler/model execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('reconcile', Path(__file__).resolve().parents[1] / 'scripts/reconcile_composite_joint_failure.py')
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Reconciliation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.snap = self.root / 'snap'
        self.registry = self.root / 'registry.json'
        scope = {'blueprint': {'schedule': ['profile/original', 'profile/algebraic', 'NEUTRAL/clean']}}
        self.scope = r.digest(scope)
        self.patch = patch.object(r, 'SCOPE', self.scope)
        self.patch.start(); self.addCleanup(self.patch.stop)
        release = {'manifest': {'scope_digest': self.scope, 'scope': scope}}
        release['release_digest'] = r.digest(release)
        manifest = {'release': release}
        self.write(self.registry, {'composite_math_attempts': {r.KEY: dict(job_id=r.JOB,
            scope_digest=self.scope, state='submitted_no_retry', output=str(self.run),
            snapshot=str(self.snap), release_digest=release['release_digest'])}})
        self.write(self.run / 'manifest.json', manifest)
        self.write(self.snap / 'resolved/manifest.json', manifest)
        self.write(self.run / 'execution/startup.json', dict(scope_digest=self.scope, state='started_no_retry'))
        self.write(self.run / 'execution/failure.json', dict(error_type='AcceleratorError',
            error='CUDA-capable device(s) is/are busy or unavailable', totals=None, retry_allowed=False,
            cpu_seconds=1, wall_seconds=2))
        self.write(self.run / 'execution/recipe-state.json', dict(status='halted', slots={k:'unrun' for k in scope['blueprint']['schedule']}))
        for path, text in [(self.run / 'logs/1115702_0.err', "model.to(torch.device('cuda:0'))\nCUDA-capable device(s) is/are busy or unavailable"),
                (self.snap / 'src/bc_phase2/composite_math_launch.py', 'sources=p.source_records(s);transport=p.open_transport(v)\njournal=implementation.Journal(')]:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
        self.verify = patch.object(r, 'verify_snapshot', return_value={'manifest_hash': r.digest(manifest)})
        self.verify.start(); self.addCleanup(self.verify.stop)
        self.accounting = dict(returncode=0, stdout='1115702_0|FAILED|1:0|00:01:09|node01|x|x\n', stderr='')

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def test_verified_preserves_every_input_and_disables_execution(self):
        before = {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = r.inspect(self.run, self.registry, self.accounting)
        self.assertEqual(result['status'], 'verified_for_replacement_review')
        self.assertFalse(result['replacement_authorized'])
        self.assertFalse(result['execution_allowed'])
        self.assertEqual(before, {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_unavailable_accounting_is_blocked_not_success(self):
        self.accounting.update(returncode=1, stdout='', stderr='database unavailable')
        self.assertEqual(r.inspect(self.run,self.registry,self.accounting)['status'], 'blocked')

    def test_running_or_missing_task_is_blocked(self):
        for text in ['1115702_0|RUNNING|0:0', '1115702_0.batch|FAILED|1:0', '']:
            self.accounting['stdout'] = text
            self.assertEqual(r.inspect(self.run,self.registry,self.accounting)['status'], 'blocked')

    def test_any_journal_blocks_replacement_review(self):
        (self.run / 'execution/journal').mkdir()
        with self.assertRaises(Exception): r.inspect(self.run,self.registry,self.accounting)

    def test_changed_manifest_rejected(self):
        self.write(self.run / 'manifest.json', {'release': {}})
        with self.assertRaises(Exception): r.inspect(self.run,self.registry,self.accounting)

    def test_attempted_slot_rejected(self):
        path=self.run/'execution/recipe-state.json'; value=json.loads(path.read_text())
        value['slots']['profile/original']='completed'; self.write(path,value)
        with self.assertRaises(Exception): r.inspect(self.run,self.registry,self.accounting)


if __name__ == '__main__': unittest.main()
