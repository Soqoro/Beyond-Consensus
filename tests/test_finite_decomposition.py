"""Constructed plans and scripted workers; never a measured model advantage."""
from copy import deepcopy
from dataclasses import replace
import json
import tempfile
from pathlib import Path
import unittest
from tests.support import ROOT
from tests.test_sqlite_compatibility import controls
from beyond_consensus.config import RunConfig
from beyond_consensus.tasks.sqlite_compatibility import tasks
from beyond_consensus.planning.decomposition import inspect, validate, select, affected, generation_prompt
from beyond_consensus.schemas import WORKERS
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.models.base import Generation
from beyond_consensus.util import canonical, BCError, read_json


def fixture():
    base = tasks()[0]
    contracts = {name:deepcopy(base.sources[base.id]) for name in ('report_a','report_b')}
    task = replace(base,id='synthetic-two-reports',sources=contracts,required_outputs=tuple(contracts),
                   metadata={**base.metadata,'synthetic_two_reports':True})
    task.metadata.pop('diagnostic_mode',None)
    def unit(name,owner,inputs=(),intermediate=False):
        contract = (dict(kind='view',name='shared_totals',requirement='Produce a view of totals and counts grouped by department_id from entries.',
                        output_columns=['department_id','total_amount','entry_count']) if intermediate else contracts[name])
        return dict(id=name,owner=owner,inputs=list(inputs),contract=contract,terminal=not intermediate,
                    read_sources=list(contracts),message_recipients=list(WORKERS))
    independent = dict(id='independent',terminal_requirements=list(contracts),
                       units=[unit('report_a','w0'),unit('report_b','w1')],schedule=list(contracts))
    shared = dict(id='shared',terminal_requirements=list(contracts),units=[unit('totals','w0',intermediate=True),
                 unit('report_a','w1',['totals']),unit('report_b','w2',['totals'])],schedule=['totals',*contracts])
    return task,[independent,shared]


class GraphWorker(MockBackend):
    def generate(self,messages,max_new_tokens,seed):
        obs=[json.loads(m['content']) for m in messages if m['role']=='user']
        assignment=next(o for o in reversed(obs) if 'assignment' in o)
        name=assignment['assignment']
        # Persistent worker histories may contain prior completed units.
        start=max(i for i,o in enumerate(obs) if 'assignment' in o)
        current=obs[start:]
        created=next((o for o in reversed(current) if 'artifact_id' in o),None)
        if created:
            action=dict(tool='submit_required_artifact',artifact_id=created['artifact_id'])
        elif not any(o.get('tool')=='read_source' for o in current):
            action=dict(tool='read_source',name=name)
        else:
            published=[o for o in current if o.get('tool')=='read_artifact' and o.get('result',{}).get('kind')=='view']
            if published:
                view=published[-1]
                tree={'columns':[{'expr':{'column':c}} for c in ('department_id','total_amount','entry_count')],
                      'from':{'table':'shared_totals'},'order_by':[{'expr':{'column':'department_id'}}]}
                action=dict(tool='run_read_query',select_sql=tree,permitted_artifact_versions={'shared_totals':view['version']})
            else:
                action=dict(tool='submit_view_definition' if name=='totals' else 'run_read_query',
                            select_sql=controls()['aggregate'],permitted_artifact_versions={})
                if name=='totals': action['artifact_name']='shared_totals'
        text=canonical(action)
        return Generation(text,(len(text)+3)//4)


class FiniteTests(unittest.TestCase):
    def test_variation_privacy_and_solver(self):
        task,plans=fixture()
        self.assertEqual(inspect(plans,task)['effective_unique_plans'],2)
        renamed=deepcopy(plans[0]);renamed['id']='renamed';renamed['units'][0]['owner']='w3'
        self.assertEqual(inspect([plans[0],renamed],task)['status'],'insufficient_decomposition_variation')
        bad=deepcopy(plans[1]);bad['units'][0]['inputs']=['report_b']
        with self.assertRaises(BCError): validate(bad,task)
        hidden=replace(task,metadata={**task.metadata,'evaluation':{'secret':'NEVER_EXPORT'},'harness':{'secret':'NEVER_EXPORT'}})
        self.assertNotIn('NEVER_EXPORT',generation_prompt(hidden))
        def costs(a,b):
            return {p['id']:dict(generation=2,selection=8,checking=3,integration=3,primary={u['id']:cost for u in p['units']},
                    repair={u['id']:cost for u in p['units']},quality_eligible=True) for p,cost in zip(plans,(a,b))}
        for a,b in [(10,100),(100,10),(20,20)]:
            c=costs(a,b)
            for mode in ('nominal','recovery'):
                r=select(plans,task,c,mode,10000,100,{'status':'constructed_engineering_only'},engineering=True)
                brute=min(r['evaluations'],key=lambda e:(e['clean'] if mode=='nominal' else e['objective'],e['id']))
                self.assertEqual(r['selected'],brute['id'])
        self.assertEqual(select(plans,task,costs(10,100),'recovery',10000,100,{'status':'constructed_engineering_only'},engineering=True)['selected'],'independent')
        with self.assertRaises(BCError): select(plans,task,{},'nominal',100,0,{},engineering=True)
        with self.assertRaises(BCError): select(plans,task,costs(10,10),'recovery',10000,0,{},engineering=False)
        split=deepcopy(plans[1]);split['units'][2]['owner']='w0'
        self.assertEqual(affected(split,'w0'),{'totals','report_a','report_b'})
        self.assertEqual(affected(plans[0],'w0',[('report_a','report_b')]),{'report_a','report_b'})

    def test_actual_engine_graph_and_common_repair_resume(self):
        task,plans=fixture()
        config=RunConfig(task_kind='sqlite_fixture',policies=('jit',),attacks=('clean','withholding'),
                         max_actions=6,monitor_id='data-structure-v1')
        with tempfile.TemporaryDirectory() as tmp:
            for p in plans:
                rows={candidate['id']:dict(generation=0,selection=8,checking=10,integration=30,
                    primary={u['id']:10 if candidate['id']==p['id'] else 1000 for u in candidate['units']},
                    repair={u['id']:10 for u in candidate['units']},quality_eligible=True) for candidate in plans}
                frozen=replace(task,metadata={**task.metadata,'finite_catalogue':{
                    'candidates':plans,'costs':rows,'selector':'nominal',
                    'provenance':{'status':'constructed_engineering_only'}}})
                manifest=build_manifest(config,ROOT,[frozen])
                out=Path(tmp)/p['id']
                results=run_manifest(manifest,out,ROOT,backend=GraphWorker())
                self.assertTrue(all(r['success'] for r in results),[(r['status'],r['error']) for r in results])
                self.assertEqual(results,run_manifest(manifest,out,ROOT,backend=GraphWorker()))
                checkpoint=read_json(out/'episodes'/manifest['episodes'][0]['episode_id']/'checkpoint.json')
                # Journal checkpoints contain the actual ordered selected graph.
                state=checkpoint.get('state',checkpoint)
                self.assertEqual([u['id'] for u in state['plan']['units']],p['schedule'])
                self.assertEqual(state['plan']['preparation'],[])

    def test_bounded_generation_and_identity_provenance(self):
        from beyond_consensus.planning.decomposition import generate_candidates, dependency_report
        from beyond_consensus.runtime.budget import BudgetLedger
        from beyond_consensus.runtime.provenance import ProvenanceStore
        task,plans=fixture()
        compact=deepcopy(plans)
        for p in compact:
            for u in p['units']:
                if u['terminal']:u['contract']={'source_contract':u['id']}
        class Planner(MockBackend):
            calls=0
            def generate(self,messages,max_new_tokens,seed):
                self.calls+=1
                assert 'evaluation' not in messages[0]['content']
                text=canonical({'tool':'message','recipient':'w0','text':canonical(compact)})
                return Generation(text,(len(text)+3)//4)
        config=RunConfig(model=replace(RunConfig().model,max_new_tokens=2048))
        backend=Planner();ledger=BudgetLedger(config.budget.total,config.budget)
        with self.assertRaises(BCError):generate_candidates(backend,task,config,ledger,0)
        self.assertEqual(backend.calls,0)
        result=generate_candidates(backend,task,config,ledger,0,user_authorized=True)
        self.assertEqual(result['inspection']['effective_unique_plans'],2)
        self.assertEqual(backend.calls,1)
        self.assertFalse(result['message_delivered'])
        self.assertGreater(ledger.spent,0);self.assertFalse(ledger.reservations)
        store=ProvenanceStore()
        first=store.submit('w0','report_a',{})
        store.message('w0','w1','public message')
        second=store.submit('w1','report_b',{})
        report=dependency_report(plans[0],store)
        self.assertIn(('report_a','report_b'),report['undeclared_observed_edges'])
        store.reset('w0')
        third=store.submit('w0','report_a',{})
        invalid=store.invalidate(set(),{'w0'})
        self.assertTrue({first.id,second.id,third.id}<=invalid)
