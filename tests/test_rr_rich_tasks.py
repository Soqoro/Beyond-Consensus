"""Authored richer requests: actual trusted child execution on labelled fixtures."""
import unittest
from pathlib import Path
from copy import deepcopy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import rich_tasks,v2
from reporecourse.tasks import ROOT,catalog,private_task,tool_contract
from reporecourse.common import load,digest
from reporecourse.engine import Engine,ScriptedWorker
from reporecourse.evaluator import evaluate
from reporecourse.qualification import runtime_versions
from reporecourse.track_f_controls import PINS
READY=all(runtime_versions().get(k)==v for k,v in PINS.items())


def inputs(task):
    # Benchmark-authored alternate data. Never labelled upstream source results.
    p=load(ROOT/'rich'/'public'/(task+'.json'));private=private_task(task)
    if p['family']=='data_product':p['tables']=deepcopy(private['fixtures'][1]['tables'])
    p['sources'].update(request=p['request'],tool_contract=tool_contract(),tables=p['tables'])
    return p,private


def run(p,pr,witness,track='clean',target=None):
    c=v2.configuration(7,planning_lane='authored_diagnostic',execution_contract='plan_scoped_v1',planner_output_cap=6144)
    plan=v2.authored_plan(p,c,witness['organization'])
    e=Engine(p,ScriptedWorker(witness),plan=plan,v2=c,track=track,target=target)
    try:
        r=e.run();r['evaluation']=evaluate(p,pr,r['state']);return r
    finally:e.env.close()


class Cards(unittest.TestCase):
    def test_inventory_three_plus_blocked_fourth(self):
        cards=catalog(ROOT/'rich')['tasks'];self.assertEqual(len(cards),3)
        self.assertEqual(len({c['source_group'] for c in cards}),3)
        b=load(ROOT/'rich'/'blocked-api-integration.json')
        self.assertFalse(b['cpu_qualified']);self.assertEqual(b['source_group'],cards[-1]['source_group'])
        self.assertTrue(all(c['independent_review']=='pending' for c in cards))

    def test_independent_expectations_and_cross_output_mutants(self):
        for task in ('jaffle-payment-release','energy-single-indicator-release'):
            p,pr=inputs(task);expected=rich_tasks.expected(pr['oracle'],p['tables'])
            self.assertTrue(rich_tasks.consistent(pr['composition_kind'],expected))
            key='customer_summary' if pr['oracle']=='rich_jaffle' else 'window_summary'
            bad=deepcopy(expected);bad[key][0][-1]+=1
            self.assertFalse(rich_tasks.consistent(pr['composition_kind'],bad))

    def test_public_planner_never_gets_witnesses(self):
        for card in catalog(ROOT/'rich')['tasks']:
            p,_=inputs(card['id']);c=v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1',planner_output_cap=6144)
            req=v2.request(p,c)
            self.assertNotIn('outlines',req['planner_input']);self.assertNotIn('witnesses',req['planner_input'])
            self.assertEqual(req['task_metadata']['source_group'],card['source_group'])
            self.assertEqual(len(p['required_outputs']),4 if card['family']=='api_schema' or card['pack']=='jaffle' else 5)

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_both_families_two_real_reference_paths_and_reset(self):
        for card in catalog(ROOT/'rich')['tasks']:
            p,pr=inputs(card['id']);before=digest(p);grades=[]
            for witness in pr['witnesses']:
                r=run(p,pr,witness);self.assertEqual(r['status'],'completed',(card['id'],r['failures']))
                self.assertTrue(r['evaluation']['success'],(card['id'],witness['organization'],r['evaluation']))
                self.assertTrue(r['conformance']['contract_conformant']);grades.append(r['evaluation']['obligations'])
            self.assertEqual(grades[0],grades[1]);self.assertEqual(before,digest(p))
            self.assertEqual(run(p,pr,pr['witnesses'][0])['evaluation']['obligations'],grades[0])

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_actual_schema_both_extreme_mutants_fail(self):
        p,pr=inputs('github-topics-client-package')
        for value in (True,False):
            w=deepcopy(pr['witnesses'][0]);w['actions'][0]['action']['content']=value
            r=run(p,pr,w);self.assertFalse(r['evaluation']['success']);self.assertTrue(r['state']['bound'])

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_fault_persistent_loss_and_originals_not_starved(self):
        p,pr=inputs('jaffle-payment-release');w=pr['witnesses'][1]
        for target in ('w0','w2'):
            r=run(p,pr,w,'F',target)
            self.assertTrue(r['intervention_triggered']);self.assertTrue(r['evaluation']['success'])
            loss=next(i for i,e in enumerate(r['events']) if e['type']=='unavailable')
            self.assertFalse(any(e.get('worker')==target and e['type']=='publish' for e in r['events'][loss+1:]))
            self.assertTrue(r['conformance']['contract_conformant'])

    @unittest.skipUnless(READY,'Pinned SQLGlot/jsonschema/referencing CPU dependencies')
    def test_missing_output_not_rescued_and_changed_source_rejected(self):
        from reporecourse.tasks import load_task
        from reporecourse.common import Rejected
        p,pr=inputs('jaffle-payment-release');r=run(p,pr,pr['witnesses'][0])
        for key in list(r['state']['bound']):
            s=deepcopy(r['state']);s['bound'].pop(key)
            self.assertFalse(evaluate(p,pr,s)['success'])
        with self.assertRaises(Rejected):load_task('jaffle-payment-release','/missing')


if __name__=='__main__':unittest.main()
