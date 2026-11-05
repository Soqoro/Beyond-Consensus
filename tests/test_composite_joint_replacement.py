"""Offline replacement gate, uncertainty, preservation and CUDA-probe tests."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from bc_phase2 import composite_joint_replacement as r
from bc_phase2.model import Invalid


class Replacement(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.record=dict(job_id='1115702',output='/failed',scope_digest=r.SCOPE)
        self.report=dict(status='verified_for_replacement_review',blockers=[],scope_digest=r.SCOPE,
            replacement_authorized=False,execution_allowed=False,failed_attempt=self.record,
            input_hashes={'/old/file':'abc','/home/registry.json':'old'},scheduler={})
        self.state={'composite_math_attempts':{r.joint.KEY:deepcopy(self.record)}}

    def test_recheck_preserves_state_and_accepts_only_stable_evidence(self):
        before=deepcopy(self.state);fresh=deepcopy(self.report)
        fresh['input_hashes']['/home/registry.json']='changed';fresh['scheduler']={'new':'terminal'}
        audit=Mock();audit.inspect.return_value=fresh
        with patch.object(r,'auditor',return_value=audit),patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='terminal',stderr='')):
            r.recheck(self.report,self.state)
            fresh['input_hashes']['/old/file']='changed'
            with self.assertRaises(Invalid):r.recheck(self.report,self.state)
        self.assertEqual(self.state,before)

    def test_consumed_or_uncertain_replacement_rejected_before_accounting(self):
        for state in [dict(self.state,uncertain_submission={'job':'unknown'}),
                      {'composite_math_attempts':{**self.state['composite_math_attempts'],r.KEY:{}}}]:
            with patch.object(r.subprocess,'run',side_effect=AssertionError('must not query')):
                with self.assertRaises(Invalid):r.recheck(self.report,state)

    def test_accounting_blocked_never_admits_replacement(self):
        fresh=deepcopy(self.report);fresh['status']='blocked';fresh['blockers']=['database']
        audit=Mock();audit.inspect.return_value=fresh
        with patch.object(r,'auditor',return_value=audit),patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='database')):
            with self.assertRaises(Invalid):r.recheck(self.report,self.state)

    def test_cuda_success_is_single_byte_and_persisted(self):
        torch=Mock();torch.uint8='uint8'
        token=r._probe_output.set(self.root)
        try:r.check_cuda(torch)
        finally:r._probe_output.reset(token)
        torch.empty.assert_called_once_with(1,dtype='uint8',device='cuda:0')
        torch.cuda.synchronize.assert_called_once_with()
        row=json.loads((self.root/'cuda-access.json').read_text())
        self.assertEqual(row['state'],'passed');self.assertFalse(row['model_executed'])
        self.assertFalse(row['contract']['qualification'])

    def test_cuda_failure_is_saved_and_propagated(self):
        torch=Mock();torch.empty.side_effect=RuntimeError('busy')
        token=r._probe_output.set(self.root)
        try:
            with self.assertRaisesRegex(RuntimeError,'busy'):r.check_cuda(torch)
        finally:r._probe_output.reset(token)
        self.assertEqual(json.loads((self.root/'cuda-access.json').read_text())['state'],'failed')
        torch.cuda.synchronize.assert_not_called()

    def test_probe_fails_before_tokenizer_or_weights_load(self):
        # The actual launcher import boundary is verified without importing GPU packages.
        import inspect
        code=inspect.getsource(r.base.open_transport)
        self.assertLess(code.index('p.check_cuda(torch)'),code.index('tokenizer=AutoTokenizer.from_pretrained'))
        self.assertLess(code.index('p.check_cuda(torch)'),code.index('model=Qwen3_5ForConditionalGeneration.from_pretrained'))

    def test_changed_workload_and_old_approval_rejected(self):
        old=dict(cluster={'output_root':'old','partition':'NA100q'},limits={'calls':57},model={'revision':'pinned'})
        previous={'manifest':{'scope':old,'scope_digest':r.digest(old)}}
        previous['release_digest']=r.digest(previous)
        report=deepcopy(self.report);report['failed_attempt']['release_digest']=previous['release_digest']
        scope=deepcopy(old);scope['cluster']['output_root']='new'
        scope['replacement']=dict(maximum_replacements=1,previous_release=previous,reconciliation=report,cuda_check=r.PROBE)
        manifest=dict(scope=scope,scope_digest=r.digest(scope),blockers=[])
        with patch.object(r,'SCOPE',r.digest(old)),patch.object(r.joint,'validate_manifest',side_effect=lambda m:m['scope']):
            r.validate_manifest(manifest)
            scope['limits']['calls']=58
            with self.assertRaises(Invalid):r.validate_manifest(manifest)
            scope['limits']['calls']=57
            approval=dict(schema='composite-joint-approval-v1',decision='approved',scope_digest='old-scope',reviewer='test',reviewed_at='test',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):r.approve(manifest,approval)

    def test_cuda_failure_in_dispatch_leaves_no_journal(self):
        torch=Mock();torch.empty.side_effect=RuntimeError('CUDA busy')
        out=self.root/'execution'
        with patch.object(r,'validate_release',return_value={}),patch.object(r,'source_records'),patch.object(r,'open_transport',side_effect=lambda v:r.check_cuda(torch)):
            with self.assertRaisesRegex(RuntimeError,'CUDA busy'):r.dispatch({},out)
        self.assertFalse((out/'journal').exists())
        self.assertIsNone(json.loads((out/'failure.json').read_text())['totals'])
        self.assertEqual(json.loads((out/'cuda-access.json').read_text())['state'],'failed')

    def submit_case(self,fail=False):
        registry=self.root/'registry';registry.mkdir()
        path=registry/'registry.json';path.write_text(json.dumps(self.state))
        cfg=dict(partition='NA100q',time='04:00:00',memory_gb=128,python='/env/python',storage_root='/dataset',cache_root='/dataset/cache',snapshot_root=str(self.root/'snapshots'),output_root=str(self.root/'outputs'))
        scope={'cluster':cfg,'runtime_identity':{},'replacement':{'reconciliation':self.report}}
        release={'manifest':{'scope_digest':'new'},'release_digest':'new-release'}
        def command(argv):
            saved=json.loads(path.read_text())
            if '--test-only' in argv:return 'ok'
            self.assertEqual(saved['composite_math_attempts'][r.joint.KEY],self.record)
            self.assertEqual(saved['composite_math_attempts'][r.KEY]['state'],'submission_uncertain')
            if fail:raise RuntimeError('ambiguous sbatch')
            return '12345'
        with patch.object(r,'validate_release',return_value=scope),patch.object(r,'source_records'),patch.object(r,'recheck'),patch.object(r.base.cluster,'registry_root',return_value=registry),patch.object(r.base.cluster,'guard'),patch.object(r.base.cluster,'validate_site'),patch.object(r.base,'source_revision',return_value='synthetic'),patch.object(r.base.pilot,'lock_for',return_value={}),patch.object(r.base,'create_snapshot',return_value=self.root/'snap'),patch.object(r.base.cluster,'command',side_effect=command):
            before=path.read_bytes();r.submit(self.root,release,dry_run=True);self.assertEqual(path.read_bytes(),before)
            if fail:
                with self.assertRaisesRegex(RuntimeError,'ambiguous'):r.submit(self.root,release,dry_run=False)
            else:
                self.assertEqual(r.submit(self.root,release,dry_run=False)['job_id'],'12345')
            with self.assertRaises(Invalid):r.submit(self.root,release,dry_run=False)
        saved=json.loads(path.read_text())
        self.assertEqual(saved['composite_math_attempts'][r.joint.KEY],self.record)
        self.assertIn(r.KEY,saved['composite_math_attempts'])
        self.assertEqual(saved['uncertain_submission'] is not None,fail)

    def test_submission_consumes_once_preserves_original(self):self.submit_case()
    def test_uncertain_sbatch_consumes_once_preserves_original(self):self.submit_case(True)


if __name__=='__main__':unittest.main()
