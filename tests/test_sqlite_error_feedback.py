"""Opt-in feedback privacy, accounting and provenance; scripted CPU controls."""
import copy
from dataclasses import replace
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from tests.test_data_workflows import domain_at
from tests.test_sqlite_compatibility import controls, ScriptedWorker
from beyond_consensus.agents.worker import WorkerLoop
from beyond_consensus.attacks.fixed import AttackController
from beyond_consensus.schemas import AttackSpec
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.models.base import Generation
from beyond_consensus.runtime.sqlite_executor import capabilities, public_error_category
from beyond_consensus.runtime.data_domain import SQLExecutionError
from beyond_consensus.tasks.sqlite_compatibility import tasks
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from pathlib import Path
from beyond_consensus.planning.costs import compatibility
from beyond_consensus.util import BCError, canonical


def config():
    return replace(load_config(ROOT/'configs/sqlite-tool-compatibility.json'),
                   model=RunConfig().model, sqlite_error_feedback='sqlite-errors-v1')


class FeedbackTests(unittest.TestCase):
    def test_opt_in_gate_and_manifest_calibration_identity(self):
        new = config()
        old = replace(new, sqlite_error_feedback='generic')
        self.assertNotEqual(build_manifest(new, ROOT)['experiment_id'], build_manifest(old, ROOT)['experiment_id'])
        self.assertNotEqual(compatibility(new), compatibility(old))
        self.assertEqual(RunConfig().sqlite_error_feedback, 'generic')
        with self.assertRaises(BCError):
            RunConfig(sqlite_error_feedback='sqlite-errors-v1')
        with self.assertRaises(BCError):
            replace(new, sqlite_error_feedback='private')

    def test_allowlist_never_exports_exception_payloads(self):
        for message, expected in [('no such column: PRIVATE_SECRET', 'unresolved_column'),
                                  ('wrong number of arguments to function PRIVATE_SECRET', 'function_arity'),
                                  ('unrecognized PRIVATE_SECRET', 'sqlite_execution_error')]:
            category = public_error_category(sqlite3.OperationalError(message))
            self.assertEqual(category, expected)
            self.assertNotIn('PRIVATE_SECRET', canonical(SQLExecutionError(category).observation()))
        self.assertEqual(SQLExecutionError('PRIVATE_SECRET').category, 'sqlite_execution_error')
        self.assertEqual(SQLExecutionError({}).category, 'sqlite_execution_error')

    @unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
    def test_worker_corrects_or_exhausts_same_charged_retries(self):
        class Scripted(MockBackend):
            def generate(self, messages, max_new_tokens, seed):
                observations = [json.loads(m['content']) for m in messages if m['role'] == 'user']
                created = next((o for o in observations if 'artifact_id' in o), None)
                if created:
                    action = {'tool':'submit_required_artifact', 'artifact_id':created['artifact_id']}
                else:
                    tree = copy.deepcopy(controls()['aggregate'])
                    errors = [o for o in observations if 'error' in o]
                    if not errors or repeat:
                        if fault == 'unresolved_column':
                            tree['columns'][0]['expr'] = {'column':'UNBOUND.department_id'}
                        else:
                            tree['columns'][1]['expr']['call']['args'].append({'literal':1})
                    action = {'tool':'run_read_query', 'select_sql':tree, 'permitted_artifact_versions':{}}
                raw = canonical(action)
                return Generation(raw, (len(raw)+3)//4)

        for fault in ('unresolved_column', 'function_arity'):
            for repeat in (False, True):
                for mode in ('generic', 'sqlite-errors-v1'):
                    with self.subTest(fault=fault, repeat=repeat, mode=mode), tempfile.TemporaryDirectory() as temp:
                        task = next(t for t in tasks() if t.id.endswith('aggregate'))
                        domain = domain_at(temp, task)
                        cfg = replace(config(), sqlite_error_feedback=mode)
                        domain.engine.config = cfg
                        loop = WorkerLoop(Scripted(), cfg, domain.engine.ledger, domain.store,
                            AttackController(AttackSpec('clean'), ()), domain=domain)
                        outcome = loop.run(task, task.id, 'w0', 'primary', 0)
                        self.assertEqual(outcome.status, 'malformed' if repeat else 'submitted')
                        self.assertEqual(outcome.actions, 3)
                        errors = [json.loads(m['content']) for m in domain.store.contexts['w0'].messages
                                  if m['role']=='user' and 'error' in json.loads(m['content'])]
                        self.assertEqual(len(errors), 3 if repeat else 1)
                        for error in errors:
                            self.assertNotIn('UNBOUND', canonical(error))
                            self.assertNotIn('expected', canonical(error))
                            if mode == 'generic':
                                self.assertEqual(error, {'error':'Action rejected by the restricted tool contract'})
                            else:
                                self.assertEqual(error['error_code'], fault)
                                self.assertEqual(error['feedback_policy'], mode)
                        entries = domain.engine.ledger.entries
                        self.assertEqual(len([e for e in entries if e['kind']=='model']), 3)
                        self.assertEqual(len([e for e in entries if e['kind']=='tool']), 3)
                        executions = [e for e in entries if e['kind']=='sql_execution']
                        self.assertEqual(len(executions), 3 if repeat else 2)
                        self.assertTrue(all(e['work']==cfg.budget.tool_charge*3 for e in executions))

    @unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
    def test_condition_report_and_all_probes_still_pass(self):
        cfg = config()
        manifest = build_manifest(cfg, ROOT)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            results = run_manifest(manifest, output, ROOT, backend=ScriptedWorker())
            self.assertEqual([r['success'] for r in results], [True]*4)
            report = aggregate(manifest, output)
            self.assertEqual(report['condition']['sqlite_error_feedback'], 'sqlite-errors-v1')
            for result in results:
                self.assertEqual(result['provenance']['condition']['sqlite_error_feedback'], 'sqlite-errors-v1')
            path = output/'episodes'/results[0]['episode_id']/'result.json'
            row = json.loads(path.read_text())
            del row['provenance']['condition']['sqlite_error_feedback']
            path.write_text(json.dumps(row))
            with self.assertRaises(BCError):
                aggregate(manifest, output)

    def test_terminal_path_does_not_request_or_raise_public_feedback(self):
        with tempfile.TemporaryDirectory() as temp:
            domain = domain_at(temp, tasks()[0])
            domain.engine.config = config()
            with patch('beyond_consensus.runtime.data_domain.execute', return_value={
                    'status':'semantic_error', 'category':'unresolved_column'}) as child:
                with self.assertRaises(BCError) as caught:
                    domain.sql([], [], 'final_evaluation')
                self.assertNotIsInstance(caught.exception, SQLExecutionError)
                self.assertNotIn('error_categories', child.call_args.kwargs)
