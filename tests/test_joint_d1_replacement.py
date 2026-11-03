"""One explicit pre-dispatch replacement; mocks only, no cluster or models."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_joint_d1_launch as base
from bc_phase2 import joint_d1_launch as launch
from bc_phase2.model import Invalid,digest
from beyond_consensus.util import BCError

ROOT=Path(__file__).resolve().parents[1]


class SingleReplacement(unittest.TestCase):
    setUp=base.ScopedLaunch.setUp
    freeze=base.ScopedLaunch.freeze
    parent=base.ScopedLaunch.parent
    approved=base.ScopedLaunch.approved
    config=base.ScopedLaunch.config
    scheduler=base.ScopedLaunch.scheduler

    def fixture(self):
        original=self.approved()
        self.parent_manifest=deepcopy(original['manifest']);self.parent_manifest['approval']=None
        self.scheduler()
        self.old_output=self.root/'old-output';self.old_output.mkdir()
        self.old_snapshot=self.root/'old-snapshot';(self.old_snapshot/'resolved').mkdir(parents=True)
        old={'schema':'joint-d1-slurm-v1','release':original,'source_revision':'mock','statement_path':str(self.path)}
        for p in (self.old_snapshot/'resolved/manifest.json',self.old_output/'manifest.json'):
            p.write_text(json.dumps(old))
        stderr=self.old_output/'logs/1114910_0.err';stderr.parent.mkdir();stderr.write_text('mock pre-dispatch traceback')
        self.failed={'job_id':'1114910','output':str(self.old_output),'snapshot':str(self.old_snapshot),
            'release_digest':original['release_digest'],'scope_digest':launch.APPROVED_SCOPE,'state':'submitted_no_retry'}
        self.stack.enter_context(patch.object(launch,'FAILED_ATTEMPT',self.failed))
        self.stack.enter_context(patch.object(launch,'FAILED_STDERR_SHA256',hashlib.sha256(stderr.read_bytes()).hexdigest()))
        self.snapshot_check=self.stack.enter_context(patch.object(launch,'verify_snapshot',return_value={'manifest_hash':digest(old)}))
        self.state={'jobs':[{'job_id':'1114910'}],'d1_scopes':{launch.APPROVED_SCOPE:deepcopy(self.failed)},'untouched':'keep'}
        self.registry=self.root/'registry/registry.json';self.registry.parent.mkdir();self.save_state()
        reg_hash=hashlib.sha256(self.registry.read_bytes()).hexdigest()
        self.stack.enter_context(patch.object(launch,'FAILED_REGISTRY_SHA256',reg_hash))
        self.accounting='1114910_0|FAILED|1:0|00:00:02|gres/gpu=1|gres/gpu=1\n1114910_0.batch|FAILED|1:0|00:00:02||gres/gpu=1\n'
        self.reconciliation={'status':'pre_dispatch_failure_verified_for_replacement_review',
            'scope_digest':launch.APPROVED_SCOPE,'failed_attempt':deepcopy(self.failed),
            'snapshot_inventory_verified':True,'snapshot_output_manifest_match':True,
            'terminal_failure_verified':True,'expected_accounting_trace_present':True,
            'execution_directory_exists':False,'stderr_sha256':launch.FAILED_STDERR_SHA256,
            'scheduler_accounting':self.accounting,'registry_sha256':reg_hash,'registry_changed':False,
            'replacement_submitted':False,'replacement_authorized_by_this_check':False}
        self.commands.side_effect=lambda argv:self.accounting if argv[0]=='sacct' else '456'

    def save_state(self):self.registry.write_text(json.dumps(self.state))

    def prepared(self):
        return launch.prepare_replacement(ROOT,self.parent_manifest,self.reconciliation,reviewer='mock reviewer')

    def submit_setup(self):
        new=self.root/'new-snapshot';new.mkdir()
        self.stack.enter_context(patch.object(launch,'create_snapshot',return_value=new))
        self.stack.enter_context(patch.object(launch,'source_revision',return_value='mock'))
        validate=launch.validate_authorization
        self.stack.enter_context(patch.object(launch,'validate_authorization',side_effect=lambda root,v:validate(ROOT,v)))
        self.stack.enter_context(patch.object(Path,'is_file',return_value=True))

    def test_prepare_preserves_scope_evidence_registry_and_all_limits(self):
        self.fixture();before=self.registry.read_bytes();original=deepcopy(self.parent_manifest)
        v=self.prepared()
        self.assertEqual(v['manifest']['scope'],original['scope'])
        self.assertEqual(self.parent_manifest,original);self.assertEqual(self.registry.read_bytes(),before)
        self.assertEqual(v['replacement']['maximum_replacements'],1)
        self.assertFalse(v['later_stages_enabled'])
        self.assertEqual(v['replacement']['reconciliation'],self.reconciliation)
        self.assertEqual(launch.summary(ROOT,v)['replacement_of'],'1114910')

    def test_modified_proof_and_generic_failures_rejected(self):
        self.fixture()
        for k,v in [('execution_directory_exists',True),('terminal_failure_verified',False),
                    ('replacement_authorized_by_this_check',True),('stderr_sha256','0'*64),
                    ('registry_sha256','0'*64),('scope_digest','0'*64),('registry_changed',True),
                    ('failed_attempt',dict(self.failed,job_id='999'))]:
            bad=deepcopy(self.reconciliation);bad[k]=v
            with self.subTest(key=k),self.assertRaises(Invalid):launch.validate_failure_report(bad)
        for text in ('1114910_0|COMPLETED|0:0','1114910_0|RUNNING|0:0',
                     '1114910_0|FAILED|1:0\n1114910_1|FAILED|1:0','1114910_0.batch|FAILED|1:0',''):
            with self.subTest(text=text),self.assertRaises(Invalid):launch._failed_accounting(text)

    def test_existing_dispatch_or_changed_trace_or_snapshot_forbids_replacement(self):
        self.fixture();execution=self.old_output/'execution';execution.mkdir()
        with self.assertRaises(Invalid):self.prepared()
        execution.rmdir();execution.symlink_to(self.root/'does-not-exist')
        with self.assertRaises(Invalid):self.prepared()
        execution.unlink()
        err=self.old_output/'logs/1114910_0.err';old=err.read_bytes();err.write_text('changed')
        with self.assertRaises(Invalid):self.prepared()
        err.write_bytes(old);self.snapshot_check.side_effect=BCError('snapshot corrupted')
        with self.assertRaises(BCError):self.prepared()

    def test_output_manifest_mismatch_rejected(self):
        self.fixture();(self.old_output/'manifest.json').write_text('{}')
        with self.assertRaises(Invalid):self.prepared()

    def test_current_terminal_state_and_registry_are_rechecked(self):
        self.fixture();self.commands.side_effect=lambda argv:'1114910_0|RUNNING|0:0'
        with self.assertRaises(Invalid):self.prepared()
        self.commands.side_effect=lambda argv:self.accounting
        self.state['d1_scopes'][launch.APPROVED_SCOPE]['job_id']='999';self.save_state()
        with self.assertRaises(Invalid):self.prepared()

    def test_uncertain_prior_submission_is_not_cleared(self):
        self.fixture();self.state['uncertain_submission']={'job':'unknown'};self.save_state();before=self.registry.read_bytes()
        with self.assertRaises(Invalid):self.prepared()
        self.assertEqual(before,self.registry.read_bytes())

    def test_dry_run_is_readonly_and_rechecks_new_dispatch_evidence(self):
        self.fixture();v=self.prepared();before=self.registry.read_bytes()
        r=launch.submit(ROOT,v,self.path,self.config(),dry_run=True)
        self.assertFalse(r['submitted']);self.assertEqual(before,self.registry.read_bytes())
        (self.old_output/'execution').mkdir()
        with self.assertRaises(Invalid):launch.submit(ROOT,v,self.path,self.config(),dry_run=True)
        self.assertEqual(before,self.registry.read_bytes())

    def test_single_submission_preserves_complete_prior_attempt_and_blocks_second(self):
        self.fixture();v=self.prepared();self.submit_setup()
        result=launch.submit(ROOT,v,self.path,self.config(),dry_run=False)
        self.assertEqual(result['job_id'],'456')
        state=json.loads(self.registry.read_text())
        self.assertEqual(state['d1_attempt_history'][launch.APPROVED_SCOPE],[self.failed])
        self.assertEqual(state['d1_replacements'][launch.APPROVED_SCOPE]['reconciliation'],self.reconciliation)
        self.assertEqual(state['d1_scopes'][launch.APPROVED_SCOPE]['job_id'],'456')
        self.assertEqual(state['untouched'],'keep');self.assertEqual(state['completed_jobs'],[{'job_id':'1114910'}])
        before=self.registry.read_bytes()
        with self.assertRaises(Invalid):launch.submit(ROOT,v,self.path,self.config(),dry_run=False)
        self.assertEqual(before,self.registry.read_bytes())
        with self.assertRaises(Invalid):self.prepared()

    def test_ambiguous_replacement_consumes_allowance_and_retains_both_attempts(self):
        self.fixture();v=self.prepared();self.submit_setup()
        def scheduler(argv):
            if argv[0]=='sacct':return self.accounting
            if '--test-only' in argv:return 'ok'
            raise BCError('ambiguous sbatch outcome')
        self.commands.side_effect=scheduler
        with self.assertRaises(BCError):launch.submit(ROOT,v,self.path,self.config(),dry_run=False)
        state=json.loads(self.registry.read_text())
        self.assertIsNotNone(state['uncertain_submission'])
        self.assertEqual(state['d1_attempt_history'][launch.APPROVED_SCOPE],[self.failed])
        self.assertEqual(state['d1_replacements'][launch.APPROVED_SCOPE]['state'],'consumed_before_submission')
        before=self.registry.read_bytes()
        with self.assertRaises(Invalid):self.prepared()
        self.assertEqual(before,self.registry.read_bytes())

    def test_rehashed_expanded_replacement_rejected(self):
        self.fixture();v=self.prepared()
        for key,x in [('maximum_replacements',2),('decision','pending'),('reconciliation_digest','0'*64)]:
            bad=deepcopy(v);bad['replacement'][key]=x
            bad['release_digest']=digest({k:v for k,v in bad.items() if k!='release_digest'})
            with self.subTest(key=key),self.assertRaises(Invalid):launch.validate_authorization(ROOT,bad)

    def test_allocated_replacement_requires_preserved_history_and_consumption(self):
        self.fixture();v=self.prepared();config=self.config()
        output=Path(config.output_root)/('d1-'+launch.APPROVED_SCOPE)
        manifest={'schema':'joint-d1-slurm-v1','source_revision':'mock','release':v,'statement_path':str(self.path)}
        self.snapshot_check.return_value={'manifest_hash':digest(manifest)}
        current={'job_id':'456','state':'submitted_no_retry','release_digest':v['release_digest'],
                 'snapshot':str(ROOT),'output':str(output)}
        state={'d1_scopes':{launch.APPROVED_SCOPE:current},
               'd1_attempt_history':{launch.APPROVED_SCOPE:[deepcopy(self.failed)]},
               'd1_replacements':{launch.APPROVED_SCOPE:{'release_digest':v['release_digest'],
                    'failed_attempt':deepcopy(self.failed),'state':'consumed_before_submission'}}}
        def read(path):
            if Path(path).name=='registry.json':return state
            if Path(path).name=='environment.json':return {'mock':'environment'}
            if Path(path)==output/'manifest.json':return manifest
            raise AssertionError(str(path))
        with patch.dict(os.environ,{'SLURM_JOB_ID':'456','SLURM_ARRAY_JOB_ID':'456','SLURM_ARRAY_TASK_ID':'0'}),\
             patch.object(launch.release,'read_evidence',return_value=manifest),\
             patch.object(launch.cluster,'load_cluster',return_value=config),\
             patch.object(launch,'read_json',side_effect=read),\
             patch.object(launch.cluster,'active_gpu_jobs',return_value={'456':1}),\
             patch.object(launch,'environment_inventory',return_value={'mock':'environment'}),\
             patch.object(launch.release,'dispatch_live',return_value={'halted':False,'sources':[],'model_executed':False}) as dispatch:
            self.assertFalse(launch.run_allocated(ROOT,output)['model_executed'])
            self.assertEqual(dispatch.call_count,1)
            state['d1_attempt_history'][launch.APPROVED_SCOPE]=[]
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,output)
            state['d1_attempt_history'][launch.APPROVED_SCOPE]=[deepcopy(self.failed)]
            state['d1_replacements'][launch.APPROVED_SCOPE]['release_digest']='0'*64
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,output)
            self.assertEqual(dispatch.call_count,1)

if __name__=='__main__':unittest.main()
