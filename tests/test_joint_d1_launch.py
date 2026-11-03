"""Exact-scope release controls; synthetic statements and mocked scheduler only."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json
import os
import unittest

import test_joint_d1_release as fixtures
from bc_phase2 import joint_d1_launch as launch
from bc_phase2 import joint_d1_release as release
from bc_phase2 import planner_qwen
from bc_phase2.model import Invalid,digest
from beyond_consensus.util import BCError

ROOT=Path(__file__).resolve().parents[1]


class ScopedLaunch(unittest.TestCase):
    setUp=fixtures.FrozenD1.setUp
    freeze=fixtures.FrozenD1.freeze

    def parent(self):
        value=self.freeze()
        value['scope']['runtime_implementation']=deepcopy(launch.PARENT_RUNTIME)
        value['scope_digest']=digest(value['scope'])
        self.stack.enter_context(patch.object(launch,'APPROVED_SCOPE',value['scope_digest']))
        return value

    def approved(self):return launch.prepare(ROOT,self.parent(),reviewer='synthetic reviewer')

    def config(self):
        return launch.cluster.ClusterConfig(partition='mock',time='01:00:00',memory_gb=128,
            python='/mock/python',storage_root=str(self.root),cache_root=str(self.root/'cache'),
            snapshot_root=str(self.root/'snapshots'),output_root=str(self.root/'outputs'))

    def scheduler(self):
        self.stack.enter_context(patch.dict(os.environ,{},clear=True))
        self.stack.enter_context(patch.object(launch.cluster,'registry_root',return_value=self.root/'registry'))
        self.guard=self.stack.enter_context(patch.object(launch.cluster,'guard',return_value=[]))
        self.site=self.stack.enter_context(patch.object(launch.cluster,'validate_site'))
        self.commands=self.stack.enter_context(patch.object(launch.cluster,'command',side_effect=AssertionError('unmocked scheduler')))

    def test_parent_approval_separate_exact_and_nonexpanding(self):
        parent=self.parent();before=deepcopy(parent)
        approved=launch.prepare(ROOT,parent,reviewer='fixture')
        self.assertEqual(parent,before);self.assertIsNone(parent['approval'])
        self.assertEqual(approved['manifest']['scope'],parent['scope'])
        self.assertFalse(approved['later_stages_enabled'])
        self.assertEqual(launch.validate_authorization(ROOT,approved),parent['scope'])
        self.assertFalse(planner_qwen._REAL_EXECUTION_RELEASED);self.assertFalse(release.LIVE_RELEASED)

    def test_changed_scope_even_rehashed_rejected(self):
        value=self.approved()
        for mutate in (
            lambda v:v['manifest']['scope']['limits'].update(calls=7),
            lambda v:v['manifest']['approval'].update(statement_transmission_authorized=False),
            lambda v:v.update(later_stages_enabled=True),
            lambda v:v['runtime_implementation'].update({'scripts/launch_joint_d1.py':'0'*64}),
        ):
            bad=deepcopy(value);mutate(bad)
            bad['manifest']['scope_digest']=digest(bad['manifest']['scope'])
            bad['release_digest']=digest({k:v for k,v in bad.items() if k!='release_digest'})
            with self.assertRaises(Invalid):launch.validate_authorization(ROOT,bad)

    def test_unreviewed_parent_dependency_rejected(self):
        p=self.parent();current=release.runtime_identity(ROOT)
        current['src/bc_phase2/joint_schema.py']='0'*64
        with patch.object(release,'runtime_identity',return_value=current):
            with self.assertRaises(Invalid):launch.validate_parent_runtime(ROOT,p)

    def test_loader_rejects_unapproved_before_inventory_or_imports(self):
        with patch.object(planner_qwen,'verify_local_inventory',side_effect=AssertionError('inventory reached')):
            with self.assertRaises(Invalid):planner_qwen.open_local({},authorization={})
            value=self.approved()
            with self.assertRaisesRegex(Invalid,'inventory mismatch'):planner_qwen.open_local({},authorization=value)

    def test_dry_run_shared_guard_one_gpu_and_no_submission(self):
        value=self.approved();self.scheduler()
        r=launch.submit(ROOT,value,self.path,self.config(),dry_run=True)
        self.assertFalse(r['submitted']);self.commands.assert_not_called()
        self.guard.assert_called_once();self.site.assert_called_once()
        self.assertIn('--gres=gpu:1',r['argv']);self.assertIn('--array=0-0%1',r['argv'])
        self.assertIn('--time=01:00:00',r['argv']);self.assertIn('--mem=128G',r['argv'])
        self.assertTrue(r['argv'][-4].endswith('/experiments/run_joint_d1.sbatch'))
        self.assertFalse((self.root/'registry').exists())

    def test_overlap_batch_self_submission_and_changed_allocation_rejected(self):
        value=self.approved();self.scheduler()
        self.guard.side_effect=BCError('other active GPU')
        with self.assertRaises(BCError):launch.submit(ROOT,value,self.path,self.config())
        self.commands.assert_not_called();self.guard.side_effect=None
        with patch.dict(os.environ,{'SLURM_JOB_ID':'1'}):
            with self.assertRaises(Invalid):launch.submit(ROOT,value,self.path,self.config())
        from dataclasses import replace
        for cfg in (replace(self.config(),time='02:00:00'),replace(self.config(),memory_gb=256)):
            with self.assertRaises(Invalid):launch.submit(ROOT,value,self.path,cfg)

    def submit_fixture(self):
        value=self.approved();self.scheduler()
        snapshot=self.root/'snapshot';snapshot.mkdir()
        self.stack.enter_context(patch.object(launch,'create_snapshot',return_value=snapshot))
        self.stack.enter_context(patch.object(launch,'source_revision',return_value='fixture'))
        real_validate=launch.validate_authorization
        self.stack.enter_context(patch.object(launch,'validate_authorization',
            side_effect=lambda root,value:real_validate(ROOT,value)))
        self.stack.enter_context(patch.object(Path,'is_file',return_value=True))
        self.commands.side_effect=['scheduler accepts','123;mock']
        return value

    def test_submission_sticky_registry_and_no_second_attempt(self):
        value=self.submit_fixture()
        result=launch.submit(ROOT,value,self.path,self.config(),dry_run=False)
        self.assertEqual(result['job_id'],'123');self.assertEqual(self.commands.call_count,2)
        state=json.loads((self.root/'registry/registry.json').read_text())
        self.assertIsNone(state['uncertain_submission'])
        self.assertEqual(state['d1_scopes'][launch.APPROVED_SCOPE]['job_id'],'123')
        self.assertEqual(state['jobs'][0]['reserved_physical_gpus'],1)
        with self.assertRaises(Invalid):launch.submit(ROOT,value,self.path,self.config(),dry_run=False)
        self.assertEqual(self.commands.call_count,2)

    def test_ambiguous_submission_keeps_global_and_scope_reservations(self):
        value=self.submit_fixture();self.commands.side_effect=['ok',BCError('connection lost')]
        with self.assertRaises(BCError):launch.submit(ROOT,value,self.path,self.config(),dry_run=False)
        state=json.loads((self.root/'registry/registry.json').read_text())
        self.assertIsNotNone(state['uncertain_submission'])
        self.assertEqual(state['d1_scopes'][launch.APPROVED_SCOPE]['state'],'submission_uncertain')
        with self.assertRaises(Invalid):launch.submit(ROOT,value,self.path,self.config(),dry_run=False)
        self.assertEqual(self.commands.call_count,2)

    def test_job_requires_allocation_before_snapshot_or_model(self):
        with patch.dict(os.environ,{},clear=True),patch.object(launch,'verify_snapshot',side_effect=AssertionError('snapshot read')):
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,self.root/'out')

    def test_authorized_dispatch_does_not_open_global_gates(self):
        from types import SimpleNamespace
        from test_phase2_planner_qwen import Tokenizer,Model,Torch
        from test_joint_d1_qwen import UNSUPPORTED
        tokenizer=Tokenizer();tokenizer.eos_token_id=248046;tokenizer.pad_token_id=248044
        original=tokenizer.convert_tokens_to_ids
        tokenizer.convert_tokens_to_ids=lambda x:248046 if x=='<eos>' else original(x)
        tokenizer.final=UNSUPPORTED
        model=Model();model.generated=[6,8,7,248046]
        model.generation_config=SimpleNamespace(eos_token_id=[248046,248044],pad_token_id=248044)
        torch=Torch();torch.cuda=SimpleNamespace(synchronize=lambda:None,
            get_device_properties=lambda i:SimpleNamespace(total_memory=85_000_000_000))
        transport=planner_qwen.QwenTransport(tokenizer,model,torch,evidence='local_runtime_unqualified')
        self.report['template']=transport.template
        timers=[]
        class Timer:
            def __init__(self,seconds,callback):self.seconds=seconds;self.cancelled=False;timers.append(self)
            def start(self):pass
            def cancel(self):self.cancelled=True
        with patch.object(fixtures.local,'TEMPLATE_HASH',digest(tokenizer.chat_template)):
            value=self.approved()
            with patch.object(release,'open_local',return_value=transport) as loader,\
                 patch.object(release.threading,'Timer',Timer),\
                 patch('beyond_consensus.models.transformers_backend.require_allocation'):
                r=release.dispatch_live(ROOT,value['manifest'],self.path,self.root/'job',authorization=value)
                self.assertTrue(r['model_executed'])  # injected runtime-evidence fixture, not a real model
                self.assertEqual([x['status'] for x in r['sources']],['unsupported']*3)
                self.assertEqual(loader.call_args.kwargs['authorization'],value)
                self.assertEqual(len(model.calls),3)
                self.assertEqual(timers[0].seconds,3600);self.assertTrue(timers[0].cancelled)
                with self.assertRaises(FileExistsError):
                    release.dispatch_live(ROOT,value['manifest'],self.path,self.root/'job',authorization=value)
                self.assertEqual(loader.call_count,1)
        self.assertFalse(release.LIVE_RELEASED);self.assertFalse(planner_qwen._REAL_EXECUTION_RELEASED)

    def test_load_failure_retains_unrun_rows_and_forbids_restart(self):
        value=self.approved()
        with patch.object(release,'open_local',side_effect=RuntimeError('synthetic loader failure')) as loader,\
             patch.object(release.threading,'Timer'),\
             patch('beyond_consensus.models.transformers_backend.require_allocation'):
            with self.assertRaises(RuntimeError):
                release.dispatch_live(ROOT,value['manifest'],self.path,self.root/'job',authorization=value)
            failure=json.loads((self.root/'job/failure.json').read_text())
            self.assertFalse(failure['model_executed'])
            self.assertEqual([r['status'] for r in failure['sources']],['unrun']*3)
            with self.assertRaises(FileExistsError):
                release.dispatch_live(ROOT,value['manifest'],self.path,self.root/'job',authorization=value)
            self.assertEqual(loader.call_count,1)

    def test_allocated_job_registry_snapshot_and_environment_checks(self):
        value=self.approved();self.scheduler();config=self.config()
        output=Path(config.output_root)/('d1-'+launch.APPROVED_SCOPE)
        manifest={'schema':'joint-d1-slurm-v1','source_revision':'fixture','release':value,'statement_path':str(self.path)}
        marker={'manifest_hash':digest(manifest)}
        record={'job_id':'123','state':'submitted_no_retry','release_digest':value['release_digest'],
                'snapshot':str(ROOT),'output':str(output)}
        state={'d1_scopes':{launch.APPROVED_SCOPE:record}}
        def read(path):
            if Path(path).name=='registry.json':return state
            if Path(path).name=='environment.json':return {'fixture':'environment'}
            if Path(path)==output/'manifest.json':return manifest
            raise AssertionError(str(path))
        with patch.dict(os.environ,{'SLURM_JOB_ID':'123','SLURM_ARRAY_JOB_ID':'123','SLURM_ARRAY_TASK_ID':'0'}),\
             patch.object(launch,'verify_snapshot',return_value=marker),\
             patch.object(release,'read_evidence',return_value=manifest),\
             patch.object(launch.cluster,'load_cluster',return_value=config),\
             patch.object(launch,'read_json',side_effect=read),\
             patch.object(launch.cluster,'active_gpu_jobs',return_value={'123_0':1}) as active,\
             patch.object(launch,'environment_inventory',return_value={'fixture':'environment'}) as env,\
             patch.object(release,'dispatch_live',return_value={'halted':False,'sources':[],'model_executed':False}) as dispatch:
            self.assertFalse(launch.run_allocated(ROOT,output)['model_executed'])
            self.assertEqual(dispatch.call_count,1)
            record['job_id']='999'
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,output)
            record['job_id']='123';active.return_value={'123_0':1,'456':1}
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,output)
            active.return_value={'123_0':1};env.return_value={'changed':'environment'}
            with self.assertRaises(Invalid):launch.run_allocated(ROOT,output)
            self.assertEqual(dispatch.call_count,1)

if __name__=='__main__':unittest.main()
