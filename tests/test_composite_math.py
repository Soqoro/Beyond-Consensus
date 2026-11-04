"""Bounded synthetic integration; no real benchmark answers or model execution."""
import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from bc_phase2 import composite_math as c,composite_math_launch as launch
from bc_phase2.joint_core import compile_organisation,evaluate
from bc_phase2.joint_pipeline_runtime import recover
from bc_phase2.model import Invalid

class Fake:
 binding={'evidence':'synthetic_mock'}
 def __init__(self,fault=None):self.calls=[];self.fault=fault
 def render(self,r):return dict(input_tokens=70,input_ids=[1]*70,payload=r['payload'])
 def generate(self,r):
  i=len(self.calls);self.calls.append(deepcopy(r['payload']));task=c.TASKS[int(r['payload']['task_id'][1:])]
  text=json.dumps({f:f'synthetic-{i}-{f}' for f in task['fields']})
  result=dict(input_tokens=70,output_tokens=20+int(task['id'][1:]),finish_reason='eos',final_text=text,boundary_error=None)
  if self.fault:result.update(self.fault(i) or {})
  return result

def retained(d,**kw):return dict(status='MOCK_RETAINED',candidate=kw['seed'],cpu_seconds=0,wall_seconds=0)

def better(d,**kw):
 # Tiny exhaustive arithmetic only in tests; not a production selector fallback.
 import itertools
 best=kw['seed'];score=evaluate(compile_organisation(d,best))['objective_pair']
 for owners in itertools.product(range(4),repeat=5):
  try:
   candidate=c.selection(d,{f't{i}':f'o{o}' for i,o in enumerate(owners)})
   value=evaluate(compile_organisation(d,candidate))['objective_pair']
   if value<score:score=value;best=candidate
  except Invalid:pass
 return dict(status='MOCK_TINY_ARITHMETIC',candidate=best,cpu_seconds=0,wall_seconds=0)

class CompositeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.sources={s:'Synthetic original statement; no gold.' for s in c.IDS}
 def journal(self,fake=None):return c.Journal(self.root/'journal',fake or Fake(),'mock-scope',lambda:None)
 def test_compile_outputs_capacity_and_fixed_edges(self):
  b=c.blueprint();d=c.domain();ex=compile_organisation(d,c.selection(d,b['ownership']))
  self.assertEqual(ex.outputs,(('q0','e1'),('q1','e4')));self.assertEqual(ex.edges,(('e0','e1'),('e2','e3'),('e3','e4')))
  self.assertEqual(sorted(map(lambda x:len(x[1]),ex.groups)),[1,1,1,2])
  bad=deepcopy(b['ownership']);bad['t0']='o9'
  with self.assertRaises(Invalid):compile_organisation(d,c.selection(d,bad))
 def test_identical_design_physical_replays_and_quality_unknown(self):
  fake=Fake();j=self.journal(fake);r=c.run_recipe(j,self.sources,self.root,retained)
  self.assertTrue(r['identical_design']);self.assertEqual(r['methods']['selected']['shared_with'],'neutral')
  neutral=r['methods']['neutral'];costs=[x['full_cost'] for x in neutral['repairs']]
  self.assertEqual(neutral['replay_max'],max(costs));self.assertIsNone(neutral['quality_preserving_saving'])
  self.assertEqual(len(fake.calls),10+sum(len(s) for s in neutral['predicted']['recovery_sets']))
  self.assertLessEqual(len(fake.calls),30)
  for repair in neutral['repairs']:
   for trace in repair['trace']:
    for read in trace['reads']:
     if read['event'] in repair['revoked']:self.assertIn(read['invocation'],repair['invocations'])
  self.assertTrue(all('synthetic-0-' not in json.dumps(x) for x in fake.calls[5:]))
 def test_distinct_organisations_fresh_clean_and_all_owners(self):
  j=self.journal();r=c.run_recipe(j,self.sources,self.root,better)
  self.assertFalse(r['identical_design'])
  for row in r['methods'].values():
   self.assertEqual(len(row['repairs']),4);self.assertTrue(row['full_cost_coverage'])
  calls=j.snapshot()['attempts'];self.assertEqual(len({x['id'] for x in calls}),len(calls))
  self.assertLessEqual(len(calls),55)
 def test_payload_invariance_and_parent_isolation(self):
  j=self.journal();e=c.MathEngine(j,self.sources,self.root);d=c.domain();ex=compile_organisation(d,c.selection(d,c.blueprint()['ownership']))
  row=e.run(ex,'one');a=c.request(c.TASKS[1],self.sources,row['store'])
  self.assertEqual(set(a['payload']['parent_artifacts']),{'t0'})
  self.assertNotIn(c.IDS[1],json.dumps(a));self.assertNotIn('owner',json.dumps(a));self.assertNotIn('method',json.dumps(a))
  changed=deepcopy(c.blueprint()['ownership']);changed={t:'o'+str((int(o[1:])+1)%4) for t,o in changed.items()}
  self.assertEqual(a,c.request(c.TASKS[1],self.sources,row['store']))
  self.assertNotEqual(ex.groups,compile_organisation(d,c.selection(d,changed)).groups)
 def test_bad_profile_stops_without_prices(self):
  j=self.journal(Fake(lambda i:{'final_text':'bad'} if i==0 else {}));r=c.run_recipe(j,self.sources,self.root,retained)
  self.assertEqual(r['status'],'profile_failed');self.assertFalse((self.root/'prices.frozen.json').exists());self.assertEqual(len(j.snapshot()['attempts']),1)
 def test_bad_clean_skips_incidents(self):
  j=self.journal(Fake(lambda i:{'final_text':'bad'} if i==5 else {}));r=c.run_recipe(j,self.sources,self.root,retained)
  rows=r['methods']['neutral']['repairs'];self.assertTrue(all(x['status']=='no_clean_snapshot' for x in rows))
  self.assertIsNone(r['methods']['neutral']['replay_mean'])
 def test_partial_repair_does_not_block_independent_incidents(self):
  j=self.journal(Fake(lambda i:{'output_tokens':3072,'finish_reason':'length_limit','final_text':'bad'} if i==10 else {}))
  r=c.run_recipe(j,self.sources,self.root,retained);rep=r['methods']['neutral']['repairs']
  self.assertFalse(rep[0]['complete']);self.assertTrue(rep[1]['complete']);self.assertIsNone(r['methods']['neutral']['replay_mean'])
 def test_unknown_usage_halts_with_reservation(self):
  j=self.journal(Fake(lambda i:{'output_tokens':None} if i==0 else {}))
  with self.assertRaises(c.Halt):c.run_recipe(j,self.sources,self.root,retained)
  self.assertEqual(j.snapshot()['totals']['reserved_tokens'],3142)
  with self.assertRaises(c.Halt):j.invoke(c.request(c.TASKS[0],self.sources,{}),'other','e0')
 def test_no_profile_or_repair_snapshot_as_original(self):
  j=self.journal();e=c.MathEngine(j,self.sources,self.root);d=c.domain();ex=compile_organisation(d,c.selection(d,c.blueprint()['ownership']))
  profile=e.run(ex,'profile',phase='profile')
  with self.assertRaises(Invalid):recover(e,ex,profile,'o0','repair',None)
  clean=e.run(ex,'clean');repair=recover(e,ex,clean,'o0','r0',None)
  with self.assertRaises(Invalid):recover(e,ex,repair,'o1','r1',None)
 def test_external_approval_and_no_model_loading(self):
  with patch.object(launch,'deployment',side_effect=AssertionError('must not reach deployment')):
   with self.assertRaises((Invalid,KeyError)):launch.open_transport({'schema':'old-screen-approval'})
 def test_prices_frozen_and_content_excluded_from_solver(self):
  j=self.journal()
  def spy(d,**kw):
   self.assertTrue((self.root/'prices.frozen.json').exists());self.assertNotIn('synthetic-',json.dumps(d))
   self.assertEqual([e['modes'][0]['replay'] for e in d['events']],['90','91','92','93','94'])
   return retained(d,**kw)
  c.run_recipe(j,self.sources,self.root,spy)
 def test_scope_cap_and_source_check_before_dispatch(self):
  f=Fake();j=self.journal(f);j.check_source=lambda:(_ for _ in ()).throw(Invalid('source changed'))
  with self.assertRaises(Invalid):j.invoke(c.request(c.TASKS[0],self.sources,{}),'x','e0')
  self.assertEqual(f.calls,[])
  self.assertEqual(c.blueprint()['limits']['maximum_calls'],55);self.assertEqual(c.blueprint()['limits']['token_cap'],55*16384)

if __name__=='__main__':unittest.main()

class GuardTests(unittest.TestCase):
 def test_prior_screen_approval_not_worker_approval(self):
  m={'scope_digest':'x','blockers':[]}
  old={'schema':'D1-math500-screen-v1-approval','decision':'approved','scope_digest':'x'}
  with patch.object(launch,'validate_manifest',return_value={}):
   with self.assertRaises(Invalid):launch.approve(m,old)
 def test_approval_nonrecursive_and_exact(self):
  m={'scope_digest':'x','blockers':[]}
  a=dict(schema='composite-r0-approval-v1',scope_digest='x',decision='approved',reviewer='synthetic',reviewed_at='synthetic',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
  with patch.object(launch,'validate_manifest',return_value={}):
   r=launch.approve(m,a);self.assertEqual(launch.validate_release(r),{})
   bad=deepcopy(r);bad['approval']['scope_digest']='y'
   with self.assertRaises(Invalid):launch.validate_release(bad)
   a['manifest']=m
   with self.assertRaises(Invalid):launch.approve(m,a)
 def test_known_overflow_vs_integrity(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fake();j=c.Journal(Path(tmp)/'j',f,'scope',lambda:None)
   with patch.object(f,'render',side_effect=Invalid('input overflow; never truncate')):
    self.assertIsNone(j.invoke({'payload':{},'payload_digest':'x'},'s','e0'))
   self.assertEqual(j.snapshot()['totals']['calls'],0)
   with patch.object(f,'render',side_effect=Invalid('template changed')):
    with self.assertRaises(c.Halt):j.invoke({'payload':{},'payload_digest':'x'},'s','e0')
 def test_aggregate_limit_reserves_before_dispatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fake();j=c.Journal(Path(tmp)/'j',f,'scope',lambda:None)
   with j._locked():
    s=j._read()
    # Artificial conservative ledger reaches the cap with fewer than max calls.
    s['attempts']=[dict(id='prior',slot='prior',event='e0',state='completed',input_tokens=13312,
        reservation_tokens=16384,actual_tokens=16384,observation=dict(input_tokens=13312,output_tokens=3072,finish_reason='eos')) for _ in range(54)]
    j._save(s)
   f.render=lambda req:dict(input_tokens=13312,input_ids=[1]*13312,payload={})
   f.generate=lambda r:dict(input_tokens=13312,output_tokens=3072,finish_reason='eos',final_text='{}',boundary_error=None)
   j.invoke({'payload':{},'payload_digest':'x'},'last','e0')
   self.assertEqual(j.snapshot()['totals']['actual_tokens'],901120)
   with self.assertRaises(c.Halt):j.invoke({'payload':{},'payload_digest':'x'},'excess','e0')

class DeploymentTests(unittest.TestCase):
 def test_exact_scheduler_shape_and_independent_sets(self):
  from beyond_consensus.experiments.cluster import ClusterConfig
  config=ClusterConfig(partition='NA100q',time='04:00:00',memory_gb=128,python='/env/python',storage_root='/data',cache_root='/cache',snapshot_root='/snapshots',output_root='/outputs')
  argv=launch.arguments(config,Path('/snapshot'),Path('/output'))
  self.assertIn('--gres=gpu:1',argv);self.assertIn('--time=04:00:00',argv)
  self.assertEqual(argv[-4],'/snapshot/experiments/run_composite_math.sbatch')
  d=c.domain();mapping=c.blueprint()['ownership'];e=compile_organisation(d,c.selection(d,mapping))
  for (owner,_),actual in zip(e.groups,evaluate(e)['recovery_sets']):self.assertEqual(c.independent_reconstruction(mapping,owner),set(actual))
  with self.assertRaises(Invalid):launch.check_allocation('Partition=NA100q TimeLimit=01:00:00')
