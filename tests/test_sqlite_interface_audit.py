"""Synthetic compiler/executor audit; no native inputs or model execution."""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT
from beyond_consensus.runtime.sqlite_executor import capabilities, compile_select, execute


@unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
class InterfaceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / 'synthetic.sqlite'
        with sqlite3.connect(self.database) as con:
            con.execute('CREATE TABLE readings(numerator REAL, denominator REAL)')
            con.executemany('INSERT INTO readings VALUES (?, ?)', [(6, 3), (10, 4)])

    def run_tree(self, tree):
        return execute(self.database, ['readings'], [], [tree])

    def test_unbound_alias_fails_but_explicit_binding_and_constant_select_work(self):
        tree = {'columns': [{'expr': {'column': 'r.numerator'}}]}
        original = copy.deepcopy(tree)
        compile_select(tree, {'readings'})  # Syntax validity is not name resolution.
        result = self.run_tree(tree)
        self.assertEqual(result['status'], 'semantic_error')
        self.assertEqual(result['reason'], 'query_execution')
        self.assertNotIn('r.numerator', str(result))
        self.assertEqual(tree, original)  # No implicit repair.
        tree['from'] = {'table': 'readings', 'as': 'r'}
        self.assertEqual(self.run_tree(tree)['outputs'][0]['rows'], [[6.0], [10.0]])
        constant = {'columns': [{'expr': {'literal': 9}}]}
        self.assertEqual(self.run_tree(constant)['outputs'][0]['rows'], [[9]])

    def test_function_arity_is_checked_by_execution(self):
        tree = {'columns': [{'expr': {'call': {'name': 'sum', 'args': [
            {'column': 'numerator'}, {'column': 'denominator'}]}}}],
            'from': {'table': 'readings'}}
        compile_select(tree, {'readings'})
        self.assertEqual(self.run_tree(tree)['status'], 'semantic_error')
        tree['columns'][0]['expr']['call']['args'].pop()
        self.assertEqual(self.run_tree(tree)['outputs'][0]['rows'], [[16.0]])

    def test_division_preserved_and_wrong_multiplication_remains_executable(self):
        tree = {'columns': [{'expr': {'binary': ['/', {'column': 'numerator'},
            {'column': 'denominator'}]}, 'as': 'ratio'}],
            'from': {'table': 'readings'},
            'order_by': [{'expr': {'column': 'numerator'}, 'direction': 'asc'}]}
        divided = self.run_tree(tree)
        tree['columns'][0]['expr']['binary'][0] = '*'
        multiplied = self.run_tree(tree)
        self.assertEqual(divided['status'], 'ok')
        self.assertEqual(multiplied['status'], 'ok')
        self.assertEqual(divided['outputs'][0]['rows'], [[2.0], [2.5]])
        self.assertEqual(multiplied['outputs'][0]['rows'], [[18.0], [40.0]])
        self.assertEqual(divided['outputs'][0]['columns'], multiplied['outputs'][0]['columns'])
