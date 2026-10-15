"""Sampled adapter gates and shared runtime; all model calls here are CPU doubles."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import unittest

from tests.support import ROOT
from tests.test_rr_sampled_cohort import catalog_fixture, fixture
from beyond_consensus.experiments import rr_sampled_run as adapter, rr_cohort as shared
from beyond_consensus.experiments.manifest import validate_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.models.base import Generation
from beyond_consensus.util import BCError, digest, atomic_json
from reporecourse import sampled_cohort as sampled, cohort
from reporecourse.tasks import private_task
from reporecourse.resources import Resources


def candidate():
    catalog,publics=catalog_fixture();worker={'test_only':'no qualification'}
    with patch.object(sampled,'qualified_candidate',return_value=True):
        p=sampled.proposal(catalog,publics,worker_lock=worker,normal_qualification={})
    configs=[x['configuration'] for x in p['configurations']]
    with patch.object(adapter,'catalog_bindings',return_value=(publics,{},configs)),patch.object(adapter,'verify'),patch.object(sampled,'qualified_candidate',return_value=True):
        m=adapter.build(ROOT,'/not-real',catalog,worker,{}, {}, {})
    return m,publics


class Boundaries(unittest.TestCase):
    def test_exact_six_plans_twelve_conditions_zero_generated_planning(self):
        m,_=candidate();config=validate_manifest(m)
        self.assertEqual(config.shards,6);self.assertEqual(config.model.action_constraint,sampled.MODE)
        self.assertEqual(m['planned_conditions'],12);self.assertFalse(m['task_execution_allowed'])
        self.assertEqual(m['maximum_model_planner_calls'],0)
        self.assertTrue(all(x['schedule']['branches']['rows'][1]['target'] in x['schedule']['branches']['rows'][1]['eligible'] for x in m['prepared']['configurations']))

    def test_approval_is_exact_and_preserves_deferred_review(self):
        m,_=candidate();a=adapter.approval_template(m)
        with patch.object(adapter,'verify'):
            with self.assertRaises(BCError):adapter.authorize(m,a,ROOT,{})
            a.update(decision='approved',reviewer='CPU double only',reviewed_at='test')
            ok=adapter.authorize(m,a,ROOT,{})
        self.assertTrue(ok['task_execution_allowed'])
        self.assertIn('independent_task_review_pending',ok['limitations'])
        for key,value in [('maximum_execution_branches',13),('maximum_model_planner_calls',1),('branch_caps',{'token_cap':200000,'cpu_cap':1200}),('reserve_rule','tuned')]:
            bad=deepcopy(ok);bad[key]=value;adapter.seal(bad)
            with self.subTest(key=key),self.assertRaises(BCError):adapter.validate(bad)

    def test_changes_to_plan_seed_and_receipt_rejected(self):
        m,_=candidate()
        for mutation in (lambda x:x['configurations'][0].update(seed_index=2),
            lambda x:x['configurations'][0]['plan']['units'][0].update(worker='w6'),
            lambda x:x['prepared']['configurations'][0]['schedule']['frozen'].update(physical_generation_count=1)):
            bad=deepcopy(m);mutation(bad);adapter.seal(bad)
            with self.assertRaises(Exception):adapter.validate(bad)

    def test_new_task_runner_rejects_injected_backend_and_retry(self):
        m,_=candidate()
        with self.assertRaisesRegex(BCError,'injected backend'):run_manifest(m,Path('/unused'),ROOT,backend=object())
        with self.assertRaises(BCError):shared.run(m,Path('/unused'),ROOT,model_lock=Path('/unused'),shard=0,retry_failures=True)

    def test_scheduler_route_has_no_pending_or_retry_bypass(self):
        from beyond_consensus.experiments.cluster import submit,ClusterConfig
        m,_=candidate()
        with TemporaryDirectory() as d,patch.object(adapter,'verify'),patch('beyond_consensus.experiments.cluster.command',side_effect=AssertionError('No scheduler before approval')):
            cluster=ClusterConfig('test','00:30:00',32,'/usr/bin/python',d,d,d,d)
            # Qualification runs inside Slurm. Simulate the login terminal
            # only within these mocked calls; never change the batch environment.
            with patch.dict(os.environ, {'SLURM_JOB_ID': ''}):
                with self.assertRaisesRegex(BCError,'approval'):submit(ROOT,cluster,m,{},1,dry_run=True)
                with self.assertRaisesRegex(BCError,'no retry'):submit(ROOT,cluster,m,{},1,dry_run=True,failed_shards=[0])
            with patch.dict(os.environ, {'SLURM_JOB_ID': 'synthetic-cpu-allocation'}):
                with self.assertRaisesRegex(BCError,'Batch/allocation'):
                    submit(ROOT,cluster,m,{},1,dry_run=True)

    def test_debug_environment_rejected_before_model_load(self):
        import os
        with patch.dict(os.environ,{'CUDA_LAUNCH_BLOCKING':'1'}),patch('beyond_consensus.models.transformers_backend.TransformersBackend') as loader:
            with self.assertRaisesRegex(BCError,'asynchronous'):adapter.load_backend({},Path('/unused'))
            loader.assert_not_called()

    def test_pending_approval_and_started_attempt_never_run(self):
        m,_=candidate()
        with TemporaryDirectory() as d,patch.object(adapter,'verify'):
            with self.assertRaisesRegex(BCError,'approval'):adapter.submission(m,ROOT,{},'run',1,d)
            a=adapter.approval_template(m);a.update(decision='approved',reviewer='test',reviewed_at='test')
            approved=adapter.authorize(m,a,ROOT,{})
            adapter.submission(approved,ROOT,{},'run',1,d)
            for mode,n in [('preflight',1),('run',2)]:
                with self.assertRaises(BCError):adapter.submission(approved,ROOT,{},mode,n,d)
            ep=Path(d)/'episodes'/m['episodes'][0]['episode_id'];ep.mkdir(parents=True)
            atomic_json(ep/'started.json',{})
            with self.assertRaises(BCError):adapter.submission(approved,ROOT,{},'run',1,d)

    def test_catalog_pass_label_does_not_replace_reference_certificates(self):
        catalog,publics=catalog_fixture()
        with patch.object(adapter,'load_task',side_effect=lambda task,sources:({},publics[task])):
            with self.assertRaisesRegex(BCError,'qualification'):adapter.catalog_bindings(catalog,'/unused')

    def test_wrong_source_or_worker_prevents_later_evidence_loading(self):
        m,_=candidate()
        with patch.object(adapter,'source_revision',return_value='different'),patch.object(adapter.normal,'inspect') as audit:
            with self.assertRaisesRegex(BCError,'source revision'):adapter.verify(m,ROOT,{})
            audit.assert_not_called()
        with patch.object(adapter,'source_revision',return_value=m['source_revision']):
            with self.assertRaisesRegex(BCError,'worker lock'):adapter.verify(m,ROOT,{'wrong':True})


    def test_verify_rechecks_saved_audit_controls_and_request_bindings(self):
        from contextlib import ExitStack
        m,publics=candidate();worker={'test_only':'no qualification'}
        audit={'run':'/normal-double','snapshots':'/snapshot-double',
            'current_compatibility':{'checked_root':'/previous-checkout','status':'compatible'}}
        m['evidence']['normal_audit']=audit
        m['prepared']['normal_qualification_evidence']=audit
        m['prepared']['proposal_id']=digest({k:v for k,v in m['prepared'].items() if k!='proposal_id'})
        m['evidence']['controls']=dict(schema='rr-sampled-run-controls-v1',status='passed',
            implementation_hashes=adapter.control_hashes(ROOT),source_revision=m['source_revision'],
            runtime_versions=adapter.runtime_versions(),tests=200,skipped=0,failures=0,errors=0,model_executed=False,
            patterns=['test_rr_sampled_run.py','test_rr_unique_review.py','test_rr_cohort.py','test_reporecourse_scoped.py'])
        adapter.seal(m)
        fresh=deepcopy(audit);fresh['current_compatibility']['checked_root']=str(ROOT)
        with ExitStack() as stack:
            stack.enter_context(patch.object(adapter,'source_revision',return_value=m['source_revision']))
            stack.enter_context(patch.object(adapter,'versions',return_value={}))
            stack.enter_context(patch.object(adapter,'require_qualification'))
            stack.enter_context(patch.object(adapter,'catalog_bindings',return_value=(publics,{},m['configurations'])))
            inspect=stack.enter_context(patch.object(adapter.normal,'inspect',return_value=fresh))
            stack.enter_context(patch.object(adapter,'load',return_value={'model_lock_sha256':digest(worker),'model':m['model']}))
            stack.enter_context(patch.object(adapter,'check_footprint'))
            adapter.verify(m,ROOT,worker)
            inspect.return_value={**fresh,'new_unreviewed_evidence':True}
            with self.assertRaisesRegex(BCError,'Normal qualification'):adapter.verify(m,ROOT,worker)
            inspect.return_value=fresh
            bad=deepcopy(m);bad['evidence']['controls']['skipped']=1;adapter.seal(bad)
            with self.assertRaisesRegex(BCError,'no-skip'):adapter.verify(bad,ROOT,worker)


class Execution(unittest.TestCase):
    def fixture(self):
        public,plans=fixture();c=sampled.configuration(public['id'],plans[0]);s=sampled.schedule(c,public,{'worker':'double'})
        m={'prepared':{'configurations':[{'configuration':c,'schedule':s}]}}
        return m,c,public

    def test_runtime_receipt_is_new_charged_and_target_is_precommitted(self):
        m,c,public=self.fixture();saved={};calls=[]
        def execute(branches,branch,public,private,worker,save):
            calls.append(branch)
            self.assertIn('schedule',saved)
            r=Resources(**deepcopy(branches['frozen']['planning_resources']))
            self.assertGreater(r.cpu_seconds,0)
            return dict(status='completed',success=False,contract_conformant=True,resource_profile=r.summary())
        with patch.object(shared.v2,'_execute_branch',side_effect=execute),patch.object(cohort,'plan',side_effect=AssertionError('no planner')):
            result=adapter.execute_configuration(m,c,public,{},object(),lambda role:self.assertEqual(role,'json'),lambda n,x:saved.update({n:deepcopy(x)}))
        self.assertEqual(len(calls),2);self.assertEqual(result['status'],'completed')
        old=m['prepared']['configurations'][0]['schedule']
        self.assertNotEqual(result['schedule_id'],old['schedule_id'])
        self.assertEqual([x['target'] for x in result['branches']],[x['target'] for x in old['branches']['rows']])
        self.assertEqual(result['planning']['physical_generation_count'],0)
        self.assertEqual([b['resource_profile']['cpu_cap_debit'] for b in result['branches']],
            [result['planning']['planning_resources']['cpu_seconds']]*2)

    def test_actual_scoped_engine_with_model_interface_double(self):
        m,c,public=self.fixture();saved={}
        class Backend:
            def count_input(self,messages):return 100
            def generate(self,messages,cap,seed):return Generation('{"tool":"finish"}',10,0,0,{'finish_reason':'eos','constraint_cpu_seconds':0})
        result=adapter.execute_configuration(m,c,public,private_task('synthetic-nullable'),Backend(),lambda role:None,lambda n,x:saved.update({n:deepcopy(x)}))
        self.assertEqual(len(result['branches']),2)
        self.assertTrue(all(b['execution_contract']=='plan_scoped_v1' for b in result['branches']))
        self.assertTrue(all(b['resource_profile']['actual_tokens']>0 for b in result['branches']))
        self.assertTrue(all(b['success'] is False for b in result['branches']))

    def test_interruption_preserves_uncertainty_and_unrun_fault(self):
        m,c,public=self.fixture();saved={}
        def interrupt(branches,bid,public,private,worker,save):
            r=Resources(**deepcopy(branches['frozen']['planning_resources']));r.reserve(100,2048);r.reserve_cpu(31)
            save({'engine':{'resources':deepcopy(vars(r))},'branch_id':bid,'manifest_id':branches['manifest_id']})
            raise InterruptedError('CPU injected interrupt')
        with patch.object(shared.v2,'_execute_branch',side_effect=interrupt):
            result=adapter.execute_configuration(m,c,public,{},object(),lambda role:None,lambda n,x:saved.update({n:deepcopy(x)}))
        self.assertEqual([b['status'] for b in result['branches']],['interrupted','unrun'])
        resource=result['branches'][0]['resource_profile']
        self.assertEqual(resource['uncertain_tokens'],2148);self.assertEqual(resource['uncertain_cpu'],31)
        self.assertEqual(resource['reserved_tokens'],0)

    def test_changed_target_or_planning_ledger_rejected(self):
        m,c,public=self.fixture();s=deepcopy(m['prepared']['configurations'][0]['schedule'])
        s['branches']['rows'][1]['target']='w6'
        with self.assertRaises(Exception):adapter.check_runtime_schedule(m,c,s,public)
        s=deepcopy(m['prepared']['configurations'][0]['schedule']);f=s['frozen']
        f['plan']=deepcopy(f['plan']);f['plan']['units'][0]['worker']='w6'
        f['frozen_id']=digest({k:v for k,v in f.items() if k!='frozen_id'});s=cohort.schedule(c,f)
        with self.assertRaises(BCError):adapter.check_runtime_schedule(m,c,s,public)

    def test_read_only_aggregation_missing_failed_and_actual_schedule_binding(self):
        m,publics=candidate();c=m['configurations'][0];public=publics[c['task']]
        with TemporaryDirectory() as d:
            before=aggregate(m,Path(d));self.assertEqual(before['missing_configurations'],6)
            self.assertIsNone(before['by_task'][c['task']]['clean']['complete_rate'])
            ep=Path(d)/'episodes'/c['configuration_id'];ep.mkdir(parents=True)
            def save(n,x):atomic_json(ep/(n+'.json'),dict(manifest_hash=digest(m),content=x))
            def wrong(*args,**kwargs):return dict(status='completed',success=False,task_correct=False,contract_conformant=True)
            with patch.object(shared.v2,'_execute_branch',side_effect=wrong):
                r=adapter.execute_configuration(m,c,public,{},object(),lambda role:None,save)
            r.update(experiment_id=m['experiment_id'],provenance={'manifest_hash':digest(m)})
            atomic_json(ep/'result.json',r)
            report=aggregate(m,Path(d));self.assertEqual(report['missing_configurations'],5)
            self.assertEqual(report['by_task'][c['task']]['F']['known'],1)
            self.assertIsNone(report['by_task'][c['task']]['F']['complete_rate'])
            r['schedule_id']='tampered';atomic_json(ep/'result.json',r)
            with self.assertRaises(BCError):aggregate(m,Path(d))
