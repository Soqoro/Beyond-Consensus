"""Plan scoped controls. Doubles are not GPU/model competence observations."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from reporecourse import v2
from reporecourse.common import Rejected,digest
from reporecourse.runtime import Environment
from reporecourse.engine import Engine,ScriptedWorker,ModelWorker
from reporecourse.resources import Resources
from reporecourse.tasks import load_task,private_task
from reporecourse.conformance import report
from reporecourse.scope import validate_bundle
from tests.test_reporecourse import optional


def prepared(task='synthetic-nullable',pool=2,outline='independent',contract='plan_scoped_v1'):
    p=load_task(task,Path('/not-needed'))[1]
    c=v2.configuration(pool,planning_lane='authored_diagnostic',execution_contract=contract)
    plan=v2.authored_plan(p,c,outline)
    plan['units'].sort(key=lambda u:(len(u['depends']), 'mapping' in u['produces'].values()))
    return p,c,plan


def pub(name,content=True,bindings=None,fmt='schema',outputs=None):
    return dict(tool='publish',name=name,format=fmt,content=content,bindings=bindings or {},obligations=outputs or [])


class ScopedTests(unittest.TestCase):
    def env(self,plan=None,**kw):
        p,c,base=prepared(**kw);plan=plan or base
        e=Environment(p,Resources(100000,1200),workers=c['workers'],plan=plan,execution_contract=c['execution_contract'])
        self.addCleanup(e.close);return e,p,c,plan

    def begin(self,e,u,stage='primary',worker=None):
        w=worker or u['worker']
        if e.scopes:e.scopes.begin(u,w,stage)
        e.assignment[w]=deepcopy(u)
        return w

    def test_config_legacy_unchanged_and_new_contract_identity(self):
        old=v2.configuration(7);self.assertNotIn('execution_contract',old)
        self.assertEqual(old['protocol'],'rr-planning-v2')
        new=v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        self.assertNotEqual(old['protocol'],new['protocol']);v2.check_config(new)
        with self.assertRaises(Rejected):v2.configuration(7,planning_lane='open_generated')

    def test_independent_metadata_binding_read_execute_denied_but_originals_available(self):
        e,p,c,plan=self.env();u,v=plan['units'];w=self.begin(e,u)
        version=e.action(w,pub(u['outputs'][0],outputs=u['outputs']))['version']
        w=self.begin(e,v);obs=e.observation(w)
        self.assertEqual(obs['artifacts'],[]);self.assertEqual(obs['bound'],{})
        self.assertEqual(e.action(w,{'tool':'read_source','name':'request'}),p['request'])
        for tool in ('read_artifact','execute_artifact','bind_output','rebind_artifact'):
            a={'tool':tool,'version':version}
            if tool=='execute_artifact':a['input_id']='default'
            if tool=='bind_output':a['obligation']=v['outputs'][0]
            if tool=='rebind_artifact':a.update(name=v['outputs'][0],bindings={},obligations=v['outputs'])
            with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(w,a)
        with self.assertRaisesRegex(Rejected,'scope_denied'):
            e.action(w,pub(v['outputs'][0],{'$ref':'rr:peer'},{'peer':version},outputs=v['outputs']))
        with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(w,{'tool':'read_artifact','version':'does-not-exist'})
        self.assertFalse(e.triggered);self.assertEqual(e.scopes.data['overlays'],[])
        self.assertEqual(e.action(w,{'tool':'check_public'}),{v['outputs'][0]:False})

    def test_declared_import_transitive_not_direct_and_unused_allowed(self):
        e,p,c,plan=self.env(outline='shared');base,a,b=plan['units']
        w=self.begin(e,base);version=e.action(w,pub(base['id']))['version']
        w=self.begin(e,a);self.assertEqual(e.observation(w)['artifacts'][0]['version'],version)
        # Can ignore helper and construct from original public contract.
        out=e.action(w,pub(a['outputs'][0],False,outputs=a['outputs']))['version']
        self.assertEqual(e.artifacts[out]['bindings'],{})
        validate_bundle(e.state())
        result=report({'plan':plan,'state':e.state(),'status':'completed'})
        self.assertTrue(result['contract_conformant']);self.assertTrue(result['allowed_not_observed'])
        self.assertTrue(result['observed_exposures'])

    def test_legacy_peer_reuse_preserved(self):
        e,p,c,plan=self.env(contract='adaptive_legacy');u,v=plan['units'];w=self.begin(e,u)
        version=e.action(w,pub(u['outputs'][0],outputs=u['outputs']))['version']
        w=self.begin(e,v);self.assertIn(version,[a['version'] for a in e.observation(w)['artifacts']])
        # Safe schema reuse is allowed by old runtime, with explicit binding.
        e.action(w,pub(v['outputs'][0],{'fields':{},'output_schema':{'$ref':'rr:peer'}}, {'peer':version},fmt='mapping',outputs=v['outputs']))

    def test_messages_checkpoint_and_restore_scoped(self):
        e,p,c,plan=self.env();u,v=plan['units'];w=self.begin(e,u)
        cp=e.action(w,{'tool':'checkpoint'})['checkpoint']
        with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(w,{'tool':'message','recipient':v['worker'],'text':'peer secret'})
        self.begin(e,v)
        with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(v['worker'],{'tool':'restore','checkpoint':cp})
        with self.assertRaisesRegex(Rejected,'recovery_trigger_required'):e.scopes.begin(v,v['worker'],'repair')

    def test_predecessor_messages_and_recovery_overlay_are_explicit(self):
        e,p,c,plan=self.env(outline='shared');u,v,_=plan['units'];w=self.begin(e,u)
        version=e.action(w,pub(u['id']))['version']
        e.action(w,{'tool':'message','recipient':v['worker'],'text':'untrusted predecessor note'})
        w=self.begin(e,v);self.assertEqual(len(e.observation(w)['messages']),1)
        e.unavailable.add(u['worker']);e.events.append({'type':'unavailable','announcement':{'worker':u['worker'],'unavailable':True,'assignment':u['id']}})
        e.scopes.begin(v,w,'repair');s=e.scopes.current(w)
        self.assertEqual(s['imports'],{u['id']:version});self.assertEqual(s['context_imports'],[])
        self.assertEqual(len(e.scopes.data['overlays']),1)
        self.assertIn(u['worker'],e.unavailable)
        self.assertNotIn('target',json.dumps(s['trigger']))

    def test_unpublished_or_mutated_final_bundle_rejected(self):
        e,p,c,plan=self.env();u=plan['units'][0];w=self.begin(e,u)
        version=e.action(w,pub(u['outputs'][0],outputs=u['outputs']))['version']
        state=e.state();validate_bundle(state)
        bad=deepcopy(state);bad['artifacts'][version]['content']=False
        with self.assertRaisesRegex(Rejected,'scope_integrity'):validate_bundle(bad)
        bad=deepcopy(state);bad['scope_state']['receipts']={}
        with self.assertRaisesRegex(Rejected,'scope_integrity'):validate_bundle(bad)
        bad=deepcopy(state);bad['bound'][u['outputs'][0]]='unpublished'
        with self.assertRaises(Rejected):validate_bundle(bad)

    def test_schema_nested_reference_cannot_use_global_peer_registry(self):
        e,p,c,plan=self.env(outline='shared');u,v,_=plan['units'];w=self.begin(e,u)
        version=e.action(w,pub(u['id'],{'type':'integer'}))['version']
        w=self.begin(e,v)
        # A reference is legal only through its explicit direct binding.
        with self.assertRaisesRegex(Rejected,'schema_reference'):e.action(w,pub(v['outputs'][0],{'$ref':'rr:'+u['id']},outputs=v['outputs']))
        e.action(w,pub(v['outputs'][0],{'$ref':'rr:'+u['id']},{u['id']:version},outputs=v['outputs']))
        validate_bundle(e.state())

    def test_same_owner_histories_are_reset_and_resume_bound(self):
        p,c,plan=prepared();plan['units'][1]['worker']='w0'
        seen=[]
        class Worker:
            mode='scripted_mock'
            def next_action(self,public,unit,observation,history,*args):
                seen.append((unit['id'],deepcopy(history),deepcopy(observation)));return {'tool':'finish'}
        eng=Engine(p,Worker(),plan=plan,v2=c,resources=Resources(100000,1200));self.addCleanup(eng.env.close)
        for u in plan['units']:eng.unit(u,'w0','primary')
        self.assertTrue(all(not h for _,h,_ in seen));self.assertEqual(len(seen),2)
        checkpoint=eng.checkpoint();eng.restore(checkpoint)
        bad=deepcopy(checkpoint);bad['histories']['w0'].append({'role':'user','content':'prior secret'})
        with self.assertRaisesRegex(Rejected,'scope_history_mismatch'):eng.restore(bad)

    def test_open_novel_graph_accepts_non_template_and_rejects_structural_errors(self):
        p,c,plan=prepared(outline='shared');c=v2.configuration(8,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        plan=deepcopy(plan);plan['id']='invented_topology';base=plan['units'][0];base['id']='producer_xyz';base['produces']={'novel_handle':'schema'}
        for u in plan['units'][1:]:
            u['depends']=['producer_xyz'];u['consumes']={'handle':{'unit':'producer_xyz','artifact':'novel_handle','format':'schema'}}
        self.assertEqual(v2.validate_work_plan(plan,p,c)['id'],'invented_topology')
        for mutation in ('owner','cycle','payload','coverage','type'):
            bad=deepcopy(plan)
            if mutation=='owner':bad['units'][0]['worker']='w8'
            if mutation=='cycle':bad['units'][0]['depends']=[bad['units'][1]['id']]
            if mutation=='payload':bad['units'][0]['content']='final answer'
            if mutation=='coverage':bad['units'][-1]['outputs']=[]
            if mutation=='type':bad['units'][0]['produces']['novel_handle']='python'
            with self.assertRaises(Rejected):v2.validate_work_plan(bad,p,c)
        visible=v2.planner_input(p,c)
        self.assertFalse({'outlines','target','examples','witnesses'} & visible.keys())

    def test_planner_revisions_backend_failure_and_separate_output_cap(self):
        p,c,plan=prepared();c=v2.configuration(2,planning_lane='open_generated',execution_contract='plan_scoped_v1',planner_output_cap=1200)
        req=v2.request(p,c)
        class Backend:
            context_limit=16384
            def __init__(self,fail=False):self.calls=0;self.fail=fail
            def count_input(self,m):return 11
            def generate(self,m,cap,seed):
                self.calls+=1
                if self.fail:raise RuntimeError('private backend detail')
                action={'tool':'submit_plan','plan':{} if self.calls<3 else plan}
                return SimpleNamespace(text=json.dumps(action),output_tokens=100,reasoning_tokens=20,device_seconds=0,diagnostics={})
        b=Backend();f=v2.PromptedPlanner(b,1200,'scripted_mock').run(req,p)
        self.assertEqual(f['status'],'valid');self.assertEqual(b.calls,3)
        self.assertEqual(f['planning_resources']['actual_tokens'],333)
        self.assertEqual(f['physical_generation_count'],3)
        self.assertEqual(len(v2.resolve_branches(f)['rows']),2)
        failed=v2.PromptedPlanner(Backend(True),1200,'scripted_mock').run(req,p)
        self.assertEqual(failed['status'],'planning_infrastructure_failure')
        self.assertEqual(failed['planning_resources']['uncertain_tokens'],1211)
        self.assertNotIn('private backend detail',json.dumps(failed))
        with self.assertRaisesRegex(Rejected,'allowance_mismatch'):v2.PromptedPlanner(b).run(req,p)

    def test_historical_conformance_descriptive_and_unknown_surfaces(self):
        plan={'units':[{'id':'stock_report','depends':[]},{'id':'zero_report','depends':[]}]}
        row={'plan':plan,'success':True,'state':{'artifacts':{'a':{'bindings':{}},'b':{'bindings':{'stock_report':'a'}}},
            'events':[{'type':'unit_end','unit':'stock_report','stage':'primary','new_versions':['a']},
                      {'type':'unit_end','unit':'zero_report','stage':'primary','new_versions':['b']}]}}
        original=deepcopy(row);r=report(row)
        self.assertEqual(r['extra_primary_edges'],[['stock_report','zero_report']]);self.assertIsNone(r['contract_conformant'])
        self.assertTrue(r['task_correct']);self.assertEqual(original,row);self.assertTrue(r['unknown_surfaces'])

    def test_planner_interruption_preserves_pending_journal_and_uncertain_charge(self):
        p,_,_=prepared();c=v2.configuration(2,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        saved=[]
        class Interrupted:
            context_limit=16384
            def count_input(self,m):return 17
            def generate(self,*a):
                self.pending=deepcopy(saved[-1])
                raise KeyboardInterrupt()
        backend=Interrupted()
        f=v2.PromptedPlanner(backend,evidence_mode='scripted_mock').run(v2.request(p,c),p,save=saved.append)
        self.assertEqual(backend.pending['status'],'generation_pending')
        self.assertTrue(backend.pending['resources']['reservations'])
        self.assertEqual(f['status'],'planning_infrastructure_failure')
        self.assertEqual(f['planning_resources']['uncertain_tokens'],2065)
        self.assertEqual(f['physical_generation_count'],1)
        self.assertEqual(saved[-1]['frozen'],f)
        self.assertFalse(f['planning_resources']['reservations'])

    def test_explicit_read_without_publication_counts_and_known_violation_is_not_unknown(self):
        e,p,c,plan=self.env(outline='shared');base,consumer,_=plan['units']
        w=self.begin(e,base);v=e.action(w,pub(base['id']))['version']
        w=self.begin(e,consumer);e.action(w,{'tool':'read_artifact','version':v})
        r=report({'plan':plan,'state':e.state()})
        self.assertIn([base['id'],consumer['id']],r['realized_edges'])
        self.assertNotIn([base['id'],consumer['id']],r['allowed_not_observed'])
        row={'plan':plan,'state':{'execution_contract':'plan_scoped_v1','events':[{'type':'protocol_violation','surface':'context'}]}}
        r=report(row);self.assertFalse(r['evidence_complete']);self.assertFalse(r['contract_conformant'])

    def test_transitive_influence_does_not_grant_direct_import(self):
        e,p,c,plan=self.env(outline='shared');base,response,consumer=plan['units']
        # Explicitly insert a novel intermediate producer between helper and response.
        middle=deepcopy(base);middle.update(id='middle',worker='w1',produces={'middle':'schema'},depends=[base['id']],
            consumes={base['id']:{'unit':base['id'],'artifact':base['id'],'format':'schema'}})
        response=deepcopy(response);response.update(depends=['middle'],consumes={'middle':{'unit':'middle','artifact':'middle','format':'schema'}})
        w=self.begin(e,base);a=e.action(w,pub(base['id'],{'type':'integer'}))['version']
        w=self.begin(e,middle);b=e.action(w,pub('middle',{'$ref':'rr:'+base['id']},{base['id']:a}))['version']
        w=self.begin(e,response);e.action(w,{'tool':'read_artifact','version':b})
        with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(w,{'tool':'read_artifact','version':a})
        e.action(w,pub(response['outputs'][0],{'$ref':'rr:middle'},{'middle':b},outputs=response['outputs']))
        validate_bundle(e.state())
        plan['units']=[base,middle,response,consumer]
        r=report({'plan':plan,'state':e.state()});self.assertEqual(r['extra_primary_edges'],[])
        self.assertTrue(any(a in d.get('transitive_versions',[]) for d in r['observed_exposures']))

    def test_report_delivered_violation_correctness_separate_and_missing_unknown(self):
        e,p,c,plan=self.env();u=plan['units'][0];w=self.begin(e,u)
        e.action(w,pub(u['outputs'][0],outputs=u['outputs']))
        row={'plan':plan,'state':e.state(),'evaluation':{'success':True}}
        sid=e.scopes.current(w)['id']
        row['state']['events'].append({'type':'scope_observation','scope_id':sid,'visible_versions':['forbidden']})
        r=report(row);self.assertFalse(r['contract_conformant']);self.assertTrue(r['task_correct'])
        row['state']['events']=[];self.assertIsNone(report(row)['contract_conformant'])

    def test_grammar_versions_and_terminal_mapping(self):
        from reporecourse.action_schema import schema_v2,controls_v2
        from beyond_consensus.models.action_schema import validate_action,contract
        for pool in (2,8):
            mode=f'reporecourse-plan-scoped-v1-pool-{pool}'
            good,_=controls_v2(mode)
            for action in good:validate_action(json.dumps(action),mode)
            self.assertNotEqual(digest(schema_v2(mode)),digest(schema_v2(f'reporecourse-plan-v2-pool-{pool}')))
            self.assertEqual(contract(mode)['execution_contract'],'plan_scoped_v1')
        p,c,plan=prepared();u=plan['units'][0];old=u['outputs'][0]
        u['produces']={'invented_final':u['produces'][old]};u['terminal_bindings']={old:'invented_final'}
        v2.validate_work_plan(plan,p,c)

    def test_planner_exhausted_revisions_no_free_fallback(self):
        p,c,_=prepared();c=v2.configuration(2,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        class InvalidBackend:
            context_limit=16384
            def count_input(self,m):return 10
            def generate(self,*a):return SimpleNamespace(text='{"tool":"submit_plan","plan":{}}',output_tokens=10,reasoning_tokens=0,device_seconds=0,diagnostics={})
        f=v2.PromptedPlanner(InvalidBackend(),evidence_mode='scripted_mock').run(v2.request(p,c),p)
        self.assertEqual(f['status'],'invalid_plan');self.assertEqual(f['physical_generation_count'],3)
        self.assertIsNone(f['plan']);self.assertEqual(f['planning_resources']['actual_tokens'],60)

    def test_actual_backend_bridge_can_be_bound_without_loading_or_approval_bypass(self):
        from beyond_consensus.models import reporecourse_planner as bridge
        from beyond_consensus.util import BCError
        p,c,_=prepared();c=v2.configuration(2,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        binding={'adapter':'test_binding'};req=v2.request(p,c,binding)
        with patch.object(bridge,'binding',return_value=binding):
            with self.assertRaisesRegex(BCError,'approval pending'):bridge.generate(req,p,'unused','unused')

    def test_open_proposal_copies_resolved_settings_and_remains_blocked(self):
        from reporecourse.open_planning import proposal
        model=dict(checkpoint='Qwen/Qwen3.5-27B',revision='fc05daec18b0a78c049392ed2e771dde82bdf654',
            tokenizer_revision='fc05daec18b0a78c049392ed2e771dde82bdf654',dtype='bfloat16',
            context_limit=16384,max_new_tokens=2048,thinking=True,do_sample=False)
        lock={k:model[k] for k in ('checkpoint','revision','tokenizer_revision')}
        c=v2.configuration(7,token_cap=99000,cpu_cap=1190,seed=3)
        raw=dict(schema='rr-v2-stock-competence-v1',task='synthetic-stock',config=c,model=model,
            seed=3,public_hash='synthetic-test',qualification={'test_only':True},model_lock_sha256=digest(lock))
        raw['experiment_id']=digest(raw)
        r=proposal(raw,lock,1200)
        self.assertEqual(r['config']['resource'],c['resource']);self.assertEqual(r['config']['seeds'],c['seeds'])
        self.assertEqual(r['worker_config']['model']['max_new_tokens'],2048)
        self.assertEqual(r['planner_config']['model']['max_new_tokens'],1200)
        self.assertEqual((r['plan_generations'],r['clean_branches'],r['conditional_F_branches']),(1,1,1))
        self.assertFalse(r['task_execution_allowed']);self.assertIsNone(r['qualified_plan_footprint'])
        raw['config']['max_actions']=48;raw['experiment_id']=digest({k:v for k,v in raw.items() if k!='experiment_id'})
        with self.assertRaises(Rejected):proposal(raw,lock)

    def test_scoped_preflight_uses_new_locks_and_cannot_submit_tasks(self):
        from beyond_consensus.experiments import rr_v2_preflight as probe
        from beyond_consensus.util import BCError
        with patch.object(probe,'check_locks'),patch.object(probe,'source_revision',return_value='synthetic-test'):
            m=probe.build(Path('.'),{'test':'worker'},{'test':'planner'},7,plan_scoped=True)
            self.assertEqual(m['execution_contract'],'plan_scoped_v1')
            probe.check_submission(m,{'test':'worker'},Path('.'),'preflight',1)
            with self.assertRaises(BCError):probe.check_submission(m,{'test':'worker'},Path('.'),'run',1)
            with self.assertRaises(BCError):probe.check_submission(m,{'test':'worker'},Path('.'),'preflight',2)

    def test_unused_inefficient_unit_allowed_but_not_loss_target(self):
        p,c,plan=prepared(pool=8);spare=deepcopy(plan['units'][0]);spare.update(id='spare',worker='w7',outputs=[],produces={'spare':'schema'})
        plan['units'].append(spare);plan=v2.validate_work_plan(plan,p,c)
        frozen=v2.freeze(v2.request(p,c),p,plan,Resources(100000,1200),[],'scripted_mock')
        manifest=v2.resolve_branches(frozen);self.assertNotIn('w7',manifest['rows'][0]['eligible'])



@unittest.skipUnless(optional(),'pinned SQLGlot/jsonschema/referencing required')
class ActualExecutionTests(unittest.TestCase):
    def test_both_families_all_topologies_pools_2_and_8_and_loss(self):
        from reporecourse.evaluator import evaluate
        for task in ('synthetic-stock','synthetic-nullable'):
            private=private_task(task)
            for pool in (2,8):
                for outline in ('independent','shared','grouped','branch_rejoin'):
                    p,c,plan=prepared(task,pool,'independent')
                    plan=v2.fixture_rejoin(p,c)[0] if outline=='branch_rejoin' else v2.authored_plan(p,c,outline)
                    for track in ('clean','F'):
                        with self.subTest(task=task,pool=pool,outline=outline,track=track):
                            worker=ScriptedWorker(v2.fixture_witness(p,private,c,outline))
                            eng=Engine(p,worker,plan=plan,v2=c,track=track,target=plan['units'][0]['worker'],resources=Resources(100000,1200))
                            try:
                                result=eng.run();grade=evaluate(p,private,result['state'])
                                self.assertTrue(grade['success'],result['failures']);self.assertTrue(result['conformance']['contract_conformant'])
                                if track=='F':self.assertTrue(result['state']['scope_state']['overlays'])
                            finally:eng.env.close()

    def test_stock_old_reuse_denied_corrected_and_wrong_conformant(self):
        from reporecourse.evaluator import evaluate
        p,c,plan=prepared('synthetic-stock');e=Environment(p,Resources(100000,1200),workers=c['workers'],plan=plan,execution_contract='plan_scoped_v1')
        try:
            u,v=plan['units'];e.scopes.begin(u,u['worker'],'primary');e.assignment[u['worker']]=u
            version=e.action(u['worker'],pub('stock_report','SELECT sku, qty FROM stock ORDER BY sku',fmt='sql',outputs=['stock_report']))['version']
            e.scopes.begin(v,v['worker'],'primary');e.assignment[v['worker']]=v
            with self.assertRaisesRegex(Rejected,'scope_denied'):e.action(v['worker'],pub('zero_report','SELECT sku FROM stock_report WHERE qty=0 ORDER BY sku',{'stock_report':version},'sql',['zero_report']))
            for query in ('SELECT sku FROM (SELECT sku FROM stock_report) AS x','SELECT sku FROM stock_report'):
                with self.assertRaises(Rejected):e.action(v['worker'],pub('zero_report',query,fmt='sql',outputs=['zero_report']))
            e.action(v['worker'],pub('zero_report','SELECT sku FROM stock WHERE qty=0 ORDER BY sku',fmt='sql',outputs=['zero_report']))
            self.assertTrue(evaluate(p,private_task('synthetic-stock'),e.state())['success'])
            self.assertTrue(report({'plan':plan,'state':e.state()})['contract_conformant'])
            e.action(v['worker'],pub('zero_report','SELECT sku FROM stock WHERE qty>0 ORDER BY sku',fmt='sql',outputs=['zero_report']))
            self.assertFalse(evaluate(p,private_task('synthetic-stock'),e.state())['success'])
            self.assertTrue(report({'plan':plan,'state':e.state()})['contract_conformant'])
        finally:e.close()

    def test_generated_plan_to_restricted_execution_through_model_interfaces(self):
        from reporecourse.open_planning import run_with_backends
        p,c,plan=prepared('synthetic-stock',7,'grouped')
        c=v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1')
        plan['id']='novel_group';plan['units'][0]['id']='new_work_unit'
        class Backend:
            context_limit=16384
            def __init__(self,actions):self.actions=iter(actions)
            def count_input(self,m):return 100
            def generate(self,*args):return SimpleNamespace(text=json.dumps(next(self.actions)),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
        planner=Backend([{'tool':'submit_plan','plan':plan}])
        worker=Backend([pub('stock_report','SELECT sku, qty FROM stock ORDER BY sku',fmt='sql',outputs=['stock_report']),
                        pub('zero_report','SELECT sku FROM stock WHERE qty=0 ORDER BY sku',fmt='sql',outputs=['zero_report'])])
        r=run_with_backends(v2.request(p,c),p,private_task('synthetic-stock'),planner,worker,evidence_mode='scripted_mock')
        self.assertTrue(r['results'][0]['success']);self.assertEqual(r['results'][0]['resource_profile']['actual_tokens'],540)
        self.assertFalse(r['model_executed']);self.assertFalse(r['F_executed'])
