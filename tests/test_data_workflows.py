"""Behavior tests for restricted data workflows; no benchmark data/model required."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import subprocess
import tarfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import RunConfig
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.experiments.manifest import build_manifest, episode_from, validate_manifest, validate_splits
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.runtime.budget import BudgetLedger, BudgetExceeded
from beyond_consensus.runtime.data_domain import DataDomain, TaskUnavailable
from beyond_consensus.runtime.episode import EpisodeEngine
from beyond_consensus.runtime.persistence import EpisodeJournal
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.runtime.sqlite_executor import execute, compile_select, capabilities, SQLRejected, authorizer
from beyond_consensus.schemas import TaskInstance, Alarm
from beyond_consensus.tasks.sqlite_tasks import fixtures, fixture_database, read_query, column, compare_rows, pair, stage, inspect, native_tasks
from beyond_consensus.tasks.silo import task as silo_task, solve, score, generate_inputs, generate_manifest, validate_record
from beyond_consensus.tasks.data_manifest import validate_reference, validate_native
from beyond_consensus.util import BCError, atomic_json, digest, file_hash, plain, read_json

SQL_AVAILABLE = all(capabilities()[k] for k in ('defensive','trusted_schema_off','process_limits','extension_loading_disabled','table_inventory'))


def domain_at(directory, task=None):
    task = task or fixtures()[0]
    config = RunConfig(task_kind=task.kind, monitor_id='data-structure-v1', max_actions=12)
    engine = SimpleNamespace(task=task, config=config, ledger=BudgetLedger(config.budget.total, config.budget),
        store=ProvenanceStore(), selected={}, candidates={}, journal=SimpleNamespace(path=Path(directory)), alarm=None)
    return DataDomain(engine)


class TreeTests(unittest.TestCase):
    def test_full_tree_denies_raw_stacked_and_nested_functions(self):
        invalid = ['SELECT 1; ATTACH DATABASE x AS y', {'columns':[{'expr':{'call':{'name':'load_extension','args':[{'literal':'x'}]}}}]},
            {'columns':[{'expr':{'select':{'columns':[{'expr':{'call':{'name':'readfile','args':[{'literal':'/etc/passwd'}]}}}]}}}]},
            {'columns':[{'expr':{'column':'sqlite_master.sql'}}], 'from':{'table':'sqlite_master'}},
            {'columns':[{'expr':{'literal':1}}],'pragma':'writable_schema'},
            {'columns':[{'expr':{'literal':1}}], 'from':{'table':'x; DROP TABLE x'}}]
        for tree in invalid:
            with self.subTest(tree=tree), self.assertRaises((SQLRejected, TypeError)):
                compile_select(tree, ['x'])

    def test_nested_depth_and_object_checks(self):
        expression = {'literal':1}
        for _ in range(20):
            expression = {'binary':['+',expression,{'literal':1}]}
        with self.assertRaises(SQLRejected):
            compile_select({'columns':[{'expr':expression}]}, [])
        with self.assertRaises(SQLRejected):
            compile_select(read_query('private',['secret']), ['public'])

    def test_authorizer_is_independent_of_tree(self):
        con = sqlite3.connect(':memory:')
        try:
            con.execute('CREATE TABLE allowed(value)')
            con.set_authorizer(authorizer({'allowed'}))
            for sql in ("ATTACH ':memory:' AS stolen", 'PRAGMA database_list', 'CREATE TABLE pwned(x)',
                        "SELECT load_extension('x')", 'SELECT * FROM sqlite_master', 'DELETE FROM allowed', 'VACUUM INTO \'x\''):
                with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                    con.execute(sql)
            self.assertEqual(con.execute('SELECT value FROM allowed').fetchall(), [])
        finally:
            con.close()

    def test_native_diagnostic_and_strict_completion_differ(self):
        self.assertTrue(compare_rows([[1],[1]],[[1]],native=True))
        self.assertFalse(compare_rows([[1],[1]],[[1]]))
        self.assertFalse(compare_rows([],[],native=True))
        self.assertTrue(compare_rows([],[]))
        self.assertTrue(compare_rows([[None],[1.004]],[[None],[1.0]],native=True))
        self.assertFalse(compare_rows([[None],[1.004]],[[None],[1.0]]))
        self.assertFalse(compare_rows([[1],[2]],[[2],[1]],ordered=True))
        self.assertTrue(compare_rows([[None],[1]],[[1],[None]]))


@unittest.skipUnless(SQL_AVAILABLE, 'Fixed SQL executor needs supported stdlib CPU resource controls')
class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = fixture_database(Path(self.temp.name)/'source.sqlite',0)
        self.source_hash = file_hash(self.path)

    def test_read_view_join_json_and_original_immutable(self):
        view = {'name':'derived','select':read_query('measurements',['id','value'])}
        tree = read_query('derived',['id','value'])
        result = execute(self.path,['measurements'],[view],[tree])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['outputs'][0]['rows'],[[1,2],[2,-3],[3,0]])
        self.assertEqual(file_hash(self.path),self.source_hash)
        self.assertEqual(list(Path(self.temp.name).iterdir()),[self.path])
        json_tree={'columns':[{'expr':{'call':{'name':'json_extract','args':[{'literal':'{"x":7}'},{'literal':'$.x'}]}}}]}
        self.assertEqual(execute(self.path,['measurements'],[],[json_tree])['outputs'][0]['rows'],[[7]])

    def test_prohibited_final_replay_is_rejected_without_paths(self):
        bad={'columns':[{'expr':{'call':{'name':'load_extension','args':[{'literal':'/private/gold'}]}}}]}
        result=execute(self.path,['measurements'],[],[bad])
        self.assertEqual(result['status'],'prohibited_operation')
        self.assertNotIn('/private',json.dumps(result))

    def expensive(self):
        return {'columns':[{'expr':{'call':{'name':'sum','args':[{'column':'a.value'}]}}}],
            'from':{'table':'measurements','as':'a'},
            'joins':[{'kind':'cross','source':{'table':'measurements','as':f'b{i}'}} for i in range(8)]}

    def test_output_and_progress_limits_have_no_partial_success(self):
        result=execute(self.path,['measurements'],[],[read_query('measurements',['value'])],{'max_rows':1})
        self.assertEqual(result['status'],'execution_limit')
        self.assertNotIn('outputs',result)
        result=execute(self.path,['measurements'],[],[self.expensive()],{'max_steps':100})
        self.assertEqual(result['status'],'execution_limit')
        self.assertEqual(file_hash(self.path),self.source_hash)

    def test_cpu_deadline_limits_and_cleanup(self):
        con=sqlite3.connect(self.path)
        con.executemany('INSERT INTO measurements VALUES(?,?)',[(i,i) for i in range(4,104)])
        con.commit();con.close()
        baseline=file_hash(self.path)
        for limits in ({'cpu_seconds':1,'seconds':4,'max_steps':10**12}, {'cpu_seconds':3,'seconds':1,'max_steps':10**12}):
            started=time.monotonic()
            result=execute(self.path,['measurements'],[],[self.expensive()],limits)
            self.assertEqual(result['status'],'execution_limit')
            self.assertLess(time.monotonic()-started,6)
            self.assertEqual(file_hash(self.path),baseline)
        # A killed executor cannot retain a lock or dirty its source.
        self.assertEqual(execute(self.path,['measurements'],[],[read_query('measurements',['id'])])['status'],'ok')

    def test_source_virtual_objects_are_rejected(self):
        con=sqlite3.connect(self.path)
        con.execute('CREATE VIEW hidden AS SELECT value FROM measurements')
        con.commit();con.close()
        result=execute(self.path,['measurements'],[],[read_query('measurements',['value'])])
        self.assertEqual(result['status'],'prohibited_operation')

    def test_virtual_word_in_ordinary_table_is_not_a_virtual_table(self):
        con=sqlite3.connect(self.path)
        con.execute('CREATE TABLE virtual_orders(value TEXT)')
        con.execute("INSERT INTO virtual_orders VALUES('CREATE VIRTUAL TABLE')")
        con.commit();con.close()
        result=execute(self.path,['measurements','virtual_orders'],[],[read_query('virtual_orders',['value'])])
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['outputs'][0]['rows'],[['CREATE VIRTUAL TABLE']])


@unittest.skipUnless(SQL_AVAILABLE, 'Fixed SQL executor needs supported stdlib CPU resource controls')
class DataEpisodeTests(unittest.TestCase):
    def test_preview_does_not_truncate_stored_final_output(self):
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp)
            rows=[[i] for i in range(40)]
            artifact=domain.store.submit('w0','u0',{'kind':'query','rows':rows},'data_artifact')
            preview=domain.preview(artifact.content['rows'])
            self.assertTrue(preview['preview_truncated'])
            self.assertEqual(len(preview['rows']),20)
            self.assertEqual(len(artifact.content['rows']),40)
            self.assertEqual(domain.preview(rows,20)['rows'],rows[20:])

    def test_missing_evaluation_status_and_sanitized_export(self):
        from beyond_consensus.experiments.export import export_bundle
        config=RunConfig(task_kind='sqlite_fixture',monitor_id='data-structure-v1',policies=('single',),attacks=('clean',),
            data_manifest='/private/DO_NOT_EXPORT.json')
        manifest=build_manifest(config,ROOT)
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'run'
            with patch('beyond_consensus.runtime.data_domain.execute',return_value={'status':'execution_limit','reason':'capacity'}):
                rows=run_manifest(manifest,output,ROOT)
            self.assertEqual(rows[0]['status'],'execution_limit')
            self.assertIsNone(rows[0]['success'])
            summary=aggregate(manifest,output)
            self.assertIsNone(summary['groups']['single/clean']['success_rate_observed'])
            event_path=output/'episodes'/rows[0]['episode_id']/'events.jsonl'
            with event_path.open('a') as stream:
                stream.write(json.dumps({'type':'failure','error':'HIDDEN_SQL_SENTINEL','traceback':'/private/SECRET_TEST_FILE'})+'\n')
            target=Path(temp)/'bundle.tar.gz'
            export_bundle(output,target)
            with tarfile.open(target) as archive:
                text='\n'.join(archive.extractfile(member).read().decode() for member in archive.getmembers())
            self.assertNotIn('HIDDEN_SQL_SENTINEL',text)
            self.assertNotIn('SECRET_TEST_FILE',text)
            self.assertNotIn('DO_NOT_EXPORT',text)
            self.assertIn('costs',text)

    def test_independent_context_cannot_reuse_primary_query_results(self):
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp)
            result=domain.store.submit('w0','u0',{'kind':'query','rows':[[5]]},'data_artifact')
            domain.store.reset('w0')
            self.assertNotIn(result.id,domain.available('w0','replicate',()))
            self.assertNotIn(result.id,domain.available('w0','prepare',()))

    def test_data_calibration_charges_cold_preparation_and_prefill(self):
        from beyond_consensus.planning.calibration import calibrate
        config=RunConfig(task_kind='sqlite_fixture',monitor_id='data-structure-v1')
        report=calibrate(config,MockBackend(),fixtures())
        self.assertEqual(report['calibration']['sample_count'],12)
        self.assertTrue(all(m['status']=='submitted' and m['work']>0 for m in report['measurements']))
        self.assertGreater(report['calibration']['costs']['prepared'],report['calibration']['costs']['cold'])

    def test_sqlite_four_policies_withholding_and_costs(self):
        config=RunConfig(task_kind='sqlite_fixture',monitor_id='data-structure-v1')
        manifest=build_manifest(config,ROOT)
        with tempfile.TemporaryDirectory() as temp:
            rows=run_manifest(manifest,Path(temp),ROOT)
            self.assertEqual(len(rows),8)
            self.assertTrue(all(r['status']=='completed' and r['success'] for r in rows))
            for row in rows:
                kinds={e['kind'] for e in row['costs']['entries']}
                self.assertTrue({'model','tool','sql_execution','complete_output_scoring'} <= kinds)
                self.assertLessEqual(row['costs']['spent'],row['costs']['cap'])
            clean={r['policy']:r for r in rows if r['attack']=='clean'}
            self.assertLess(clean['jit']['costs']['spent'],clean['replication']['costs']['spent'])
            self.assertEqual(manifest['schema'],'bc-manifest-v2')
            self.assertEqual(aggregate(manifest,Path(temp))['independent_source_groups'],1)

    def test_lazy_bindings_transitive_reads_messages_and_cheap_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp)
            store=domain.store
            template=store.submit('w1','u1',{'kind':'query_template','select':read_query('first',['id','value']), 'view_names':['first']},'data_artifact')
            original=store.submit('w0','u0',{'kind':'view','name':'first','select':read_query('measurements',['id','value']),'bindings':{}},'implementation')
            store.reset('w1')
            old=domain.replay('u1','w1',template.id,{'first':original.id},'primary')
            old_final=store.submit('w1','u1',old.content)
            self.assertIn(original.id,old.parents)
            nested=store.submit('w2','u2',{'kind':'view','name':'second','select':read_query('first',['id','value']),'bindings':{'first':original.id}},'implementation')
            content={'kind':'query','select':read_query('second',['id','value']),'bindings':{'second':nested.id}}
            domain.closure(content,'w3')
            self.assertTrue({original.id,nested.id} <= store.contexts['w3'].reads)
            store.message('w0','w2','poisoned description')
            tainted=store.submit('w2','u3',{'kind':'query_template','select':read_query('measurements',['id']),'view_names':[]},'data_artifact')
            unaffected=store.submit('w3','independent',{'kind':'query','select':read_query('measurements',['id']),'bindings':{}})
            # Create an actually independent artifact after resetting inherited reads.
            store.reset('w3')
            independent=store.submit('w3','independent',{'safe':True})
            invalid=store.invalidate({original.id},{'w0'})
            self.assertIn(old_final.id,invalid)
            self.assertFalse(tainted.valid)
            self.assertTrue(template.valid)
            self.assertTrue(independent.valid)
            with self.assertRaises(BCError): domain.closure(old.content)
            store.reset('w2')
            replacement=store.submit('w2','u0',original.content)
            domain.engine.selected={'u0':replacement.id}
            domain.engine.candidates={'u1':[old_final.id]}
            before=domain.engine.ledger.spent
            repaired=domain.try_replay('u1','w3','repair')
            self.assertIsNotNone(repaired)
            self.assertEqual(repaired.content['bindings'],{'first':replacement.id})
            self.assertEqual(old.content['bindings'],{'first':original.id})
            self.assertGreater(domain.engine.ledger.spent,before)
            self.assertNotIn('w0',repaired.contributors)

    def test_query_reads_cannot_spend_protected_reserve(self):
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp)
            before=domain.engine.ledger.spent
            with self.assertRaises(BudgetExceeded):
                domain.sql([], [read_query('measurements',['id'])], 'primary', domain.engine.ledger.cap)
            self.assertEqual(before,domain.engine.ledger.spent)

    def test_resume_keeps_bindings_budget_and_coverage(self):
        config=RunConfig(task_kind='sqlite_fixture',monitor_id='data-structure-v1',policies=('jit',),attacks=('clean',))
        manifest=build_manifest(config,ROOT)
        row=episode_from(manifest['episodes'][0])
        with tempfile.TemporaryDirectory() as temp:
            journal=EpisodeJournal(Path(temp),row.episode_id)
            stop=[False]
            engine=EpisodeEngine(fixtures()[0],row,config,MockBackend(),journal,journal.begin(digest(row)),lambda:stop[0])
            original=engine.boundary
            def boundary(name):
                if name=='operation_complete': stop[0]=True
                original(name)
            engine.boundary=boundary
            first=engine.run()
            self.assertEqual(first.status,'interrupted')
            next_engine=EpisodeEngine(fixtures()[0],row,config,MockBackend(),journal,journal.begin(digest(row)))
            second=next_engine.run()
            self.assertTrue(second.success)
            self.assertGreater(second.costs['spent'],first.costs['spent'])
            self.assertEqual(set(next_engine.selected),set(fixtures()[0].required_outputs))


class SILOTests(unittest.TestCase):
    def test_calibration_cannot_cross_access_regimes(self):
        from beyond_consensus.planning.calibration import calibrate
        from beyond_consensus.planning.costs import estimates
        from beyond_consensus.tasks.data_manifest import policy_view
        config=RunConfig(task_kind='silo',monitor_id='data-structure-v1',max_actions=12)
        report=calibrate(config,MockBackend(),[silo_task(seed=0)])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'calibration.json'
            atomic_json(path,report['calibration'])
            configured=replace(config,calibration_file=str(path))
            value=estimates(configured,MockBackend(),policy_view(silo_task(seed=1)))
            self.assertEqual(value.status,'development-calibrated')
            with self.assertRaises(BCError):
                estimates(configured,MockBackend(),policy_view(silo_task(seed=1,access='no_recovery_copy')))
    def test_new_cli_is_stdlib_only(self):
        result=subprocess.run([sys.executable,'-I','-S',str(ROOT/'scripts/bc.py'),'silo-validate','--help'],
            text=True,capture_output=True,check=True)
        self.assertIn('--input',result.stdout)
    def test_all_policies_complete_both_families_under_withholding(self):
        for family in ('II-11','II-20'):
            config=RunConfig(task_kind='silo',monitor_id='data-structure-v1',max_actions=12)
            manifest=build_manifest(config,ROOT,[silo_task(family)])
            with tempfile.TemporaryDirectory() as temp:
                rows=run_manifest(manifest,Path(temp),ROOT)
                self.assertEqual(len(rows),8)
                self.assertTrue(all(r['status']=='completed' and r['success'] for r in rows))

    def test_shard_tool_denies_unauthorized_reads_and_charges_transfer(self):
        from beyond_consensus.agents.worker import WorkerLoop
        from beyond_consensus.attacks.fixed import AttackController
        from beyond_consensus.schemas import AttackSpec,DelegationPlan
        from beyond_consensus.policies.core import common_units
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp,silo_task())
            domain.engine.plan=DelegationPlan('test',common_units(domain.task))
            loop=WorkerLoop(MockBackend(),domain.engine.config,domain.engine.ledger,domain.store,
                AttackController(AttackSpec('clean'),()),domain=domain)
            with self.assertRaises(BCError):
                loop._tool(domain.task,'u0','w1',{'tool':'read_shard','unit':'u0'},'primary','implement',())
            prior=domain.engine.ledger.spent
            domain.engine.alarm=Alarm(('u0',),('w0',),('public missing submission',))
            loop._tool(domain.task,'u0','w1',{'tool':'read_shard','unit':'u0'},'repair','implement',())
            self.assertGreater(domain.engine.ledger.spent,prior)
            observed=json.loads(domain.store.contexts['w1'].messages[-1]['content'])
            self.assertEqual(observed['result'],generate_inputs('II-11',0)[0])
            self.assertNotEqual(observed['result'],solve('II-11',generate_inputs('II-11',0))[0])

    def test_published_input_and_scorer_parity(self):
        data=read_json(ROOT/'tests/fixtures/silo-public-parity.json')
        for vector in data['vectors']:
            shards=vector['input_shards']
            expected=solve(vector['family'],shards)
            self.assertEqual(digest(expected),vector['expected_sha256'])
            if vector['family']=='II-20':
                self.assertEqual(generate_inputs('II-20',999,vector['workers']),shards)
            record={'case_id':vector['family'],'metadata':{'num_agents':vector['workers'],'is_segmented':True},
                'agent_configs':[{'agent_id':i,'input_shard':s,'expected_output':expected[i]} for i,s in enumerate(shards)],
                'expected_output':{'per_agent_values':expected}}
            parsed=validate_record(record)
            self.assertEqual(parsed['shards'],shards)
            record['expected_output']['per_agent_values'][0][0]+=1
            with self.assertRaises(BCError): validate_record(record)

    def test_four_worker_generator_complete_segmentation(self):
        self.assertEqual(generate_inputs('II-11',0)[0],[25,49,27,3,17,33,32,26,20,31,23,38,14,33,9])
        for family,size in [('II-11',15),('II-20',5)]:
            shards=generate_inputs(family,0)
            self.assertEqual([len(s) for s in shards],[size]*4)
            flat=[v for s in shards for v in s]
            computed=solve(family,shards)
            if family=='II-11':
                self.assertEqual([v for s in computed for v in s],[sum(flat[:i+1]) for i in range(len(flat))])
            self.assertEqual(shards,generate_inputs(family,0))
        with self.assertRaises(BCError): generate_manifest('II-20',[0,1],'protected_original_shards')

    def test_native_partial_is_not_complete_and_missing_segment_counts(self):
        shards=generate_inputs('II-11',0)
        expected=solve('II-11',shards)
        selected={f'u{i}':str(s) for i,s in enumerate(expected)}
        self.assertTrue(score('II-11',shards,selected)['complete_task_success'])
        del selected['u0']
        result=score('II-11',shards,selected)
        self.assertEqual(result['native_S'],.75)
        self.assertFalse(result['complete_task_success'])

    def test_protected_recovery_and_no_copy_are_separate(self):
        for access in ('protected_original_shards','no_recovery_copy'):
            task=silo_task('II-11',0,access)
            config=RunConfig(task_kind='silo',monitor_id='data-structure-v1',max_actions=12,policies=('jit',),attacks=('withholding',))
            manifest=build_manifest(config,ROOT,[task])
            with tempfile.TemporaryDirectory() as temp:
                rows=run_manifest(manifest,Path(temp),ROOT)
                self.assertEqual(rows[0]['status'],'completed')
                self.assertEqual(rows[0]['success'],access=='protected_original_shards')
                checkpoint=read_json(next((Path(temp)/'episodes').glob('*/checkpoint.json')))
                state=checkpoint.get('state',checkpoint)
                transfers=[e for e in state['store']['events'] if e['type']=='shard_transfer']
                self.assertTrue(transfers)
                if access=='no_recovery_copy': self.assertTrue(all(e['reason']=='owner' for e in transfers))

    def test_worker_view_and_source_leakage(self):
        task=silo_task()
        serialized=canonical_worker(task)
        self.assertNotIn('expected_output',serialized)
        self.assertNotIn('shards',serialized)
        other=replace(task,id='rerun',group='other-group')
        with self.assertRaises(BCError): validate_splits({'development':[task],'test':[other]})
        config=RunConfig(task_kind='silo',task_count=2,monitor_id='data-structure-v1')
        with self.assertRaises(BCError): build_manifest(config,ROOT,[task,silo_task('II-11',1,'no_recovery_copy')])


def canonical_worker(task):
    return json.dumps({'specification':task.specification,'sources':task.sources})


@unittest.skipUnless(SQL_AVAILABLE, 'Fixed SQL executor needs supported stdlib CPU resource controls')
class NativeFixtureTests(unittest.TestCase):
    """Synthetic records testing the upstream schema, never benchmark evidence."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        dbdir=self.root/'fixturedb'
        dbdir.mkdir()
        fixture_database(dbdir/'fixturedb_template.sqlite',0)
        (dbdir/'fixturedb_schema.txt').write_text('measurements(id,value)')
        (dbdir/'fixturedb_column_meaning_base.json').write_text('{"value":"public measurement"}')
        (dbdir/'fixturedb_kb.jsonl').write_text(json.dumps({'id':0,'knowledge':'public knowledge','description':'data',
            'definition':'numbers','type':'calculation_knowledge','children_knowledge':-1})+'\n')
        raw=[]
        for key,kind in [('fixture_view','Management'),('fixture_report','Query')]:
            raw.append({'instance_id':key,'selected_database':'fixturedb','query':key+' exact synthetic requirement',
                'preprocess_sql':[],'clean_up_sqls':[],'category':kind,'conditions':{'order':False,'decimal':[],'distinct':False},
                'sol_sql':[],'test_cases':[],'external_knowledge':[]})
        self.raw=raw
        meta=self.root/'livesqlbench_data_sqlite.jsonl'
        meta.write_text(''.join(json.dumps(r)+'\n' for r in raw))
        self.addCleanup(patch.stopall)
        patch('beyond_consensus.tasks.sqlite_tasks.PUBLIC_SHA256',file_hash(meta)).start()
        gold=copy.deepcopy(raw)
        for r in gold:
            r['sol_sql']=['GOLD_SQL_SENTINEL']
            r['test_cases']=['HIDDEN_TEST_SENTINEL']
            r['external_knowledge']=['GOLD_KNOWLEDGE_SENTINEL']
        material=self.root/'private-material.jsonl'
        material.write_text(''.join(json.dumps(r)+'\n' for r in gold))
        query=read_query('measurements',['id','value'])
        self.review={'schema':'bc-sqlite-reviewed-evaluation-v1','reviewer':'test fixture reviewer','tasks':{}}
        for public,private in zip(raw,gold):
            is_view=public['category']=='Management'
            artifact={'kind':'view' if is_view else 'query','select':query}
            if is_view: artifact['name']='derived'
            check={'reference':query,'order':False}
            if is_view: check['select']=read_query('derived',['id','value'])
            else: check['submitted_report']=True
            self.review['tasks'][public['instance_id']]={'record_hash':digest(public),'material_hash':digest(private),
                'test_translation_reviewed':True,'review_notes':'Synthetic test-only reviewed comparison',
                'artifact':artifact,'checks':[check],'tables':['measurements'],'schema':{'measurements':['id','value']},
                'supported_requirement':True,'setup':[],'cleanup':[]}
        self.review_path=self.root/'review.json'
        atomic_json(self.review_path,self.review)
        self.staged_path=self.root/'stage.json'
        stage(self.root,self.staged_path,material,self.review_path)
        self.staged=read_json(self.staged_path)

    def test_distinct_views_hide_gold_paths_and_selected_knowledge(self):
        tasks,excluded=native_tasks(self.staged)
        self.assertEqual(excluded,[])
        self.assertEqual(len(tasks),2)
        for task in tasks:
            with tempfile.TemporaryDirectory() as temp:
                domain=domain_at(temp,task)
                public=json.dumps(domain.initial('w0','implement',()))+canonical_worker(task)+json.dumps(task.metadata['harness']['documents'])
                for marker in ('GOLD_SQL_SENTINEL','HIDDEN_TEST_SENTINEL','GOLD_KNOWLEDGE_SENTINEL',str(self.root)):
                    self.assertNotIn(marker,public)
            self.assertEqual(task.specification,next(r['query'] for r in self.raw if r['instance_id']==task.id))
        from beyond_consensus.tasks.data_manifest import policy_view
        visible=policy_view(tasks[0])
        self.assertNotIn('evaluation',visible.metadata)
        self.assertNotIn('harness',visible.metadata)

    def test_reference_approval_is_invalidated_by_task_change(self):
        from beyond_consensus.tasks.data_manifest import validate_data
        data=validate_native(self.staged,None,2)
        path=self.root/'validated.json'
        atomic_json(path,data)
        self.assertEqual(len(validate_data(path)),2)
        data['tasks'][0]['sources']['fixture_view']['requirement']='changed obligation'
        atomic_json(path,data)
        with self.assertRaises(BCError): validate_data(path)

    def test_near_duplicate_cross_database_split_is_rejected(self):
        tasks,_=native_tasks(self.staged)
        left=copy.deepcopy(tasks[0]);right=copy.deepcopy(tasks[1])
        left.sources[left.id]['requirement']='Find the total value of all current public records grouped by category and owner'
        right.sources[right.id]['requirement']='Find the total value of all current public records grouped by category and owner please'
        right=replace(right,group='another_database')
        right.metadata['base_hash']='other-base'
        with self.assertRaises(BCError): validate_splits({'development':[left],'test':[right]})

    def test_missing_gold_is_unavailable_and_no_invented_ten_tasks(self):
        public_only={**self.staged,'materials':None,'review':None}
        report=inspect(public_only)
        self.assertTrue(all(t['status']=='blocked' for t in report['tasks']))
        result=validate_native(public_only,None,10)
        self.assertEqual(result['status'],'scoring_unavailable')
        self.assertEqual(result['tasks'],[])
        self.assertNotIn('accuracy',result)

    def test_native_reference_controls_and_two_obligation_joint_state(self):
        tasks,_=native_tasks(self.staged)
        self.assertTrue(all(validate_reference(t)['status']=='validated' for t in tasks))
        paired=pair(tasks[0],tasks[1],'Independent report and view share one immutable input database')
        report=validate_reference(paired)
        self.assertEqual(report['status'],'validated')
        self.assertTrue(all(report['missing_obligation_controls'].values()))
        self.assertTrue(all(report['corrupt_obligation_controls'].values()))
        self.assertEqual(set(paired.required_outputs),{'fixture_view','fixture_report'})

    def test_setup_conflicts_unsafe_evaluators_and_source_changes_block(self):
        tasks,_=native_tasks(self.staged)
        bad=copy.deepcopy(tasks[1])
        bad.metadata['harness']['setup']=['CREATE TRIGGER forbidden']
        with self.assertRaises(BCError): pair(tasks[0],bad,'conflicting setup')
        self.review['tasks']['fixture_view']['checks'][0]['exec']='HIDDEN_TEST_SENTINEL'
        atomic_json(self.review_path,self.review)
        self.staged['review']['sha256']=file_hash(self.review_path)
        tasks,excluded=native_tasks(self.staged)
        self.assertEqual(len(tasks),1)
        self.assertEqual(excluded[0]['status'],'blocked')
        (self.root/'fixturedb/fixturedb_template.sqlite').write_bytes(b'changed')
        tasks,excluded=native_tasks(self.staged)
        self.assertEqual(tasks,[])

    def test_binding_old_view_and_new_required_view_cannot_claim_joint_state(self):
        tasks,_=native_tasks(self.staged)
        paired=pair(tasks[0],tasks[1],'common input')
        with tempfile.TemporaryDirectory() as temp:
            domain=domain_at(temp,paired)
            old={'kind':'view','name':'derived','select':read_query('measurements',['id','value']),'bindings':{}}
            v1=domain.store.submit('w0','fixture_view',old)
            changed=copy.deepcopy(old)
            changed['select']['columns'][1]['expr']={'literal':0}
            v2=domain.store.submit('w1','fixture_view',changed)
            report=domain.store.submit('w2','fixture_report',{'kind':'query','select':read_query('derived',['id','value']),'bindings':{'derived':v1.id}})
            domain.engine.selected={'fixture_view':v2.id,'fixture_report':report.id}
            with self.assertRaises(BCError): domain.bundle(domain.engine.selected)


if __name__=='__main__': unittest.main()
