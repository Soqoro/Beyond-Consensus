"""v0.2 behavior controls; real child tests explicitly depend on pinned CPU libs."""
import copy
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import v2
from reporecourse.common import Rejected,digest
from reporecourse.engine import Engine,ScriptedWorker
from reporecourse.runtime import Environment
from reporecourse.resources import Resources
from reporecourse.tasks import load_task,private_task
from tests.test_reporecourse import optional


def task(name='synthetic-stock'):return load_task(name,Path('/nonexistent-sources'))[1]

def prepared(n=4,outline='independent',name='synthetic-stock',**kw):
    p=task(name);c=v2.configuration(n,**kw);plan=v2.authored_plan(p,c,outline)
    req=v2.request(p,c);f=v2.freeze(req,p,plan,Resources(100000,1200),[],'scripted_mock')
    return p,c,plan,v2.resolve_branches(f)


class Contracts(unittest.TestCase):
    def test_every_pool_and_topology_owner_invariance(self):
        p=task()
        for n in range(2,9):
            c=v2.configuration(n)
            p1=v2.authored_plan(p,c,'shared');p2=copy.deepcopy(p1)
            p2['units'][0]['worker']=f'w{n-1}'
            self.assertEqual(v2.descriptors(p1)['structural_key'],v2.descriptors(p2)['structural_key'])
            self.assertNotEqual(v2.descriptors(p1)['structural_key'],v2.descriptors(v2.authored_plan(p,c,'grouped'))['structural_key'])
            self.assertEqual(len(v2.worker_registry(n)),n)
        for n in (1,9,True):
            with self.assertRaises(Rejected):v2.worker_registry(n)

    def test_dag_sort_cycles_interfaces_and_unused_helpers(self):
        p,c,plan,_=prepared(outline='shared')
        plan['units'].reverse()
        valid=v2.validate_work_plan(plan,p,c)
        self.assertEqual(valid['units'][0]['id'],'shared_base')
        wrong=copy.deepcopy(valid);wrong['units'][-1]['consumes']['shared_base']['format']='mapping'
        with self.assertRaises(Rejected):v2.validate_work_plan(wrong,p,c)
        wrong=copy.deepcopy(valid);wrong['units'][-1]['produces']['shared_base']='sql'
        with self.assertRaisesRegex(Rejected,'ambiguous_artifact_producer'):v2.validate_work_plan(wrong,p,c)
        wrong=copy.deepcopy(valid);wrong['units'][0]['depends']=['zero_report']
        with self.assertRaises(Rejected):v2.validate_work_plan(wrong,p,c)
        wrong=copy.deepcopy(valid);wrong['units'].append({**copy.deepcopy(valid['units'][0]),'id':'unused'})
        with self.assertRaises(Rejected):v2.validate_work_plan(wrong,p,c)

    def test_matched_count_and_no_idle_targets(self):
        p,c,plan,m=prepared(8,target_rule='all')
        self.assertEqual([r['target'] for r in m['rows']],[None,'w0','w1'])
        self.assertEqual(m['planned_episodes'],3)
        c=v2.configuration(8,'matched_primary_count',2)
        v2.validate_work_plan(plan,p,c)
        c['primary_count']=3
        with self.assertRaises(Rejected):v2.validate_work_plan(plan,p,c)
        with self.assertRaises(Rejected):v2.configuration(8,recovery='restart')

    def test_every_fixture_organization_has_explicit_reference_driver(self):
        for name in ('synthetic-stock','synthetic-nullable'):
            public=task(name);private=private_task(name);original=copy.deepcopy(private)
            for pool in range(2,9):
                config=v2.configuration(pool,lane='fixed_plan')
                for organization in ('independent','shared','grouped','branch_rejoin'):
                    driver=v2.fixture_witness(public,private,config,organization)
                    self.assertEqual(driver['organization'],organization)
                    covered=[o for row in driver['actions'] for o in row['action']['obligations']]
                    self.assertCountEqual(covered,[r['id'] for r in public['required_outputs']])
                    if organization=='grouped':
                        independent=next(w for w in private['witnesses'] if w['organization']=='independent')
                        self.assertEqual(driver['actions'],independent['actions'])
                        self.assertEqual(driver['reference_program_source'],'independent')
                        plan=v2.authored_plan(public,config,organization)
                        self.assertEqual(len(plan['units']),1)
                        self.assertEqual(len({u['worker'] for u in plan['units']}),1)
            self.assertEqual(private,original)
            with self.assertRaisesRegex(Rejected,'fixture_witness_unavailable'):
                v2.fixture_witness(public,private,config,'not-an-organization')

    def test_schema_registry_bound_and_no_planner_publication(self):
        from reporecourse.action_schema import schema_v2
        for n in range(2,9):
            s=schema_v2(f'reporecourse-json-v2-pool-{n}')
            message=next(a for a in s['anyOf'] if a['properties']['tool']['enum']==['message'])
            self.assertEqual(message['properties']['recipient']['enum'],list(v2.worker_registry(n)))
            planner=schema_v2(f'reporecourse-plan-v2-pool-{n}')
            self.assertNotIn('publish',[a['properties']['tool']['enum'][0] for a in planner['anyOf']])
        self.assertNotEqual(digest(schema_v2('reporecourse-json-v2-pool-4')),digest(schema_v2('reporecourse-json-v2-pool-8')))

    def test_freeze_targets_invalid_retained_and_public_input(self):
        p,c,plan,m=prepared(7,target_rule='all')
        visible=m['frozen']['request']['planner_input']
        for forbidden in ('outlines','witnesses','target','evaluation','seeds'):
            self.assertNotIn(forbidden,visible)
        req=v2.request(p,c)
        f=v2.freeze(req,p,{},Resources(100000,1200),[],'scripted_mock')
        bad=v2.resolve_branches(f)
        self.assertEqual(len(bad['rows']),2)
        self.assertTrue(all(b['status']=='invalid_plan' for b in bad['rows']))
        agg=v2.aggregate_v2([bad],[])
        self.assertTrue(all(g['complete_at_budget']==0 for g in agg['groups'].values()))
        changed=copy.deepcopy(f);changed['status']='valid'
        with self.assertRaises(Rejected):v2.resolve_branches(changed)

    def test_planner_revision_reads_and_charging(self):
        p,c,plan,m=prepared()
        class Backend:
            context_limit=16384
            def __init__(self):self.calls=0;self.inputs=[]
            def count_input(self,m):self.inputs.append(copy.deepcopy(m));return 10
            def generate(self,m,cap,seed):
                answers=[{'tool':'read_source','name':'request'},{'tool':'submit_plan','plan':{}},{'tool':'submit_plan','plan':plan}]
                answer=answers[self.calls];self.calls+=1
                return SimpleNamespace(text=json.dumps(answer),output_tokens=5,reasoning_tokens=2,device_seconds=0,diagnostics={})
        backend=Backend();f=v2.PromptedPlanner(backend,evidence_mode="scripted_mock").run(v2.request(p,c),p)
        self.assertEqual(f['status'],'valid');self.assertEqual(f['planning_resources']['actual_tokens'],45)
        self.assertEqual(len(f['planning_events']),3)
        self.assertNotIn('outlines',backend.inputs[0][1]['content'])
        branches=v2.resolve_branches(f)
        self.assertEqual(branches['frozen']['planning_resources']['actual_tokens'],45)

    def test_planner_context_failure_releases_cpu_admission_estimate(self):
        p,c,plan,m=prepared()
        class TooLong:
            context_limit=100
            def count_input(self,m):return 200
            def generate(self,*a):raise AssertionError('must not generate')
        f=v2.PromptedPlanner(TooLong(),evidence_mode='scripted_mock').run(v2.request(p,c),p)
        self.assertEqual(f['status'],'invalid_plan')
        self.assertEqual(f['physical_generation_count'],0)
        self.assertEqual(f['planning_resources']['actual_tokens'],0)
        self.assertFalse(f['planning_resources']['cpu_pending'])
        self.assertEqual(f['planning_resources']['uncertain_cpu'],0)
        events=[e for e in f['planning_resources']['events'] if e.get('category')=='planner_failed_call_host']
        self.assertTrue(events)
        self.assertTrue(all(e['cap_debit']==e['actual_cpu_seconds'] for e in events))

    def test_plan_selection_requires_measured_compatible_costs(self):
        p=task();c=v2.configuration(lane='shared_catalog');req=v2.request(p,c)
        plans=[v2.authored_plan(p,c,n) for n in ('independent','shared')]
        f=v2.shared_catalog(req,p,plans,Resources(100000,1200))
        self.assertEqual(f['catalog']['candidate_hash'],digest(plans))
        with self.assertRaises(Rejected):v2.shared_catalog(req,p,plans,Resources(100000,1200),selector='recovery')

    def test_upper_identity_messages_loss_and_checkpoint(self):
        p,c,plan,m=prepared(8)
        env=Environment(p,workers=v2.worker_registry(8),active=('w7',),track='F',target='w7')
        try:
            env.assignment['w7']={'id':'stock_report','outputs':['stock_report']}
            env.action('w6',{'tool':'message','recipient':'w7','text':'public'})
            self.assertEqual(env.messages['w7'][0]['sender'],'w6')
            stale=env.state()
            with self.assertRaisesRegex(Rejected,'worker_unavailable'):
                env.action('w7',{'tool':'publish','name':'stock_report','format':'sql','content':'SELECT 1','bindings':{},'obligations':['stock_report']})
            self.assertFalse(env.artifacts)
            with self.assertRaises(Rejected):env.restore_state(stale)
            with self.assertRaises(Rejected):env.action('w7',{'tool':'finish'})
        finally:env.close()

    def test_branch_resume_incompatible_and_no_new_worker(self):
        class Finisher:
            mode='scripted_mock'
            def next_action(self,*args):return {'tool':'finish'}
        p,c,plan,m=prepared(2)
        e=Engine(p,Finisher(),plan=plan,v2=c)
        try:
            state=e.checkpoint();bad=copy.deepcopy(state);bad['compatibility']='wrong'
            with self.assertRaises(Rejected):e.restore(bad)
            e.restore(state);e.run()
            self.assertEqual(set(e.histories),{'w0','w1'})
            self.assertTrue(e.trajectories)
        finally:e.env.close()


class Reports(unittest.TestCase):
    def test_task_balanced_missing_and_group_leakage(self):
        manifests=[];results=[]
        for n,tid,count in ((8,'a',1),(8,'b',2)):
            p,c,plan,m=prepared(n,target_rule='all')
            # Distinct immutable tasks, not duplicated target rows.
            p['id']=tid;req=v2.request(p,c)
            if count==1:
                plan=v2.authored_plan(p,c,'grouped')
            m=v2.resolve_branches(v2.freeze(req,p,plan,Resources(100000,1200),[],'scripted_mock'))
            # Pool held constant in score group to isolate task weighting.
            manifests.append(m)
            for b in m['rows']:
                results.append(dict(branch_id=b['branch_id'],provenance=m['manifest_id'],status='completed',success=tid=='a',mode='scripted_mock'))
        summary=v2.aggregate_v2(manifests,results)
        self.assertEqual(len(summary['groups']),2)
        self.assertTrue(all(g['complete_at_budget']==0.5 for g in summary['groups'].values()))
        provisional=v2.aggregate_v2(manifests,results[:-1])
        self.assertTrue(any(g['provisional'] for g in provisional['groups'].values()))
        with self.assertRaises(Rejected):v2.validate_splits([{'id':'a','source_group':'x'},{'id':'b','source_group':'x'}],{'a':'train','b':'test'})
        self.assertEqual(v2.coverage([2,3,4,6],[5,8],[2])['pool_tests'],{'5':'interpolation','8':'extrapolation'})

    def test_export_inputs_labels_and_reference_guard(self):
        p,c,plan,m=prepared()
        r=[dict(branch_id=b['branch_id'],provenance=m['manifest_id'],status='completed',success=False,mode='scripted_mock',trajectories=[]) for b in m['rows']]
        export=v2.training_export(m,r,[{'id':p['id'],'source_group':'fixture'}],{p['id']:'dev'},'dev')
        self.assertNotIn('target',export['records'][0]['inputs'])
        self.assertIn('target',export['records'][1]['targets']['branch'])
        r[0]['mode']='scripted_reference'
        with self.assertRaises(Rejected):v2.training_export(m,r,[{'id':p['id'],'source_group':'fixture'}],{p['id']:'dev'},'dev','event_trajectories')

    def test_different_planners_not_pooled_and_not_prompt_labels(self):
        p,c,plan,m=prepared()
        other=copy.deepcopy(c);other['planner']='different_adapter'
        request=v2.request(p,other)
        self.assertNotIn('planner',request['planner_input'])
        second=v2.resolve_branches(v2.freeze(request,p,plan,Resources(100000,1200),[],'scripted_mock'))
        self.assertEqual(len(v2.aggregate_v2([m,second],[])['groups']),4)
        self.assertTrue(v2.paired_comparison([m,second])['compatible'])

    def test_b0_censored_never_winners_only(self):
        rows=[{'family':'f','worker_binding':'w','status':'completed','usage_complete':True,'actual_tokens':20,'success':False}]*2
        self.assertEqual(v2.estimate_b0(rows,minimum=2,family='f',worker_binding='w')['B0'],20)
        rows[0]={**rows[0],'status':'resource_exhausted'}
        self.assertEqual(v2.estimate_b0(rows,minimum=2,family='f',worker_binding='w')['status'],'uncalibrated')


@unittest.skipUnless(optional(),'pinned optional CPU dependencies unavailable')
class ExecutableFamilies(unittest.TestCase):
    def test_both_families_all_pools_reference_clean_and_loss(self):
        for name in ('synthetic-stock','synthetic-nullable'):
            private=private_task(name)
            for pool in range(2,9):
                for outline in ('independent','shared','grouped','branch_rejoin'):
                    p,c,plan,m=prepared(pool,'independent' if outline=='branch_rejoin' else outline,name,lane='fixed_plan',target_rule='all')
                    if outline=='branch_rejoin':
                        plan,_=v2.fixture_rejoin(p,c)
                        m=v2.resolve_branches(v2.freeze(v2.request(p,c),p,plan,Resources(100000,1200),[],'scripted_reference'))
                    witness=v2.fixture_witness(p,private,c,outline)
                    for b in m['rows']:
                        with self.subTest(task=name,pool=pool,outline=outline,target=b['target']):
                            row=v2.run_branch(m,b['branch_id'],p,private,ScriptedWorker(witness))
                            self.assertTrue(row['success'])
                            self.assertLessEqual(row['K_total_observed'],pool)
                            if b['target']:self.assertTrue(row['intervention_triggered'])


    def test_common_jit_rebinds_unchanged_consumer_without_model_call(self):
        from reporecourse.v2_recovery import reuse_consumer
        p,c,plan,m=prepared(2,'shared','synthetic-nullable',lane='fixed_plan')
        class NoGeneration:
            mode='scripted_mock'
            def next_action(self,*args):raise AssertionError('unnecessary model regeneration')
        e=Engine(p,NoGeneration(),plan=plan,v2=c)
        try:
            bad={'type':'object','properties':{'id':{'type':'integer'},'note':{'type':'string'}},'required':['id','note'],'additionalProperties':False}
            old=e.env.publish('w0','shared_base','schema',bad,{},[])['version']
            consumer=e.env.publish('w1','response','schema',{'$ref':'rr:base'},{'base':old},['response'])['version']
            fixed=copy.deepcopy(bad);fixed['properties']['note']['type']=['string','null']
            replacement=e.env.publish('w0','shared_base','schema',fixed,{},[])['version']
            e.env.bound.pop('response')
            unit=next(u for u in plan['units'] if u['outputs']==['response'])
            self.assertTrue(reuse_consumer(e,unit,'w1'))
            selected=e.env.artifacts[e.env.bound['response']]
            self.assertEqual(selected['content'],e.env.artifacts[consumer]['content'])
            self.assertEqual(selected['bindings'],{'base':replacement})
            self.assertEqual(e.env.artifacts[consumer]['bindings'],{'base':old})
            self.assertEqual(e.env.resources.actual_tokens,0)
            self.assertTrue(any(x['type']=='jit_reexecute' for x in e.env.events))
        finally:e.env.close()


class BranchControls(unittest.TestCase):
    class Finisher:
        mode='scripted_mock'
        def next_action(self,*args):return {'tool':'finish'}

    def test_planning_usage_all_branches_and_resume_no_token_replay(self):
        p,c,plan,_=prepared(2,target_rule='all')
        ledger=Resources(100000,1200);key=ledger.reserve(11,9);ledger.reconcile(key,7,3)
        f=v2.freeze(v2.request(p,c),p,plan,ledger,[],'scripted_mock');m=v2.resolve_branches(f)
        for b in m['rows']:
            row=v2.run_branch(m,b['branch_id'],p,private_task(p['id']),self.Finisher())
            self.assertEqual(row['resource_profile']['actual_tokens'],18)
            self.assertEqual(row['K_primary_observed'],2)
            if b['track']=='F':
                self.assertFalse(row['intervention_triggered'])
                self.assertEqual(row['nontrigger_reason'],'selected_identity_never_reached_handoff')
            resumed=v2.run_branch(m,b['branch_id'],p,private_task(p['id']),self.Finisher(),checkpoint=row['checkpoint'])
            self.assertEqual(resumed['resource_profile']['actual_tokens'],18)
            self.assertEqual(len(resumed['trajectories']),len(row['trajectories']))
            other=next(x for x in m['rows'] if x!=b)
            with self.assertRaises(Rejected):v2.run_branch(m,other['branch_id'],p,private_task(p['id']),self.Finisher(),checkpoint=row['checkpoint'])

    def test_runtime_hash_is_frozen_and_rejects_changed_code(self):
        from unittest.mock import patch
        p,c,plan,m=prepared()
        before=v2.compatibility(m)
        with patch('reporecourse.qualification.implementation_hashes',return_value={'changed':'yes'}):
            self.assertEqual(v2.compatibility(m),before)
            with self.assertRaisesRegex(Rejected,'frozen_runtime_changed'):
                v2.run_branch(m,m['rows'][0]['branch_id'],p,private_task(p['id']),self.Finisher())

    def test_fixed_state_policy_change_only_in_separate_lane(self):
        from reporecourse.recovery import freeze,resume
        p,c,plan,m=prepared(2,lane='fixed_plan',threat='F')
        e=Engine(p,self.Finisher(),plan=plan,v2=c,track='F',target='w0')
        target=None
        try:
            e.phase='repair';e.env.unavailable.add('w0');e.env.triggered=True
            snapshot=freeze(e,{'unavailable':['w0'],'localization':'announced_loss'})
            alternate=copy.deepcopy(c);alternate['threat']='R';alternate['recovery']='restart'
            frozen=v2.freeze(v2.request(p,alternate),p,plan,Resources(100000,1200),[],'scripted_mock')
            with self.assertRaisesRegex(Rejected,'R_requires_common_incident'):v2.resolve_branches(frozen)
            branches=v2.resolve_branches(frozen,snapshot)
            self.assertEqual([(b['track'],b['target']) for b in branches['rows']],[('R','w0')])
            self.assertEqual(branches['incident_hash'],snapshot['fixed_state_hash'])
            target=Engine(p,self.Finisher(),policy='restart',plan=plan,v2=alternate,track='R',target='w0')
            resume(target,snapshot,100000,1200)
            self.assertEqual(target.env.unavailable,{'w0'})
            self.assertEqual(target.env.track,'R')
            self.assertIsNotNone(target.historical_resources)
            changed=copy.deepcopy(alternate);changed['pool_size']=3;changed['workers']=list(v2.worker_registry(3))
            other=Engine(p,self.Finisher(),plan=plan,v2=changed,track='R')
            try:
                with self.assertRaises(Rejected):resume(other,snapshot,100000,1200)
            finally:other.env.close()
        finally:
            e.env.close()
            if target:target.env.close()

    def test_standalone_import_without_bc_or_site_packages(self):
        import subprocess
        script="import sys;sys.path.insert(0,'src');from reporecourse.v2_cli import main;assert not any(k.startswith('beyond_consensus') for k in sys.modules)"
        result=subprocess.run([sys.executable,'-I','-S','-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
