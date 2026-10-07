"""Clean-only boundary controls. All generations here are explicit CPU doubles."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from beyond_consensus.experiments import rr_open_clean as clean
from beyond_consensus.experiments import rr_open_review as review
from beyond_consensus.util import BCError, digest
from reporecourse import v2
from reporecourse.tasks import load_task, private_task
from tests.test_reporecourse import optional


def candidate():
    with patch.object(clean.profile,'check_locks'), patch.object(clean.profile,'source_revision',return_value='test-source'):
        base=clean.profile.build(Path('.'),{}, {},7,plan_scoped=True,planner_output_cap=6144)
    c=v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1')
    old={'config':c}
    m=dict(schema=clean.SCHEMA, source_revision='test-source', backend_profile=base, model=base['model'],
           model_lock_sha256=digest({}),historical_proposal=old, config=clean.config(old), task='synthetic-stock',
           public_hash='public-test', condition='clean', fault_branches=0, maximum_execution_branches=1,
           maximum_planning_sequences=1, shards=1, planned_episodes=1, campaign_allowed=False, confirmatory=False,
           task_execution_allowed=False, approval=None, limitations=clean.LIMITATIONS,
           footprint_audit={'test_double':True}, budget_basis='uncalibrated_engineering_cap')
    m['episodes']=[dict(episode_id=digest([clean.SCHEMA,m['source_revision'],m['public_hash'],digest(base),digest(m['config'])]),shard=0)]
    return clean.seal(m)


def approved():
    m=candidate();r=clean.approval_template(m)
    r.update(decision='approved',reviewer='CPU control, not real approval',reviewed_at='test')
    return clean.authorize(m,r)


class Boundaries(unittest.TestCase):
    def test_approval_is_specific_and_cannot_expand_scope(self):
        m=candidate();clean.validate(m)
        receipt=clean.approval_template(m)
        with self.assertRaises(BCError):clean.authorize(m,receipt)
        good=approved();clean.validate(good)
        self.assertFalse(m['task_execution_allowed']);self.assertTrue(good['task_execution_allowed'])
        for key,value in [('fault_branches',1),('planned_episodes',2),('condition','F'),('campaign_allowed',True)]:
            bad=deepcopy(good);bad[key]=value;clean.seal(bad)
            with self.subTest(key=key),self.assertRaises(BCError):clean.validate(bad)
        bad=deepcopy(good);bad['source_revision']='changed';clean.seal(bad)
        with self.assertRaises(BCError):clean.validate(bad)
        bad=deepcopy(good);bad['approval']['proposal_id']='another';clean.seal(bad)
        with self.assertRaises(BCError):clean.validate(bad)

    def test_submission_requires_approval_and_blocks_started_attempt(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(clean,'verify'):
            with self.assertRaises(BCError):clean.submission(candidate(),Path('.'),{},'run',1,temp)
            m=approved();clean.submission(m,Path('.'),{},'run',1,temp)
            for mode,n in [('preflight',1),('run',2)]:
                with self.assertRaises(BCError):clean.submission(m,Path('.'),{},mode,n,temp)
            ep=Path(temp)/'episodes'/m['episodes'][0]['episode_id'];ep.mkdir(parents=True)
            (ep/'started.json').write_text('{}')
            with self.assertRaises(BCError):clean.submission(m,Path('.'),{},'run',1,temp)

    def test_routing_rejects_injected_backend_and_retries_before_loading(self):
        from beyond_consensus.experiments.runner import run_manifest
        m=approved()
        with self.assertRaises(BCError):run_manifest(m,Path('/unused'),Path('.'),backend=object())
        with self.assertRaises(BCError):clean.run(m,Path('/unused'),Path('.'),model_lock=None,retry_failures=True)
        from beyond_consensus.experiments.manifest import validate_manifest
        self.assertEqual(validate_manifest(m).task_kind,'rr_open_clean')

    def test_invalid_planning_is_retained_without_engine_or_fault_selection(self):
        m=candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
        class Backend:
            context_limit=16384
            def count_input(self,messages):return 40
            def generate(self,*args):return SimpleNamespace(text='{}',output_tokens=2,reasoning_tokens=0,device_seconds=0,diagnostics={})
        records={};roles=[]
        with patch('reporecourse.engine.Engine') as engine,patch.object(v2,'resolve_branches',side_effect=AssertionError('fault selection')):
            row=clean.execute(m,p,{},Backend(),roles.append,lambda k,v:records.update({k:deepcopy(v)}))
        engine.assert_not_called()
        self.assertEqual(row['status'],'invalid_plan');self.assertFalse(row['success'])
        self.assertEqual(row['resource_profile']['actual_tokens'],3*42)
        self.assertEqual(row['execution_branches'],0);self.assertEqual(roles,['plan'])
        self.assertIn('frozen-plan',records)

    def test_planner_overflow_and_unknown_generation_usage(self):
        m=candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
        class Backend:
            context_limit=16384
            def count_input(self,_):return 10241
            def generate(self,*a):raise AssertionError('Must not dispatch')
        row=clean.execute(m,p,{},Backend(),lambda _:None,lambda *_:None)
        self.assertEqual(row['resource_profile']['actual_tokens'],0)
        self.assertFalse(any(e['generation_dispatched'] for e in row['planning']['planning_events']))
        b=Backend();b.count_input=lambda _:100
        row=clean.execute(m,p,{},b,lambda _:None,lambda *_:None)
        self.assertEqual(row['status'],'planning_infrastructure_failure');self.assertIsNone(row['success'])
        self.assertEqual(row['resource_profile']['uncertain_tokens'],6244)

    def test_shared_budget_and_clean_conformance_without_task_sql(self):
        m=candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
        plan=v2.authored_plan(p,m['config'],'grouped');records={};roles=[]
        class Backend:
            context_limit=16384
            def count_input(self,_):return 100
            def generate(self,*a):return SimpleNamespace(text=json.dumps({'tool':'submit_plan','plan':plan}),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
        class Engine:
            def __init__(self,public,worker,**kw):
                self.r=kw['resources'];self.trajectories=[]
                self.env=SimpleNamespace(close=lambda:None)
                assert kw['track']=='clean' and kw['target']==kw['plan']['units'][0]['worker']
                assert self.r.actual_tokens==180 and self.r.token_cap==100000
            def run(self):
                key=self.r.reserve(100,2048);self.r.reconcile(key,40)
                return dict(status='completed',state={},conformance={'contract_conformant':True})
        with patch('reporecourse.engine.Engine',Engine),patch('reporecourse.evaluator.evaluate',return_value={'success':True}),patch.object(v2,'resolve_branches',side_effect=AssertionError('no fault targets')):
            row=clean.execute(m,p,{},Backend(),roles.append,lambda k,v:records.update({k:deepcopy(v)}))
        self.assertTrue(row['success']);self.assertEqual(row['resource_profile']['actual_tokens'],320)
        self.assertEqual(row['planning']['planning_resources']['actual_tokens'],180)
        self.assertEqual(row['execution_branches'],1);self.assertEqual(roles,['plan','json'])
        self.assertEqual(row['planning_logical_charges'],1)

    def test_execution_interruption_keeps_planning_and_uncertain_reservations(self):
        m=candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
        plan=v2.authored_plan(p,m['config'],'grouped');saved={}
        class Backend:
            context_limit=16384
            def count_input(self,_):return 100
            def generate(self,*a):return SimpleNamespace(text=json.dumps({'tool':'submit_plan','plan':plan}),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
        class Engine:
            def __init__(self,public,worker,**kw):
                self.r=kw['resources'];self.trajectories=[];self.failures=[]
                self.env=SimpleNamespace(close=lambda:None,state=lambda:{},events=[])
            def run(self):
                self.r.reserve(100,2048);self.r.reserve_cpu(31)
                raise InterruptedError('CPU interruption control')
        with patch('reporecourse.engine.Engine',Engine),patch('reporecourse.evaluator.evaluate') as evaluate:
            row=clean.execute(m,p,{},Backend(),lambda _:None,lambda k,v:saved.update({k:deepcopy(v)}))
        evaluate.assert_not_called()
        self.assertEqual(row['status'],'interrupted');self.assertIsNone(row['success'])
        self.assertEqual(row['resource_profile']['actual_tokens'],180)
        self.assertEqual(row['resource_profile']['uncertain_tokens'],2148)
        self.assertEqual(row['resource_profile']['uncertain_cpu'],31)
        self.assertEqual(saved['execution-record']['resource_profile']['reserved_tokens'],0)

    @unittest.skipUnless(optional(),'Pinned optional execution dependencies required')
    def test_actual_scoped_engine_with_shared_model_interface_double(self):
        from tests.test_reporecourse_scoped import pub
        m=candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
        plan=v2.authored_plan(p,m['config'],'grouped')
        actions=iter([{'tool':'submit_plan','plan':plan},
            pub('stock_report','SELECT sku, qty FROM stock ORDER BY sku',fmt='sql',outputs=['stock_report']),
            pub('zero_report','SELECT sku FROM stock WHERE qty=0 ORDER BY sku',fmt='sql',outputs=['zero_report'])])
        class Backend:
            context_limit=16384
            def count_input(self,_):return 100
            def generate(self,*a):return SimpleNamespace(text=json.dumps(next(actions)),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
        row=clean.execute(m,p,private_task('synthetic-stock'),Backend(),lambda _:None,lambda *_:None)
        self.assertTrue(row['success']);self.assertTrue(row['contract_conformant'])
        self.assertEqual(row['resource_profile']['actual_tokens'],540)
        self.assertEqual(row['execution_branches'],1)


class Evidence(unittest.TestCase):
    def sample(self):
        from tests.test_rr_planner_4096 import PlannerCapacityTests
        from beyond_consensus.experiments import rr_open_footprint as f
        h,p,_=PlannerCapacityTests().packet(6144)
        worker={k:'test-'+k for k in ('checkpoint','revision','tokenizer_revision','metadata_hashes','weight_hashes','model_path','tokenizer_path')}
        planner=deepcopy(worker)
        for role,lock in (('json',worker),('plan',planner)):
            lock['decoder_qualification']=dict(status='passed',model_executed=False,sql_executed=False,context_limit=16384,
                qualification_key=role,output_cap=2048 if role=='json' else 6144,packages={},contract={'mode':f.base.grammar(p['base_manifest'],role)},
                effective_generation_tokens={'eos_token_id':[1],'pad_token_id':1},thinking_template={'template_hash':'test'})
        b=p['base_manifest'];b['planner_lock']=planner;b['model_lock_sha256']=digest(worker);h.seal(b,'experiment_id')
        p['measurement_runtime']['qualification_keys']={'json':'json','plan':'plan'}
        p['measurement_runtime']['worker_lock_sha256']=digest(worker);h.seal(p,'packet_id')
        with patch.object(f.base,'check_submission'),patch.object(f,'source_revision',return_value='test-source'):
            m=f.build(Path('.'),p,worker)
        runtime=dict(snapshot_id='a'*64,model_lock_hash=digest(worker),settings=b['model'],
            checkpoint_revision=worker['revision'],tokenizer_revision=worker['tokenizer_revision'],dependencies={},
            generation_tokens={'eos_token_id':[1],'pad_token_id':1},chat_template={'template_hash':'test'},
            qualification_key='json',vram_total_bytes=3)
        report=dict(schema='rr-open-footprint-report-v3',protocol=f.PROTOCOL_V3,status='passed_observed_cases',command_failed=False,
            experiment_id=m['experiment_id'],manifest_hash=digest(m),packet_id=p['packet_id'],proposal_id=p['proposal']['proposal_id'],
            source_revision=m['source_revision'],model_executed=True,model_instances=1,pool=7,role_output_caps={'json':2048,'plan':6144},
            sql_executed=False,task_inputs_used=False,qualification_keys={'json':'json','plan':'plan'},runtime=runtime,calls=[],uncertain_tokens=0,**f.FLAGS)
        for case in p['cases']:
            lock=worker if case['role']=='json' else planner
            report['calls'].append(dict(id=case['id'],passed=True,dispatched=True,status='passed',uncertain_tokens=0,
                input_tokens=300,output_tokens=100,output_cap=report['role_output_caps'][case['role']],
                generation=dict(text=json.dumps(case['expected']),output_tokens=100,diagnostics=dict(rendered_input_tokens=300,
                    rendered_input_ids_hash=case['measurement']['rendered_input_ids_hash'],finish_reason='eos',constraint_complete=True,
                    action_constraint=lock['decoder_qualification']['contract'],eos_token_id=[1],last_generated_token_id=1)),
                memory=dict(peak_allocated_bytes=1,peak_reserved_bytes=2,total_bytes=3)))
        report['actual_tokens']=2000
        return m,report,worker

    def test_report_rejects_bad_accounting_role_keys_partial_cases_and_changed_response(self):
        m,r,w=self.sample();review.check_report(m,r,w)
        mutations=[lambda x:x.update(actual_tokens=2001),lambda x:x['calls'].pop(),
                   lambda x:x['qualification_keys'].update(plan='wrong'),
                   lambda x:x['calls'][0]['generation'].update(text='{}'),
                   lambda x:x['calls'][0]['generation']['diagnostics'].update(constraint_complete=False),
                   lambda x:x.update(task_execution_allowed=True)]
        for mutation in mutations:
            bad=deepcopy(r);mutation(bad)
            with self.assertRaises(BCError):review.check_report(m,bad,w)

    def test_snapshot_inventory_and_saved_file_changes_are_checked(self):
        m,r,w=self.sample()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run=root/'run';run.mkdir();snapshots=root/'snapshots';snapshot=snapshots/r['runtime']['snapshot_id']
            (snapshot/'resolved').mkdir(parents=True)
            r['runtime']['import_path']=str(snapshot/'src/beyond_consensus/models/transformers_backend.py')
            for path,value in ((run/'manifest.json',m),(run/'preflight.json',r),(snapshot/'resolved/manifest.json',m),(snapshot/'resolved/model-lock.json',w),(snapshot/'resolved/cluster.json',{})):
                path.write_text(json.dumps(value))
            marker=dict(cluster_hash=digest({}),manifest_hash=digest(m),source_revision=m['source_revision'],files={str(p.relative_to(snapshot)):review.file_hash(p) for p in snapshot.rglob('*') if p.is_file()})
            (snapshot/'snapshot.json').write_text(json.dumps(marker))
            audit=review.inspect(run,snapshots)
            self.assertTrue(audit['snapshot_inventory_verified']);self.assertFalse(audit['task_execution_allowed'])
            (snapshot/'unexpected.txt').write_text('changed')
            with self.assertRaises(BCError):review.inspect(run,snapshots)
