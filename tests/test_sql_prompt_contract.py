"""Worker-visible representation separation; no native answers or model calls."""
import json
from types import SimpleNamespace
import unittest
from tests.support import ROOT
from beyond_consensus.runtime.data_domain import DataDomain, SQL_INSTRUCTIONS, SQL_COLUMN_HINT, SILO_INSTRUCTIONS
from beyond_consensus.models.action_schema import validate_action


class SQLPromptContractTests(unittest.TestCase):
    def instructions(self, mode, kind='sqlite_fixture'):
        engine = SimpleNamespace(task=SimpleNamespace(kind=kind),
                                 config=SimpleNamespace(model=SimpleNamespace(action_constraint=mode)))
        return DataDomain(engine).instructions

    def test_text_worker_receives_only_text_query_examples(self):
        mode = 'sqlite-sql-text-v1'
        text = self.instructions(mode)
        self.assertNotIn(SQL_COLUMN_HINT, text)
        self.assertNotIn('"expr"', text)
        self.assertIn('sqlite-sql-text-names-v2', text)
        self.assertIn('database|table|column', text)
        self.assertIn('Database/schema-qualified table references are unsupported', text)
        actions = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
        queries = [a for a in actions if 'select_sql' in a]
        self.assertTrue(queries)
        for action in queries:
            self.assertIsInstance(action['select_sql'], str)
            validate_action(json.dumps(action), mode)
        # Public binding requirements survive the representation conversion.
        self.assertIn('exact version ID', text)
        self.assertIn('Unsupported syntax is rejected', text)

    def test_tree_and_silo_prompts_preserved(self):
        self.assertEqual(self.instructions('sqlite-json-schema-v1'), SQL_INSTRUCTIONS)
        self.assertIn(SQL_COLUMN_HINT, self.instructions('sqlite-json-schema-v1'))
        self.assertEqual(self.instructions('none', kind='silo'), SILO_INSTRUCTIONS)
