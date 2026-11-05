"""Bounded offline checks for exactly two methods; no real transport or CP-SAT run."""
import csv,json,tempfile,unittest
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import composite_joint as j, composite_joint_launch as launch, composite_math as base
from bc_phase2.joint_core import compile_organisation,evaluate
from bc_phase2.joint_oracle import assess
from bc_phase2.joint_constraints import build,input_bits,decode_solution
from bc_phase2.model import Invalid

class Fake:
 binding={'evidence':'synthetic_mock'}
 def __init__(self,fault=None):self.calls=[];self.fault=fault
 def render(self,req):return dict(input_tokens=70,input_ids=[1]*70,payload=req['payload'])
 def generate(self,r):
  p=r['payload'];i=len(self.calls);self.calls.append(deepcopy(p));t=j.base.TASKS[int(p['task_id'][1:])]
  value=json.dumps({f:f'Synthetic incorrect mathematics from call {i}' for f in t['fields']})
  result=dict(input_tokens=70,output_tokens=20 if j.ALGEBRAIC in p['responsibility'] else 60,finish_reason='eos',final_text=value,boundary_error=None)
  result.update(self.fault(i) or {} if self.fault else {});return result

def retained(d,**kw):return dict(status='MOCK_RETAINED',candidate=kw['seed'],model_executed=False)
def tiny(d,**kw):
 candidates=[]
 for a in j.A_OPTIONS:
  for pair in combinations(range(5),2):
   groups=[list(pair)]+[[i] for i in range(5) if i not in pair]
   own={f't{i}':f'o{o}' for o,g in enumerate(groups) for i in g};s=j.selection(d,a,own)
   candidates.append((evaluate(compile_organisation(d,s))['objective_pair'],s))
 return dict(status='MOCK_TINY_ORACLE',candidate=min(candidates,key=lambda r:r[0])[1])

class JointRecipe(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.sources={s:'Synthetic original only' for s in base.IDS}
 def run_mock(self,solver=tiny,fault=None):
  fake=Fake(fault);journal=j.Journal(self.root/'journal',fake,'mock',lambda:None)
  return j.run_recipe(journal,self.sources,self.root,solver),journal,fake
 def test_domain_modes_and_neutral_preservation(self):
  b=j.blueprint();self.assertEqual(b['ownership'],base.blueprint()['ownership']);self.assertEqual(b['tasks'],base.TASKS)
  self.assertEqual(b['prompt'],base.PROMPT);self.assertEqual(b['methods'],['NEUTRAL','JOINT'])
  self.assertEqual(len(j.coverage()),7);self.assertEqual(len({r['key'] for r in j.coverage()}),7)
  d=j.domain();self.assertEqual(d['budgets'],{'initial':None,'incident':None})
  for a in j.A_OPTIONS:
   ex=compile_organisation(d,j.selection(d,a));self.assertEqual(ex.outputs,(('q0','e1'),('q1','e4')))
   self.assertEqual(ex.edges,(('e0','e1'),('e2','e3'),('e3','e4')))
  self.assertEqual(b['profiling_call_cap']+10*b['Lmax'],57)
 def test_price_coverage_and_incompatible_mode_rejection(self):
  prices={r['id']:i+2 for i,r in enumerate(j.coverage())};d=j.domain(prices)
  original=compile_organisation(d,j.selection(d));alt=compile_organisation(d,j.selection(d,'algebraic'))
  self.assertNotEqual(original.operations[1].replay,alt.operations[1].replay)
  bad=j.selection(d);bad['modes']['e1']='algebraic'
  with self.assertRaises(Invalid):compile_organisation(d,bad)
  with self.assertRaises(Invalid):j.domain({k:v for k,v in prices.items() if k!='e1.algebraic'})
  bad=j.selection(d);bad['C']={'relay':'yes'}
  with self.assertRaises(Invalid):compile_organisation(d,bad)
 def test_twenty_tiny_candidates_independent_oracle_and_circuit(self):
  d=j.domain({r['id']:i+2 for i,r in enumerate(j.coverage())});encoded=build(d)
  for a in j.A_OPTIONS:
   for pair in combinations(range(5),2):
    groups=[list(pair)]+[[i] for i in range(5) if i not in pair]
    own={f't{i}':f'o{o}' for o,g in enumerate(groups) for i in g};s=j.selection(d,a,own)
    _,reference=assess(d,s['A'],s['C'],own)
    score=evaluate(compile_organisation(d,s));bits=input_bits(encoded,s['A'],s['C'],own);ok,values=encoded['circuit'].evaluate(bits)
    self.assertTrue(ok);_,decoded=decode_solution(encoded,values)
    self.assertEqual(score['objective_pair'],decoded['objective_pair'])
    self.assertEqual(score['objective_pair'],reference['objective_pair'])
 def test_complete_two_distinct_designs_and_fresh_parent_versions(self):
  r,journal,fake=self.run_mock();self.assertEqual(set(r['methods']),set(j.METHODS));self.assertFalse(r['shared_observations'])
  self.assertEqual(r['designs']['methods']['JOINT']['A'],{'proof':'algebraic'})
  self.assertEqual(journal.snapshot()['totals']['calls'],len(fake.calls));self.assertLessEqual(len(fake.calls),57)
  self.assertEqual(len(r['prices']['observations']),7)
  for m,row in r['methods'].items():
   self.assertEqual(len(row['repairs']),4);self.assertTrue(row['full_cost_coverage'])
   self.assertEqual(row['question_quality'],'unknown');self.assertIsNone(row['quality_preserving_saving'])
   for rep in row['repairs']:
    for e,artifact in rep['store'].items():
     if e in rep['revoked']:self.assertIn(artifact['invocation'],rep['invocations'])
     else:self.assertEqual(artifact,row['clean']['store'][e])
  for p in fake.calls[7:]:self.assertNotIn('from call 0',json.dumps(p))
  self.assertEqual(len(list(csv.DictReader((self.root/'NEUTRAL_VS_JOINT_RESULTS.csv').read_text().splitlines()))),2)
 def test_identical_full_design_shares_only_one_sweep(self):
  r,_,_=self.run_mock(retained);self.assertTrue(r['shared_observations'])
  self.assertEqual(r['methods']['JOINT']['shared_with'],'NEUTRAL')
  self.assertTrue(all(x['slot'].startswith('NEUTRAL/') for x in r['methods']['JOINT']['repairs']))
 def test_equal_prompts_and_scores_do_not_share_distinct_ownership(self):
  def swapped(d,**kw):
   s=deepcopy(kw['seed']);s['ownership']={t:'o'+str((int(o[1:])+1)%4) for t,o in s['ownership'].items()}
   return dict(status='MOCK_LABEL_SWAP',candidate=s)
  r,_,_=self.run_mock(swapped);self.assertFalse(r['shared_observations'])
  self.assertEqual(len(r['methods']['JOINT']['repairs']),4)
 def test_incomplete_profile_never_selects_or_changes_domain(self):
  with patch.object(j,'checked_candidate',side_effect=AssertionError('must not select')):
   r,journal,_=self.run_mock(fault=lambda i:dict(final_text='bad') if i==5 else {})
  self.assertEqual(r['status'],'profile_coverage_failed');self.assertEqual(journal.snapshot()['totals']['calls'],6)
  self.assertFalse((self.root/'prices.frozen.json').exists());self.assertTrue(all(x['status']=='unrun' for x in r['methods'].values()))
 def test_bad_clean_does_not_cancel_other_method(self):
  r,_,_=self.run_mock(fault=lambda i:dict(final_text='bad') if i==7 else {})
  self.assertTrue(all(x['status']=='no_clean_snapshot' for x in r['methods']['NEUTRAL']['repairs']))
  self.assertTrue(r['methods']['JOINT']['full_cost_coverage']);self.assertIsNone(r['recovery_token_reduction'])
 def test_bad_repair_preserved_independent_incidents_continue(self):
  r,_,_=self.run_mock(fault=lambda i:dict(final_text='bad',finish_reason='length_limit',output_tokens=3072) if i==17 else {})
  self.assertFalse(r['methods']['NEUTRAL']['repairs'][0]['complete'])
  self.assertTrue(r['methods']['NEUTRAL']['repairs'][1]['complete']);self.assertIsNone(r['methods']['NEUTRAL']['replay_mean'])
 def test_unknown_usage_halts_and_preserves_reservation(self):
  fake=Fake(lambda i:dict(output_tokens=None));journal=j.Journal(self.root/'j',fake,'scope',lambda:None)
  with self.assertRaises(base.Halt):j.run_recipe(journal,self.sources,self.root,retained)
  self.assertEqual(len(fake.calls),1);self.assertEqual(journal.snapshot()['totals']['reserved_tokens'],3142)
  self.assertEqual(json.loads((self.root/'result.json').read_text())['status'],'halted')
 def test_freeze_before_one_joint_solver_call_and_evaluation(self):
  seen=[]
  def solver(d,**kw):
   seen.append(d);self.assertTrue((self.root/'prices.frozen.json').exists());self.assertNotIn('Synthetic incorrect',json.dumps(d))
   self.assertEqual(kw['seconds'],10);self.assertNotIn('partial',kw);return tiny(d,**kw)
  self.run_mock(solver);self.assertEqual(len(seen),1)
 def test_source_integrity_and_budget_before_dispatch(self):
  fake=Fake();journal=j.Journal(self.root/'j',fake,'scope',lambda:None);journal.limits['token_cap']=1
  req=base.request(base.TASKS[0],self.sources,{})
  with self.assertRaises(base.Halt):journal.invoke(req,'x','e0')
  journal.limits['token_cap']=9999;journal.check_source=lambda:(_ for _ in ()).throw(Invalid('changed source'))
  with self.assertRaises(Invalid):journal.invoke(req,'x','e0')
  self.assertEqual(fake.calls,[])
 def test_certificate_mismatch_rejected(self):
  d=j.domain();seed=j.selection(d)
  for certificate in (dict(candidate=seed,score={}),dict(candidate=seed,lower='999999'),dict(candidate=seed,lexicographic_certified=True,primary_certified=False)):
   with self.assertRaises(Invalid):j.checked_candidate(d,certificate,seed)
 def test_old_or_absent_approval_cannot_load_model(self):
  with patch.object(launch.base,'deployment',side_effect=AssertionError('no deployment reached')):
   with self.assertRaises((Invalid,KeyError)):launch.open_transport({'schema':'composite-r0-release-v1'})
  with patch.object(launch,'validate_manifest',return_value={}):
   m=dict(scope_digest='new',blockers=[])
   old=dict(schema='composite-r0-approval-v1',scope_digest='new',decision='approved',reviewer='mock',reviewed_at='mock',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
   with self.assertRaises(Invalid):launch.approve(m,old)
   old['schema']='composite-joint-approval-v1';v=launch.approve(m,old);self.assertEqual(launch.validate_release(v),{})
   old['scope_digest']='other'
   with self.assertRaises(Invalid):launch.approve(m,old)
 def test_shared_launcher_dispatch_uses_new_recipe_and_caps(self):
  fake=Fake()
  with patch.object(launch,'validate_release',return_value={'bound':'synthetic'}),patch.object(launch,'source_records',return_value=self.sources),patch.object(launch,'open_transport',return_value=fake),patch('bc_phase2.joint_solver.solve',side_effect=retained):
   r=launch.dispatch({},self.root/'allocated')
  self.assertEqual(r['condition'],j.CONDITION);self.assertEqual(set(r['methods']),set(j.METHODS))
  self.assertEqual(r['totals']['calls'],21)  # seven profile + five clean + nine owner-replay calls
  ledger=json.loads((self.root/'allocated/journal/ledger.json').read_text())
  self.assertEqual(ledger['state']['binding']['condition'],j.CONDITION)
 def test_dry_run_routes_to_new_batch_without_submission(self):
  cfg=dict(partition='NA100q',time='04:00:00',memory_gb=128,python='/env/bin/python',storage_root='/dataset',cache_root='/dataset/cache',snapshot_root='/dataset/snapshots',output_root=str(self.root/'outputs'))
  scope={'cluster':cfg};release={'manifest':{'scope_digest':'synthetic'},'release_digest':'synthetic'}
  with patch.object(launch,'validate_release',return_value=scope),patch.object(launch,'source_records',return_value=self.sources),patch.object(launch.base.cluster,'registry_root',return_value=self.root/'registry'),patch.object(launch.base.cluster,'guard'),patch.object(launch.base.cluster,'validate_site'),patch.object(launch.base.cluster,'command',side_effect=AssertionError('no submission command')):
   result=launch.submit(self.root,release,dry_run=True)
  self.assertFalse(result['submitted']);self.assertTrue(result['argv'][-4].endswith('run_composite_joint.sbatch'))
  self.assertIn('--gres=gpu:1',result['argv']);self.assertIn('--cpus-per-task=4',result['argv'])
if __name__=='__main__':unittest.main()
