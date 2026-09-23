"""Synthetic failure evidence, without models or task material."""
import json
import unittest
from unittest.mock import patch
from tests.support import ROOT
from beyond_consensus.models.base import Generation
from beyond_consensus.models.transformers_backend import check_sql_frontend_probe


class ProbeReportingTests(unittest.TestCase):
    def test_bad_json_and_envelope_keep_generation_without_execution(self):
        for text, stage in [('not JSON', 'json_decode'), ('[]', 'action_envelope'),
                            ('{"tool":"inspect_schema","database_id":"fixture"}', 'action_envelope')]:
            with self.subTest(text=text), patch('beyond_consensus.runtime.sql_text.lower') as lower:
                report = check_sql_frontend_probe(Generation(text, 10))
                self.assertFalse(report['passed'])
                self.assertEqual(report['failure_stage'], stage)
                self.assertEqual(report['generation']['text'], text)
                lower.assert_not_called()

    def test_unfinished_generation_never_reaches_compiler(self):
        # Even a parseable prefix is not a completed constrained action.
        text = json.dumps({'tool': 'run_read_query', 'permitted_artifact_versions': {}, 'select_sql': 'SELECT id FROM entries'})
        for diagnostics, stage in [
            ({'finish_reason': 'length_limit', 'constraint_complete': False}, 'generation_limit'),
            ({'finish_reason': 'eos', 'constraint_complete': False}, 'incomplete_action'),
        ]:
            with patch('beyond_consensus.runtime.sql_text.lower') as lower:
                report = check_sql_frontend_probe(Generation(text, 2048, diagnostics=diagnostics))
            self.assertFalse(report['passed'])
            self.assertEqual(report['failure_stage'], stage)
            self.assertEqual(report['generation']['text'], text)
            lower.assert_not_called()

    def test_compiler_rejection_is_retained_without_database(self):
        text = json.dumps({'tool': 'run_read_query', 'permitted_artifact_versions': {}, 'select_sql': 'bad SQL'})
        with patch('beyond_consensus.runtime.sql_text.lower', return_value={'status': 'rejected', 'category': 'test'}), \
             patch('beyond_consensus.tasks.sqlite_compatibility.database') as database:
            report = check_sql_frontend_probe(Generation(text, 10))
        self.assertEqual(report['failure_stage'], 'sql_compilation')
        self.assertEqual(report['compiler']['category'], 'test')
        database.assert_not_called()

    def test_execution_and_comparison_failures_remain_distinct(self):
        text = json.dumps({'tool': 'run_read_query', 'permitted_artifact_versions': {}, 'select_sql': 'SELECT id FROM entries ORDER BY id'})
        for result, stage, passed in [
            ({'status': 'semantic_error'}, 'sql_execution', False),
            ({'status': 'ok', 'outputs': [{'columns': ['id'], 'rows': []}]}, 'result_comparison', False),
            ({'status': 'ok', 'outputs': [{'columns': ['id'], 'rows': [[i] for i in range(1, 6)]}]}, None, True),
        ]:
            with patch('beyond_consensus.runtime.sql_text.lower', return_value={'status': 'ok', 'tree': {}}), \
                 patch('beyond_consensus.tasks.sqlite_compatibility.database'), \
                 patch('beyond_consensus.runtime.sqlite_executor.execute', return_value=result):
                report = check_sql_frontend_probe(Generation(text, 10))
            self.assertEqual(report['failure_stage'], stage)
            self.assertEqual(report['passed'], passed)
            self.assertEqual(report['executor'], result)
