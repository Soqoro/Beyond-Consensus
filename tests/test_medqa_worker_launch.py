"""Bounded synthetic worker integration; no model, private dataset or scheduler."""
import json,itertools,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import medqa_worker_launch as l,medqa_development as m,composite_math as worker
from bc_phase2.model import digest,Invalid
from bc_phase2.joint_core import compile_organisation,explicit_selection

class Fake:
    binding={'evidence':'synthetic_mock'}
    def __init__(self,fault=None):self.calls=[];self.fault=fault
    def render(self,r):return dict(payload=r['payload'],input_tokens=30,input_ids=[1]*30)
    def generate(self,r):
        self.calls.append(deepcopy(r['payload']));p=r['payload']
        obj={k:'synthetic evidence '+str(len(self.calls)) for k in p['required_string_fields']}
        if 'option_label' in obj:obj['option_label']='B'
        v=dict(input_tokens=30,output_tokens=10,finish_reason='eos',boundary_error=None,final_text=json.dumps(obj))
        if self.fault:v.update(self.fault(len(self.calls)) or {})
        return v

def alternate(d,**kw):
    s=deepcopy(kw['seed']);s['ownership']={t:'o'+str((int(o[1:])+1)%4) for t,o in s['ownership'].items()}
    return dict(status='MOCK_DIFFERENT_LABELS',candidate=s)

class MedqaWorker(unittest.TestCase):
    def synthetic(self):
        cfg=l.frozen();sources={}
        for c in cfg['components']:
            pub=dict(id=c['source_id'],question='Synthetic question',options=dict(A='a',B='b',C='c',D='d'));sources[c['source_id']]=pub
            c['statement_sha256']=digest(pub);c['contract_id']=digest({k:c[k] for k in ('source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode')});c['namespace']='c'+c['contract_id'][:10]
        return cfg,sources
    def run_case(self,fault=None):
        cfg,sources=self.synthetic()
        with tempfile.TemporaryDirectory() as td,patch.object(l,'frozen',return_value=cfg):
            w=l.wave();f=Fake(fault);j=worker.Journal(Path(td)/'journal',f,w['wave_id'],lambda:None,limits=w['limits'])
            result=l.runtime.run_wave(j,sources,td,w,alternate,interface=l)
            return result,j.snapshot(),f
    def test_five_task_domain_and_all_ownerships(self):
        w=l.wave();d=l.domain(w['components'],4);ids=sorted(t['id'] for t in d['tasks'])
        for pair in itertools.combinations(ids,2):
            groups=[list(pair)]+[[t] for t in ids if t not in pair];own={t:'o'+str(i) for i,g in enumerate(groups) for t in g}
            compile_organisation(d,explicit_selection(d,{}, {},own))
        self.assertEqual(w['limits']['maximum_calls'],33);self.assertEqual(len(w['bundles']),1)
        self.assertTrue(l.spec.isolation(d))
    def test_full_fresh_profile_clean_all_owner_sweep(self):
        r,j,f=self.run_case();self.assertEqual(r['status'],'completed_wave_recipe')
        c=r['conditions'][0];self.assertEqual(c['status'],'completed_comparison')
        for method in ('NEUTRAL','JOINT'):
            self.assertEqual(len(c['methods'][method]['repairs']),4)
            self.assertTrue(c['methods'][method]['full_cost_coverage'])
        self.assertLessEqual(j['totals']['calls'],33);self.assertEqual(j['totals']['reserved_tokens'],0)
        for p in f.calls:
            self.assertEqual(set(p['source']),{'id','question','options'})
            self.assertEqual(set(p['source']['options']),set('ABCD'))
            self.assertFalse({'method','owner','correct_option','reviewer','prices'} & set(p))
    def test_failed_profile_blocks_without_retry(self):
        r,j,f=self.run_case(lambda n:{'finish_reason':'length_limit','output_tokens':3072} if n==1 else {})
        self.assertEqual(r['conditions'][0]['status'],'blocked_profile_coverage')
        self.assertLessEqual(j['totals']['calls'],5)
    def test_uncertain_usage_halts(self):
        with self.assertRaises(worker.Halt):self.run_case(lambda n:{'output_tokens':None})
    def test_option_label_strict_no_prose_salvage(self):
        e=object.__new__(l.Engine);t={'fields':['justification','option_label']}
        for label in ('a','A or B',' A ', ''):
            with self.assertRaises(Invalid):e.parse_artifact(json.dumps(dict(justification='A',option_label=label)),t)
        self.assertEqual(json.loads(e.parse_artifact('{"justification":"wrong reasoning","option_label":"D"}',t))['option_label'],'D')
    def test_pending_approval_rejected(self):
        dep=dict(packages=l.base.EXPECTED_PACKAGES,solver_importable=True)
        with patch.object(l,'validate_manifest',return_value={'deployment':dep}):
            a=dict(schema=l.KEY+'-approval',scope_digest='x',decision='pending',reviewer='test',reviewed_at='now',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):l.approve({'scope_digest':'x','blockers':[]},a)
            a['decision']='approved';a['scope_digest']='other'
            with self.assertRaises(Invalid):l.approve({'scope_digest':'x','blockers':[]},a)
    def test_source_fields_fail_closed(self):
        with self.assertRaises(Invalid):m.assert_public(dict(id='x',question='x',options=dict(A='a',B='b',C='c',D='d'),answer_idx='B'))

    def test_offline_grade_keeps_wrong_labels_and_unrun(self):
        cfg,sources=self.synthetic()
        protected={sid:dict(id=sid,public_digest=digest(pub),correct_option='A',status='known') for sid,pub in sources.items()}
        with patch.object(l,'frozen',return_value=cfg):
            w=l.wave();c=cfg['components'][0];eid=c['namespace']+'_e0'
            result=dict(wave_id=w['wave_id'],conditions=[dict(preprice_id=w['bundles'][0]['preprice_id'],methods={
                'NEUTRAL':dict(clean=dict(complete=True,store={eid:dict(value='{"justification":"A in prose","option_label":"B"}',invocation='test')})),
                'JOINT':dict(status='unrun')})])
            graded=l.grade_results(result,sources,protected)
            self.assertEqual(len(graded['rows']),30)
            self.assertFalse(graded['rows'][0]['grade']['correct'])
            self.assertEqual(graded['rows'][-1]['grade']['status'],'missing_artifact')
    def test_neutral_independent_of_future_profile_costs(self):
        w=l.wave();old=deepcopy(w['bundles'][0]['neutral']);cs=w['components']
        prices={e['key']:100+i for i,e in enumerate(l.coverage(cs))}
        l.domain(cs,4,prices)
        self.assertEqual(l.wave()['bundles'][0]['neutral'],old)
    def test_shared_launcher_overlap_dry_run_and_retry_guard(self):
        from types import SimpleNamespace
        from bc_phase2 import composite_math_launch as base
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as td:
            config=SimpleNamespace(output_root=td+'/out',snapshot_root=td+'/snap')
            scope=dict(cluster={},scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4})
            proto=SimpleNamespace(KEY=l.KEY,validate_release=lambda v:scope,source_records=lambda s:None,
                                  arguments=lambda c,s,o:['sbatch','synthetic-only'])
            value={'manifest':{'scope_digest':'scope'}}
            with patch.dict('os.environ',{},clear=True),patch.object(base.cluster,'ClusterConfig',return_value=config),patch.object(base.cluster,'registry_root',return_value=Path(td)),patch.object(base.cluster,'guard') as guard,patch.object(base.cluster,'validate_site'),patch.object(base.cluster,'command') as command:
                result=base.submit(Path(td),value,protocol=proto)
                self.assertFalse(result['submitted']);guard.assert_called_once_with({'jobs':[]},allow_accounted_overlap=True,requested_gpus=1);command.assert_not_called()
                (Path(td)/'registry.json').write_text(json.dumps({'jobs':[],'composite_math_attempts':{l.KEY:{'state':'submitted_no_retry'}}}))
                with self.assertRaises(Invalid):base.submit(Path(td),value,protocol=proto)
    def test_role_specific_prompts_and_all_fresh_price_keys(self):
        cfg,sources=self.synthetic()
        with patch.object(l,'frozen',return_value=cfg):
            for c in cfg['components']:
                for t in c['tasks']:
                    parents={p:{'derivation':'synthetic','artifact':'synthetic'} for p in t['parents']}
                    new=l.worker_request(c,t,sources,parents)
                    old=m.worker_request(c,t,sources,parents)
                    self.assertEqual({k:v for k,v in new['payload'].items() if k!='instruction'},
                                     {k:v for k,v in old['payload'].items() if k!='instruction'})
                    self.assertEqual(new['payload_digest'],digest(new['payload']))
                    prompt=new['payload']['instruction']
                    if t['id'] in c['outputs']:
                        self.assertIn('This is a terminal task.',prompt)
                        self.assertIn('option_label',prompt)
                    else:
                        self.assertIn('This is an intermediate task',prompt)
                        self.assertNotIn('option_label',prompt)
                        self.assertNotIn('For a terminal task',prompt)
                    self.assertNotEqual(l.key(c,t,'base'),m.key(c,t,'base'))
                    self.assertEqual(l.descriptor(c,t,'base')['prompt'],prompt)
            w=l.wave();self.assertEqual(w['reused_profiles'],{})
            self.assertEqual(sum(s['calls'] for s in w['profile_schedule']),5)
            self.assertEqual(w['bundles'][0]['neutral'],l.spec.neutral(cfg['components'],4)['neutral'])
    def test_real_call_path_uses_role_specific_prompt_in_every_phase(self):
        result,journal,fake=self.run_case()
        self.assertGreater(len(fake.calls),5)
        for payload in fake.calls:
            self.assertEqual(payload['instruction'],l.role_prompt({'fields':payload['required_string_fields']}))
    def test_old_version_approval_is_not_transferable(self):
        dep=dict(packages=l.base.EXPECTED_PACKAGES,solver_importable=True)
        with patch.object(l,'validate_manifest',return_value={'deployment':dep}):
            a=dict(schema='medqa-first-worker-composite-v1-approval',scope_digest='x',decision='approved',reviewer='test',reviewed_at='now',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):l.approve({'scope_digest':'x','blockers':[]},a)
