"""Prospective timing/coverage controls; no GPU or source downloads."""
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import cohort,v2
from reporecourse.common import Rejected,digest
from reporecourse.tasks import load_task,private_task
from reporecourse.resources import Resources
from beyond_consensus.experiments import rr_cohort as adapter
from beyond_consensus.util import BCError
from tests.test_reporecourse import optional

ROOT=Path(__file__).resolve().parents[1]

class Prospective(unittest.TestCase):
    def setUp(self):
        _,self.public=load_task('synthetic-stock','/nonexistent')
        self.c=cohort.configuration('synthetic-stock','requirement_level',target_rule='all')
        self.f=cohort.plan(self.c,self.public,{'frozen_worker':'same'})
        self.s=cohort.schedule(self.c,self.f)

    def test_commitment_and_streams(self):
        self.assertEqual(len(set(self.c['config']['seeds'].values())),4)
        self.assertEqual(self.c['seed_index'],1)
        self.assertEqual(self.c['config']['planner_output_cap'],6144)
        bad=deepcopy(self.c);bad['target_rule']='uniform'
        with self.assertRaises(Rejected):cohort.schedule(bad,self.f)
        self.assertEqual([r['target'] for r in self.s['branches']['rows']],[None,'w0','w1'])

    def test_schedule_saved_before_failure_does_not_filter_faults(self):
        saved=[];seen=[]
        def execute(m,b):
            self.assertEqual(saved[0],'schedule');seen.append(b['track'])
            self.assertNotIn('evaluation',m)
            return dict(status='completed',success=False,contract_conformant=True)
        r=cohort.run_scheduled(self.c,self.s,execute,lambda n,x:saved.append(n))
        self.assertEqual(seen,['clean','F','F']);self.assertEqual(len(r['branches']),3)
        self.assertEqual(self.s,cohort.schedule(self.c,self.f))

    def test_invalid_configuration_has_no_fabricated_episodes(self):
        f=v2.freeze(self.f['request'],self.public,{},Resources(100000,1200),[],'scripted_mock')
        s=cohort.schedule(self.c,f)
        self.assertIsNone(s['branches'])
        with patch.object(cohort,'plan',side_effect=AssertionError('no replanning')):
            result=cohort.run_scheduled(self.c,s,lambda *a:self.fail('no worker'),lambda *a:None)
        summary=cohort.summarize([self.c],{self.c['configuration_id']:result})
        self.assertEqual(summary['task_balanced']['requirement_level']['fault_configuration_mean'],0)
        self.assertEqual(result['branches'],[])
        self.assertEqual(summary['configurations'][0]['target_status'],'not_applicable_invalid_planning')

    def test_infrastructure_pause_retains_unrun(self):
        result=cohort.run_scheduled(self.c,self.s,lambda *a:dict(status='infrastructure_failed',success=None),lambda *a:None)
        self.assertEqual([b['status'] for b in result['branches']],['infrastructure_failed','unrun','unrun'])
        self.assertIsNone(cohort.summarize([self.c],{self.c['configuration_id']:result})['task_balanced']['requirement_level']['fault_configuration_mean'])

    def test_untriggered_loss_keeps_target_and_denominator(self):
        result=cohort.run_scheduled(self.c,self.s,lambda *a:dict(status='completed',success=False,no_intervention=True,intervention_triggered=False),lambda *a:None)
        self.assertEqual(len(result['branches']),3)
        self.assertEqual([b['target'] for b in result['branches'][1:]],['w0','w1'])

    def test_each_branch_gets_only_frozen_planning(self):
        copies=[]
        def execute(m,b):
            r=Resources(**deepcopy(m['frozen']['planning_resources']));copies.append(deepcopy(vars(r)))
            m['frozen']['planning_resources']['actual_tokens']=999
            return dict(status='completed',success=True,answer='not_visible_to_sibling')
        cohort.run_scheduled(self.c,self.s,execute,lambda *a:None)
        self.assertTrue(all(x==self.f['planning_resources'] for x in copies))
        self.assertEqual(self.f['planning_resources']['actual_tokens'],0)

    def test_default_uses_public_requirements_not_private_catalog(self):
        p=deepcopy(self.public);p['outlines']=[{'poison':'secret'}]
        f=cohort.plan(self.c,p,None)
        self.assertEqual(len(f['plan']['units']),len(p['required_outputs']))
        self.assertEqual(f['physical_generation_count'],0)
        self.assertGreater(f['planning_resources']['cpu_seconds'],0)
        self.assertNotIn('outlines',f['request']['planner_input'])

    def test_model_planner_can_group_outputs_no_catalog(self):
        c=cohort.configuration('synthetic-stock','prompted_open')
        p=v2.requirement_plan(self.public,c['config'])
        u=p['units'][0];other=p['units'][1]
        u['outputs']+=other['outputs'];u['produces'].update(other['produces']);p['units']=[u]
        import json
        class Backend:
            def count_input(self,m):return 10
            def generate(self,*args):return SimpleNamespace(text=json.dumps({'tool':'submit_plan','plan':p}),output_tokens=80,reasoning_tokens=5,device_seconds=0,diagnostics={})
        f=cohort.plan(c,self.public,None,Backend(),mode='scripted_mock')
        self.assertEqual(f['status'],'valid');self.assertEqual(len(f['plan']['units']),1)
        self.assertEqual(f['planning_resources']['actual_tokens'],90)
        self.assertEqual(len(cohort.schedule(c,f)['branches']['rows']),2)

    def test_task_balanced_no_success_only_cost_selection(self):
        r=cohort.run_scheduled(self.c,self.s,lambda *a:dict(status='resource_exhausted',success=False,resource_profile={'actual_tokens':100000}),lambda *a:None)
        summary=cohort.summarize([self.c],{self.c['configuration_id']:r})
        self.assertEqual(summary['task_balanced']['requirement_level']['fault_configuration_mean'],0)
        self.assertEqual(sum(b['resource_profile']['actual_tokens'] for b in summary['configurations'][0]['branches']),300000)
        with self.assertRaises(Rejected):cohort.summarize([self.c,self.c],{})

    def test_changed_frozen_or_schedule_rejected(self):
        s=deepcopy(self.s);s['branches']['rows'][0]['target']='w6'
        with self.assertRaises(Rejected):cohort.run_scheduled(self.c,s,None,None)
        f=deepcopy(self.f);f['planning_resources']['actual_tokens']=5
        with self.assertRaises(Rejected):cohort.schedule(self.c,f)

    def test_scoped_manifest_counts_no_approval_bypass(self):
        stock=adapter.build(ROOT,'/nonexistent','stock_protocol')
        rich=adapter.build(ROOT,'/nonexistent','rich_pilot')
        self.assertEqual(stock['maximum_execution_branches'],8)
        self.assertEqual(rich['maximum_execution_branches'],16)
        self.assertEqual(rich['maximum_model_planning_sequences'],4)
        self.assertEqual(rich['maximum_logical_tokens'],1600000)
        self.assertEqual(len(rich['configurations']),8)
        self.assertFalse(stock['task_execution_allowed'])
        adapter.validate(stock)
        with self.assertRaises(BCError):adapter.authorize(stock,adapter.approval_template(stock),ROOT,{})
        bad=deepcopy(stock);bad['model']['max_new_tokens']=4096;adapter.seal(bad)
        with self.assertRaises(BCError):adapter.validate(bad)

    def test_scheduler_and_backend_injection_stay_gated(self):
        from beyond_consensus.experiments.runner import run_manifest
        from beyond_consensus.experiments.cluster import submit,ClusterConfig
        m=adapter.build(ROOT,'/nonexistent','stock_protocol')
        with TemporaryDirectory() as d:
            with self.assertRaises(BCError):run_manifest(m,Path(d),ROOT,backend=object())
            with self.assertRaises(BCError):adapter.submission(m,ROOT,{},'run',2,d)
            with patch('beyond_consensus.experiments.cluster.command',side_effect=AssertionError('No scheduler call before gates')):
                with self.assertRaises(BCError):submit(ROOT,ClusterConfig("test","00:30:00",32,"/usr/bin/python",d,d,d,d),m,{},1,dry_run=True)

    def test_cap_unknown_usage_preserved(self):
        r=Resources(100,1200);k=r.reserve(10,80);r.reconcile(k)
        self.assertEqual(r.uncertain_tokens,90)
        with self.assertRaises(Rejected):r.reserve(11,1)

    def test_resealed_false_ledger_rejected(self):
        f=deepcopy(self.f);f['planning_resources']['actual_tokens']=10
        f['frozen_id']=digest({k:v for k,v in f.items() if k!='frozen_id'})
        with self.assertRaises(Rejected):cohort.schedule(self.c,f)

    def test_missing_final_result_recovers_unrun_schedule_without_resume(self):
        from beyond_consensus.util import atomic_json
        m=adapter.build(ROOT,'/nonexistent','stock_protocol');c=m['configurations'][0]
        f=v2.freeze(v2.request(self.public,c['config']),self.public,v2.requirement_plan(self.public,c['config']),Resources(100000,1200),[],'scripted_mock')
        s=cohort.schedule(c,f)
        with TemporaryDirectory() as d:
            ep=Path(d)/'episodes'/c['configuration_id'];ep.mkdir(parents=True)
            atomic_json(ep/'schedule.json',{'manifest_hash':digest(m),'content':s})
            b=s['branches']['rows'][0]
            atomic_json(ep/('branch-start-'+b['branch_id']+'.json'),{'manifest_hash':digest(m),'content':{'schedule_id':s['schedule_id']}})
            r=adapter.aggregate(m,d)['configurations'][0]
            self.assertEqual([b['status'] for b in r['branches']],['interrupted','unrun','unrun'])
            self.assertIsNone(r['clean_success'])

    def test_approval_scope_cannot_expand_or_rebind(self):
        m=adapter.build(ROOT,'/nonexistent','stock_protocol');r=adapter.approval_template(m)
        r.update(decision='approved',reviewer='test reviewer',reviewed_at='2026-10-08')
        with patch.object(adapter,'verify'):
            approved=adapter.authorize(m,r,ROOT,{})
        adapter.validate(approved)
        bad=deepcopy(approved);bad['approval']['maximum_execution_branches']=9;adapter.seal(bad)
        with self.assertRaises(BCError):adapter.validate(bad)

    def test_footprint_public_scenario_is_reproducible(self):
        a=adapter.prompt_cases(self.public);b=adapter.prompt_cases(self.public)
        self.assertEqual(digest(a),digest(b))
        self.assertTrue(any(c['id'].startswith('worker_initial') for c in a))
        self.assertTrue(all(c['role'] in ('plan','json') for c in a))

    def test_negative_offset_ledger_rejected(self):
        f=deepcopy(self.f)
        f['planning_resources']['events'] += [dict(kind='model_usage',input_tokens=-2,output_tokens=2)]
        f['frozen_id']=digest({k:v for k,v in f.items() if k!='frozen_id'})
        with self.assertRaises(Rejected):cohort.schedule(self.c,f)

    def test_planning_infrastructure_pauses_without_worker_targets(self):
        f=deepcopy(self.f);f.update(status='planning_infrastructure_failure',plan=None)
        f['frozen_id']=digest({k:v for k,v in f.items() if k!='frozen_id'})
        s=cohort.schedule(self.c,f)
        r=cohort.run_scheduled(self.c,s,lambda *a:self.fail('No worker'),lambda *a:None)
        self.assertEqual(r['status'],'paused');self.assertEqual(r['branches'],[])
        self.assertEqual(r['target_status'],'unresolved_planning_failure')

    def test_interrupted_planning_retains_uncertain_reservation(self):
        from beyond_consensus.util import atomic_json
        m=adapter.build(ROOT,'/nonexistent','stock_protocol');c=m['configurations'][0]
        resources=Resources(100000,1200);resources.reserve(100,6144)
        with TemporaryDirectory() as d:
            ep=Path(d)/'episodes'/c['configuration_id'];ep.mkdir(parents=True)
            atomic_json(ep/'started.json',{'manifest_hash':digest(m)})
            atomic_json(ep/'planner-journal.json',{'manifest_hash':digest(m),'content':{'resources':vars(resources)}})
            row=adapter.aggregate(m,d)['configurations'][0]
            self.assertEqual(row['status'],'interrupted')
            self.assertEqual(row['interrupted_planning_usage']['uncertain_tokens'],6244)
            self.assertEqual(row['branches'],[])

    def test_global_pause_and_unresolved_started_configuration_block(self):
        from beyond_consensus.util import atomic_json
        m=adapter.build(ROOT,'/nonexistent','stock_protocol');receipt=adapter.approval_template(m)
        receipt.update(decision='approved',reviewer='test',reviewed_at='2026-10-08')
        with patch.object(adapter,'verify'):m=adapter.authorize(m,receipt,ROOT,{})
        with TemporaryDirectory() as d,patch.object(adapter,'verify'):
            atomic_json(Path(d)/'cohort-pause.json',{'reason':'infrastructure_failed'})
            with self.assertRaisesRegex(BCError,'paused'):adapter.submission(m,ROOT,{},'run',1,d)
            (Path(d)/'cohort-pause.json').unlink()
            ep=Path(d)/'episodes'/m['episodes'][0]['episode_id'];ep.mkdir(parents=True)
            atomic_json(ep/'started.json',{'manifest_hash':digest(m)})
            with self.assertRaisesRegex(BCError,'Unresolved started'):adapter.submission(m,ROOT,{},'run',1,d)

    @unittest.skipUnless(optional(),'Pinned optional execution dependencies required')
    def test_both_planners_use_actual_scoped_engine_and_common_repair(self):
        import json
        from tests.test_reporecourse_scoped import pub
        for planner in cohort.PLANNERS:
            c=cohort.configuration('synthetic-stock',planner)
            plan=v2.requirement_plan(self.public,c['config'])
            # The model double chooses a grouped plan, outside the default
            # requirement allocation; its actual scopes drive both branches.
            plan['units'][0]['outputs']+=plan['units'][1]['outputs']
            plan['units'][0]['produces'].update(plan['units'][1]['produces'])
            plan['units']=plan['units'][:1]
            class Backend:
                role='json'
                def count_input(self,_):return 100
                def generate(self,messages,*args):
                    if self.role=='plan':action={'tool':'submit_plan','plan':plan}
                    else:
                        obs=json.loads(messages[-1]['content'])
                        missing=[o for o in obs['assigned_outputs'] if o not in obs['bound']]
                        if not missing:action={'tool':'finish'}
                        else:
                            name=missing[0]
                            sql='SELECT sku, qty FROM stock ORDER BY sku' if name=='stock_report' else 'SELECT sku FROM stock WHERE qty=0 ORDER BY sku'
                            action=pub(name,sql,fmt='sql',outputs=[name])
                    return SimpleNamespace(text=json.dumps(action),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
            backend=Backend();saved={}
            m={'model':adapter.model_settings(),'model_lock_sha256':'mock','backend_profile':{'planner_lock':{}}}
            result=adapter.execute_configuration(m,c,self.public,private_task('synthetic-stock'),backend,
                lambda role:setattr(backend,'role',role),lambda name,value:saved.update({name:deepcopy(value)}))
            self.assertEqual(result['status'],'completed')
            self.assertEqual(len(result['branches']),2)
            self.assertTrue(all(b['success'] and b['contract_conformant'] for b in result['branches']))
            self.assertTrue(result['branches'][1]['intervention_triggered'])
            f=result['planning'];planning_tokens=180 if planner=='prompted_open' else 0
            self.assertEqual(f['planning_resources']['actual_tokens'],planning_tokens)
            self.assertEqual(len(f['plan']['units']),1 if planner=='prompted_open' else 2)
            for branch in result['branches']:
                events=branch['resource_profile']['events']
                self.assertEqual(events[:len(f['planning_resources']['events'])],f['planning_resources']['events'])
            self.assertEqual(saved['schedule']['frozen'],f)


if __name__=='__main__':unittest.main()
