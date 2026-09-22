"""Trusted synthetic parity only; original SQL never enters the worker executor."""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tests.support import ROOT
from beyond_consensus.runtime.sql_text import lower, MAX_BYTES, MODE
from beyond_consensus.runtime.sqlite_executor import compile_select, execute
from beyond_consensus.models.action_schema import validate_action, contract
from beyond_consensus.util import BCError

QUERIES = [
 'SELECT id FROM t ORDER BY id',
 'SELECT DISTINCT value FROM t ORDER BY value DESC',
 'SELECT SUM(value) AS s, COUNT(value) AS n, AVG(value) AS a, TOTAL(value) AS total FROM t',
 'SELECT SUM(DISTINCT value) AS s FROM t',
 'SELECT COUNT(*) AS n FROM t',
 'SELECT g, SUM(value) AS s FROM t GROUP BY g HAVING SUM(value)>0 ORDER BY g',
 'SELECT a.id AS id, b.name AS name FROM t a INNER JOIN d b ON a.g=b.id ORDER BY a.id',
 'SELECT a.id AS id, b.name AS name FROM t a LEFT OUTER JOIN d b ON a.g=b.id ORDER BY a.id',
 'SELECT a.id AS id, b.id AS other FROM t a CROSS JOIN d b ORDER BY a.id,b.id LIMIT 3',
 'SELECT id FROM t WHERE value IS NULL', 'SELECT id FROM t WHERE value IS NOT NULL ORDER BY id',
 'SELECT id FROM t WHERE value > 999',
 'SELECT value/2 AS divided, value%2 AS remainder FROM t ORDER BY id',
 'SELECT CASE WHEN value>0 THEN value WHEN value IS NULL THEN -1 ELSE 0 END AS result FROM t ORDER BY id',
 'SELECT q.id FROM (SELECT id FROM t WHERE value>0) q ORDER BY q.id',
 'SELECT (SELECT MAX(id) AS m FROM d) AS m FROM t ORDER BY id',
 'SELECT "id", [value] AS v FROM `t` ORDER BY id',
 "SELECT 'semi;colon -- /* quote '' here' AS text FROM t LIMIT 1; -- tail",
 "SELECT COALESCE(value,7) AS v, IFNULL(value,8) AS w, NULLIF(value,2) AS n FROM t ORDER BY id",
 "SELECT ROUND(value,1) AS v, ABS(value) AS a FROM t ORDER BY id",
 "SELECT LOWER(name) AS l, UPPER(name) AS u, LENGTH(name) AS n, SUBSTR(name,1,2) AS s FROM d ORDER BY id",
 "SELECT TRIM(' x ') AS t, REPLACE('xx','x','y') AS r, MIN(1,2) AS m, MAX(1,2) AS n",
 "SELECT JSON_EXTRACT('{\"a\":2}','$.a') AS a, JSON_TYPE('null') AS t, JSON_ARRAY_LENGTH('[1,2]') AS n",
 'SELECT 2+3*4 AS v, -2 AS neg, NULL AS missing',
 'SELECT id FROM t WHERE (value=2 OR value=4) AND id!=9 ORDER BY id DESC',
]
BAD = ['SELECT TOP 1 id FROM t', 'SELECT id FROM t FETCH FIRST 1 ROWS ONLY', 'SELECT * FROM t', 'SELECT COUNT(DISTINCT *) AS n FROM t', 'SELECT SUM(value) FROM t',
 'SELECT id FROM t; DELETE FROM t', 'SELECT id FROM t;;', 'PRAGMA table_info(t)',
 "ATTACH 'x' AS a", "VACUUM INTO 'x'", 'CREATE VIEW x AS SELECT id FROM t',
 'WITH x AS (SELECT id FROM t) SELECT id FROM x', 'SELECT id FROM t UNION SELECT id FROM t',
 'SELECT SUM(value) OVER () AS s FROM t', 'SELECT CAST(value AS TEXT) AS s FROM t',
 "SELECT load_extension('x') AS s", "SELECT readfile('/etc/passwd') AS s",
 'SELECT id FROM t LIMIT 1 OFFSET 1', 'SELECT value FROM t ORDER BY value NULLS LAST',
 'SELECT id FROM main.t', 'SELECT id FROM sqlite_master', 'SELECT id FROM unknown',
 'SELECT id FROM t RIGHT JOIN d ON t.g=d.id', 'SELECT id FROM t NATURAL JOIN d',
 'SELECT id FROM t JOIN d USING(id)', 'SELECT id FROM t WHERE id IN (1,2)',
 'SELECT id FROM t WHERE id BETWEEN 1 AND 2', 'SELECT id FROM t ORDER BY id COLLATE NOCASE',
 'SELECT CASE value WHEN 1 THEN 2 ELSE 3 END AS c FROM t', 'SELECT 1 AS "bad name"',
 'SELECT SUM(value) FILTER(WHERE value>0) AS s FROM t', 'SELECT id FROM t LIMIT 1001']


class SchemaTests(unittest.TestCase):
    def test_distinct_envelopes_and_incomplete_actions(self):
        text = json.dumps(dict(tool='run_read_query', permitted_artifact_versions={}, select_sql='SELECT id FROM t'))
        validate_action(text, MODE)
        with self.assertRaises(BCError): validate_action(text)
        with self.assertRaises(BCError): validate_action(text[:-1], MODE)
        self.assertNotEqual(contract(), contract(MODE))
        self.assertEqual(lower('x'*(MAX_BYTES+1), [])['category'], 'sql_input_limit')


@unittest.skipUnless(importlib.util.find_spec('sqlglot'), 'optional pinned SQLGlot required')
class CompilerTests(unittest.TestCase):
    def test_synthetic_semantic_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'fixture.sqlite'
            con = sqlite3.connect(path)
            con.executescript('CREATE TABLE t(id INTEGER,g INTEGER,value INTEGER); CREATE TABLE d(id INTEGER,name TEXT);')
            con.executemany('INSERT INTO t VALUES(?,?,?)', [(1,1,2),(2,1,2),(3,2,4),(4,3,None),(5,4,-3)])
            con.executemany('INSERT INTO d VALUES(?,?)', [(1,'Amber'),(2,'Blue'),(3,'Cedar')]); con.commit()
            for query in QUERIES:
                with self.subTest(query=query):
                    result = lower(query, ['t','d'])
                    self.assertEqual(result['status'], 'ok', result)
                    expected = con.execute(query)
                    columns = [c[0] for c in expected.description]; rows = [list(r) for r in expected]
                    actual = execute(path, ['t','d'], [], [result['tree']])
                    self.assertEqual(actual['status'], 'ok', actual)
                    self.assertEqual(actual['outputs'][0]['columns'], columns)
                    self.assertEqual(actual['outputs'][0]['rows'], rows)
            # Versioned view path still passes only trees to the protected backend.
            tree = lower('SELECT id, value*2 AS v FROM t', ['t'])['tree']
            query = lower('SELECT id, v FROM doubled ORDER BY id', ['doubled'])['tree']
            out = execute(path, ['t','d'], [{'name':'doubled','select':tree}], [query])
            self.assertEqual(out['status'], 'ok')
            self.assertEqual(out['outputs'][0]['rows'][0], [1,4])
            con.close()

    def test_rejects_and_resource_bounds(self):
        for query in BAD + ['SELECT '+'('*1000+'1'+')'*1000+' AS v', 'SELECT 1 AS v'+', 1 AS v'*401]:
            with self.subTest(query=query[:80]):
                report = lower(query, ['t','d'])
                self.assertEqual(report['status'], 'rejected', report)
                self.assertNotIn('tree', report)
                self.assertNotIn('/etc/passwd', json.dumps(report))
        # No arity correction, join inference or formula repair.
        tree = lower('SELECT SUM(value,0) AS s FROM t', ['t'])['tree']
        self.assertEqual(len(tree['columns'][0]['expr']['call']['args']), 2)
        self.assertNotIn('from', lower('SELECT missing.value AS v', [])['tree'])
        self.assertEqual(lower('SELECT value*2 AS v FROM t', ['t'])['tree']['columns'][0]['expr']['binary'][0], '*')

    def test_runtime_fail_closed_charges_and_wrong_query(self):
        from types import SimpleNamespace
        from tests.test_data_workflows import domain_at
        from beyond_consensus.tasks.sqlite_compatibility import tasks
        from unittest.mock import patch
        from beyond_consensus.util import plain
        with tempfile.TemporaryDirectory() as tmp:
            domain=domain_at(tmp,tasks()[0])
            cfg=plain(domain.engine.config)
            cfg['model']=SimpleNamespace(action_constraint=MODE)
            domain.engine.config=SimpleNamespace(**cfg)
            # Preserve typed budget object; test only the already-public tool boundary.
            from beyond_consensus.config import BudgetConfig
            domain.engine.config.budget=BudgetConfig()
            seen=[];loop=SimpleNamespace(_observe=lambda identity,value:seen.append(value))
            for query in BAD:
                with patch.object(domain,'sql') as db:
                    with self.assertRaises((BCError,ValueError)):
                        domain.handle(loop,domain.task.id,'w0',dict(tool='run_read_query',select_sql=query,permitted_artifact_versions={}), 'primary','implement',(),0)
                    db.assert_not_called()
            self.assertEqual(sum(e['work'] for e in domain.engine.ledger.entries if e['kind']=='sql_compilation'),30*len(BAD))
            domain.handle(loop,domain.task.id,'w0',dict(tool='run_read_query',select_sql='SELECT id FROM entries ORDER BY id',permitted_artifact_versions={}), 'primary','implement',(),0)
            version=seen[-1]['artifact_id']
            artifact=domain.handle(loop,domain.task.id,'w0',dict(tool='submit_required_artifact',artifact_id=version),'primary','implement',(),0)
            domain.engine.selected={domain.task.id:artifact.id}
            self.assertTrue(domain.integrate())
            self.assertFalse(domain.evaluate()['complete_task_success'])
