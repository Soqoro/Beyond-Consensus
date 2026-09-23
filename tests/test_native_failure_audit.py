"""Offline replay diagnostics never reveal rows or replace scientific scores."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace
from types import SimpleNamespace
from tests.support import ROOT
from beyond_consensus.diagnostics.sqlite_failure import error_category, execute_probe, replay_task, ReplayLedger, audit
from beyond_consensus.runtime.sqlite_executor import DEFAULT_LIMITS
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.tasks.sqlite_compatibility import tasks
from beyond_consensus.util import BCError, file_hash


class FailureAuditTests(unittest.TestCase):
    def test_error_categories_never_echo_identifiers(self):
        for text, expected in [('no such column: PRIVATE','unresolved_column'),
                               ('ambiguous column name: PRIVATE','ambiguous_column'),
                               ('misuse of aggregate function sum()','aggregate_misuse'),
                               ('unknown PRIVATE','sqlite_execution_error')]:
            self.assertEqual(error_category(sqlite3.OperationalError(text)),expected)
        with patch.dict('os.environ', {}, clear=True), self.assertRaisesRegex(BCError,'sbatch'):
            audit(Path('/not-read'))

    def test_restricted_child_replays_missing_column_without_raw_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp)/'source.sqlite'
            with sqlite3.connect(db) as con:
                con.execute('CREATE TABLE entries(id INTEGER)')
                con.execute('INSERT INTO entries VALUES(1)')
            before = file_hash(db)
            result = execute_probe(db,['entries'],[],[{'columns':[{'expr':{'column':'PRIVATE_MISSING'}}],
                'from':{'table':'entries'}}],DEFAULT_LIMITS,before)
            self.assertEqual(result['status'],'semantic_error')
            self.assertEqual(result['category'],'unresolved_column')
            self.assertNotIn('PRIVATE',json.dumps(result))
            self.assertEqual(file_hash(db),before)

    def test_selected_checks_use_original_comparison_and_export_no_rows(self):
        task = replace(tasks()[0], id='solar_M_3', kind='sqlite_native', required_outputs=('u0',))
        task.metadata['evaluation']={'u0':{'checks':[
            {'select':{'marker':'candidate'},'reference':{'marker':'reference'}}], 'conditions':{'order':True}}}
        store = ProvenanceStore()
        artifact = store.submit('w0','u0',{'kind':'view','name':'PRIVATE_VIEW','select':{}})
        state = {'store':store.export(), 'selected':{'u0':artifact.id}}
        class Ledger:
            def call(self, task, views, queries, label):
                if label=='selected_bundle': return {'status':'ok','outputs':[]}
                return {'status':'ok','outputs':[{'rows':[['PRIVATE_ACTUAL' if label=='candidate_check' else 'PRIVATE_REFERENCE']]}]}
        with patch('beyond_consensus.runtime.data_domain.DataDomain.bundle',return_value=([],[],[])):
            report = replay_task(task,state,{'success':False},Ledger())
        self.assertFalse(report['checks'][0]['exact_match'])
        self.assertFalse(report['checks'][0]['native_comparison_match'])
        self.assertNotIn('PRIVATE',json.dumps(report))
        self.assertFalse(report['historical_success'])

    def test_failed_query_alignment_does_not_guess_missing_context(self):
        task=replace(tasks()[0],id='solar_2')
        action={'tool':'run_read_query','permitted_artifact_versions':{},'select_sql':{'PRIVATE':1}}
        state={'store':{'contexts':{'w0':{'messages':[{'role':'assistant','content':json.dumps(action)}]}},
                       'events':[{'type':'generation_metadata'}, {'type':'sql_execution','stage':'primary','status':'semantic_error'}]},
               'selected':{}}
        ledger=SimpleNamespace(call=lambda *args:{'status':'semantic_error','category':'unresolved_column'})
        report=replay_task(task,state,{'success':False},ledger)
        self.assertEqual(report['failed_query_replays'][0]['category'],'unresolved_column')
        self.assertNotIn('PRIVATE',json.dumps(report))
        state['store']['contexts']={}
        report=replay_task(task,state,{'success':False},ledger)
        self.assertEqual(report['failed_query_replays'][0]['status'],'history_unavailable')

    def test_ledger_accounts_failed_calls_and_enforces_bound(self):
        task=replace(tasks()[0])
        task.metadata['harness']={'database':{'path':'unused','sha256':'hash'},'tables':[], 'limits':DEFAULT_LIMITS}
        ledger=ReplayLedger(10,max_calls=1)
        with patch('beyond_consensus.tasks.sqlite_tasks.verify_file',return_value=Path('unused')), \
             patch('beyond_consensus.diagnostics.sqlite_failure.execute_probe',return_value={'status':'semantic_error'}):
            ledger.call(task,[],[],'failed_query')
            with self.assertRaisesRegex(BCError,'bound'): ledger.call(task,[],[],'failed_query')
        self.assertEqual(ledger.entries[0]['work'],10*DEFAULT_LIMITS['cpu_seconds'])

    def test_unsubmitted_invalidated_candidate_is_compared_without_promotion(self):
        from beyond_consensus.diagnostics.sqlite_failure import replay_candidate, candidate_content
        from beyond_consensus.util import digest, plain
        task = replace(tasks()[0], id='solar_2', required_outputs=('solar_2',))
        task.metadata['evaluation'] = {'solar_2': {'checks': [
            {'submitted_report': True, 'reference': {'private': 'reference'}}],
            'conditions': {'order': True}}}
        tree = {'columns': [{'expr': {'literal': 1}}]}
        content = {'kind': 'query', 'select': tree, 'bindings': {}, 'rows': [[1]],
                   'execution_binding_hash': digest([[], tree])}
        store = ProvenanceStore()
        artifact = store.submit('w0', 'solar_2', content, 'data_artifact')
        store.events.append({'type': 'sql_execution', 'stage': 'primary', 'status': 'ok',
                             'views': digest([]), 'queries': digest([tree])})
        store.invalidate({artifact.id})
        state = plain({'store': store.export(), 'selected': {}})
        before = digest(state)
        class Ledger:
            def call(self, task, views, queries, label):
                return {'status': 'ok', 'outputs': [{'rows': [[1]]}]}
        report = replay_candidate(task, state, {'success': False}, Ledger(), artifact.id)
        self.assertTrue(report['checks'][0]['native_comparison_match'])
        self.assertFalse(report['historical_artifact_valid'])
        self.assertFalse(report['historical_success'])
        self.assertFalse(report['candidate_promoted'])
        self.assertEqual(digest(state), before)
        self.assertNotIn('reference', json.dumps(report).replace('reference_status', ''))
        state['store']['artifacts'][artifact.id]['content']['select'] = {}
        with self.assertRaisesRegex(BCError, 'binding'):
            candidate_content(task, state, artifact.id)
        state['store']['artifacts'][artifact.id]['content'] = content
        state['store']['events'] = []
        with self.assertRaisesRegex(BCError, 'creation'):
            candidate_content(task, state, artifact.id)
