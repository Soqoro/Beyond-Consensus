"""Narrow Track F scope: stdlib gates plus explicitly pinned executor controls."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reporecourse.common import digest,Rejected,load
from reporecourse.resources import Resources,ACCOUNTING
from reporecourse.engine import Engine,ModelWorker
from reporecourse.tasks import ROOT,private_task,tool_contract
from reporecourse.track_f import (TYPE,TASK,CONDITIONS,RESOURCE,REVISION,CONTROLS,
                                  build,require,select,classification,report)
from reporecourse.qualification import runtime_versions
from reporecourse.track_f_controls import PINS,exercise


def rehash(m):
    m['experiment_id']=digest({k:v for k,v in m.items() if k not in ('episodes','experiment_id','planned_episodes')})
    for e in m['episodes']:
        e['experiment_id']=m['experiment_id'];e['episode_id']=digest({k:v for k,v in e.items() if k!='episode_id'})
    m['planned_episodes']=len(m['episodes'])
    return m


def fixture():
    """Constructed metadata for gate unit tests; not an executable approval."""
    card=next(c for c in load(ROOT/'catalog.json')['tasks'] if c['id']==TASK)
    public=load(ROOT/'public'/f'{TASK}.json')
    plan=next(p for p in public['outlines'] if p['id']=='independent')
    model=dict(backend='transformers',checkpoint='Qwen/Qwen3.5-27B',revision=REVISION,tokenizer_revision=REVISION,
        dtype='bfloat16',context_limit=16384,max_new_tokens=2048,thinking=True,do_sample=False,
        temperature=.7,top_p=.8,top_k=20,action_constraint='reporecourse-json-v1')
    m=dict(schema='rr-manifest-v1',source_revision='constructed-test',sources_root='/not-staged',model=model,
        model_lock_sha256=digest({'revision':REVISION}),resource=copy.deepcopy(RESOURCE),tasks=[card],public_hashes={TASK:'test-public'},
        engineering_smoke=True,confirmatory=False,policy_campaign_enabled=False,independent_review='pending',
        lane='requirement_delegation',shards=1,qualification=None)
    e=dict(task_id=TASK,source_group=card['source_group'],family='data_product',policy='delegation_jit',
        outline='independent',plan=plan,seed=7,track='clean',target=None,shard=0,resource_profile=RESOURCE['profile'])
    m['episodes']=[e];rehash(m)
    historical=dict(manifest=copy.deepcopy(m),manifest_hash=digest(m),snapshot_hash='test',result_hash='test',max_actions=24)
    m['qualification']=dict(status='cpu_qualified_review_pending',task_hash=digest(card),track_f_controls=dict(
        status='passed',accounting_version=ACCOUNTING,public_hash='test-public',controls={c:True for c in CONTROLS}))
    return build(m,historical)


def save_result(output,m,index,success=True,**kw):
    e=m['episodes'][index]
    r=dict(experiment_id=m['experiment_id'],episode_id=e['episode_id'],provenance={'manifest_hash':digest(e)},
        status='completed',success=success,resource_profile=Resources(100000,1200).summary(),failures=[],
        intervention_triggered=False,track=e['track'],target=e['target'],events=[],state={},**kw)
    path=Path(output)/'episodes'/e['episode_id']/'result.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r));return r


class AccountingTests(unittest.TestCase):
    def test_over_estimate_preserves_actual_no_credit_or_dispatch(self):
        r=Resources(1000,35);r.reserve_cpu(31)
        with self.assertRaisesRegex(Rejected,'cpu_cap'):r.reconcile_cpu('model_host',31,36)
        self.assertEqual(r.cpu_seconds,36);self.assertEqual(r.cpu_reserved,0)
        self.assertEqual(r.events[-1]['released_allowance'],0)
        self.assertEqual(r.events[-1]['estimate_overrun'],5)
        self.assertEqual(r.events[-1]['episode_overshoot'],1)
        with self.assertRaises(Rejected):r.ensure_dispatch()
        with self.assertRaises(Rejected):r.reserve(1,1)
        with self.assertRaisesRegex(Rejected,'reservation_missing'):r.reconcile_cpu('model_host',31,36)
        self.assertEqual(r.cpu_seconds,36)

    def test_uncertain_and_invalid_usage(self):
        r=Resources(100,10);r.reserve_cpu(4);r.reconcile_cpu('interrupted',4,None)
        self.assertEqual(r.uncertain_cpu,4);self.assertEqual(r.cpu_seconds,4)
        self.assertTrue(r.events[-1]['usage_uncertain'])
        for actual in (-1,float('nan'),float('inf')):
            with self.assertRaises(Rejected):r.reconcile_cpu('x',0,actual)
        k=r.reserve(10,20);r.reconcile(k);self.assertEqual(r.uncertain_tokens,30)
        with self.assertRaises((Rejected,KeyError)):r.reconcile(k)

    def test_model_cpu_overshoot_charges_tokens_before_exception(self):
        from types import SimpleNamespace
        class B:
            def count_input(self,m):return 2
            def generate(self,*a):return SimpleNamespace(text='{"tool":"finish"}',output_tokens=3,reasoning_tokens=0,device_seconds=0,diagnostics={})
        r=Resources(100,35)
        with patch('reporecourse.engine.time.process_time',side_effect=[0,36]):
            with self.assertRaisesRegex(Rejected,'cpu_cap'):
                ModelWorker(B(),100,10).next_action({}, {}, {}, [],r,0,lambda:None)
        self.assertEqual(r.actual_tokens,5);self.assertEqual(r.cpu_seconds,36)
        self.assertFalse(r.reservations)

    def test_no_tool_or_model_after_exhaustion(self):
        from reporecourse.tasks import load_task
        p=load_task('synthetic-nullable','/missing')[1]
        class W:
            def next_action(self,*a):raise AssertionError('dispatched after cap')
        e=Engine(p,W())
        try:
            e.env.resources.cpu_seconds=e.env.resources.cpu_cap
            with self.assertRaisesRegex(Rejected,'cpu_cap'):e.env.action('w0',{'tool':'list_sources'})
            self.assertEqual(e.run()['status'],'resource_exhausted')
        finally:e.env.close()

    def test_unavailable_context_reset_and_stale_restore(self):
        from reporecourse.tasks import load_task
        from reporecourse.runtime import Environment
        p=load_task('synthetic-nullable','/missing')[1];env=Environment(p,track='F',target='w0')
        try:
            env.assignment['w0']={'id':'response','outputs':['response']};old=env.state()
            with self.assertRaisesRegex(Rejected,'unavailable'):env.publish('w0','x','schema',True,{},['response'])
            with self.assertRaisesRegex(Rejected,'rollback'):env.restore_state(old)
            with self.assertRaisesRegex(Rejected,'unavailable'):env.action('w0',{'tool':'list_sources'})
            self.assertFalse(env.artifacts)
        finally:env.close()


class GateTests(unittest.TestCase):
    def test_exact_three_and_seed_copied(self):
        m=fixture();require(m)
        self.assertEqual([e['condition'] for e in m['episodes']],list(CONDITIONS))
        self.assertEqual({e['seed'] for e in m['episodes']},{7})
        self.assertEqual(sum(m['resource']['token_cap'] for e in m['episodes']),300000)

    def test_reject_rehashed_expansions_and_changed_limits(self):
        edits=[lambda m:m['episodes'].append(copy.deepcopy(m['episodes'][0])),
            lambda m:m['episodes'][1].update(seed=9),lambda m:m['episodes'][1].update(policy='restart'),
            lambda m:m['episodes'][1].update(track='S'),lambda m:m['episodes'][1].update(target='w3'),
            lambda m:m['tasks'].append(copy.deepcopy(m['tasks'][0])),lambda m:m.update(max_actions=25),
            lambda m:m['resource'].update(cpu_cap=1201),lambda m:m['model'].update(context_limit=32768),
            lambda m:m['qualification']['track_f_controls']['controls'].update(resume_after=False)]
        for edit in edits:
            m=fixture();edit(m);rehash(m)
            with self.subTest(edit=edit),self.assertRaises(Rejected):require(m)

    def test_order_and_unlaunched_report(self):
        m=fixture()
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(select(m,d,'fresh_clean'),0)
            self.assertEqual([r['status'] for r in report(m,d)['conditions']],['unlaunched']*3)
            with self.assertRaises(Rejected):select(m,d,'loss_w0')
            save_result(d,m,0,False)
            with self.assertRaises(Rejected):select(m,d,'loss_w0')
            save_result(d,m,0,True);self.assertEqual(select(m,d,'loss_w0'),1)
            with self.assertRaises(Rejected):select(m,d,'loss_w1')
            save_result(d,m,1,False);self.assertEqual(select(m,d,'loss_w1'),2)

    def test_correct_overcap_and_completed_harness_failure(self):
        with tempfile.TemporaryDirectory() as d:
            r=save_result(d,fixture(),0,True);r['resource_profile']['cpu_cap_debit']=1201
            self.assertEqual(classification(r),'resource_cap_failure')
            r['failures']=[{'category':'episode_closed'}]
            self.assertEqual(classification(r),'harness_state_or_dispatch_failure')

    def test_scheduler_one_condition_snapshot_and_guard(self):
        from beyond_consensus.experiments.cluster import ClusterConfig,submit
        from beyond_consensus.util import BCError
        m=fixture();lock={'revision':REVISION}
        with tempfile.TemporaryDirectory() as d:
            cfg=ClusterConfig('USER-PARTITION','02:00:00',128,'/env/python',d,d,d,d)
            snap=Path(d)/'snapshot with spaces'
            with patch.dict(os.environ,{},clear=True),patch('beyond_consensus.experiments.reporecourse.verify_inputs'), \
                 patch('beyond_consensus.models.competence.require_qualification'), \
                 patch('beyond_consensus.experiments.cluster.registry_root',return_value=Path(d)/'registry'), \
                 patch('beyond_consensus.experiments.cluster.validate_site'), \
                 patch('beyond_consensus.experiments.cluster.guard',return_value=[]) as guard, \
                 patch('beyond_consensus.experiments.cluster.verify_snapshot',return_value={'manifest_hash':digest(m),'cluster_hash':digest(vars(cfg))}), \
                 patch('beyond_consensus.experiments.cluster.command') as command:
                with self.assertRaises(BCError):submit(Path(d),cfg,m,lock,1,dry_run=True,condition='fresh_clean')
                r=submit(Path(d),cfg,m,lock,1,dry_run=True,condition='fresh_clean',existing_snapshot=snap)
                self.assertIn('--array=0-0%1',r['argv']);self.assertIn(str(snap),r['argv'])
                self.assertFalse(r['submitted']);command.assert_not_called();guard.assert_called_once()
                with self.assertRaises(BCError):submit(Path(d),cfg,m,lock,2,dry_run=True,condition='fresh_clean',existing_snapshot=snap)


@unittest.skipUnless(all(runtime_versions().get(k)==v for k,v in PINS.items()),'current pinned SQLGlot/jsonschema/referencing CPU children required')
class ExecutorControls(unittest.TestCase):
    def test_both_losses_resume_visibility_wrong_repair(self):
        # Constructed local tables from finite test inputs, explicitly no claim
        # of staged-source provenance. Cluster qualification uses verified pack.
        p=load(ROOT/'public'/f'{TASK}.json');pr=private_task(TASK)
        p['tables']=copy.deepcopy(next(f['tables'] for f in pr['fixtures'] if 'tables' in f))
        p['sources'].update(request=p['request'],tables=p['tables'],tool_contract=tool_contract())
        controls,evidence=exercise(p,pr)
        self.assertTrue(all(controls.values()),controls)
        self.assertEqual(set(evidence),set(CONDITIONS))

    def test_actual_journal_runner_three_shards_and_overcap_correctness(self):
        from types import SimpleNamespace
        from beyond_consensus.experiments.reporecourse import run
        from reporecourse.resources import success_at_budget
        p=load(ROOT/'public'/f'{TASK}.json');pr=private_task(TASK)
        p['tables']=copy.deepcopy(next(f['tables'] for f in pr['fixtures'] if 'tables' in f))
        p['sources'].update(request=p['request'],tables=p['tables'],tool_contract=tool_contract())
        witness=next(w for w in pr['witnesses'] if w['organization']=='independent')
        class ScriptedBackend:
            def count_input(self,messages):return 2
            def generate(self,messages,n,seed):
                observation=json.loads(messages[-1]['content']);outputs=observation['assignment']['outputs']
                action=next(a['action'] for a in witness['actions'] if set(a['action']['obligations']) & set(outputs))
                return SimpleNamespace(text=json.dumps(action),output_tokens=3,reasoning_tokens=0,device_seconds=0,diagnostics={})
        m=fixture()
        with tempfile.TemporaryDirectory() as d,patch('beyond_consensus.experiments.reporecourse.verify_inputs'), \
             patch('beyond_consensus.experiments.reporecourse.load_task',return_value=(m['tasks'][0],p)):
            for i in range(3):
                r=run(m,d,ROOT.parents[1],shard=i,backend=ScriptedBackend())[0]
                self.assertTrue(r['success'],r.get('failures'))
                self.assertEqual(r['intervention_triggered'],i!=0)
                self.assertNotIn('episode_closed',[f['category'] for f in r['failures']])
                self.assertEqual(run(m,d,ROOT.parents[1],shard=i,backend=object()),[r])
            self.assertEqual(len(list((Path(d)/'episodes').iterdir())),3)
            over=Resources(100000,1200);over.cpu_seconds=1201
            self.assertTrue(r['evaluation']['success'])
            self.assertFalse(success_at_budget('completed',r['evaluation']['success'],over))


class HistoricalTests(unittest.TestCase):
    def test_literal_settings_from_verified_snapshot_and_tamper_rejection(self):
        from beyond_consensus.experiments.reporecourse_history import resolve
        from beyond_consensus.util import BCError
        from reporecourse.common import file_hash
        m=fixture()['historical_resolution']['manifest'];e=m['episodes'][0]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);snap=root/'snapshot';run=root/'run'
            files={'resolved/manifest.json':json.dumps(m),
                   'src/reporecourse/engine.py':'class Engine:\n def __init__(self, *, max_actions=24): pass\n',
                   'src/beyond_consensus/experiments/reporecourse.py':'def run():\n return Engine(public, worker)\n'}
            for name,text in files.items():
                path=snap/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            marker={'files':{name:file_hash(snap/name) for name in files},'manifest_hash':digest(m),'source_revision':m['source_revision']}
            (snap/'snapshot.json').write_text(json.dumps(marker))
            run.mkdir();(run/'manifest.json').write_text(json.dumps(m))
            r=save_result(run,m,0,True)
            r.update(plan=e['plan'],evaluation={'obligations':{'customer_summary':True,'method_summary':True}},
                state={'bound':{'customer_summary':'a','method_summary':'b'},'artifacts':{'a':{'author':'w0'},'b':{'author':'w1'}}})
            (run/'episodes'/e['episode_id']/'result.json').write_text(json.dumps(r))
            resolved=resolve(run,snap)
            self.assertEqual(resolved['max_actions'],24);self.assertEqual(resolved['manifest']['episodes'][0]['seed'],7)
            (snap/'src/reporecourse/engine.py').write_text('modified')
            with self.assertRaises(BCError):resolve(run,snap)

    def test_cpu_wrapper_dry_run_from_spool_directory(self):
        import subprocess
        wrapper=ROOT.parents[1]/'experiments/qualify_reporecourse.sh'
        with tempfile.TemporaryDirectory() as spool:
            r=subprocess.run(['bash',str(wrapper),'--track-f-controls','--dry-run'],cwd=spool,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('No model weights or GPU jobs',r.stdout)
            self.assertEqual(list(Path(spool).iterdir()),[])

    def test_missing_current_children_block_qualification(self):
        from reporecourse.track_f_controls import qualify_controls
        with patch('reporecourse.track_f_controls.runtime_versions',return_value={}):
            self.assertEqual(qualify_controls('/not-staged')['status'],'blocked_prerequisite')
