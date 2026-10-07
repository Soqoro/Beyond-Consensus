"""Conditional F adapter controls; generated responses are labelled CPU doubles."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments import rr_open_fault as fault, rr_open_clean as clean
from beyond_consensus.util import BCError, digest, atomic_json
from reporecourse import v2
from reporecourse.resources import Resources
from reporecourse.tasks import load_task, private_task
from reporecourse.common import Rejected
from tests.test_rr_open_clean import candidate as clean_candidate
from tests.test_reporecourse import optional


def candidate():
    q=clean_candidate();p=load_task('synthetic-stock',Path('/unused'))[1]
    plan=v2.authored_plan(p,q['config'],'independent')
    a,b=plan['units'];a['id']='u0';b['id']='u1';b['depends']=['u0']
    b['consumes']={'stock_report':{'unit':'u0','artifact':'stock_report','format':'sql'}}
    r=Resources(100000,1200);key=r.reserve(100,6144);r.reconcile(key,80,20);r.reconcile_cpu('planner',0,0.01)
    frozen=v2.freeze(v2.request(p,q['config']),p,plan,r,[{'generation_dispatched':True}], 'real_model')
    assert frozen['status']=='valid',frozen['error']
    q.update(public_hash=digest(p),private_hash=digest(private_task('synthetic-stock')),task_hash='test-task',implementation_hashes={})
    q['episodes']=[dict(episode_id=digest([clean.SCHEMA,q['source_revision'],q['public_hash'],digest(q['backend_profile']),digest(q['config'])]),shard=0)]
    clean.seal(q)
    h=dict(frozen=frozen,config=q['config'],manifest_hash='historical-manifest',experiment_id='historical-clean',
           **{k:q[k] for k in ('model','public_hash','private_hash','task_hash','implementation_hashes')})
    m=dict(schema=fault.SCHEMA,source_revision=q['source_revision'],qualification=q,history=h,controls={},
           model=q['model'],config=q['config'],model_lock_sha256=q['model_lock_sha256'],shards=2,planned_episodes=2,
           episodes=fault.episodes(h),selection_rule=fault.SELECTION,approval=None,task_execution_allowed=False,
           campaign_allowed=False,confirmatory=False,limitations=fault.LIMITATIONS)
    return clean.seal(m),p


def approved():
    m,p=candidate();receipt=fault.approval_template(m)
    receipt.update(decision='approved',reviewer='CPU double only',reviewed_at='test')
    return fault.authorize(m,receipt),p


class Contracts(unittest.TestCase):
    def test_approval_separate_exact_and_scope_cannot_expand(self):
        m,p=candidate();fault.validate(m)
        with self.assertRaises(BCError):fault.authorize(m,fault.approval_template(m))
        with self.assertRaises(BCError):fault.authorize(m,clean.approval_template(m['qualification']))
        good,_=approved();fault.validate(good)
        for key,value in [('selection_rule','uniform'),('planned_episodes',3),('campaign_allowed',True),('task_execution_allowed',False)]:
            bad=deepcopy(good);bad[key]=value;clean.seal(bad)
            with self.subTest(key=key),self.assertRaises(BCError):fault.validate(bad)
        bad=deepcopy(good);bad['episodes'][1]['target']='w6';clean.seal(bad)
        with self.assertRaises(BCError):fault.validate(bad)

    def test_historical_plan_ledger_and_uniform_request_not_rewritten(self):
        m,p=candidate();before=deepcopy(m['history']['frozen'])
        self.assertEqual([e['target'] for e in fault.episodes(m['history'])],['w0','w1'])
        self.assertEqual(before,m['history']['frozen'])
        for field,value in [('actual_tokens',0),('uncertain_tokens',1),('cpu_seconds',0),('reservations',{'x':[1,2]})]:
            bad=deepcopy(m);f=bad['history']['frozen'];f['planning_resources'][field]=value
            f['frozen_id']=digest({k:v for k,v in f.items() if k!='frozen_id'});clean.seal(bad)
            with self.subTest(field=field),self.assertRaises((BCError,Rejected)):fault.validate(bad)
        bad=deepcopy(m);bad['history']['frozen']['plan']['units'][0]['worker']='w6';clean.seal(bad)
        with self.assertRaises((BCError,Rejected)):fault.validate(bad)

    def test_repeat_admission_and_other_shard_independence(self):
        m,p=approved()
        with tempfile.TemporaryDirectory() as tmp,patch.object(fault,'verify'):
            with self.assertRaises(BCError):fault.submission(candidate()[0],'.',{},'run',1,tmp)
            fault.submission(m,'.',{},'run',1,tmp)
            for mode,n in [('preflight',1),('run',2)]:
                with self.assertRaises(BCError):fault.submission(m,'.',{},mode,n,tmp)
            ep=Path(tmp)/'episodes'/m['episodes'][0]['episode_id'];ep.mkdir(parents=True)
            (ep/'started.json').write_text('{}')
            with self.assertRaises(BCError):fault.admission(m,tmp)
            with self.assertRaises(BCError):fault.admission(m,tmp,0)
            fault.admission(m,tmp,1)

    def test_routing_and_missing_or_changed_results_remain_visible(self):
        from beyond_consensus.experiments.runner import run_manifest
        from beyond_consensus.experiments.manifest import validate_manifest
        from beyond_consensus.evaluation.aggregate import aggregate
        m,p=approved();self.assertEqual(validate_manifest(m).shards,2)
        with self.assertRaises(BCError):run_manifest(m,Path('/unused'),Path('.'),backend=object())
        with self.assertRaises(BCError):fault.run(m,'/unused','.',model_lock=None,shard=0)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(aggregate(m,Path(tmp))['observed'],0)
            e=m['episodes'][0];path=Path(tmp)/'episodes'/e['episode_id']/'result.json'
            atomic_json(path,dict(provenance={'manifest_hash':digest(m)},experiment_id=m['experiment_id'],episode_id=e['episode_id'],track='F',target='w0',status='interrupted',success=None))
            summary=aggregate(m,Path(tmp));self.assertEqual(summary['observed'],1)
            self.assertIsNone(summary['branches'][0]['result']['success'])
            self.assertIsNone(summary['branches'][1]['result'])
            row=json.loads(path.read_text());row['target']='w1';atomic_json(path,row)
            with self.assertRaises(BCError):aggregate(m,Path(tmp))

    def test_interruption_preserves_planning_and_uncertain_reservations(self):
        m,p=candidate();saved={}
        class Engine:
            def __init__(self,*args,resources,**kw):
                self.r=resources;self.env=SimpleNamespace(state=lambda:{},events=[],close=lambda:None)
                self.failures=[];self.trajectories=[]
            def run(self):
                self.r.reserve(100,2048);self.r.reserve_cpu(31);raise InterruptedError()
        with patch('reporecourse.engine.Engine',Engine),patch('reporecourse.evaluator.evaluate') as evaluator:
            row=fault.execute(m,m['episodes'][0],p,{},object(),lambda k,v:saved.update({k:deepcopy(v)}))
        evaluator.assert_not_called();self.assertEqual(row['status'],'interrupted')
        self.assertEqual(row['resource_profile']['actual_tokens'],180)
        self.assertEqual(row['resource_profile']['uncertain_tokens'],2148)
        self.assertEqual(row['resource_profile']['uncertain_cpu'],31)
        self.assertEqual(row['resource_profile']['reserved_tokens'],0)
        self.assertTrue(row['model_executed']);self.assertEqual(saved['execution-record'],row)

    def test_new_roles_or_changed_public_material_blocked(self):
        m,p=candidate()
        for key,value in [('public_hash','changed'),('model',{})]:
            bad=deepcopy(m);bad['history'][key]=value;clean.seal(bad)
            with self.subTest(key=key),self.assertRaises(BCError):fault.validate(bad)
        bad=deepcopy(m);bad['config']['planner_output_cap']=2048;clean.seal(bad)
        with self.assertRaises((BCError,Rejected)):fault.validate(bad)

    @unittest.skipUnless(optional(),'Pinned optional execution dependencies required')
    def test_both_faults_real_engine_with_cpu_backend_double(self):
        m,p=candidate();old=deepcopy(m['history']['frozen']);outputs=[]
        class Backend:
            context_limit=16384
            def count_input(self,messages):return 100
            def generate(self,messages,*args):
                obs=json.loads(messages[-1]['content']);unit=obs['assignment'];name=unit['outputs'][0]
                imports=obs['execution_scope']['imports'];bindings={}
                if name=='stock_report':sql='SELECT sku, qty FROM stock ORDER BY sku'
                elif 'stock_report' in imports:
                    sql='SELECT sku FROM stock_report WHERE qty=0 ORDER BY sku';bindings={'stock_report':imports['stock_report']}
                else:sql='SELECT sku FROM stock WHERE qty=0 ORDER BY sku'
                action=dict(tool='publish',name=name,format='sql',content=sql,bindings=bindings,obligations=[name])
                return SimpleNamespace(text=json.dumps(action),output_tokens=80,reasoning_tokens=20,device_seconds=0,diagnostics={})
        for e in m['episodes']:
            row=fault.execute(m,e,p,private_task('synthetic-stock'),Backend(),lambda *_:None);outputs.append(row)
            self.assertTrue(row['success'],row);self.assertTrue(row['contract_conformant'])
            self.assertTrue(row['intervention_triggered']);self.assertIn(e['target'],row['state']['unavailable'])
            loss=next(v for v in row['events'] if v['type']=='unavailable')
            self.assertTrue(loss['before_publication']);self.assertEqual(loss['worker'],e['target'])
            self.assertEqual(row['resource_profile']['events'][:len(old['planning_resources']['events'])],old['planning_resources']['events'])
            self.assertEqual(row['planning_physical_generations'],0)
            self.assertTrue(row['physical_planning_reuse'])
            self.assertEqual(row['planning_logical_charges'],1)
            self.assertFalse(row['evaluation']['worker_feedback'])
            if e['target']=='w1':self.assertTrue(loss['retained_versions'])
            else:self.assertEqual(loss['retained_versions'],[])
        self.assertEqual(m['history']['frozen'],old)
        self.assertIsNot(outputs[0]['state'],outputs[1]['state'])

    def test_constructor_failure_is_recorded_not_evaluated(self):
        m,p=candidate()
        with patch('reporecourse.engine.Engine',side_effect=RuntimeError()),patch('reporecourse.evaluator.evaluate') as evaluator:
            row=fault.execute(m,m['episodes'][0],p,{},object(),lambda *_:None)
        evaluator.assert_not_called();self.assertEqual(row['status'],'infrastructure_failed')
        self.assertIsNone(row['success']);self.assertFalse(row['model_executed'])
        self.assertEqual(row['resource_profile']['actual_tokens'],180)

    def test_history_audit_checks_full_snapshot_and_changed_journals(self):
        from beyond_consensus.util import file_hash
        m,p=candidate();historical=m['qualification']
        receipt=clean.approval_template(historical)
        receipt.update(decision='approved',reviewer='CPU double',reviewed_at='test')
        historical=clean.authorize(historical,receipt)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'run';snapshots=root/'snapshots';snapshot=snapshots/('a'*64)
            ep=run/'episodes'/historical['episodes'][0]['episode_id']
            frozen=m['history']['frozen'];runtime=dict(snapshot_id='a'*64,model_lock_hash=digest({}),settings=historical['model'],
                import_path=str(snapshot/'src/beyond_consensus/models/transformers_backend.py'))
            result=dict(experiment_id=historical['experiment_id'],episode_id=historical['episodes'][0]['episode_id'],
                        provenance={'manifest_hash':digest(historical)},status='completed',success=True,contract_conformant=True,
                        execution_branches=1,fault_branches=0,evaluation={'success':True},runtime=runtime,
                        planning=frozen,plan=frozen['plan'],planning_logical_charges=1,
                        resource_profile=Resources(**deepcopy(frozen['planning_resources'])).summary())
            atomic_json(run/'manifest.json',historical);atomic_json(ep/'result.json',result)
            for name,data in [('started',None),('frozen-plan',frozen),('execution-record',result)]:
                atomic_json(ep/(name+'.json'),dict(manifest_hash=digest(historical),**({'content':data} if data else {})))
            atomic_json(snapshot/'resolved/manifest.json',historical)
            atomic_json(snapshot/'resolved/model-lock.json',{});atomic_json(snapshot/'resolved/cluster.json',{})
            marker=dict(files={str(f.relative_to(snapshot)):file_hash(f) for f in snapshot.rglob('*') if f.is_file()},
                        source_revision=historical['source_revision'],manifest_hash=digest(historical),cluster_hash=digest({}))
            atomic_json(snapshot/'snapshot.json',marker)
            submission=root/'receipt.json';atomic_json(submission,dict(job_id='123',output=str(run),snapshot=str(snapshot)))
            # Only conformance is doubled; actual saved-file hashes/inventory are checked.
            with patch('reporecourse.conformance.report',return_value={'contract_conformant':True}):
                audit=fault.inspect_history(run,snapshots,submission)
                self.assertTrue(audit['snapshot_inventory_verified']);self.assertFalse(audit['scheduler_completion_verified'])
                atomic_json(ep/'frozen-plan.json',dict(manifest_hash=digest(historical),content={}))
                with self.assertRaises(BCError):fault.inspect_history(run,snapshots,submission)
                atomic_json(ep/'frozen-plan.json',dict(manifest_hash=digest(historical),content=frozen))
                (snapshot/'unexpected.txt').write_text('changed')
                with self.assertRaises(BCError):fault.inspect_history(run,snapshots,submission)

    def test_cli_approval_keeps_pending_proposal_immutable(self):
        from beyond_consensus.reporecourse_cli import dispatch
        m,_=candidate()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);proposal=root/'proposal.json';receipt=root/'approval.json';out=root/'approved.json'
            atomic_json(proposal,m);a=fault.approval_template(m)
            a.update(decision='approved',reviewer='CPU double',reviewed_at='test');atomic_json(receipt,a)
            dispatch(SimpleNamespace(command='rr-open-fault-approve',manifest=proposal,approval=receipt,output=out))
            self.assertEqual(json.loads(proposal.read_text()),m)
            fault.validate(json.loads(out.read_text()))
            with self.assertRaises(FileExistsError):dispatch(SimpleNamespace(command='rr-open-fault-approve',manifest=proposal,approval=receipt,output=out))
