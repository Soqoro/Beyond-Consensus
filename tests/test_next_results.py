"""Focused synthetic next-results checks. No model, dataset or scheduler access."""
from copy import deepcopy
import hashlib,json,tempfile,unittest
from pathlib import Path
from bc_phase2 import composite_dice_next as d, composite_scaling as s, composite_scaling_launch as old
from bc_phase2 import composite_common_derivation_launch as common, composite_derivation_interface as ci
from bc_phase2 import composite_scaling_runtime as runtime,composite_math as worker,medqa_development as med
from bc_phase2.model import digest,Invalid
from test_composite_scaling import Fake,retain,alternate,BANK

class Dice(unittest.TestCase):
    def setUp(self):
        self.parent=common.make_wave(old.make_wave(json.loads(BANK.read_text()),{}))
        self.wave=d.freeze(self.parent)
    def receipts(self):
        return {e['key']:dict(key=e['key'],descriptor=e['descriptor'],tokens=40,kind='historical_profile',invocation='mock-designated',reuse_verified=True) for e in self.wave['profile_coverage'] if e['source_id']!=d.DICE}
    def test_boundary_and_lineage(self):
        changed=[]
        for c in self.wave['components']:
            for t in c['tasks']:
                for a in c['A_modes']:
                    before=ci.descriptor(c,t,a);after=d.descriptor(c,t,a)
                    self.assertEqual(after['task']['fields'],before['task']['fields'])
                    if c['source_id']==d.DICE:
                        self.assertNotEqual(d.key(c,t,a),digest(before));changed.append(t['id'])
                        self.assertEqual(after['task']['responsibility'],before['task']['responsibility']+(d.BOUNDARY if t['id']=='t2' else ''))
                    else:self.assertEqual(after,before)
        self.assertEqual(changed,['t2','t3','t4'])
        self.assertFalse(any(x.isdigit() for x in d.BOUNDARY))
    def test_neutral_preservation_and_bounds(self):
        self.assertEqual([b['n'] for b in self.wave['bundles']],[4,3,5,7,8])
        self.assertEqual(self.wave['limits']['maximum_calls'],259)
        self.assertEqual(self.wave['limits']['token_cap'],4243456)
        self.assertEqual(self.wave['evaluation_sessions_ceiling'],64)
        for b in self.wave['bundles']:
            if b['n'] in (4,8):self.assertEqual(b['neutral'],next(x for x in self.parent['bundles'] if x['n']==b['n'])['neutral'])
            own=b['neutral']['ownership'];self.assertEqual(set(own.values()),{'o'+str(i) for i in range(b['n'])})
            self.assertTrue(all(list(own.values()).count(v)<=2 for v in set(own.values())))
        self.assertEqual([b['n'] for b in self.wave['bundles'] if d.DICE not in b['sources']],[3])
        self.assertEqual(len(self.receipts()),13)
    def run_mock(self,fault=None,solver=alternate):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
        w=d.attach_prices(self.wave,self.receipts());f=Fake(fault)
        j=worker.Journal(root/'journal',f,w['wave_id'],lambda:None,condition=d.VERSION,limits=w['limits'])
        result=runtime.run_wave(j,{c['source_id']:'synthetic' for c in w['components']},root,w,solver,interface=d)
        return result,j,f,root
    def test_one_profile_and_all_odd_owner_loops(self):
        r,j,f,out=self.run_mock()
        self.assertEqual(len(r['profile_records']),1);self.assertEqual(len(r['profile_records'][0]['invocations']),3)
        self.assertEqual([c['status'] for c in r['conditions']],['completed_comparison']*5)
        self.assertLessEqual(r['totals']['calls'],259)
        for c in r['conditions']:
            for m in ('NEUTRAL','JOINT'):
                self.assertEqual(len(c['methods'][m]['repairs']),c['n'])
        self.assertEqual(len(list(out.glob('per-n-*-after-slot-1.json'))),5)
    def test_local_producer_failure_independent_continuation(self):
        r,j,f,out=self.run_mock(lambda p,n:{'final_text':'{}'} if n==1 else {})
        self.assertEqual([c['status'] for c in r['conditions']],['blocked_profile_coverage','completed_comparison','blocked_profile_coverage','blocked_profile_coverage','blocked_profile_coverage'])
        dice=[x for x in f.calls if x['source']['id']==d.DICE];self.assertEqual(len(dice),1)
        self.assertEqual(r['profile_records'][0]['known_attempted_spend'],40)
        self.assertIsNone(r['profile_records'][0]['full_cost'])
    def test_explicit_inability_stops_consumers_but_wrong_complete_does_not(self):
        r,j,f,out=self.run_mock(lambda p,n:{'final_text':json.dumps({k:'UNAVAILABLE' for k in p['required_string_fields']})} if n==1 else {})
        self.assertEqual(len(r['profile_records'][0]['invocations']),1)
        self.assertEqual(r['conditions'][1]['status'],'completed_comparison')
    def test_reuse_no_missing_or_evaluation_prices(self):
        receipts=self.receipts();receipts.pop(next(iter(receipts)))
        with self.assertRaises(Invalid):d.attach_prices(self.wave,receipts)
        receipts=self.receipts();next(iter(receipts.values()))['kind']='evaluation'
        with self.assertRaises(Invalid):d.attach_prices(self.wave,receipts)
    def test_uncertain_usage_global_stop(self):
        with self.assertRaises(worker.Halt):self.run_mock(lambda p,n:{'output_tokens':None} if n==1 else {})

class MedQA(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(id='item'+str(i),question='Synthetic exam '+str(i),options=dict(A='first',B='second',C='third',D='fourth'),answer_idx='B',answer='second',rationale='PRIVATE') for i in range(14)]
    def intake(self,rows=None):
        raw=('\n'.join(json.dumps(r) for r in (rows or self.rows))).encode()
        p=dict(read_authorized=True,dataset='MedQA-USMLE',language='English',variant='four-option',split='dev',revision='synthetic',artifact='synthetic',terms_reference='synthetic',source_verification='synthetic',sha256=hashlib.sha256(raw).hexdigest())
        return med.intake(raw,p)
    def test_public_gold_independent_selection_and_all_options(self):
        packet,private=self.intake();self.assertEqual(len(packet['records']),12)
        other=deepcopy(self.rows)
        for r in other:r.update(answer_idx='D',answer='fourth',rationale='DIFFERENT')
        changed,_=self.intake(other)
        self.assertEqual(packet['records'],changed['records'])
        r=packet['records'][0];p=med.planner_request(r)['payload']
        self.assertEqual(p['source']['options'],self.rows[0]['options'])
        self.assertNotIn('PRIVATE',json.dumps(p));self.assertNotIn('answer_idx',json.dumps(p))
        bad=deepcopy(r);bad['answer_idx']='B'
        with self.assertRaises(Invalid):med.planner_request(bad)
    def test_exact_grading_and_ambiguous_mapping(self):
        p,priv=self.intake();r=p['records'][0];gold=priv[r['id']]
        def grade(label):return med.grade(json.dumps(dict(justification='A prose answer is not authoritative',option_label=label)),gold,r)
        self.assertTrue(grade('B')['correct']);self.assertFalse(grade('A')['correct'])
        self.assertEqual(grade(' B')['status'],'structurally_invalid')
        self.assertEqual(med.grade('{"justification":"ok","option_label":"B","answer":"second"}',gold,r)['status'],'structurally_invalid')
        row=dict(question='q',options=dict(A='same',B='same',C='c',D='d'),answer='same')
        pub=med.public_record(row,'x');pro=med.protected_record(row,'x',pub)
        self.assertEqual(med.grade('{"justification":"ok","option_label":"A"}',pro,pub)['status'],'unknown_grade')
        row['answer_idx']='B';self.assertEqual(med.protected_record(row,'x',pub)['correct_option'],'B')
    def component(self,i,count=2):
        pub=dict(id='synthetic'+str(i),question='Synthetic '+str(i),options=dict(A='a',B='b',C='c',D='d'))
        plan=dict(raw_response=json.dumps(dict(schema=med.natural.VERSION,source_id=pub['id'],status='single_task',tasks=[dict(id='T1',responsibility='Reason about synthetic exam',required_inputs=['problem_statement'],produces='candidate')],final_assembly='[T1]')))
        tasks=[dict(id='t'+str(j),responsibility='Synthetic substantive responsibility '+str(j),parents=[] if j==0 else ['t'+str(j-1)],fields=['justification','option_label'] if j==count-1 else ['derivation','artifact']) for j in range(count)]
        review=dict(decision='admitted',reviewer='synthetic',reviewed_at='synthetic',public_digest=digest(pub),plan_digest=digest(plan),substantive_no_answer_leakage=True,tasks=tasks,outputs=['t'+str(count-1)])
        return pub,plan,review
    def test_review_gate_and_unique_profile_caps(self):
        entries=[];sources={}
        for i in range(6):
            pub,plan,rev=self.component(i);entries.append(med.admit(pub,plan,rev));sources[pub['id']]=pub
        bad=deepcopy(rev);bad['decision']='pending'
        with self.assertRaises(Invalid):med.admit(pub,plan,bad)
        w=med.freeze_bundles(entries);self.assertEqual(len(w['bundles']),3)
        self.assertLessEqual(w['profile_calls'],24);self.assertLessEqual(w['evaluation_calls'],240)
        self.assertEqual(w['limits']['maximum_calls'],w['profile_calls']+w['evaluation_calls'])
        c=entries[0];req=med.worker_request(c,c['tasks'][0],sources,{})
        self.assertEqual(req['payload']['source'],sources[c['source_id']]);self.assertNotIn('reviewer',json.dumps(req))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fake=Fake();j=worker.Journal(root/'journal',fake,w['wave_id'],lambda:None,condition=med.VERSION,limits=w['limits'])
            out=runtime.run_wave(j,sources,root,w,retain,interface=med)
            self.assertEqual([c['status'] for c in out['conditions']],['completed_comparison']*3)
    def test_source_permission_and_variant_fail_closed(self):
        with self.assertRaises(Invalid):med.intake(b'',{'read_authorized':False})
        rows=deepcopy(self.rows);rows[0]['options']['E']='fifth'
        packet,_=self.intake(rows);self.assertEqual(len(packet['blocked']),1)

if __name__=='__main__':unittest.main()

class HistoricalProjection(unittest.TestCase):
    def test_designated_receipt_projection_and_mutations(self):
        from bc_phase2.composite_math_decoder import schema
        from bc_phase2.joint_core import explicit_selection,compile_organisation
        c=deepcopy(next(c for c in s.reviewed(json.loads(BANK.read_text())) if c['source_id']=='test/geometry/880.json'))
        source='synthetic profile source';c['statement_sha256']=hashlib.sha256(source.encode()).hexdigest()
        c['contract_id']=digest({k:c[k] for k in ('source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode')});c['namespace']='c'+c['contract_id'][:10]
        model=dict(checkpoint='Qwen/Qwen3.5-27B',revision='fc05daec18b0a78c049392ed2e771dde82bdf654',non_thinking_verification={'synthetic':True},generation_tokens={},local_path='/synthetic',current_inventory={'files':[]})
        scope=dict(model=model,wave={'components':[c]})
        binding=dict(checkpoint=model['checkpoint'],revision=model['revision'],template=model['non_thinking_verification'],tokens={},context=16384,output=3072,do_sample=False,thinking=False,evidence='real_composite_worker_development',inventory_digest=digest(common.base.pilot.lock_for(scope)),decoder='task-fields-xgrammar-v1',xgrammar_version='0.1.32',decoder_cpu_seconds_per_call=30,schema_hashes={c['source_id']+':'+t['id']:digest(schema(d.revised_task(c,t,'base'))) for t in c['tasks']})
        class RenderedFake(Fake):
            def render(self,req):
                r=super().render(req);r.update(payload_digest=req['payload_digest'],rendered_ids_digest=digest(r['input_ids']));return r
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=RenderedFake();f.binding=binding
            j=worker.Journal(root/'journal',f,d.PARENT_SCOPE,lambda:None)
            domain=d.domain([c],2);neutral=s.neutral([c],2)['neutral']
            ex=compile_organisation(domain,explicit_selection(domain,neutral['A'],{},neutral['ownership']))
            engine=d.Engine(j,{c['source_id']:source},root,[c]);slot='profile/'+c['namespace']+'/base'
            row=engine.run(ex,slot,phase='profile');saved=worker.serial(row)
            receipts={}
            for t,trace in zip(c['tasks'],row['trace']):
                k=d.key(c,t,'base');receipts[k]=dict(kind='new_profile',key=k,descriptor=d.descriptor(c,t,'base'),invocation=trace['invocation'],tokens=trace['usage'],ledger_digest=digest(j.snapshot()))
            env=json.loads((root/'journal/ledger.json').read_text());prices={'receipts':receipts};profiles={slot:saved}
            got=d.import_profiles(scope,env,prices,profiles);self.assertEqual(len(got),2)
            self.assertTrue(all(v['reuse_verified'] and v['original_receipt']['kind']=='new_profile' for v in got.values()))
            for mutation in ('model','receipt','parent','ledger'):
                ss=deepcopy(scope);ee=deepcopy(env);pp=deepcopy(prices);rr=deepcopy(profiles)
                if mutation=='model':ss['model']['revision']='changed'
                if mutation=='receipt':next(iter(pp['receipts'].values()))['kind']='evaluation'
                if mutation=='parent':next(iter(rr[slot]['store'].values()))['value']='changed'
                if mutation=='ledger':ee['state']['attempts'][0]['actual_tokens']+=1
                with self.assertRaises(Invalid,msg=mutation):d.import_profiles(ss,ee,pp,rr)

class DispatchBoundaries(unittest.TestCase):
    def test_math_pending_and_changed_scope_approval_rejected(self):
        from unittest.mock import patch
        from bc_phase2 import composite_dice_next_launch as l
        with patch.object(l,'validate_manifest',return_value={'deployment':{'packages':l.base.EXPECTED_PACKAGES,'solver_importable':True}}):
            a=dict(schema=l.KEY+'-approval',scope_digest='x',decision='pending',reviewer='test',reviewed_at='now',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):l.approve({'blockers':[],'scope_digest':'x'},a)
            a['decision']='approved'
            with self.assertRaises(Invalid):l.approve({'blockers':[],'scope_digest':'other'},a)
    def test_twelve_planning_calls_invalid_continues_no_retry(self):
        helper=MedQA();helper.setUp();packet,_=helper.intake()
        class PlannerFake(Fake):
            def generate(self,r):
                self.calls.append(deepcopy(r['payload']))
                source=r['payload']['source']['id']
                text='{}' if len(self.calls)==1 else json.dumps(dict(schema=med.natural.VERSION,source_id=source,status='unsupported',tasks=[],reason='Synthetic finding'))
                return dict(input_tokens=30,output_tokens=10,finish_reason='eos',boundary_error=None,final_text=text)
        with tempfile.TemporaryDirectory() as td:
            f=PlannerFake();j=worker.Journal(Path(td)/'journal',f,packet['cohort_digest'],lambda:None,condition=med.VERSION,limits=med.PLAN_LIMITS)
            result=med.plan_batch(j,packet)
            self.assertEqual(result['usage']['calls'],12);self.assertEqual(len(result['rows']),12)
            self.assertEqual(result['rows'][0]['review']['status'],'invalid')
            self.assertFalse(result['worker_execution_allowed'])
            self.assertEqual(len({p['source']['id'] for p in f.calls}),12)
            with self.assertRaises(worker.Halt):med.plan_batch(j,packet)
            with self.assertRaises(FileExistsError):worker.Journal(Path(td)/'journal',f,'different',lambda:None)
