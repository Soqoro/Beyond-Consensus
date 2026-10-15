"""Public structure controls and optional real restricted reference execution."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import organization_sampler as sampler,v2
from reporecourse.common import Rejected,load,digest
from reporecourse.tasks import ROOT,private_task,tool_contract
from reporecourse.qualification import runtime_versions
from reporecourse.track_f_controls import PINS
READY=all(runtime_versions().get(k)==v for k,v in PINS.items())


def public(task):
    # Source documents are NOT fabricated or labelled upstream-loaded. Structural
    # controls can operate on the existing public outline contract without assets.
    return load(ROOT/'rich'/'public'/(task+'.json'))


def fixture(task):
    p=public(task);private=private_task(task)
    if p['family']=='data_product':p['tables']=deepcopy(private['fixtures'][1]['tables'])
    p['sources'].update(request=p['request'],tool_contract=tool_contract(),tables=p['tables'])
    return p,private


class Sampler(unittest.TestCase):
    def test_bounded_deterministic_selection_both_families(self):
        for task in sampler.TASKS:
            a=sampler.sample(task,public(task));b=sampler.sample(task,public(task))
            self.assertEqual(a['candidates'],b['candidates']);self.assertEqual(len(a['selected']),3)
            self.assertEqual(a['candidates_examined'],6);self.assertLessEqual(a['candidates_examined'],a['candidate_limit'])
            self.assertEqual([r['recipe'] for r in a['candidates'] if r['selected']],
                ['separate_obligations','merge_compatible_assignments','share_public_semantic_interface'])
            self.assertEqual(a['candidates'][4]['validity'],'duplicate')
            self.assertEqual(a['candidates'][5]['validity'],'inapplicable')
            self.assertTrue(all(x['qualification']['status']=='not_requested' for x in a['candidates']))
        for cap in (2,13,True):
            with self.assertRaises(Rejected):sampler.sample(sampler.TASKS[0],public(sampler.TASKS[0]),candidate_limit=cap)

    def test_actual_grouping_differs_from_owner_concentration(self):
        for task in sampler.TASKS:
            rows=sampler.sample(task,public(task))['candidates'];ind,group,shared,owners=rows[:4]
            self.assertEqual(len(group['plan']['units']),1)
            self.assertEqual(len(group['plan']['units'][0]['outputs']),len(public(task)['required_outputs']))
            self.assertEqual(len(owners['plan']['units']),len(ind['plan']['units']))
            self.assertEqual(len({u['worker'] for u in owners['plan']['units']}),1)
            self.assertEqual(len({r['canonical_key'] for r in rows[:4]}),4)
            helpers=[u for u in shared['plan']['units'] if not u['outputs']]
            self.assertEqual(len(helpers),1);self.assertTrue(helpers[0]['interfaces'])
            self.assertTrue(any(u['consumes'] for u in shared['plan']['units']))
            with self.assertRaisesRegex(Rejected,'merge_requires_independent_terminals'):
                sampler.merge_independent(shared['plan'],public(task),sampler.configuration())

    def test_canonical_equivalence_keeps_ownership_partition_and_bounds(self):
        plan=sampler.sample(sampler.TASKS[1],public(sampler.TASKS[1]))['candidates'][2]['plan']
        changed=deepcopy(plan);ids={u['id']:'changed'+str(i) for i,u in enumerate(changed['units'])}
        for i,u in enumerate(changed['units']):
            u['id']=ids[u['id']];u['worker']='w'+str((i+1)%7)
            u['depends']=[ids[d] for d in u['depends']]
            for binding in u['consumes'].values():binding['unit']=ids[binding['unit']]
        changed['units'].reverse();changed['id']='different'
        self.assertEqual(sampler.canonical_key(plan),sampler.canonical_key(changed))
        changed['units'][0]['worker']=changed['units'][1]['worker']
        self.assertNotEqual(sampler.canonical_key(plan),sampler.canonical_key(changed))
        with self.assertRaises(Rejected):sampler.canonical_key({'units':plan['units']*5})

    def test_public_plans_no_reference_bodies_and_original_sources_preserved(self):
        for task in sampler.TASKS:
            p=public(task);p['sources']={'request':p['request'],'original_contract':'available source text'}
            with patch('reporecourse.organization_sampler.private_task',side_effect=AssertionError('private read during construction')):
                rows=sampler.sample(task,p)['candidates']
            for row in rows:
                if row['plan'] is None:continue
                for unit in row['plan']['units']:
                    self.assertEqual(set(unit['sources']),set(p['sources']))
                    self.assertEqual(set(unit['terminal_bindings']),set(unit['outputs']))
                serialized=json.dumps(row['plan'])
                for key in ('"content"','"fixtures"','"witnesses"','"expected"'):
                    self.assertNotIn(key,serialized)

    def test_missing_sources_remain_blocked_even_with_qualification_requested(self):
        with tempfile.TemporaryDirectory() as sources:
            report=sampler.qualify_catalog(sources,qualify=True)
        self.assertEqual(report['status'],'blocked_prerequisite');self.assertFalse(report['model_executed'])
        self.assertFalse(report['task_execution_allowed'])
        self.assertEqual(report['catalog_id'],digest({k:v for k,v in report.items() if k!='catalog_id'}))
        for row in report['tasks']:
            self.assertFalse(row['source_available']);self.assertEqual(row['qualified_plans'],0)
            self.assertEqual(row['split'],'development');self.assertEqual(len(row['selected']),3)
            self.assertTrue(all(c['qualification']['status']=='blocked_prerequisite' for c in row['candidates'] if c['selected']))

    def test_dependencies_missing_do_not_certify_references(self):
        p=public(sampler.TASKS[0]);candidate=sampler.sample(p['id'],p)['candidates'][0]
        with patch('reporecourse.qualification.runtime_versions',return_value={}):
            q=sampler.qualify_plan(p,{},candidate,sampler.configuration())
        self.assertEqual(q['status'],'blocked_prerequisite')

    def test_qualification_exception_retained_without_replacement(self):
        p=public(sampler.TASKS[0]);candidate=sampler.sample(p['id'],p)['candidates'][0]
        with patch('reporecourse.organization_sampler._qualify_plan',side_effect=RuntimeError('private value')):
            q=sampler.qualify_plan(p,{},candidate,sampler.configuration())
        self.assertEqual(q['status'],'failed');self.assertEqual(q['error_type'],'RuntimeError')
        self.assertNotIn('private value',json.dumps(q));self.assertIn('offline_process_cpu_seconds',q)
        self.assertEqual(q['private_task_hash'],digest({}))

    def test_supported_pools_and_bad_terminals_rejected(self):
        for pool in range(2,9):
            for task in sampler.TASKS:
                p=public(task);result=sampler.sample(task,p,pool)
                for row in result['candidates']:
                    if row['plan'] is not None:v2.validate_work_plan(row['plan'],p,result['config'])
        p=public(sampler.TASKS[0]);c=sampler.configuration();plan=sampler.public_seed(p,c,'independent')
        plan['units'][0]['outputs']=[]
        with self.assertRaises(Rejected):v2.validate_work_plan(plan,p,c)

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_all_six_references_and_semantic_controls_use_actual_bundle_scorer(self):
        for task in sampler.TASKS:
            p,private=fixture(task);report=sampler.sample(task,p)
            for row in report['candidates']:
                if not row['selected']:continue
                q=sampler.qualify_plan(p,private,row,report['config'])
                self.assertEqual(q['status'],'cpu_qualified_reference',(task,row['recipe'],q))
                self.assertTrue(q['evaluation']['success']);self.assertTrue(q['reset_repeat_identical'])
                self.assertTrue(all(x['detected'] for x in q['negative_controls']))
                if row['recipe']=='share_public_semantic_interface':self.assertGreater(q['executable_binding_edges'],0)
                else:self.assertEqual(q['executable_binding_edges'],0)

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_actual_shared_fault_recovery_keeps_loss_and_conformance(self):
        from reporecourse.engine import Engine,ScriptedWorker
        from reporecourse.evaluator import evaluate
        for task in sampler.TASKS:
            p,private=fixture(task);report=sampler.sample(task,p);candidate=report['candidates'][2]
            engine=Engine(p,ScriptedWorker(sampler.reference_witness(candidate,private)),plan=candidate['plan'],
                v2=report['config'],track='F',target='w0')
            try:run=engine.run();grade=evaluate(p,private,run['state'])
            finally:engine.env.close()
            self.assertTrue(grade['success']);self.assertTrue(run['intervention_triggered'])
            self.assertTrue(run['conformance']['contract_conformant'])
            lost=next(i for i,e in enumerate(run['events']) if e['type']=='unavailable')
            self.assertFalse(any(e.get('worker')=='w0' and e['type']=='publish' for e in run['events'][lost+1:]))

if __name__=='__main__':unittest.main()
