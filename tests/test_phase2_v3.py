"""Bounded CPU/mock acceptance controls. No outbound connections permitted."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import importlib.util
import itertools
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import allocation as a, analysis as an, planning as p, runtime as r, data, template
from bc_phase2.model import *
from bc_phase2.campaign import demo
NX=importlib.util.find_spec('networkx') is not None


class Offline(unittest.TestCase):
    def setUp(self):
        for target in ('socket.socket.connect','socket.create_connection'):
            m=patch(target,side_effect=AssertionError('outbound networking prohibited in mock controls'));m.start();self.addCleanup(m.stop)
    def workflow(self,edges=(),m=4):
        tasks=tuple(Task(f'x{i}',tuple(f'x{u}' for u,v in edges if v==i),base=i+1) for i in range(m))
        return Workflow('synthetic',tasks,tuple(t.id for t in tasks))


@unittest.skipUnless(NX,'optional local NetworkX 3.4.2 unavailable; matching not tested')
class Exact(Offline):
    def test_both_objectives_small_independent_oracle(self):
        for m in range(2,7):
            for edges in [[],[(i,i+1) for i in range(m-1)],[(0,i) for i in range(1,m)]]:
                w=self.workflow(edges,m);cs={t:str(F(i+1,3)) for i,t in enumerate(w.ids)}
                for n in range((m+1)//2,m+1):
                    for obj in ('mean','worst'):
                        result=a.solve(w,n,cs,obj);ref=a.reference(w,n,cs,obj)
                        pair=(result['sum'],result['max']) if obj=='mean' else (result['max'],result['sum'])
                        self.assertEqual(pair,ref['pair']);self.assertEqual(sum(len(g)==2 for g in result['groups']),m-n)
                        self.assertEqual(sum(len(g)==1 for g in result['groups']),2*n-m)
                        self.assertEqual(result['virtual_virtual_edges'],0)
    def test_rational_and_budget_thresholds(self):
        w=self.workflow(m=3);cs={'x0':'0.1','x1':'1/3','x2':'0.20'}
        best=a.solve(w,2,cs,'worst');self.assertEqual(best['integer_scale'],30)
        for budget in (0,best['max']-F(1,100),best['max'],best['max']+1):
            v=a.solve(w,2,cs,'mean',budget);ref=a.reference(w,2,cs,'mean',budget)
            self.assertEqual(v['status'],ref['status'])
    def test_nonperfect_and_arbitrary_labels(self):
        w=Workflow('labels',(Task('virtual:0'),Task('Z'),Task('aardvark')),('virtual:0','Z','aardvark'))
        self.assertEqual(a.solve(w,2,dict.fromkeys(w.ids,1))['status'],'optimal')
        import networkx as nx
        with patch.object(nx,'min_weight_matching',return_value={(0,1)}):
            self.assertEqual(a.solve(w,2,dict.fromkeys(w.ids,1))['status'],'infeasible')
    def test_independent_mean_invariance_and_no_choice(self):
        w=self.workflow(m=5);cs={t:i+1 for i,t in enumerate(w.ids)}
        vals=[a.metrics(w,3,g,cs)['sum'] for g in a.partitions(w.ids,3)]
        self.assertEqual(set(vals),{15});self.assertEqual(a.solve(w,5,cs)['groups'],tuple((t,) for t in w.ids))
    def test_shared_descendants_nested_pair_lower_bound(self):
        w=self.workflow([(0,2),(1,2),(2,3)]);cs=dict.fromkeys(w.ids,1)
        _,_,weights=a.prepare(w,2,cs);self.assertEqual(weights['x0','x1'],4)
        w=self.workflow([(0,2),(1,3)]);v=a.solve(w,2,cs,'worst');self.assertEqual(v['max'],2)
    def test_uniform_multiplicity_and_direct_balance(self):
        w=self.workflow(m=5);counts={}
        for order in itertools.permutations(w.ids):
            gs=groups(w,3,[order[:2],order[2:4],order[4:]]);counts[gs]=counts.get(gs,0)+1
        self.assertEqual(len(set(counts.values())),1)
        cs={t:i+1 for i,t in enumerate(w.ids)};best=a.solve(w,3,cs,'worst',direct=True)
        self.assertEqual(max(best['owned_costs']),min(max(sum(cs[t] for t in g) for g in gs) for gs in a.partitions(w.ids,3)))
    def test_greedy_strict_bounded_no_fallback(self):
        w=self.workflow([(0,2),(1,2),(2,3)]);cs={t:i+1 for i,t in enumerate(w.ids)}
        with patch.object(a,'solve',side_effect=AssertionError('no matching fallback')):
            result=a.greedy(w,2,cs,a.random_valid(w,2,4),'mean')
        pairs=[v['pair'] for v in result['moves']]
        self.assertLessEqual(len(pairs),20);self.assertTrue(all(x>y for x,y in zip(pairs,pairs[1:])))
    def test_unit_ablation_preserves_real_weights(self):
        w=self.workflow([(0,2),(1,2),(2,3)]);cs={t:i+1 for i,t in enumerate(w.ids)}
        allocation,details=a.allocate(w,2,cs,'matching_mean_unit')
        self.assertEqual(details['evaluation_under_supplied_costs'],a.metrics(w,2,allocation.groups,cs))


class Contracts(Offline):
    def test_invalid_dag_padding_costs_bounds(self):
        for tasks,outputs in [((Task('a',('b',)),Task('b',('a',))),('b',)),((Task('a'),Task('b')),('a',))]:
            with self.assertRaises(Invalid):Workflow('bad',tasks,outputs)
        w=self.workflow(m=3)
        for costs in [{'x0':1},dict.fromkeys(w.ids,0),dict.fromkeys(w.ids,0.1),dict.fromkeys(w.ids,'NaN'),dict.fromkeys(w.ids,True)]:
            with self.assertRaises(Invalid):a.prepare(w,2,costs)
        for n in (0,1,4,True):
            with self.assertRaises(Invalid):a.prepare(w,n,dict.fromkeys(w.ids,1))
    def test_llm_prompt_validation_no_fallback(self):
        w=self.workflow();req=a.llm_request(w,2,dict.fromkeys(w.ids,1),'mean')
        self.assertEqual(len(req['group_scores']),10)
        bad={'groups':[['x0']]};good={'groups':[['x0','x1'],['x2','x3']]}
        with patch.object(a,'solve',side_effect=AssertionError()):
            self.assertEqual(a.llm_reply(w,2,[bad])['status'],'invalid_allocation')
            self.assertEqual(a.llm_reply(w,2,[bad,good])['status'],'valid')
        with self.assertRaises(Invalid):a.llm_reply(w,2,[bad,bad,good])
    def test_mock_only_backend_guards(self):
        for backend in ('transformers','openai','http://localhost:8000','slurm','mock;curl'):
            with self.assertRaises(Invalid):r.worker_for(r.Executor(backend))
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml');p.validate_disabled(config)
        for key in ('api_calls_enabled','local_model_inference_enabled','downloads_enabled','cluster_submission_enabled','real_backends_registered_in_this_handoff'):
            bad=copy.deepcopy(config);bad['execution'][key]=True
            with self.assertRaises(Invalid):p.validate_disabled(bad)
        config['execution']['approval_record']={'approved':True};p.validate_disabled(config)
        self.assertFalse(p.stage_readiness(config,'main')['execution_allowed'])
    def test_template_mirror_and_budget_comparison(self):
        yaml=template.load(ROOT/'PILOT_MANIFEST_V3.yaml');j=template.load(ROOT/'configs/phase2/pilot-v3.disabled.json');self.assertEqual(yaml,j)
        j['comparative_run']['predicted_incident_budget']=0
        with self.assertRaises(Invalid):p.validate_disabled(j)
    def test_data_gold_isolation_and_source_split(self):
        row={'id':'p','problem':'2+2','answer':'4','solution':'SECRET'}
        pub,private=data.adapt('math500',row);self.assertEqual(set(pub),{'id','problem'});self.assertNotIn('SECRET',str(pub))
        gp={'id':'q','Question':'Pick','Correct Answer':'A','Incorrect Answer 1':'B','Incorrect Answer 2':'C','Incorrect Answer 3':'D','Explanation':'SECRET'}
        pub,priv=data.adapt('gpqa',gp);self.assertNotIn('Correct Answer',str(pub));self.assertNotIn('permutation',pub);self.assertEqual(pub,data.adapt('gpqa',gp)[0])
        self.assertEqual(pub['choices'][priv['answer']],'A')
        pub,_=data.adapt('gaia',{'id':'g','Question':'Q','Final answer':'SECRET','annotated_steps':'SECRET'});self.assertNotIn('SECRET',str(pub))
        with self.assertRaises(Invalid):data.adapt('arc100',row)
        with self.assertRaises(Invalid):data.source_split(['p'],['p'])
        with self.assertRaises(Invalid):data.source_split(['p','p'],[])
    def test_synthetic_evaluation_unknown_and_private_boundary(self):
        self.assertEqual(data.evaluate_fixture('math500',None,{'answer':'4'})['semantic'],'unknown')
        self.assertEqual(data.evaluate_fixture('gpqa',2,{'answer':2})['semantic'],'valid')
        self.assertEqual(data.evaluate_fixture('gaia','wrong',{'answer':'right'})['semantic'],'invalid')
        with self.assertRaises(Invalid):Task('mutable',parents=[])
    def test_estimator_no_heldout_runtime(self):
        w=self.workflow();e=data.SuppliedEstimator('v1',('dev',),tuple((t,'1') for t in w.ids))
        with self.assertRaises(Invalid):e.estimate(w,{'realised_tokens':1})
        with self.assertRaises(Invalid):e.validate_fit_sources(['test'])
        self.assertEqual(set(e.estimate(w)),set(w.ids))
    def test_stage_dependency_order(self):
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml');keys=config['stage_gate_requirements']
        config['verified_bindings']={k:'mock-bound' for k in keys['all_model_execution']+keys['calibration']}
        self.assertTrue(p.stage_readiness(config,'calibration')['dependencies_ready'])
        self.assertFalse(p.stage_readiness(config,'calibration')['execution_allowed'])
        self.assertFalse(p.stage_readiness(config,'main')['dependencies_ready'])
        self.assertNotIn('attack_policy_owner_budget_sham_and_detection_boundary',p.stage_readiness(config,'calibration')['missing'])
    def test_pilot_actual_arithmetic_and_scale(self):
        ws=[(fixture(n+1,source=f'pilot:{n}:{i}'),n) for n in (4,7,10) for i in range(4)]
        self.assertEqual(p.pilot_eligibility(ws),{'clean':24,'repairs':1008,'total':1032})
        with self.assertRaises(Invalid):p.pilot_eligibility(ws[:-1])
        self.assertEqual(p.scale_coverage([4],[4,7,10])['unsupported_n'],[7,10])
    def test_frozen_slot_schedule_invalid_kept(self):
        w=fixture(6);gs=a.random_valid(w,4,17);aa=Allocation(w.key,4,gs,'e','random_valid',17)
        cc=[{'method':'random_valid','allocation':aa},{'method':'llm_mean','allocation':None}]
        reg=p.compile_slots(w,4,cc,2,'exec','e',seed=1)
        self.assertEqual(len(reg['slots']),16);self.assertEqual(sum(s['invalid_allocation'] for s in reg['slots']),8)
        self.assertEqual(reg['slots'],p.compile_slots(w,4,list(reversed(cc)),2,'exec','e',seed=1)['slots'])
        self.assertEqual({s['allocation'] for s in reg['slots'] if s['method']=='random_valid'},{aa.key})
        with self.assertRaises(Invalid):p.compile_slots(w,4,cc,2,'exec','other')


class Runtime(Offline):
    def setUp(self):
        super().setUp();self.w=fixture(3);self.e=r.Executor();self.a=Allocation(self.w.key,2,(('t00','t02'),('t01',)),'e','test',1)
    def clean(self):return r.execute(self.w,self.e,0,r.Budget(1000))
    def test_chain_interleaved_owner_and_payload_invariance(self):
        other=replace(self.a,groups=(('t00',),('t01','t02')),method='other')
        proof=r.invariance(self.w,[self.a,other],self.e);self.assertEqual(proof['status'],'passed')
        trace=self.clean();self.assertEqual(trace.execution,'completed');self.assertEqual(trace.semantic,'valid')
        for t in self.w.tasks:
            payload=r.payload(self.w,t,self.e);self.assertFalse({'owner','method','gold','history'}&payload.keys())
    def test_protected_reads_and_no_hidden_memory(self):
        access=r.Access({},{} )
        with self.assertRaises(Invalid):access.parent('secret')
        with self.assertRaises(Invalid):access.source('gold')
        class Bad:
            def invoke(self,payload,access,key):access.parent('t02')
        out=r.execute(self.w,self.e,0,r.Budget(1000),worker=Bad());self.assertEqual(out.execution,'protocol_violation')
    def test_independent_physical_replay_fresh_versions(self):
        clean=self.clean();before=digest(clean);count=[]
        class Count(r.MockWorker):
            def invoke(self,*args):count.append(args[0]['task']);return super().invoke(*args)
        results=[r.repair(self.w,self.e,0,r.Budget(1000),clean,self.a,g,worker=Count())['trace'] for g in self.a.groups]
        self.assertEqual(digest(clean),before);self.assertEqual(len(count),5)
        self.assertEqual([v.full_cost for v in results],[6,5])
        for result,g in zip(results,self.a.groups):
            original={v.task:v for v in clean.artifacts};affected=closure(g,self.w.edges)
            for v in result.artifacts:
                if v.task in affected:self.assertNotEqual(v.version,original[v.task].version)
                else:self.assertEqual(v,original[v.task])
    def test_missing_snapshot_and_wrong_clean(self):
        incomplete=r.execute(self.w,self.e,0,r.Budget(1));result=r.repair(self.w,self.e,0,r.Budget(100),incomplete,self.a,self.a.groups[0])
        self.assertEqual(result['execution'],'no_clean_snapshot');self.assertIsNone(result['full_cost'])
        class Wrong(r.MockWorker):
            def invoke(self,*args):v,u=super().invoke(*args);return v+1,u
        wrong=r.execute(self.w,self.e,0,r.Budget(100),worker=Wrong());self.assertEqual(wrong.semantic,'invalid');self.assertIsNotNone(wrong.full_cost)
        repaired=r.repair(self.w,self.e,0,r.Budget(100),wrong,self.a,self.a.groups[0]);self.assertFalse(repaired['restored_from_valid_clean'])
    def test_streams_label_independence_and_repeat_separation(self):
        args=(self.w,self.e,0,'t01','repair',0,self.a,self.a.groups[0])
        base=r.stream_id(*args);label=replace(self.a,method='another label')
        self.assertEqual(base,r.stream_id(*args[:6],label,self.a.groups[0]))
        self.assertNotEqual(base,r.stream_id(self.w,self.e,1,'t01','repair',0,self.a,self.a.groups[0]))
        self.assertNotEqual(base,r.stream_id(*args[:7],self.a.groups[1]))
    def test_corruption_internal_terminal_and_sham(self):
        clean=self.clean()
        attack=r.corrupt_and_restore(self.w,self.e,0,r.Budget(1000),clean,self.a,self.a.groups[0])
        self.assertTrue(attack['downstream_reads']);self.assertEqual(attack['continuation'].semantic,'invalid');self.assertEqual(attack['repair'].semantic,'valid')
        terminal=replace(self.a,groups=(('t00','t01'),('t02',)))
        x=r.corrupt_and_restore(self.w,self.e,0,r.Budget(1000),clean,terminal,('t02',))
        self.assertEqual(x['direct_output_exposure'],['t02']);self.assertEqual(x['downstream_reads'],[])
        sham=r.corrupt_and_restore(self.w,self.e,0,r.Budget(1000),clean,self.a,self.a.groups[0],sham=True)
        self.assertEqual(sham['continuation'].semantic,'valid');self.assertEqual(sham['direct_output_exposure'],[])
    def test_early_abort_completes_missing_unaffected_tasks(self):
        w=Workflow('abort',tuple(Task(f't{i}') for i in range(4)),tuple(f't{i}' for i in range(4)))
        aa=Allocation(w.key,2,(('t0','t1'),('t2','t3')),'e','test',1);clean=r.execute(w,self.e,0,r.Budget(100))
        x=r.corrupt_and_restore(w,self.e,0,r.Budget(100),clean,aa,('t0','t1'),abort_after=1)
        self.assertEqual(x['repair_tasks'],('t0','t1','t2','t3'));self.assertEqual(x['completion_tasks'],('t1','t2','t3'))
        self.assertEqual(x['reconstruction_tasks'],('t0',));self.assertFalse(x['theorem_complete_work_cost_applicable']);self.assertEqual(x['repair'].full_cost,4)
        self.assertEqual(x['reconstruction_observed_spend'],1);self.assertEqual(x['completion_observed_spend'],3)
    def test_failed_attempt_is_missing_completion_and_unaffected_prefix_preserved(self):
        w=Workflow('failed',tuple(Task(f't{i}') for i in range(4)),tuple(f't{i}' for i in range(4)))
        aa=Allocation(w.key,2,(('t0','t3'),('t1','t2')),'e','test',1);clean=r.execute(w,self.e,0,r.Budget(100))
        class Bad(r.MockWorker):
            def invoke(self,payload,*args):
                v,u=super().invoke(payload,*args)
                return ('bad' if payload['task']=='t2' else v),u
        result=r.corrupt_and_restore(w,self.e,0,r.Budget(100),clean,aa,('t1','t2'),worker=Bad())
        self.assertEqual(result['preserved_tasks'],('t0',));self.assertEqual(result['completion_tasks'],('t2','t3'))
        self.assertEqual(result['reconstruction_tasks'],('t1',));self.assertEqual(result['continuation'].schema,'invalid')
        self.assertEqual(result['repair'].semantic,'valid')
        self.assertEqual(result['repair'].artifacts[0],clean.artifacts[0])
    def test_missing_usage_retained_and_schema_error_not_cheap(self):
        class Unknown(r.MockWorker):
            def invoke(self,*args):v,_=super().invoke(*args);return v,Usage(None,'missing')
        b=r.Budget(100);x=r.execute(self.w,self.e,0,b,worker=Unknown());self.assertIsNone(x.full_cost);self.assertTrue(b.unresolved)
        with self.assertRaises(r.BudgetStop):b.reserve('other',1)
        class BadSchema(r.MockWorker):
            def invoke(self,*args):v,u=super().invoke(*args);return 'invalid',u
        x=r.execute(self.w,self.e,0,r.Budget(100),worker=BadSchema());self.assertEqual(x.schema,'invalid');self.assertGreater(x.observed_spend,0);self.assertIsNone(x.full_cost)
    def test_atomic_reservations(self):
        b=r.Budget(8);results=[]
        def use(k):
            try:b.reserve(k,8);results.append(True)
            except r.BudgetStop:results.append(False)
        ts=[threading.Thread(target=use,args=(str(i),)) for i in range(8)]
        for t in ts:t.start()
        for t in ts:t.join()
        self.assertEqual(results.count(True),1)
    def test_append_only_attempts_resume_and_retry_limits(self):
        with tempfile.TemporaryDirectory() as td:
            j=r.Journal(td,{'fixed':1});self.assertTrue(j.begin('slot'))
            with self.assertRaises(Invalid):j.begin('slot')
            j.finish('slot',0,{'execution':'infrastructure_failure','bill':None})
            with self.assertRaises(Invalid):j.begin('slot',1,0)
            self.assertTrue(j.begin('slot',1,1));j.finish('slot',1,{'execution':'completed','bill':3})
            self.assertFalse(j.begin('slot',2,2));self.assertEqual(len(j.events()),4)
            with self.assertRaises(Invalid):j.finish('slot',1,{'execution':'completed'})
            with self.assertRaises(Invalid):r.Journal(td,{'fixed':2})
    def test_schema_failure_cannot_retry(self):
        with tempfile.TemporaryDirectory() as td:
            j=r.Journal(td,{});j.begin('x');j.finish('x',0,{'execution':'task_error'})
            with self.assertRaises(Invalid):j.begin('x',1,3)


class Reporting(Offline):
    def rows(self):
        w=fixture(3);aa=Allocation(w.key,2,(('t00','t02'),('t01',)),'e','test',1)
        rows=[{'condition':aa.key,'partition':aa.partition,'estimator':'e','executor':'exec','unit':'synthetic_work',
               'owner':aa.owner(g),'repeat':rep,'full_cost':v,'execution':'completed','usage':'complete','semantic':'invalid','schema':'valid','observed_spend':v}
              for g,vs in zip(aa.groups,((1,9),(6,6))) for rep,v in enumerate(vs)]
        return aa,rows
    def test_full_cost_matrix_three_statistics_and_wrong_retained(self):
        aa,rows=self.rows();v=an.matrix(rows,aa,2,'exec','synthetic_work')
        self.assertEqual((v['mean'],v['worst_owner_mean'],v['observed_max']),(F(11,2),6,9));self.assertEqual(v['semantic_invalid_retained'],4)
        self.assertEqual(an.matrix(rows[:-1],aa,2,'exec','synthetic_work')['status'],'incomplete')
    def test_mixed_duplicate_and_unknown_matrix(self):
        aa,rows=self.rows()
        with self.assertRaises(Invalid):an.matrix(rows+rows[:1],aa,2,'exec','synthetic_work')
        for field in ('condition','partition','estimator','executor','unit'):
            bad=copy.deepcopy(rows);bad[0][field]='changed'
            with self.assertRaises(Invalid):an.matrix(bad,aa,2,'exec','synthetic_work')
        rows[0]['full_cost']=None;self.assertEqual(an.matrix(rows,aa,2,'exec','synthetic_work')['status'],'incomplete')
    def test_common_complete_vs_biased_individual_subsets(self):
        l={'a':{'status':'complete','mean':F(1)},'b':{'status':'incomplete'}};rr={'a':{'status':'complete','mean':F(2)},'b':{'status':'complete','mean':F(100)}}
        v=an.common_complete(l,rr,{'a':1,'b':1});self.assertEqual(v['cohort'],['a']);self.assertEqual(v['right'],2)
    def test_budget_known_failure_unknown_grade_not_run(self):
        good={'execution':'completed','semantic':'valid','schema':'valid','usage':'complete','full_cost':3,'observed_spend':3}
        self.assertEqual(an.restoration(good,3),'pass')
        self.assertEqual(an.restoration({**good,'semantic':'unknown'},3),'unknown')
        self.assertEqual(an.restoration({**good,'semantic':'invalid'},3),'fail')
        self.assertEqual(an.restoration({**good,'execution':'not_run_due_campaign_stop','full_cost':None},3),'unknown')
        self.assertEqual(an.restoration({**good,'execution':'invalid_allocation','full_cost':None},3),'fail')
        self.assertEqual(an.budget_status(None,5,4),'exceeded');self.assertEqual(an.budget_status(None,0,4),'unknown')
        self.assertEqual(an.budget_status(None,None,None),'not_applicable')
    def test_equal_source_endpoint_bounds_not_ci(self):
        row={'execution':'completed','semantic':'valid','schema':'valid','usage':'complete','full_cost':1,'observed_spend':1}
        v=an.endpoints({'a':[row]*10,'b':[{'execution':'pending'}]}, {'a':1,'b':1},2)
        self.assertEqual(v['bounds'],[F(1,2),F(1)]);self.assertIn('not confidence',v['kind'])


@unittest.skipUnless(NX,'optional local NetworkX 3.4.2 unavailable')
class EndToEnd(Offline):
    def test_complete_demo_three_ledgers_and_resume(self):
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml')
        with tempfile.TemporaryDirectory() as td:
            result=demo(td,config);self.assertEqual(len(result['outcomes']),64)
            self.assertEqual(result['summaries']['llm_worst']['status'],'invalid_allocation')
            self.assertEqual(result['accounting']['physical_clean_sessions'],2)
            self.assertTrue(any(x.get('physical_reuse') for x in result['outcomes']))
            for row in result['outcomes']:
                if row['execution']=='completed':self.assertEqual(row['deployment_cost'],row['clean_deployment_charge']+row['full_cost'])
            before=Path(td,'events.jsonl').read_bytes()
            with patch('bc_phase2.campaign.allocate',side_effect=AssertionError('no redraw on resume')):
                resumed=demo(td,config)
            self.assertEqual(resumed['spec'],result['spec']);self.assertEqual(before,Path(td,'events.jsonl').read_bytes())
            with self.assertRaises(Invalid):demo(td,config,cap=100)
    def test_resume_completed_checkpoint_without_reallocation_or_double_billing(self):
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml')
        original=r.Journal.append
        def interrupt(j,event):
            if event['type']=='logical_outcome':raise KeyboardInterrupt('simulated between-slot interruption')
            return original(j,event)
        with tempfile.TemporaryDirectory() as td:
            with patch.object(r.Journal,'append',interrupt):
                with self.assertRaises(KeyboardInterrupt):demo(td,config)
            history=r.Journal(td,json.loads(Path(td,'spec.json').read_text())).events()
            old_invocations={e['invocation'] for e in history if e['type']=='call_start'}
            with patch('bc_phase2.campaign.allocate',side_effect=AssertionError('no redraw')):
                result=demo(td,config)
            history=r.Journal(td,json.loads(Path(td,'spec.json').read_text())).events()
            invocations=[e['invocation'] for e in history if e['type']=='call_start']
            self.assertEqual(len(invocations),len(set(invocations)))
            self.assertTrue(old_invocations<=set(invocations))
            charged=sum(e['usage']['actual'] for e in history if e['type']=='call_end')
            self.assertEqual(charged,result['accounting']['known_research_spend'])
    def test_campaign_stop_keeps_all_slots(self):
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml')
        with tempfile.TemporaryDirectory() as td:
            result=demo(td,config,cap=20)
            self.assertEqual(len(result['outcomes']),64)
            self.assertTrue(any(x['execution']=='not_run_due_campaign_stop' for x in result['outcomes']))
            self.assertTrue(all(v.get('mean') is None for v in result['summaries'].values()))
