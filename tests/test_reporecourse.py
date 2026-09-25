"""Independent benchmark contracts. Optional child tests skip only without pins."""
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reporecourse.common import Rejected,digest
from reporecourse.resources import Resources,PROFILE
from reporecourse.tasks import load_task,private_task,catalog,split_check,ROOT
from reporecourse.runtime import Environment
from reporecourse.engine import Engine,ScriptedWorker,ModelWorker,open_catalog
from reporecourse.policies import choose_plan,organization_key,select_calibrated,variation
from reporecourse.experiments import build,validate,require_run,aggregate


def optional():
    try:return all(importlib.metadata.version(k)==v for k,v in {'sqlglot':'27.28.1','jsonschema':'4.25.1','referencing':'0.36.2'}.items())
    except importlib.metadata.PackageNotFoundError:return False


def public(name='synthetic-nullable'):return load_task(name,Path('/nonexistent-sources'))[1]


class CoreTests(unittest.TestCase):
    def test_worker_finish_preserves_episode_and_other_workers(self):
        env=Environment(public())
        try:
            self.assertEqual(env.action('w0',{'tool':'finish'}),{'assignment_finished':True})
            self.assertFalse(env.finished)
            self.assertIsInstance(env.action('w1',{'tool':'list_sources'}),list)
            self.assertFalse(env.bound)
            env.finished=True
            with self.assertRaisesRegex(Rejected,'episode_closed'):
                env.action('w1',{'tool':'list_sources'})
        finally:env.close()

    def test_finish_continues_primary_and_repair_and_resumes_locally(self):
        class Finisher:
            mode='scripted_cpu'
            def __init__(self):self.calls=[]
            def next_action(self,p,u,o,h,r,seed,save):
                self.calls.append(u['id'])
                return {'tool':'finish'}
        p=public();worker=Finisher();saved=[]
        engine=Engine(p,worker,save=lambda s:saved.append(copy.deepcopy(s)))
        try:
            expected=[u['id'] for u in engine.plan['units']]
            row=engine.run()
            self.assertEqual(worker.calls,expected+expected)
            self.assertEqual(row['failures'],[])
            self.assertEqual(row['obligations_bound'],0)
            self.assertEqual(set(row['public_alarm']),{r['id'] for r in p['required_outputs']})
            self.assertTrue(engine.env.finished)
            self.assertEqual([(e['stage'],e['unit']) for e in row['events'] if e['type']=='unit_end'],
                             [(stage,u) for stage in ('primary','repair') for u in expected])
            checkpoint=next(s for s in saved if 'primary:'+expected[0] in s['completed'])
            other=Finisher();resumed=Engine(p,other)
            try:
                resumed.restore(checkpoint)
                resumed.run()
                self.assertEqual(other.calls,expected[1:]+expected)
            finally:resumed.env.close()
            before=len(worker.calls)
            engine.unit(engine.plan['units'][0],'w0','after_final')
            self.assertEqual(len(worker.calls),before)
        finally:engine.env.close()

    def test_repair_stops_model_calls_after_resource_exhaustion(self):
        class Exhausted:
            mode='scripted_cpu'
            calls=0
            def next_action(self,*args):
                self.calls+=1
                raise Rejected('token_cap')
        worker=Exhausted();engine=Engine(public(),worker)
        try:
            engine.phase='repair'
            engine.public_alarm=[r['id'] for r in engine.public['required_outputs']]
            row=engine.run()
            self.assertEqual(worker.calls,1)
            self.assertEqual(row['status'],'resource_exhausted')
        finally:engine.env.close()

    def test_source_connection_closed_on_success_and_failure(self):
        import sqlite3
        from reporecourse.runtime import create_database
        connect = sqlite3.connect
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as directory:
                connection = connect(Path(directory) / 'source.sqlite')
                tables = {'items': {'columns': [('id', 'INVALID' if fail else 'INTEGER')],
                                    'rows': [[1]]}}
                with patch('reporecourse.runtime.sqlite3.connect', return_value=connection):
                    if fail:
                        with self.assertRaisesRegex(Rejected, 'source_type'):
                            create_database(Path(directory) / 'source.sqlite', tables)
                    else:
                        create_database(Path(directory) / 'source.sqlite', tables)
                with self.assertRaises(sqlite3.ProgrammingError):
                    connection.execute('SELECT 1')
                if not fail:
                    with connect(Path(directory) / 'source.sqlite') as check:
                        self.assertEqual(check.execute('SELECT id FROM items').fetchall(), [(1,)])
                    check.close()

    def test_stdlib_cli_and_policy_independent_imports(self):
        proc=subprocess.run([sys.executable,'-I','-S','scripts/bc.py','--help'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr);self.assertIn('rr-demo',proc.stdout)
        script="""import sys,importlib.abc
sys.path.insert(0,'src')
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.startswith('beyond_consensus'):raise AssertionError(fullname)
sys.meta_path.insert(0,Deny())
import reporecourse.runtime,reporecourse.evaluator,reporecourse.engine,reporecourse.tasks
import restricted_artifacts.sql_text,restricted_artifacts.sqlite_executor
assert not any(x.startswith('beyond_consensus') for x in sys.modules)
"""
        p=subprocess.run([sys.executable,'-I','-S','-c',script],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_catalog_and_missing_assets_fail_closed(self):
        self.assertEqual(len(catalog()['tasks']),5)
        with self.assertRaisesRegex(Rejected,'source_missing'):load_task('jaffle-recorded-payments','/not-staged')
        with self.assertRaisesRegex(Rejected,'unknown_task'):load_task('fake','/not-staged')

    def test_source_group_split(self):
        with self.assertRaisesRegex(Rejected,'split_overlap'):
            split_check([dict(source_group='same',base_change='a',split='development'),dict(source_group='same',base_change='b',split='test')])

    def test_private_visibility_and_no_path_read(self):
        env=Environment(public())
        try:
            for name in ('/etc/passwd','../private','witnesses','fixtures'):
                with self.assertRaises(Rejected):env.action('w0',{'tool':'read_source','name':name})
                self.assertEqual(env.action('w0',{'tool':'search_sources','query':name}),[])
            self.assertNotIn('oracle',json.dumps(env.observation('w0')))
            self.assertNotIn('witnesses',json.dumps(env.public))
        finally:env.close()

    def test_malformed_values_are_candidate_errors(self):
        env=Environment(public())
        try:
            for action in ({'tool':'read_source','name':[]}, {'tool':'read_artifact','version':{}},
                           {'tool':'publish','name':'bad','format':'schema','content':{},'bindings':{},'obligations':[{}]}):
                with self.assertRaises(Rejected):env.action('w0',action)
            self.assertFalse(env.artifacts)
        finally:env.close()

    def test_reservations_actual_reasoning_and_uncertainty(self):
        r=Resources(100,10);k=r.reserve(10,30);self.assertEqual(r.actual_tokens,0)
        r.reconcile(k,8,5);self.assertEqual(r.actual_tokens,18);self.assertEqual(r.remaining,82)
        k=r.reserve(5,10);r.reconcile(k);self.assertEqual(r.actual_tokens,18);self.assertEqual(r.uncertain_tokens,15)
        self.assertEqual(r.remaining,67)
        with self.assertRaises(Rejected):r.reserve(70,1)
        r.reserve_cpu(3);r.reconcile_cpu('tool',3,.1);self.assertEqual(r.cpu_seconds,.1)
        k=r.reserve(1,5)
        with self.assertRaises(Rejected):r.reconcile(k,4,5)
        self.assertIn(k,r.reservations)

    def test_atomic_binding_immutable_references_and_restore(self):
        env=Environment(public())
        try:
            args=dict(name='helper',format='schema',content={'type':'integer'},bindings={},obligations=[])
            v=env.publish('w0',**args)['version']
            with self.assertRaises(Rejected):env.publish('w0',**{**args,'obligations':['nonexistent']})
            self.assertEqual(len(env.artifacts),1)
            v2=env.publish('w1',**{**args,'content':{'type':'string'}})['version']
            consumer=env.publish('w2',name='consumer',format='schema',content={'$ref':'rr:h'},bindings={'h':v},obligations=['response'])['version']
            self.assertEqual(env.artifacts[consumer]['bindings']['h'],v)
            self.assertNotEqual(v,v2)
            cp=env.action('w2',{'tool':'checkpoint'})['checkpoint']
            env.unavailable.add('w0');env.action('w1',{'tool':'restore','checkpoint':cp})
            self.assertIn('w0',env.unavailable)
            self.assertIn(consumer,env.artifacts)
            with patch.object(env,'execute',return_value={'status':'ok','valid':True}):
                env.action('w3',{'tool':'execute_artifact','version':consumer,'input_id':'default'})
            self.assertIn(consumer,env.exposure['w3'])
            with self.assertRaises(Rejected):env.publish('w0',**args)
        finally:env.close()

    def test_persistent_fault_targets_and_nontrigger(self):
        env=Environment(public(),active=['w1'],track='F',seed=8)
        try:
            self.assertEqual(env.target,'w1');self.assertFalse(env.triggered)
            env.assignment['w1']={'id':'response','outputs':['response']}
            retained=env.publish('w1','earlier','schema',True,{},[])['version']
            self.assertFalse(env.triggered)
            with self.assertRaisesRegex(Rejected,'unavailable'):
                env.publish('w1','x','schema',True,{},['response'])
            self.assertTrue(env.triggered);self.assertEqual(set(env.artifacts),{retained})
        finally:env.close()
        with self.assertRaisesRegex(Rejected,'inactive_target'):Environment(public(),active=['w1'],track='F',target='w0')

    def test_sabotage_no_truth_in_worker_view_and_persistence(self):
        env=Environment(public(),track='S',target='w0',active=['w0'],sabotage='persistent')
        try:
            for _ in range(2):
                v=env.publish('w0','a','schema',{'type':'integer'},{},['response'])['version']
                self.assertIs(env.artifacts[v]['content'],False)
            self.assertNotIn('target',env.observation('w1'));self.assertFalse(env.unavailable)
        finally:env.close()

    def test_fixed_state_restoration_keeps_persistent_compromise(self):
        from reporecourse.recovery import freeze,resume
        p=public();worker=ScriptedWorker(private_task(p['id'])['witnesses'][0])
        old=Engine(p,worker,track='S',target='w0',sabotage='persistent')
        fresh=Engine(p,worker)
        try:
            old.env.publish('w0','first','schema',True,{},['response']);old.phase='repair';old.public_alarm=['response']
            snap=freeze(old,{'unavailable':[],'localization':'public_alarm'})
            resume(fresh,snap,1000,120)
            v=fresh.env.publish('w0','later','schema',True,{},['response'])['version']
            self.assertIs(fresh.env.artifacts[v]['content'],False)
            self.assertEqual(fresh.env.fault_track,'S');self.assertEqual(fresh.env.track,'R')
            self.assertGreater(fresh.env.resources.cpu_seconds,0)
            self.assertEqual(fresh.alarm_resources['cpu_cap_debit'],0)
            self.assertEqual(fresh.historical_resources,snap['historical_resources'])
        finally:old.env.close();fresh.env.close()

    def test_schema_subset_forbidden_refs_and_mapping(self):
        from reporecourse.schema_runtime import resolve,mapping
        for sch in ({'$ref':'https://example.com'},{'$ref':'file:///etc/passwd'},{'pattern':'.*'}, {'format':'python'}, {'x-exec':'x'}):
            with self.assertRaises(Rejected):resolve(sch,{})
        with self.assertRaises(Rejected):resolve({'$ref':'rr:a'},{'a':{'$ref':'rr:a'}})
        p={'fields':{'name':{'path':['a','b'],'missing':'null'}}}
        self.assertEqual(mapping(p,{}),{'name':None})
        self.assertEqual(mapping({'each':p},[{'a':{'b':3}},{}]),[{'name':3},{'name':None}])
        p['fields']['name']['missing']='error'
        with self.assertRaises(Rejected):mapping(p,{})

    def test_plan_variation_and_calibration_gate(self):
        p=public();plans=p['outlines'];self.assertEqual(variation(plans,p)['organizations'],3)
        changed=copy.deepcopy(plans[0]);changed['units'][0]['worker']='w3'
        self.assertEqual(organization_key(changed),organization_key(plans[0]))
        with self.assertRaisesRegex(Rejected,'calibration'):select_calibrated(plans,p,None,'recovery',{})

    def test_optional_existing_finite_selector_shared_eligibility(self):
        from beyond_consensus.experiments.reporecourse import select_plan
        p=public();plans=p['outlines'][:2];r=Resources(100,30)
        # Constructed unit-test numbers only; no empirical calibration artifact.
        compatibility={'test_only':True}
        c={'compatibility':compatibility,'measured':True,'plans':{
            organization_key(plans[0]):{'eligible':True,'clean_tokens':20,'worst_total_tokens':90},
            organization_key(plans[1]):{'eligible':True,'clean_tokens':30,'worst_total_tokens':60}}}
        a=select_plan(plans,p,c,'nominal',compatibility,r,reserve=10)
        b=select_plan(plans,p,c,'recovery',compatibility,r,reserve=10)
        self.assertEqual(a['id'],plans[0]['id']);self.assertEqual(b['id'],plans[1]['id'])
        self.assertNotEqual(a['units'],b['units'])
        self.assertEqual(len([e for e in r.events if e.get('category')=='finite_selection']),2)
        with self.assertRaises(Rejected):select_plan(plans,p,None,'nominal',compatibility,r)

    def test_manifest_coverage_scope_and_pooling(self):
        m=build('/missing',['synthetic-nullable'],{},'source',smoke=False)
        self.assertEqual(m['planned_episodes'],4);validate(m)
        with self.assertRaises(Rejected):require_run(m)
        with tempfile.TemporaryDirectory() as tmp:
            a=aggregate(m,tmp);self.assertEqual(len(a['missing_episode_ids']),4)
            self.assertTrue(all(g['complete_at_budget'] is None for g in a['groups'].values()))
            e=m['episodes'][0];p=Path(tmp)/'episodes'/e['episode_id'];p.mkdir(parents=True)
            (p/'result.json').write_text(json.dumps({'experiment_id':m['experiment_id'],'episode_id':e['episode_id'],'resource_profile':{'profile':'legacy'},'track':e['track']}))
            with self.assertRaises(Rejected):aggregate(m,tmp)
        broken=copy.deepcopy(m);broken['resource']['token_cap']+=1
        with self.assertRaises(Rejected):validate(broken)

    def test_model_adapter_counts_reprefill_and_planner_charges(self):
        class Backend:
            def count_input(self,m):return len(json.dumps(m))//4
            def generate(self,m,n,seed):
                from types import SimpleNamespace
                text=json.dumps({'tool':'plan_catalog','plans':public()['outlines'][:1]})
                return SimpleNamespace(text=text,output_tokens=100,reasoning_tokens=30,device_seconds=.1,diagnostics={})
        r=Resources(100000,300)
        c=open_catalog(public(),Backend(),r)
        self.assertEqual(c['lane'],'open_planning');self.assertGreater(r.actual_tokens,100)
        self.assertEqual(sum(e.get('output_tokens',0) for e in r.events),100)


@unittest.skipUnless(optional(),'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children')
class VerticalTests(unittest.TestCase):
    def test_replica_checkpoint_preserves_primary_and_resumes(self):
        from reporecourse.evaluator import evaluate
        p=public();pr=private_task(p['id']);saved=[]
        e=Engine(p,ScriptedWorker(pr['witnesses'][0]),policy='replication',save=lambda s:saved.append(copy.deepcopy(s)))
        try:
            r=e.run();self.assertTrue(evaluate(p,pr,r['state'])['success'])
            state=next(s for s in saved if s['replica_saved'] and s['environment']['artifacts'])
            primaries=set(state['replica_saved']['artifacts'])
            n=Engine(p,ScriptedWorker(pr['witnesses'][0]),policy='replication')
            try:
                n.restore(state);resumed=n.run()
                self.assertTrue(primaries<=set(resumed['state']['artifacts']))
                self.assertTrue(evaluate(p,pr,resumed['state'])['success'])
            finally:n.env.close()
        finally:e.env.close()

    def test_existing_journal_runner_adapter_with_explicit_test_backend(self):
        from types import SimpleNamespace
        from beyond_consensus.experiments.reporecourse import run
        from beyond_consensus.experiments.manifest import source_revision
        from reporecourse.qualification import implementation_hashes
        root=ROOT.parents[1];card,p=load_task('synthetic-nullable','/missing')
        actions=iter(copy.deepcopy(private_task(card['id'])['witnesses'][0]['actions']))
        class Backend:
            def count_input(self,messages):return 10
            def generate(self,messages,limit,seed):
                return SimpleNamespace(text=json.dumps(next(actions)['action']),output_tokens=20,
                    reasoning_tokens=0,device_seconds=0,diagnostics={})
        # Test double for qualification routing, not a reusable approval record.
        q={'status':'cpu_qualified_review_pending','task_hash':digest(card),'implementation_hashes':implementation_hashes()}
        m=build('/missing',[card['id']],{'context_limit':16384,'max_new_tokens':2048},
            source_revision(root),smoke=True,qualification=q)
        with tempfile.TemporaryDirectory() as tmp:
            rows=run(m,Path(tmp),root,backend=Backend())
            self.assertEqual(len(rows),1);self.assertTrue(rows[0]['success'],rows)
            self.assertEqual(rows[0]['resource_profile']['actual_tokens'],60)
            # No new generation for a terminal result, even with retry requested.
            self.assertEqual(run(m,Path(tmp),root,backend=object(),retry_failures=True),rows)
            summary=aggregate(m,Path(tmp));self.assertTrue(all(g['complete_coverage'] for g in summary['groups'].values()))

    def test_both_families_witnesses_and_negatives(self):
        from reporecourse.qualification import qualify
        for name in ('synthetic-stock','synthetic-nullable'):
            with self.subTest(name=name):
                r=qualify(name,'/missing');self.assertEqual(r['status'],'cpu_qualified_review_pending',r)
                self.assertEqual(len(r['witnesses']),2);self.assertTrue(all(x['detected'] for x in r['negative_controls']))

    def test_all_baselines_clean_and_announced_loss(self):
        from reporecourse.qualification import run_reference
        for name in ('synthetic-stock','synthetic-nullable'):
            for policy in ('solo','delegation_jit','restart','replication'):
                for track in (('clean',) if policy=='solo' else ('clean','F')):
                    with self.subTest(name=name,policy=policy,track=track):
                        r=run_reference(public(name),private_task(name),policy=policy,track=track,target='w0')
                        self.assertTrue(r['success'],r['failures'])
                        self.assertFalse(r['model_executed']);self.assertEqual(r['resource_profile']['actual_tokens'],0)
                        self.assertLessEqual(len(r['publications_by_worker']),4)

    def test_shared_plan_repair_and_no_forced_regeneration(self):
        p=public('synthetic-stock');pr=private_task(p['id'])
        from reporecourse.qualification import run_reference
        r=run_reference(p,pr,'shared',track='F',target='w2')
        self.assertTrue(r['success']);self.assertTrue(r['retained_versions'])
        env=Environment(p)
        try:
            h=env.publish('w0','h','sql','SELECT sku, qty FROM stock',{},[])['version']
            c=env.publish('w1','c','sql','SELECT sku, qty FROM helper ORDER BY sku',{'helper':h},['stock_report'])['version']
            env.action('w2',{'tool':'read_artifact','version':c})
            h2=env.publish('w2','h','sql','SELECT sku, qty FROM stock',{},[])['version']
            c2=env.publish('w1','c','sql','SELECT sku, qty FROM helper ORDER BY sku',{'helper':h2},['stock_report'])['version']
            self.assertEqual(env.execute(c)['outputs'],env.execute(c2)['outputs'])
            self.assertIn(c,env.artifacts);self.assertEqual(env.artifacts[c]['bindings']['helper'],h)
        finally:env.close()

    def test_schema_rebind_reuses_program_preserves_exposure(self):
        env=Environment(public())
        try:
            bad=env.publish('w0','base','schema',{'type':'integer'},{},[])['version']
            consumer=env.publish('w1','response','schema',{'$ref':'rr:base'},{'base':bad},['response'])['version']
            self.assertFalse(env.execute(consumer,None)['valid'])
            good=env.publish('w2','base','schema',{'type':['integer','null']},{},[])['version']
            new=env.action('w3',{'tool':'rebind_artifact','version':consumer,'name':'reused','bindings':{'base':good},'obligations':['response']})['version']
            self.assertEqual(env.artifacts[new]['content'],env.artifacts[consumer]['content'])
            self.assertIn(consumer,env.artifacts[new]['exposure'])
            self.assertTrue(env.execute(new,None)['valid'])
            self.assertFalse(env.execute(consumer,None)['valid'])
        finally:env.close()

    def test_independent_benchmark_execution_without_bc(self):
        script="""import sys,importlib.abc
sys.path.insert(0,'src')
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.startswith('beyond_consensus'):raise AssertionError(fullname)
sys.meta_path.insert(0,Deny())
from reporecourse.tasks import load_task,private_task
from reporecourse.qualification import run_reference
for task in ('synthetic-stock','synthetic-nullable'):
 p=load_task(task,'/missing')[1]
 assert run_reference(p,private_task(task),track='F',target='w0')['success']
"""
        r=subprocess.run([sys.executable,'-I','-c',script],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)

    def test_fixed_state_graph_and_equal_remaining(self):
        from reporecourse.recovery import freeze,resume
        p=public();pr=private_task(p['id']);w=ScriptedWorker(pr['witnesses'][0])
        engine=Engine(p,w,track='F',target='w0')
        try:
            for u in engine.plan['units']:engine.unit(u,u['worker'],'primary')
            engine.phase='repair';snap=freeze(engine,{'unavailable':['w0'],'localization':'announced_loss'})
            new=Engine(p,w,track='R',target='w0')
            try:
                resume(new,snap,2000,120);r=new.run()
                self.assertEqual(r['protocol'],'equal_remaining');self.assertIsNotNone(r['historical_resources'])
                self.assertEqual(r['obligations_bound'],2)
            finally:new.env.close()
            changed=Engine(p,w,outline='shared',track='R',target='w0')
            try:
                with self.assertRaisesRegex(Rejected,'graph'):resume(changed,snap,2000,120)
            finally:changed.env.close()
        finally:engine.env.close()

    def test_resume_and_latest_bound_not_best(self):
        from reporecourse.evaluator import evaluate
        p=public();pr=private_task(p['id']);w=ScriptedWorker(pr['witnesses'][0]);e=Engine(p,w)
        try:
            u=e.plan['units'][0];e.unit(u,u['worker'],'primary');state=e.checkpoint()
            n=Engine(p,w)
            try:
                n.restore(state);r=n.run();self.assertTrue(evaluate(p,pr,r['state'])['success'])
                n.env.finished=False
                n.env.publish('w1','bad','schema',True,{},['response'])
                self.assertFalse(evaluate(p,pr,n.env.state())['success'])
            finally:n.env.close()
        finally:e.env.close()

class IntegrationTests(unittest.TestCase):
    def test_additive_decoder_schema_and_cpu_charge_contract(self):
        from beyond_consensus.util import BCError
        from beyond_consensus.models.action_schema import validate_action,contract
        from reporecourse.action_schema import controls
        good,bad=controls()
        for a in good:self.assertEqual(validate_action(json.dumps(a),'reporecourse-json-v1'),a)
        for a in bad:
            with self.assertRaises(BCError):validate_action(a,'reporecourse-json-v1')
        self.assertEqual(contract('reporecourse-json-v1')['decoder_charge'],'measured_cpu_subset_no_token_conversion')
        self.assertEqual(contract('sqlite-sql-text-v1')['decoder_charge'],'ceil_process_cpu_seconds_times_tool_charge')

    def test_existing_slurm_guard_and_manifest_adapter(self):
        from beyond_consensus.util import BCError
        from beyond_consensus.experiments.cluster import ClusterConfig,sbatch_arguments,failed_shard_ids
        from beyond_consensus.experiments.manifest import validate_manifest
        from beyond_consensus.models.competence import REVISION
        model=dict(backend='transformers',checkpoint='Qwen/Qwen3.5-27B',revision=REVISION,tokenizer_revision=REVISION,
            thinking=True,context_limit=16384,max_new_tokens=2048,action_constraint='reporecourse-json-v1')
        m=build('/missing',['synthetic-nullable'],model,'source',smoke=True)
        c=validate_manifest(m);self.assertEqual(c.task_kind,'reporecourse');self.assertEqual(c.shards,1)
        cfg=ClusterConfig('TEST','00:30:00',96,'/env/python','/storage','/cache','/snapshots','/outputs')
        args=sbatch_arguments(cfg,Path('/snapshot'),Path('/output'),[0],1,mode='run',dependencies=[])
        self.assertIn('--gres=gpu:1',args)
        with self.assertRaises(BCError):sbatch_arguments(cfg,Path('/s'),Path('/o'),[0],5,mode='run',dependencies=[])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(failed_shard_ids(m,Path(tmp)),[0])
            e=m['episodes'][0];p=Path(tmp)/'episodes'/e['episode_id'];p.mkdir(parents=True)
            (p/'result.json').write_text(json.dumps(dict(status='completed',provenance={'manifest_hash':digest(e)})))
            self.assertEqual(failed_shard_ids(m,Path(tmp)),[])

    def test_submission_adapter_dry_run_preserves_repo_and_guard(self):
        from beyond_consensus.experiments.cluster import ClusterConfig,submit
        from beyond_consensus.models.competence import REVISION
        model=dict(backend='transformers',checkpoint='Qwen/Qwen3.5-27B',revision=REVISION,tokenizer_revision=REVISION,
            thinking=True,context_limit=16384,max_new_tokens=2048,action_constraint='reporecourse-json-v1')
        lock={'revision':REVISION};m=build('/missing',['synthetic-nullable'],model,'source',smoke=True,model_lock_hash=digest(lock))
        cfg=ClusterConfig('TEST','00:30:00',96,'/env/python','/storage','/cache','/snapshots','/outputs')
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{},clear=True), \
                patch('reporecourse.experiments.require_run'), \
                patch('beyond_consensus.experiments.reporecourse.verify_inputs') as verify, \
                patch('beyond_consensus.models.competence.require_qualification'), \
                patch('beyond_consensus.experiments.cluster.registry_root',return_value=Path(tmp)), \
                patch('beyond_consensus.experiments.cluster.validate_site'), \
                patch('beyond_consensus.experiments.cluster.guard',return_value=[]) as guard, \
                patch('beyond_consensus.experiments.cluster.command') as command:
            r=submit(Path('/repo'),cfg,m,lock,1,dry_run=True)
            self.assertFalse(r['submitted']);verify.assert_called_once_with(m,Path('/repo'))
            guard.assert_called_once();command.assert_not_called()

    def test_sensitivity_counts_only_actual_contributors(self):
        m=build('/missing',['synthetic-nullable'],{},'src',sensitivity=True)
        # 2 seeds * [(2+1) independent + (3+1) shared + (1+1) grouped].
        self.assertEqual(m['planned_episodes'],18)
        for e in m['episodes']:
            if e['track']=='F':self.assertIn(e['target'],{u['worker'] for u in e['plan']['units']})
