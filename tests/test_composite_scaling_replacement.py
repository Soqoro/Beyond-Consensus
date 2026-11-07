"""Bounded offline reconciliation/replacement checks; no scheduler or CUDA access."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from bc_phase2 import composite_scaling_replacement as r
from bc_phase2.model import Invalid,digest

class Replacement(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.output=self.root/'failed';self.output.mkdir();self.exe=self.output/'execution';self.exe.mkdir()
        self.snap=self.root/'snapshot';(self.snap/'resolved').mkdir(parents=True)
        (self.snap/'src/bc_phase2').mkdir(parents=True)
        self.old=dict(cluster=dict(output_root='old',partition='NA100q'),wave={'frozen':'unchanged'},limits={'maximum_calls':185},runtime_identity={'prior':'hash'},decoder_qualification={'status':'passed'})
        self.scope=digest(self.old)
        self.previous={'manifest':{'scope':self.old,'scope_digest':self.scope}}
        self.previous['release_digest']=digest(self.previous)
        manifest={'release':self.previous}
        self.put(self.output/'manifest.json',manifest);self.put(self.snap/'resolved/manifest.json',manifest)
        self.marker={'manifest_hash':digest(manifest)}
        code=Path(r.base.__file__).read_text();(self.snap/'src/bc_phase2/composite_math_launch.py').write_text(code)
        self.record=dict(job_id=r.JOB,scope_digest=self.scope,release_digest=self.previous['release_digest'],state='submitted_no_retry',snapshot=str(self.snap),output=str(self.output))
        self.state={'composite_math_attempts':{r.original.KEY:self.record}}
        self.registry=self.root/'registry.json';self.put(self.registry,self.state)
        self.put(self.exe/'startup.json',dict(scope_digest=self.scope,state='started_no_retry'))
        failure=dict(error_type='AcceleratorError',error='CUDA-capable device(s) is/are busy or unavailable',totals=None,retry_allowed=False,cpu_seconds=84,wall_seconds=184)
        self.put(self.exe/'failure.json',failure)
        self.put(self.exe/'recipe-state.json',{'status':'halted','slots':{'wave1':'unrun'}})
        self.put(self.exe/'cuda-access.json',dict(contract=r.probe.PROBE,state='failed',model_executed=False,job_id=r.JOB,error_type='AcceleratorError',error=failure['error']))
        (self.output/'logs').mkdir();(self.output/'logs'/f'{r.JOB}_0.err').write_text("torch.empty(1,dtype=torch.uint8,device='cuda:0')\n"+failure['error'])
        self.account=dict(returncode=0,stdout=f'{r.JOB}_0|FAILED|1:0|00:03:07|node01|gres/gpu=1|gres/gpu=1\n',stderr='')
        p=patch.object(r,'SCOPE',self.scope);p.start();self.addCleanup(p.stop)
        p=patch.object(r,'verify_snapshot',return_value=self.marker);p.start();self.addCleanup(p.stop)
    def put(self,p,v):p.write_text(json.dumps(v))
    def inspect(self):return r.inspect(self.output,self.registry,self.account)
    def test_exact_failed_probe_no_journal_and_preserved_registry(self):
        before=self.registry.read_bytes();report=self.inspect()
        self.assertEqual(report['status'],'verified_for_replacement_review');self.assertFalse(report['replacement_authorized'])
        self.assertEqual(report['startup_resources'],{'cpu_seconds':84,'wall_seconds':184});self.assertEqual(self.registry.read_bytes(),before)
    def test_any_journal_or_results_reject(self):
        for name in ('journal','result.json','wave-result.json'):
            path=self.exe/name;path.write_text('{}')
            with self.assertRaises(Invalid):self.inspect()
            path.unlink()
    def test_failed_probe_and_frozen_snapshot_required(self):
        p=self.exe/'cuda-access.json';v=json.loads(p.read_text());v['state']='passed';self.put(p,v)
        with self.assertRaises(Invalid):self.inspect()
        v['state']='failed';self.put(p,v)
        with patch.object(r,'verify_snapshot',side_effect=Invalid('snapshot changed')):
            with self.assertRaises(Invalid):self.inspect()
    def test_accounting_unavailable_or_wrong_job_is_blocked(self):
        self.account['returncode']=1;self.assertEqual(self.inspect()['status'],'blocked')
        self.account.update(returncode=0,stdout='other_0|FAILED|1:0\n');self.assertEqual(self.inspect()['status'],'blocked')
    def test_one_consumed_replacement_or_uncertainty_blocks_recheck(self):
        report=self.inspect()
        for state in [dict(self.state,uncertain_submission={'job':'unknown'}),{'composite_math_attempts':{**self.state['composite_math_attempts'],r.KEY:{}}}]:
            with patch.object(r,'accounting',side_effect=AssertionError('must not query')):
                with self.assertRaises(Invalid):r.recheck(report,state)
    def test_stable_recheck_binds_failure_files(self):
        report=self.inspect();before=deepcopy(self.state)
        with patch.object(r.base.cluster,'registry_root',return_value=self.root),patch.object(r,'accounting',return_value=self.account):
            r.recheck(report,self.state)
            self.put(self.exe/'failure.json',{**json.loads((self.exe/'failure.json').read_text()),'wall_seconds':999})
            with self.assertRaises(Invalid):r.recheck(report,self.state)
        self.assertEqual(self.state,before)
    def manifest(self):
        s=deepcopy(self.old);s['cluster']['output_root']='new';s['runtime_identity']=r.identity()
        s['replacement']=dict(maximum_replacements=1,previous_release=self.previous,reconciliation=self.inspect())
        return dict(schema='composite-scaling-replacement-manifest-v1',scope=s,scope_digest=digest(s),blockers=[],execution_allowed=False)
    def test_only_output_root_and_wrapper_may_change(self):
        with patch.object(r.original,'validate_release',return_value=self.old):
            m=self.manifest();r.validate_manifest(m)
            for mutate in (lambda s:s['limits'].update(maximum_calls=186),lambda s:s['wave'].update(frozen='changed'),lambda s:s['decoder_qualification'].update(status='fake'),lambda s:s['cluster'].update(partition='HPCAIq')):
                changed=deepcopy(m);mutate(changed['scope']);changed['scope_digest']=digest(changed['scope'])
                with self.assertRaises(Invalid):r.validate_manifest(changed)
            approval=dict(schema='composite-scaling-replacement-approval-v1',scope_digest='prior',decision='approved',reviewer='test',reviewed_at='test',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):r.approve(m,approval)
            approval['scope_digest']=m['scope_digest'];r.validate_release(r.approve(m,approval))
    def test_probe_before_weights_and_journal_no_changed_worker(self):
        code=Path(r.base.__file__).read_text()
        self.assertLess(code.index('p.check_cuda(torch)'),code.index('model=Qwen3_5ForConditionalGeneration.from_pretrained'))
        self.assertIs(r.recipe,r.original.recipe)

    def submit_case(self,fail=False):
        registry=self.root/'registry';registry.mkdir()
        path=registry/'registry.json';path.write_text(json.dumps(self.state))
        cfg=dict(partition='NA100q',time='04:00:00',memory_gb=128,python='/env/python',storage_root='/dataset',cache_root='/dataset/cache',snapshot_root=str(self.root/'snapshots'),output_root=str(self.root/'outputs'))
        scope={'cluster':cfg,'runtime_identity':{},'replacement':{'reconciliation':self.inspect()}}
        release={'manifest':{'scope_digest':'new'},'release_digest':'new-release'}
        def command(argv):
            saved=json.loads(path.read_text())
            if '--test-only' in argv:return 'ok'
            self.assertEqual(saved['composite_math_attempts'][r.original.KEY],self.record)
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
        self.assertEqual(saved['composite_math_attempts'][r.original.KEY],self.record)
        self.assertIn(r.KEY,saved['composite_math_attempts'])
        self.assertEqual(saved['uncertain_submission'] is not None,fail)

    def test_submission_consumes_once_preserves_original(self):self.submit_case()
    def test_uncertain_sbatch_consumes_once_preserves_original(self):self.submit_case(True)

