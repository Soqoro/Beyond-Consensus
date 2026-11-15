import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from bc_phase2 import prospective_sources as s, prospective_adapters as a, prospective_pipeline as p
from bc_phase2 import composite_math as worker, composite_scaling_runtime as rt
from bc_phase2.model import digest,Invalid
from test_medqa_worker_launch import Fake,alternate

class Prospective(unittest.TestCase):
    def fixture(self,dataset='math500',count=24):
        pubs={str(i):dict(id=str(i),problem=f'Synthetic x + {i} = 10') for i in range(count)}
        if dataset in ('medqa','gpqa'):
            pubs={str(i):dict(id=str(i),question=f'Synthetic item {i}',options=dict(zip('ABCD',['a','b','c','d']))) for i in range(count)}
        records=[dict(source_id=k,canonical_id=dataset+':'+k,exact_hash=s.faithful_identity(v)[0],normalized_hash=s.faithful_identity(v)[1],family_id='',status='eligible') for k,v in pubs.items()]
        exp=dict(cutoff='before',records=[],aliases=[])
        review=dict(dataset=dataset,revision='r',inventory_digest=digest(records),reviewer='synthetic',reviewed_at='now',decisions={k:'clear' for k in pubs})
        c=s.freeze(records,dataset,'r',exp,p.procedure(dataset),review)
        return pubs,records,exp,review,c
    def contracts(self,dataset='math500'):
        pubs,_,_,_,cohort=self.fixture(dataset)
        ids=[r['source_id'] for r in cohort['blocks'][0]['records']];dis={sid:{'status':'unsupported'} for sid in ids}
        for sid,length in zip(ids,[3,2]):
            tasks=[dict(id='T'+str(i+1),responsibility='Synthetic operation',required_inputs=['problem_statement'] if i==0 else ['T'+str(i)],produces='synthetic artifact') for i in range(length)]
            raw=json.dumps(dict(schema=p.natural.VERSION,source_id=sid,status='decomposed',tasks=tasks,final_assembly='[T'+str(length)+']'))
            terminal=['justification','option_label'] if dataset=='medqa' else ['justification','final_answer']
            review=dict(decision='admitted',reviewer='fixture',reviewer_kind='AI-assisted',reviewed_at='now',public_digest=digest(pubs[sid]),plan_digest=digest(raw),substantive_no_answer_leakage=True,
                tasks=[dict(id='t'+str(i),responsibility='Synthetic operation',parents=[] if i==0 else ['t'+str(i-1)],fields=terminal if i==length-1 else ['derivation','artifact']) for i in range(length)],outputs=['t'+str(length-1)])
            dis[sid]=p.admit(dataset,cohort,pubs[sid],raw,review)
        return pubs,cohort,dis
    def test_fixed_blocks_and_record_not_split_exclusion(self):
        pubs,records,exp,r,c=self.fixture('medqa',30);exp['records']=[dict(dataset='medqa',source_id='2',phase='historical')]
        out=s.freeze(records,'medqa','r',exp,p.procedure('medqa'),r)
        ids=[x['source_id'] for b in out['blocks'] for x in b['records']]
        self.assertNotIn('2',ids);self.assertEqual(len(ids),24);self.assertEqual(len(set(ids)),24)
        r['decisions'][ids[0]]='pending'
        changed=s.freeze(records,'medqa','r',exp,p.procedure('medqa'),r)
        self.assertEqual(ids,[x['source_id'] for b in changed['blocks'] for x in b['records']])
        self.assertEqual(changed['blocks'][0]['records'][0]['status'],'blocked')
    def test_duplicate_alias_failed_exposure(self):
        _,records,exp,r,_=self.fixture();exp['records']=[dict(dataset='math500',source_id='old',phase='historical',normalized_hash=records[0]['normalized_hash'])]
        exp['aliases']=[['math500','1','math500','old']]
        out=s.freeze(records,'math500','r',exp,p.procedure('math500'),r)
        self.assertEqual({x['source_id'] for x in out['excluded']},{'0','1'})
    def test_current_profile_not_historical(self):
        _,records,exp,r,_=self.fixture();exp['records']=[dict(dataset='math500',source_id='0',phase='prospective_profile')]
        out=s.freeze(records,'math500','r',exp,p.procedure('math500'),r)
        self.assertIn('0',[x['source_id'] for b in out['blocks'] for x in b['records']])
    def test_normalization_keeps_math_and_numbers(self):
        def h(t):return s.faithful_identity(dict(id='x',problem=t))[1]
        self.assertEqual(h('x + 2'),h(' x  + 2\n'));self.assertNotEqual(h('x+2'),h('x-2'));self.assertNotEqual(h('2'),h('3'))
    def test_aime_strict_parser_year_and_rich_intermediate(self):
        for x in ('0','099',' 999 '):self.assertIsInstance(a.integer(x),int)
        for x in (True,2,'1.0','1000','A: 2','2 or 3','１２','-1'):
            with self.assertRaises(Invalid):a.integer(x)
        x,k,m=a.aime(dict(problem='Synthetic',problem_idx=1,answer=2,problem_type='Algebra'),2025,'r',1)
        y,_,n=a.aime(dict(problem='Synthetic',problem_idx=1,answer='002'),2026,'r',1)
        self.assertNotEqual(x['id'],y['id']);self.assertIsNone(n['problem_type']);self.assertIsNone(n['sitting'])
        self.assertTrue(a.grade_aime('{"justification":"synthetic","final_integer":"002"}',k,x)['correct'])
        self.assertFalse(a.grade_aime('{"justification":"2","final_integer":"003"}',k,x)['correct'])
    def test_gpqa_no_answer_position_convention(self):
        prov=dict(repository='Idavidrein/gpqa',revision='r',configuration='gpqa_diamond')
        row={'Question':'Synthetic','Correct Answer':'oak','Incorrect Answer 1':'pine','Incorrect Answer 2':'fir','Incorrect Answer 3':'elm'}
        pub,private,_=a.gpqa(row,prov)
        other=dict(row);other['Correct Answer'],other['Incorrect Answer 1']=other['Incorrect Answer 1'],other['Correct Answer']
        pub2,key2,_=a.gpqa(other,prov)
        self.assertEqual(pub,pub2);self.assertNotEqual(private['correct_option'],key2['correct_option'])
        self.assertEqual(pub['options'][private['correct_option']],'oak')
        self.assertEqual(set(pub),{'id','question','options'})
        row['Incorrect Answer 1']=' oak '
        with self.assertRaises(Invalid):a.gpqa(row,prov)
    def test_medqa_preserves_option_order(self):
        row=dict(question='Synthetic',options=dict(D='four',C='three',B='two',A='one'),answer_idx='C',answer='three')
        pub,key=a.medqa_record(row,'x');self.assertEqual(pub['options']['C'],'three');self.assertEqual(key['correct_option'],'C')
        row['options']['D']='three'
        with self.assertRaises(Invalid):a.medqa_record(row,'x')
    def test_selection_whole_components_no_refill_timeout(self):
        pubs,c,d=self.contracts();w=p.wave(c,1,d)
        self.assertEqual(w['bundles'][0]['m'],5);self.assertEqual(len(w['components']),2)
        self.assertEqual(w['reused_profiles'],{});self.assertEqual(w['limits']['maximum_calls'],41)
        with self.assertRaises(Invalid):s.select_block(c,1,{**d,'foreign':{'status':'admitted'}})
        def timeout(*args):raise TimeoutError()
        self.assertEqual(s.select_block(c,1,d,timeout)['status'],'unresolved_feasibility')
        d2=deepcopy(d)
        for row in d2.values():row.update(future_cost=0,correct=True)
        self.assertEqual(p.wave(c,1,d2)['bundles'][0]['neutral'],w['bundles'][0]['neutral'])
    def test_selected_mode_changes_request_not_admin(self):
        pubs,c,d=self.contracts();component=next(r['component'] for r in d.values() if r['status']=='admitted')
        component['A_modes']=['original','algebraic'];component['reference_mode']='original'
        t=component['tasks'][0];original=p.spec.task(component,t,'original');alternative=p.spec.task(component,t,'algebraic')
        x=p.worker_request(component,original,pubs,{});y=p.worker_request(component,alternative,pubs,{})
        self.assertNotEqual(x['payload_digest'],y['payload_digest'])
        self.assertFalse({'method','owner','prices','score'} & y['payload'].keys())
        self.assertEqual(p.descriptor(component,t,'algebraic')['task'],alternative)
    def test_full_mock_sweep(self):
        pubs,c,d=self.contracts('medqa');w=p.wave(c,1,d)
        with tempfile.TemporaryDirectory() as td:
            fake=Fake();j=worker.Journal(Path(td)/'journal',fake,w['wave_id'],lambda:None,limits=w['limits'])
            result=rt.run_wave(j,pubs,td,w,alternate,interface=p)
            self.assertEqual(result['conditions'][0]['status'],'completed_comparison')
            summary=json.loads((Path(td)/'per-n-4-after-slot-1.json').read_text())
            self.assertEqual(summary['planned_slots'],len(c['blocks']))
            for m in result['conditions'][0]['methods'].values():self.assertEqual(len(m['repairs']),4)
            for payload in fake.calls:self.assertNotIn('correct_option',payload['source'])
            self.assertEqual(j.snapshot()['totals']['reserved_tokens'],0)
    def test_invalid_plan_continues_without_retry(self):
        pubs,_,_,_,c=self.fixture();size=len(c['blocks'][0]['records'])
        class PlanFake(Fake):
            def generate(self,r):return dict(input_tokens=30,output_tokens=1,finish_reason='eos',boundary_error=None,final_text='invalid')
        with tempfile.TemporaryDirectory() as td:
            j=worker.Journal(Path(td)/'j',PlanFake(),c['cohort_digest'],lambda:None,limits=dict(p.LIMITS,maximum_calls=size,wall_seconds=3600,token_cap=size*16384))
            rows=p.plan_block(j,c,1,pubs,Path(td)/'out')
            self.assertEqual(len(rows),size);self.assertTrue(all(r['review']['status']=='invalid' for r in rows))
            self.assertEqual(j.snapshot()['totals']['calls'],size)

    def test_tie_one_physical_sweep_and_unknown_reservations(self):
        pubs,c,d=self.contracts('medqa');w=p.wave(c,1,d)
        def same(domain,**kw):return dict(status='MOCK_TIE',candidate=kw['seed'])
        with tempfile.TemporaryDirectory() as td:
            fake=Fake();j=worker.Journal(Path(td)/'journal',fake,w['wave_id'],lambda:None,limits=w['limits'])
            r=rt.run_wave(j,pubs,td,w,same,interface=p)
            self.assertTrue(r['conditions'][0]['shared_observations'])
            self.assertEqual(r['conditions'][0]['paired_saving'],'0')
        with tempfile.TemporaryDirectory() as td:
            fake=Fake(lambda n:{'output_tokens':None});j=worker.Journal(Path(td)/'journal',fake,w['wave_id'],lambda:None,limits=w['limits'])
            with self.assertRaises(worker.Halt):rt.run_wave(j,pubs,td,w,same,interface=p)
            self.assertGreater(j.snapshot()['totals']['reserved_tokens'],0)
            with self.assertRaises(worker.Halt):j.invoke({'payload':{}},'other','other')
            self.assertEqual(len(fake.calls),1)
    def test_failed_profile_retains_unknown_and_no_selection(self):
        pubs,c,d=self.contracts('medqa');w=p.wave(c,1,d)
        def forbidden(*args,**kw):raise AssertionError('solver on incomplete prices')
        with tempfile.TemporaryDirectory() as td:
            fake=Fake(lambda n:{'finish_reason':'length_limit','output_tokens':3072} if n==1 else {})
            j=worker.Journal(Path(td)/'journal',fake,w['wave_id'],lambda:None,limits=w['limits'])
            r=rt.run_wave(j,pubs,td,w,forbidden,interface=p)
            self.assertEqual(r['conditions'][0]['status'],'blocked_profile_coverage')
            self.assertIsNone(r['profile_records'][0]['full_cost'])
            self.assertGreater(r['profile_records'][0]['known_attempted_spend'],0)
            self.assertTrue(r['profile_records'][1]['complete'])
    def test_disabled_planning_packet_and_policy_freeze(self):
        pubs,_,_,_,c=self.fixture('aime2025',12)
        packet=p.planning_packet(c,1,pubs)
        self.assertEqual(len(packet['requests']),6)
        self.assertEqual(packet['limits']['maximum_calls'],6)
        self.assertEqual(packet['limits']['token_cap'],98304)
        self.assertFalse(packet['execution_allowed'])
        self.assertEqual(packet['model_policy']['revision'],'fc05daec18b0a78c049392ed2e771dde82bdf654')
        changed=deepcopy(c);changed['procedure_digest']='wrong';changed['cohort_digest']=digest({k:v for k,v in changed.items() if k!='cohort_digest'})
        with self.assertRaises(Invalid):p.planning_packet(changed,1,pubs)

    def test_protected_source_and_cross_dataset_order_rejected(self):
        with self.assertRaises(Invalid):s.faithful_identity(dict(id='x',problem='x',answer='key'))
        _,records,exp,r,_=self.fixture()
        r['prior_selected']=[dict(dataset='gpqa')]
        with self.assertRaises(Invalid):s.freeze(records,'math500','r',exp,p.procedure('math500'),r)

if __name__=='__main__':unittest.main()
