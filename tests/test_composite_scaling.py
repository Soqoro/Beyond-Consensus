"""Focused offline component scaling integration; no real model/scheduler calls."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bc_phase2 import composite_scaling as s, composite_scaling_runtime as r, composite_scaling_launch as l
from bc_phase2 import composite_math as base
from bc_phase2.model import digest,Invalid
from bc_phase2.joint_core import explicit_selection,compile_organisation,evaluate

BANK=Path(__file__).resolve().parents[1]/'configs/phase2/composite_scaling_bank_v2.json'

class Fake:
    binding={'evidence':'synthetic_mock'}
    def __init__(self,fault=None):self.calls=[];self.fault=fault
    def render(self,req):return dict(input_tokens=30,input_ids=[1]*30,payload=req['payload'])
    def generate(self,x):
        self.calls.append(deepcopy(x['payload']));p=x['payload']
        result=dict(input_tokens=30,output_tokens=10,finish_reason='eos',boundary_error=None,
                    final_text=json.dumps({f:'incorrect synthetic answer' for f in p['required_string_fields']}))
        if self.fault:result.update(self.fault(p,len(self.calls)) or {})
        return result


def retain(d,**kw):return dict(status='MOCK_RETAINED',candidate=kw['seed'])
def alternate(d,**kw):
    seed=deepcopy(kw['seed']);own=seed['ownership'];tasks=sorted(own)
    # A label permutation must not share the other organisation's physical sweep.
    seed['ownership']={t:'o'+str((int(o[1:])+1)%d['n']) for t,o in own.items()}
    return dict(status='MOCK_EQUAL_SCORE_LABEL_CHANGE',candidate=seed)


class Scaling(unittest.TestCase):
    def setUp(self):
        self.bank=json.loads(BANK.read_text());self.entries=s.reviewed(self.bank)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def run_wave(self,n=2,solver=retain,fault=None):
        w=l.make_wave(self.bank,{})
        b=s.construct(self.entries,n,1);w['bundles']=[b]
        w['components']=b['components'];w['profile_coverage']=s.coverage(b['components'])
        w['profile_schedule']=r.schedule_profiles(b['components'],{});w['wave_id']=digest(w)
        fake=Fake(fault);journal=base.Journal(self.root/'journal',fake,w['wave_id'],lambda:None,condition=s.CONDITION,limits=w['limits'])
        result=r.run_wave(journal,{c['source_id']:'synthetic own source' for c in b['components']},self.root,w,solver)
        return result,journal,fake,b
    def test_supported_wave_and_pending_denominators(self):
        p=l.make_wave(self.bank,{})
        self.assertEqual([(b['n'],b['m']) for b in p['bundles']],[(2,3),(4,6),(6,9),(8,12)])
        self.assertEqual(len(p['matrix']),21);self.assertEqual(len(r.pending_rows(p)),42)
        self.assertEqual(sum(x['status']=='PENDING_REVIEW_NOT_FROZEN' for x in p['matrix']),17)
    def test_exclusions_search_budget_and_multiple_sources(self):
        first=s.construct(self.entries,2,1)
        second=s.construct(self.entries,2,2,[first['sources']])
        self.assertNotEqual(set(first['sources']),set(second['sources']))
        self.assertEqual(s.construct(self.entries,8,1,max_states=1)['status'],'CONSTRUCTION_UNRESOLVED')
        self.assertTrue(all(len(x['sources'])>=2 for x in [first,second]))
    def test_invalid_component_inputs_not_count_feasible_admission(self):
        c=deepcopy(self.entries[0]);c['tasks'][0]['parents']=['missing']
        c['contract_id']=digest({k:c[k] for k in ['source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode']});c['namespace']='c'+c['contract_id'][:10]
        with self.assertRaises(Invalid):s.domain([c,self.entries[1]],2)
    def test_prices_do_not_redraw_neutral_and_n_changes_domain(self):
        b=s.construct(self.entries,4,1);cs=b['components'];a=s.neutral(cs,4);z=s.neutral(cs,5)
        self.assertEqual(a['work_id'],z['work_id']);self.assertNotEqual(a['domain_structure_id'],z['domain_structure_id'])
        prices={x['key']:i+1 for i,x in enumerate(s.coverage(cs))}
        d=s.domain(cs,4,prices);before=s.neutral(cs,4)
        for k in prices:prices[k]*=9
        e=s.domain(cs,4,prices);after=s.neutral(cs,4)
        self.assertEqual(before,after);self.assertNotEqual(d,e);self.assertEqual(s.structural(d),s.structural(e))
        self.assertEqual(a['preprice_id'],digest(a['preprice_specification']))
    def test_payload_isolation_and_legacy_exactness(self):
        b=s.construct(self.entries,8,1)
        for c in b['components']:
            for t in c['tasks']:
                ps={p:{'synthetic':'same artifact'} for p in t['parents']}
                req=r.request(c,t,c['reference_mode'],{c['source_id']:'only own'},ps)
                self.assertNotIn('owner',req['payload']);self.assertNotIn('n',req['payload'])
                self.assertEqual(r.request(c,t,c['reference_mode'],{c['source_id']:'only own','unrelated':'secret'},ps),req)
        c=next(c for c in self.entries if c['source_id']==base.IDS[0]);t=c['tasks'][0]
        expected=base.request(base.TASKS[0],{base.IDS[0]:'only own'}, {})
        self.assertEqual(r.request(c,t,'original',{c['source_id']:'only own'},{}),expected)
    def test_profile_key_mismatch_and_evaluation_reuse_rejected(self):
        cov=s.coverage(self.entries);entry=cov[0];receipt=dict(key=entry['key'],descriptor=entry['descriptor'],tokens=40,kind='new_profile',invocation='x')
        r.validate_receipts({entry['key']:receipt},cov)
        receipt['kind']='evaluation'
        with self.assertRaises(Invalid):r.validate_receipts({entry['key']:receipt},cov)
        receipt['kind']='new_profile';receipt['descriptor']={}
        with self.assertRaises(Invalid):r.validate_receipts({entry['key']:receipt},cov)
    def test_chains_not_mean_invariant_edgeless_is(self):
        from bc_phase2.joint_fixtures import graph_fixture
        for parents,invariant in [({0:[],1:[0],2:[],3:[2]},False),({i:[] for i in range(4)},True)]:
            d=graph_fixture(2,4,2,parents)
            x=explicit_selection(d,{}, {},{'t0':'o0','t1':'o0','t2':'o1','t3':'o1'})
            y=explicit_selection(d,{}, {},{'t0':'o0','t1':'o1','t2':'o0','t3':'o1'})
            a=evaluate(compile_organisation(d,x))['sum'];b=evaluate(compile_organisation(d,y))['sum']
            self.assertEqual(a==b,invariant)
    def test_component_bound_and_cross_read_fallback(self):
        for n in (2,5,8):
            b=s.construct(self.entries,n,1);d=s.domain(b['components'],n);sel=explicit_selection(d,**dict(A=b['neutral']['A'],C={},ownership=b['neutral']['ownership']))
            ex=compile_organisation(d,sel);exact=2*(len(ex.operations)+sum(map(len,evaluate(ex)['recovery_sets'])))
            bounds=s.call_bounds(b['components'],n);self.assertLessEqual(exact,bounds['component']);self.assertLessEqual(bounds['component'],bounds['generic'])
            d['events'][0]['allowed_sources'].append('foreign_s0');self.assertFalse(s.isolation(d))
    def test_variable_n_two_rows_fresh_forks_and_tie(self):
        for n in (2,5,8):
            with self.subTest(n=n),tempfile.TemporaryDirectory() as directory:
                self.root=Path(directory);result,journal,fake,b=self.run_wave(n)
                c=result['conditions'][0];self.assertTrue(c['shared_observations']);self.assertEqual(set(c['methods']),{'NEUTRAL','JOINT'})
                row=c['methods']['NEUTRAL'];self.assertEqual(len(row['repairs']),n);self.assertEqual(row['question_quality'],'unknown')
                for repair in row['repairs']:
                    for event,art in repair.get('store',{}).items():
                        if event in repair['reconstruction']:self.assertIn(art['invocation'],repair['invocations'])
                        else:self.assertEqual(art,row['clean']['store'][event])
                self.assertEqual(journal.snapshot()['totals']['calls'],len(fake.calls))
    def test_equal_score_distinct_labels_do_not_share(self):
        result,_,_,_=self.run_wave(solver=alternate)
        c=result['conditions'][0];self.assertFalse(c['shared_observations'])
        self.assertNotEqual(c['methods']['NEUTRAL']['clean']['invocations'],c['methods']['JOINT']['clean']['invocations'])
    def test_wrong_complete_retained_missing_and_unknown_distinguished(self):
        result,_,_,_=self.run_wave();self.assertEqual(result['conditions'][0]['methods']['NEUTRAL']['status'],'complete')
        # Completeness is not a mathematical pass.
        self.assertEqual(result['conditions'][0]['methods']['NEUTRAL']['composite_quality'],'unknown')
        with tempfile.TemporaryDirectory() as d:
            self.root=Path(d);result,_,_,_=self.run_wave(fault=lambda p,i:{'final_text':'invalid'} if i==1 else {})
            self.assertEqual(result['conditions'][0]['status'],'blocked_profile_coverage')
        with tempfile.TemporaryDirectory() as d:
            self.root=Path(d)
            with self.assertRaises(base.Halt):self.run_wave(fault=lambda p,i:{'output_tokens':None})
            ledger=json.loads((self.root/'journal/ledger.json').read_text())['state']
            self.assertIsNone(ledger['attempts'][0]['actual_tokens'])
    def test_old_approval_and_imports_never_dispatch(self):
        with self.assertRaises((KeyError,Invalid)):l.open_transport({'manifest':{}})

    def test_timeout_does_not_select_easier_bundle(self):
        with patch.object(s,'neutral',side_effect=TimeoutError('fixture')) as call:
            row=s.construct(self.entries,4,1)
        self.assertEqual(row['status'],'CONSTRUCTION_UNRESOLVED');self.assertEqual(call.call_count,1)
    def test_rendered_component_invariance_and_source_scoped_decoder(self):
        from bc_phase2.composite_math_decoder import TaskTransport
        class Tokenizer:
            chat_template='synthetic test template'
            def encode(self,text,**kw):return list(text.encode())
            def apply_chat_template(self,messages,tokenize,**kw):
                text='<user>'+messages[0]['content']+'</user><assistant>'
                return {'input_ids':self.encode(text)} if tokenize else text
        transport=TaskTransport.__new__(TaskTransport);transport.tasks=r.catalog(self.entries)
        transport.tokenizer=Tokenizer();transport.template={'template_hash':digest(Tokenizer.chat_template)}
        shared=set(s.construct(self.entries,2,1)['sources'])&set(s.construct(self.entries,8,1)['sources'])
        for c in self.entries:
            if c['source_id'] not in shared:continue
            t=c['tasks'][0];req=r.request(c,t,c['reference_mode'],{c['source_id']:'same synthetic statement'}, {})
            a=transport.render(req);b=transport.render(deepcopy(req))
            self.assertEqual(a['input_ids'],b['input_ids']);self.assertEqual(a['decoder_task_id'],c['source_id']+':'+t['id'])
        self.assertGreater(len({TaskTransport.task_key(t) for t in transport.tasks}),len({t['id'] for t in transport.tasks}))
    def test_full_mock_wave_shared_profiles_counted_once(self):
        w=l.make_wave(self.bank,{});fake=Fake();j=base.Journal(self.root/'journal',fake,w['wave_id'],lambda:None,condition=s.CONDITION,limits=w['limits'])
        result=r.run_wave(j,{c['source_id']:'synthetic source' for c in w['components']},self.root,w,retain)
        self.assertEqual(len(result['conditions']),4);self.assertEqual(len(result['rows']),42)
        ledger=j.snapshot();pcalls=[a for a in ledger['attempts'] if a['slot'].startswith('profile/')]
        self.assertEqual(len(pcalls),16)
        p=json.loads((self.root/'prices.frozen.json').read_text());self.assertEqual(p['physical_new_profile_tokens'],16*40)
        self.assertEqual(len(p['receipts']),16)
        self.assertTrue(any(len(cs)>1 for cs in p['consumers'].values()))
        calls=len(fake.calls);again=r.run_wave(j,{},self.root,w,retain)
        self.assertEqual(again['totals'],result['totals']);self.assertEqual(len(fake.calls),calls)
        changed=deepcopy(w);changed['wave_id']='different'
        with self.assertRaises(Invalid):r.run_wave(j,{},self.root,changed,retain)
        c=result['conditions'][0];self.assertFalse(r.fixed_work_receipt_link(c,c)['independent_observation'])
        changed=deepcopy(c);changed['priced_domain_id']='different'
        with self.assertRaises(Invalid):r.fixed_work_receipt_link(c,changed)
    def test_import_actual_profile_only_and_no_evaluation_artifacts(self):
        # Portable synthetic rejection checks; actual historical receipts are separately exported.
        with self.assertRaises((Invalid,KeyError)):
            r.import_profiles({'files':{}},self.entries)
        with self.assertRaises((Invalid,KeyError)):
            r.import_ab_profiles({'files':{}},self.entries)
        c=self.entries[0];all_keys=s.coverage([c])
        receipts={x['key']:dict(key=x['key'],tokens=40,kind='historical_profile',invocation='prior',descriptor=x['descriptor']) for x in all_keys}
        self.assertEqual(r.schedule_profiles([c],receipts),[])
        self.assertEqual(len(self.bank['source_universe']),26)
        self.assertEqual(sum(c['status']=='diagram_blocked' for c in self.bank['components']),3)

    def test_ab_profile_import_filters_evaluation_and_verifies_requests(self):
        import hashlib
        from bc_phase2 import composite_joint as ab
        c=deepcopy(next(c for c in self.entries if c['source_id']==base.IDS[0]))
        c['statement_sha256']=hashlib.sha256(b'synthetic statement').hexdigest()
        scope={'model':{'non_thinking_verification':{'synthetic':True}}};scope_id=digest(scope)
        release={'manifest':{'scope':scope,'scope_digest':scope_id}};release['release_digest']=digest(release)
        binding={'scope':scope_id,'transport':dict(ab.WORKER_POLICY,template=scope['model']['non_thinking_verification'])}
        rows=[]
        for i,t in enumerate(c['tasks']):
            req=r.request(c,t,'algebraic',{c['source_id']:'synthetic statement'},{p:{'synthetic':'parent'} for p in t['parents']})
            rows.append(dict(id=f'call-{i}',slot='profile/algebraic',state='completed',request=req,rendered={'input_tokens':30},input_tokens=30,actual_tokens=40,reservation_tokens=3102,observation={'input_tokens':30,'output_tokens':10,'finish_reason':'eos'}))
        state={'binding':binding,'binding_digest':digest(binding),'attempts':rows+[dict(slot='JOINT/clean',actual_tokens=99999)]}
        env={'state':state,'sha256':digest(state)}
        files={'release/approved-release.json':{'content':release},'execution/journal/ledger.json':{'content':env},'execution/profile_algebraic.json':{'content':dict(snapshot_role='profile',slot='profile/algebraic',complete=True,invocations=['call-0','call-1'],full_cost=80)}}
        with patch.object(r,'AB_PROFILE_SCOPE',scope_id):
            receipts=r.import_ab_profiles({'files':files},[c]);self.assertEqual(sum(x['tokens'] for x in receipts.values()),80)
            rows[0]['request']['payload']['responsibility']='changed';env['sha256']=digest(state)
            with self.assertRaises(Invalid):r.import_ab_profiles({'files':files},[c])

if __name__=='__main__':unittest.main()
