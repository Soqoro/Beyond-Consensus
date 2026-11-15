import json,sys,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from bc_phase2 import prospective_worker_launch as p, prospective_pipeline as pipeline
from bc_phase2.model import digest,Invalid
import test_prospective_cohort as fixtures
from test_medqa_worker_launch import Fake,alternate
from bc_phase2 import composite_math as worker,composite_scaling_runtime as runtime

class WorkerLaunch(unittest.TestCase):
    def test_actual_contract_freeze_and_bound(self):
        v=p.packet();w=v['wave'];b=w['bundles'][0]
        self.assertEqual(b['sources'],[r['source_id'] for r in p.planner.cohort()['blocks'][0]['records'][:4]])
        self.assertEqual((b['n'],b['m']),(4,6));self.assertTrue(b['call_bounds']['isolation_verified'])
        self.assertEqual(b['call_bounds']['evaluation_calls'],32)
        self.assertEqual(sum(x['calls'] for x in w['profile_schedule']),6)
        self.assertEqual(w['limits']['maximum_calls'],38);self.assertEqual(w['limits']['token_cap'],622592)
        self.assertEqual(w['reused_profiles'],{});self.assertEqual(w['planned_slots'],3)
        self.assertEqual(len(v['dispositions']),8)
        self.assertTrue(all(c['A_modes']==['base'] and c['C']=='direct_parent_artifacts' for c in w['components']))
        self.assertEqual(sum(len(t['parents']) for c in w['components'] for t in c['tasks']),2)
        self.assertEqual(len({digest(p.schema(t)) for t in p.transport_tasks({'wave':w})}),3)
    def test_pending_and_planner_approval_rejected(self):
        s={'deployment':{'packages':p.base.EXPECTED_PACKAGES,'solver_importable':True}}
        m={'scope_digest':'exact','blockers':[],'scope':s}
        a=dict(schema=p.KEY+'-approval',scope_digest='exact',decision='approved',reviewer='fixture',reviewed_at='now',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
        with patch.object(p,'validate_manifest',return_value=s):
            r=p.approve(m,a);self.assertEqual(p.validate_release(r),s)
            for key,value in [('decision','pending'),('schema',p.planner.KEY+'-approval'),('scope_digest','old'),('gpu_recipe_authorized',False)]:
                bad=dict(a);bad[key]=value
                with self.assertRaises(Invalid):p.approve(m,bad)
    def test_unapproved_dispatch_no_load_or_directory(self):
        with tempfile.TemporaryDirectory() as td,patch.object(p,'validate_release',side_effect=Invalid('unapproved')),patch.object(p,'open_transport') as load:
            out=Path(td)/'execution'
            with self.assertRaises(Invalid):p.dispatch({},out)
            load.assert_not_called();self.assertFalse(out.exists())
    def test_registry_dry_run_and_no_retry(self):
        with tempfile.TemporaryDirectory() as td:
            c=SimpleNamespace(output_root=td+'/out',snapshot_root=td+'/snap')
            s=dict(cluster={},scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4})
            with patch.dict('os.environ',{},clear=True),patch.object(p,'validate_release',return_value=s),patch.object(p,'source_records'),patch.object(p,'arguments',return_value=['sbatch','mock']),patch.object(p.base.cluster,'ClusterConfig',return_value=c),patch.object(p.base.cluster,'registry_root',return_value=Path(td)),patch.object(p.base.cluster,'guard'),patch.object(p.base.cluster,'validate_site'),patch.object(p.base.cluster,'command') as cmd:
                self.assertFalse(p.submit(Path(td),{'manifest':{'scope_digest':'scope'}})['submitted']);cmd.assert_not_called()
                (Path(td)/'registry.json').write_text(json.dumps({'composite_math_attempts':{p.KEY:{'state':'submitted_no_retry'}}}))
                with self.assertRaises(Invalid):p.submit(Path(td),{'manifest':{'scope_digest':'scope'}})
    def test_recipe_uses_existing_pipeline_and_retains_overhead(self):
        pubs,c,dis=fixtures.Prospective().contracts();w=pipeline.wave(c,1,dis)
        scope={'wave':w,'limits':w['limits'],'planning_overhead':{'calls':8,'actual_tokens':11491,'charged_physically_once':True}}
        token=p._scope.set(scope)
        try:
            with tempfile.TemporaryDirectory() as td:
                j=p.Journal(Path(td)/'journal',Fake(),w['wave_id'],lambda:None)
                original=pipeline.run_wave
                def run(j,s,out,w):return runtime.run_wave(j,s,out,w,alternate,interface=pipeline)
                with patch.object(pipeline,'run_wave',side_effect=run):r=p.run_recipe(j,pubs,td)
                self.assertEqual(r['conditions'][0]['status'],'completed_comparison')
                self.assertEqual(r['planning_overhead'],scope['planning_overhead'])
                for method in r['conditions'][0]['methods'].values():self.assertEqual(len(method['repairs']),4)
                self.assertEqual(r['totals']['reserved_tokens'],0)
        finally:p._scope.reset(token)
    def test_prepare_qualification_and_tamper_rejection(self):
        pubs,cohort,dis=fixtures.Prospective().contracts();w=pipeline.wave(cohort,1,dis)
        packet={'packet_digest':'packet','wave':w}
        model={'non_thinking_verification':{'template_hash':'fixture'}}
        old={'model':model,'source_package':{},'scheduler_policy':{'allow_accounted_external_jobs':True,'maximum_user_gpus':4}}
        h={'run':'/synthetic/run','release':{'manifest':{'scope':old}}}
        dep={'python':str(Path(sys.executable).resolve()),'packages':p.base.EXPECTED_PACKAGES,'solver_importable':True}
        cfg=dict(partition='HPCAIq',time='04:00:00',memory_gb=128,python=dep['python'],storage_root='/synthetic',cache_root='/synthetic/cache',snapshot_root='/synthetic/snap',output_root='/synthetic/out')
        def qualify(scope):
            schemas={digest(p.schema(t)):p.schema(t) for t in p.transport_tasks(scope)}
            controls={'derivation_first':dict(string_plus_eos=True,tokens_plus_eos=True,roundtrip_exact=True)}
            controls.update({name:dict(string_plus_eos=False,tokens_plus_eos=False) for name in ('derivation_last','extra_key','missing_field','malformed')})
            rows=[dict(schema_hash=h,schema=schema,passed=True,observations=[dict(eos=e,passed=True,checks=deepcopy(controls)) for e in (248046,248044)]) for h,schema in schemas.items()]
            requests=[]
            for c in w['components']:
                for mode in c['A_modes']:
                    for t0 in c['tasks']:
                        t=p.spec.task(c,t0,mode)
                        parents={pid:{f:'Synthetic parent artifact.' for f in next(x for x in c['tasks'] if x['id']==pid)['fields']} for pid in t['parents']}
                        req=pipeline.worker_request(c,t,pubs,parents)
                        requests.append(dict(source_id=c['source_id'],task=t['id'],mode=mode,synthetic_parents=bool(parents),input_tokens=100,payload_digest=req['payload_digest'],rendered_ids_digest='1'*64))
            return dict(status='passed_cpu_checks',model_executed=False,xgrammar_version='0.1.32',template=model['non_thinking_verification'],rows=rows,requests=requests)
        with patch.object(p,'packet',return_value=packet),patch.object(p,'parent_evidence',return_value=h),patch.object(p,'source_records',return_value=pubs),patch.object(p.base,'deployment',return_value=dep),patch.object(p,'qualify',side_effect=qualify):
            m=p.prepare('/synthetic/run',cfg,'PartitionName=HPCAIq State=UP')
            self.assertFalse(m['execution_allowed']);self.assertEqual(m['blockers'],[])
            for mutate in (lambda s:s['limits'].update(maximum_calls=999),lambda s:s['cpu_qualification']['requests'][0].update(payload_digest='0'*64),lambda s:s['cpu_qualification']['rows'][0]['observations'][0]['checks']['extra_key'].update(tokens_plus_eos=True),lambda s:s['planning_overhead'].update(actual_tokens=0)):
                bad=deepcopy(m);mutate(bad['scope']);bad['scope_digest']=digest(bad['scope'])
                with self.assertRaises(Invalid):p.validate_manifest(bad)

    def test_parent_wrong_result_hash_stops_before_reading_result(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'manifest.json').write_text(json.dumps({'release':{'manifest':{'scope_digest':p.packet()['planner_scope']}}}))
            Path(td,'execution').mkdir();Path(td,'execution/result.json').write_text('{}')
            with patch.object(p.planner,'validate_release',return_value={}):
                with self.assertRaisesRegex(Invalid,'original planner result bytes'):p.parent_evidence(td)

if __name__=='__main__':unittest.main()
