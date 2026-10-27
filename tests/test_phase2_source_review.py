"""Bounded source-review fixtures; independent raw-edge oracle, no models."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import allocation as a, runtime as r, campaign, template
from bc_phase2.model import Task,Workflow,Allocation,Usage,Invalid,digest,plain

A_EDGES=((0,3),(1,3),(1,4),(2,3),(2,5),(3,4),(3,5),(4,5))
A_COSTS=(5,8,5,5,1,1)


def raw_closure(group,edges):
    seen=set(group)
    while True:
        more={v for u,v in edges if u in seen}
        if more<=seen:return seen
        seen.update(more)


def raw_partitions(ids,n):
    # Independent insertion enumeration, not production's first-item pairing recursion.
    result=[]
    def visit(i,bins):
        if i==len(ids):
            if len(bins)==n:result.append(tuple(tuple(b) for b in bins))
            return
        for j in range(len(bins)):
            if len(bins[j])<2:
                bins[j].append(ids[i]);visit(i+1,bins);bins[j].pop()
        if len(bins)<n:visit(i+1,bins+[[ids[i]]])
    visit(0,[]);return result


def raw_rows(ids,n,edges,costs):
    rows=[]
    for gs in raw_partitions(ids,n):
        closures=[sorted(raw_closure(g,edges)) for g in gs]
        prices=[sum((F(costs[t]) for t in ds),F()) for ds in closures]
        rows.append({'groups':gs,'closures':closures,'R':prices,'sum':sum(prices),'max':max(prices)})
    return rows


def fixture_a():
    return Workflow('review:A',tuple(Task(str(i),tuple(str(u) for u,v in A_EDGES if v==i),synthetic_cost=c,call_cap=c) for i,c in enumerate(A_COSTS)),('5',))


class SourceReview(unittest.TestCase):
    def setUp(self):
        for name in ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection'):
            guard=patch(name,side_effect=AssertionError('offline review'));guard.start();self.addCleanup(guard.stop)

    def test_fixture_A_all_partitions_ties_budgets_relabelling(self):
        rows=raw_rows(tuple(range(6)),3,A_EDGES,A_COSTS);self.assertEqual(len(rows),15)
        self.assertEqual(min((v['sum'],v['max']) for v in rows),(34,17))
        self.assertEqual(min((v['max'],v['sum']) for v in rows),(15,39))
        by={v['groups']:v for v in rows}
        self.assertEqual(by[((0,2),(1,3),(4,5))]['R'],[17,15,2])
        self.assertEqual(by[((0,3),(1,4),(2,5))]['R'],[12,15,12])
        self.assertEqual(by[((0,1),(2,3),(4,5))]['R'],[20,12,2])
        for labels in (('0','1','2','3','4','5'),('virt:9','Z','a','two','q','root')):
            w=Workflow('review:A:labels',tuple(Task(labels[i],tuple(labels[u] for u,v in reversed(A_EDGES) if v==i)) for i in reversed(range(6))),(labels[5],))
            costs={labels[i]:c for i,c in enumerate(A_COSTS)}
            for b in (None,0,14,15,17):
                for objective in ('mean','worst'):
                    valid=[v for v in rows if b is None or v['max']<=b]
                    result=a.solve(w,3,costs,objective,b)
                    if not valid:self.assertEqual(result['status'],'infeasible');continue
                    key=lambda v:(v['sum'],v['max']) if objective=='mean' else (v['max'],v['sum'])
                    expected=min(valid,key=key)
                    self.assertEqual((result['sum'],result['max']),(expected['sum'],expected['max']))

    def test_fixture_A_all_owner_recorded_usage_and_artifacts(self):
        w=fixture_a();e=r.Executor();costs={str(i):c for i,c in enumerate(A_COSTS)}
        clean=r.execute(w,e,0,r.Budget(1000));original={v.task:v for v in clean.artifacts};before=digest(clean)
        for objective in ('mean','worst'):
            result=a.solve(w,3,costs,objective);alloc=Allocation(w.key,3,result['groups'],'fixture-costs',objective,0)
            for group,predicted in zip(alloc.groups,result['R']):
                calls=[]
                class Observed(r.MockWorker):
                    def invoke(self,payload,*args):calls.append(payload['task']);return super().invoke(payload,*args)
                out=r.repair(w,e,0,r.Budget(1000),clean,alloc,group,worker=Observed())['trace']
                expected={str(i) for i in raw_closure(tuple(map(int,group)),A_EDGES)}
                self.assertEqual(Counter(calls),Counter(expected));self.assertEqual(set(out.attempted),expected)
                recorded=sum(event['usage'].actual for event in out.events)
                self.assertEqual(out.full_cost,recorded);self.assertEqual(recorded,predicted)
                self.assertEqual(out.semantic,'valid');self.assertEqual(digest(clean),before)
                current={v.task:v for v in out.artifacts}
                self.assertEqual(current['5'].value,original['5'].value)
                for t,artifact in current.items():
                    if t not in expected:self.assertEqual(json.dumps(plain(artifact),sort_keys=True),json.dumps(plain(original[t]),sort_keys=True))
                    else:self.assertNotEqual(artifact.version,original[t].version)
                    self.assertEqual(artifact.parent_versions,tuple((p,current[p].version) for p in sorted(w.task(t).parents)))

    def test_fixture_B_rational_singletons_and_original_vertex_coverage(self):
        edges=((0,1),(1,2));costs=(F(1,2),F(1,3),F(1,6))
        w=Workflow('review:B',(Task('0'),Task('1',('0',)),Task('2',('1',))),('2',));cs=dict(zip(w.ids,costs))
        rows=raw_rows((0,1,2),2,edges,costs);self.assertEqual(len(rows),3)
        self.assertEqual(sorted(v['sum'] for v in rows),[F(7,6),F(3,2),F(3,2)])
        for obj in ('mean','worst'):
            out=a.solve(w,2,cs,obj);self.assertEqual((out['sum'],out['max']),(F(7,6),1));self.assertEqual(out['virtual_vertices'],1)
            self.assertEqual(sum(len(g)==1 for g in out['groups']),1)
            out=a.solve(w,3,cs,obj);self.assertEqual((out['sum'],out['max']),(F(5,3),1));self.assertEqual(out['virtual_vertices'],3)
            self.assertTrue(all(len(g)==1 for g in out['groups']))
        isolated=Workflow('review:isolated',(Task('x'),Task('y')),('x','y'))
        import networkx as nx
        real=nx.min_weight_matching;graphs=[]
        def observe(g,**kw):graphs.append(g.copy());return real(g,**kw)
        with patch.object(nx,'min_weight_matching',side_effect=observe):
            self.assertEqual(a.solve(isolated,2,{'x':1,'y':2},budget=1)['status'],'infeasible')
        self.assertEqual(set(graphs[0]),set(range(4)));self.assertGreater(graphs[0].number_of_edges(),0)
        self.assertEqual(graphs[0].degree[1],0)

    def test_fixture_C_committed_reconstruction_vs_missing_completion(self):
        w=Workflow('review:C',(Task('a'),Task('b',('a',)),Task('c'),Task('d')),('b','c','d'))
        e=r.Executor();alloc=Allocation(w.key,3,(('a',),('b',),('c','d')),'e','fixture',0)
        clean=r.execute(w,e,0,r.Budget(100));out=r.corrupt_and_restore(w,e,0,r.Budget(100),clean,alloc,('a',),abort_after=2)
        E={v.task for v in out['continuation'].artifacts};D=raw_closure(('a',),(('a','b'),));U=D|(set(w.ids)-E)
        self.assertEqual(E,{'a','b'});self.assertEqual(D,{'a','b'});self.assertEqual(U,set(w.ids))
        self.assertEqual(set(out['reconstruction_tasks']),D&E);self.assertEqual(set(out['completion_tasks']),{'c','d'})
        self.assertEqual(Counter(out['repair'].attempted),Counter(U));self.assertEqual(out['repair'].semantic,'valid')
        self.assertEqual(out['reconstruction_observed_spend'],2);self.assertEqual(out['completion_observed_spend'],2)
        self.assertEqual(out['combined_full_cost'],4);self.assertFalse(out['theorem_complete_work_cost_applicable'])
        self.assertTrue(set(out['continuation'].attempted).isdisjoint(out['completion_tasks']))
        self.assertTrue({e['invocation'] for e in out['continuation'].events}.isdisjoint(e['invocation'] for e in out['repair'].events))

    def test_coupled_sham_rng_is_not_shared_physical_invocation(self):
        w=fixture_a();e=r.Executor('seeded_mock');alloc=Allocation(w.key,3,(("0","2"),("1","3"),("4","5")),"e","fixture",0)
        # Allow the seeded mock's extra synthetic work without changing graph/cost truth.
        w=replace(w,tasks=tuple(replace(t,call_cap=t.synthetic_cost+2) for t in w.tasks))
        alloc=replace(alloc,workflow=w.key);clean=r.execute(w,e,0,r.Budget(1000))
        args=(w,e,0,r.Budget(1000),clean,alloc,alloc.groups[0])
        attack=r.corrupt_and_restore(*args,coupling='declared_common_random_numbers_v1')
        sham=r.corrupt_and_restore(*args,coupling='declared_common_random_numbers_v1',sham=True)
        ae=attack['continuation'].events;se=sham['continuation'].events
        self.assertEqual([x['stream'] for x in ae],[x['stream'] for x in se])
        self.assertTrue({x['invocation'] for x in ae}.isdisjoint(x['invocation'] for x in se))
        self.assertEqual(sham['continuation'].semantic,'valid');self.assertEqual(attack['continuation'].semantic,'invalid')
        self.assertEqual([x['usage'] for x in ae],[x['usage'] for x in se])

    def test_no_second_llm_reply_after_valid_response(self):
        w=Workflow('llm',(Task('a'),Task('b')),('a','b'));good={'groups':[['a'],['b']]}
        out=a.llm_reply(w,2,[good,good]);self.assertEqual(out['status'],'invalid_allocation')
        self.assertEqual(out['attempts'],['valid']);self.assertIsNone(out['groups'])

    def test_malformed_usage_remains_unknown_not_negative_spend(self):
        w=Workflow('usage',(Task('a'),),('a',))
        class Bad(r.MockWorker):
            def invoke(self,*args):return 1,Usage(-1)
        budget=r.Budget(20);out=r.execute(w,r.Executor(),0,budget,worker=Bad())
        self.assertEqual(out.usage,'missing');self.assertEqual(out.observed_spend,0);self.assertIsNone(out.full_cost)
        self.assertTrue(budget.unresolved);self.assertEqual(out.events[-1]['usage'].status,'missing')

    def test_repair_rejects_previous_incident_as_clean_snapshot(self):
        w=fixture_a();e=r.Executor();aa=Allocation(w.key,3,(('0','2'),('1','3'),('4','5')),'e','fixture',0)
        clean=r.execute(w,e,0,r.Budget(1000));previous=r.repair(w,e,0,r.Budget(1000),clean,aa,aa.groups[0])['trace']
        with self.assertRaises(Invalid):r.repair(w,e,0,r.Budget(1000),previous,aa,aa.groups[1])
        with self.assertRaises(Invalid):r.corrupt_and_restore(w,e,0,r.Budget(1000),previous,aa,aa.groups[1])

    def test_incomplete_physical_checkpoint_is_not_reused(self):
        config=template.load(ROOT/'PILOT_MANIFEST_V3.yaml');real=campaign.repair;original=r.Journal.append
        def bad_repair(*args,**kwargs):
            result=real(*args,**kwargs);result['trace']=replace(result['trace'],execution='task_error',schema='invalid',full_cost=None);return result
        with tempfile.TemporaryDirectory() as td:
            def interrupt(j,event):
                original(j,event)
                if event['type']=='logical_outcome':raise KeyboardInterrupt('after failed logical row')
            with patch.object(campaign,'repair',side_effect=bad_repair),patch.object(r.Journal,'append',interrupt):
                with self.assertRaises(KeyboardInterrupt):campaign.demo(td,config)
            with patch.object(campaign,'repair',side_effect=AssertionError('must stop after failed record')):
                out=campaign.demo(td,config)
            failed=[v for v in out['outcomes'] if v['execution']=='task_error']
            self.assertEqual(len(failed),1);self.assertFalse(any(v.get('physical_reuse') for v in out['outcomes']))
            self.assertEqual(len(out['outcomes']),64)


class ReuseIdentity(unittest.TestCase):
    def test_exact_conditions_and_clean_artifacts_bind_physical_reuse(self):
        w=fixture_a();e=r.Executor();alloc=Allocation(w.key,3,(('0','2'),('1','3'),('4','5')),'e','method',0)
        clean=r.execute(w,e,0,r.Budget(1000));g=alloc.groups[0]
        key=campaign.repair_identity('frozen-code-limits',clean,alloc,g,e,0)
        same=replace(alloc,method='another display method')
        self.assertEqual(key,campaign.repair_identity('frozen-code-limits',clean,same,g,e,0))
        changed=replace(clean,artifacts=(replace(clean.artifacts[0],value=99),)+clean.artifacts[1:])
        variants=[('other-code-or-limits',clean,alloc,g,e,0),('frozen-code-limits',changed,alloc,g,e,0),
                  ('frozen-code-limits',clean,alloc,alloc.groups[1],e,0),('frozen-code-limits',clean,alloc,g,replace(e,config='v2'),0),
                  ('frozen-code-limits',clean,alloc,g,e,1)]
        for args in variants:self.assertNotEqual(key,campaign.repair_identity(*args))

    def test_allocation_identity_canonical_and_immutable(self):
        w=fixture_a();one=Allocation(w.key,3,(("0","2"),("1","3"),("4","5")),"e","m",0)
        reordered=Allocation(w.key,3,(("5","4"),("3","1"),("2","0")),"e","m",0)
        self.assertEqual(one.partition,reordered.partition)
        self.assertEqual(one.key,reordered.key)
        with self.assertRaises(Invalid):Allocation(w.key,3,[["0","2"],["1","3"],["4","5"]],"e","m",0)

    def test_dummy_credentials_approvals_cannot_register_live_backend(self):
        with patch.dict('os.environ',{'OPENAI_API_KEY':'FAKE-NOT-A-KEY','PHASE2_BACKEND':'local_model','APPROVED':'true'}):
            for name in ('local_model','api','slurm'):
                with self.assertRaises(Invalid):r.worker_for(r.Executor(name))
            self.assertIsInstance(r.worker_for(r.Executor()),r.MockWorker)

if __name__=='__main__':unittest.main()
