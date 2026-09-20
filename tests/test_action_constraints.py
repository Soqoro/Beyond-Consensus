"""Stdlib schema, reasoning-boundary, budget and provenance controls.

The native XGrammar/tokenizer qualification is scripts/check_action_constraints.py;
these CPU test doubles do not claim native mask or GPU/model validation.
"""
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from tests.test_sqlite_compatibility import ScriptedWorker, controls
from beyond_consensus.config import ModelConfig, RunConfig, load_config
from beyond_consensus.models.action_schema import MODE, contract, validate_action
from beyond_consensus.models.constrained import ReasoningGate, load_xgrammar
from beyond_consensus.models.base import Generation
from beyond_consensus.experiments.manifest import build_manifest, validate_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.planning.costs import compatibility
from beyond_consensus.util import BCError, canonical, digest, read_json


class Matrix:
    def __init__(self, row, batch=1):
        self.row, self.shape = row, (batch, len(row))

    def __getitem__(self, index):
        class Vector(list):
            def tolist(self):
                return list(self)
        return Vector(self.row[index[1]])


class ConstrainedScript(ScriptedWorker):
    def generate(self, messages, max_new_tokens, seed):
        result = super().generate(messages, max_new_tokens, seed)
        validate_action(result.text)
        return replace(result, diagnostics={"action_constraint": contract(), "constraint_complete": True,
            "constraint_cpu_seconds": 0.125, "constraint_mask_calls": 1})


class ConstraintTests(unittest.TestCase):
    def config(self):
        config = load_config(ROOT/"configs/sqlite-tool-compatibility-constrained.json")
        return replace(config, model=replace(config.model, backend="mock"))

    def test_public_schema_accepts_independent_controls_and_rejects_observed_errors(self):
        for name, tree in controls().items():
            action = {"tool": "run_read_query", "permitted_artifact_versions": {}, "select_sql": tree}
            self.assertEqual(validate_action(canonical(action)), action)
        # Same structure with different names/values is allowed: no answer selection.
        tree = {"columns": [{"expr": {"literal": "not a correct answer"}, "as": "unseen_name"}]}
        action = {"tool": "run_read_query", "permitted_artifact_versions": {}, "select_sql": tree}
        validate_action(canonical(action))
        defects = [
            {"function": "sum", "column": "amount"},
            {"binary": [">", "amount", 0]},
            {"case": {"when": [{"condition": {"column": "amount"}, "value": {"literal": 1}}], "else": {"literal": 0}}},
        ]
        for expr in defects:
            bad = copy.deepcopy(action)
            bad["select_sql"]["columns"][0]["expr"] = expr
            with self.subTest(expr=expr), self.assertRaises(BCError):
                validate_action(canonical(bad))
        bad = copy.deepcopy(action)
        bad["select_sql"]["group_by"] = [{"expr": {"column": "id"}}]
        with self.assertRaises(BCError):
            validate_action(canonical(bad))
        for text in ('{"tool":"run_read_query",', '{"tool":"read_source","tool":"read_source","name":"x"}',
                     '{"tool":"run_read_query","select_sql":"SELECT 1","permitted_artifact_versions":{}}'):
            with self.subTest(text=text), self.assertRaises(BCError):
                validate_action(text)

    def test_reasoning_gate_ignores_prompt_and_masks_first_action_token(self):
        called = []
        def inner(ids, scores):
            called.append(ids.row[:])
            return "masked"
        gate = ReasoningGate(inner, 2, 9)
        self.assertEqual(gate(Matrix([9,3]), "raw"), "raw")
        self.assertEqual(gate(Matrix([9,3,4]), "raw"), "raw")
        self.assertFalse(called)
        self.assertEqual(gate(Matrix([9,3,4,9]), "raw"), "masked")
        self.assertEqual(gate(Matrix([9,3,4,9,7]), "raw"), "masked")
        self.assertEqual(len(called), 2)
        # Fresh call resets state; a call with no closing token stays reasoning.
        fresh = ReasoningGate(inner, 2, 9)
        self.assertEqual(fresh(Matrix([9,3]), "raw"), "raw")
        self.assertFalse(fresh.active)
        self.assertEqual(ReasoningGate(inner,2,None)(Matrix([9,3]), "raw"), "masked")
        with self.assertRaises(BCError):
            fresh(Matrix([9,3],batch=2), "raw")
        clock = iter([0.,31.])
        with self.assertRaises(BCError):
            ReasoningGate(inner,2,9,clock=lambda: next(clock))(Matrix([9,3]), "raw")

    def test_missing_or_wrong_dependency_has_no_unconstrained_fallback(self):
        import importlib.metadata
        with patch('importlib.metadata.version', side_effect=importlib.metadata.PackageNotFoundError), self.assertRaises(BCError):
            load_xgrammar()
        with patch('importlib.metadata.version', return_value='other'), self.assertRaises(BCError):
            load_xgrammar()

    def test_frozen_manifest_contract_and_historical_model_hash(self):
        config = self.config()
        baseline = load_config(ROOT/"configs/sqlite-tool-compatibility-reasoning.json")
        configured = load_config(ROOT/"configs/sqlite-tool-compatibility-constrained.json")
        self.assertEqual(replace(configured.model, action_constraint="none"), baseline.model)
        self.assertEqual(replace(configured, name=baseline.name, development_profile=baseline.development_profile,
                                 model=baseline.model), baseline)
        with self.assertRaises(BCError):
            replace(config, task_kind="silo")
        with self.assertRaises(BCError):
            replace(config, shards=2)
        manifest = build_manifest(config, ROOT)
        self.assertEqual(manifest["action_constraint"], contract())
        self.assertEqual(validate_manifest(manifest), config)
        tampered = copy.deepcopy(manifest)
        tampered["action_constraint"]["schema_sha256"] = 'changed'
        with self.assertRaises(BCError):
            validate_manifest(tampered)
        before = compatibility(config)
        with patch('beyond_consensus.models.action_schema.XGRAMMAR_VERSION','changed'):
            self.assertNotEqual(before, compatibility(config))
        old = build_manifest(RunConfig(), ROOT)
        old["config"]["model"].pop("action_constraint")
        old["config_hash"] = digest(old["config"])
        old["model_hash"] = digest(old["config"]["model"])
        old["experiment_id"] = digest([old[k] for k in ("source_revision","config_hash","data_hash","model_hash","fixed_state_hash","calibration_hash")])
        for episode in old["episodes"]:
            episode.update(config_hash=old["config_hash"],model_hash=old["model_hash"],experiment_id=old["experiment_id"])
            task = next(t for t in old["tasks"] if t['id'] == episode['task_id'])
            episode['episode_id'] = digest([old['experiment_id'], digest(task),
                episode['policy'], episode['attack']['family'], episode['seed']])
        validate_manifest(old)

    def test_charged_cpu_episodes_and_missing_accounting_fail_closed(self):
        manifest = build_manifest(self.config(), ROOT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            results = run_manifest(manifest, root, ROOT, backend=ConstrainedScript())
            self.assertTrue(all(r['success'] for r in results))
            report = aggregate(manifest,root)
            self.assertEqual(report['condition']['action_constraint'], MODE)
            for result in results:
                ledger=read_json(root/'episodes'/result['episode_id']/'checkpoint.json')['ledger']
                charges=[e for e in ledger['entries'] if e['kind']=='constrained_decoding']
                self.assertEqual(len(charges),3)
                self.assertTrue(all(e['work']==10 and e['cpu_seconds']==0.125 for e in charges))
                self.assertFalse(ledger['reservations'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            results=run_manifest(manifest,root,ROOT,backend=ScriptedWorker())
            self.assertTrue(all(not r['success'] for r in results))
            for result in results:
                state=read_json(root/'episodes'/result['episode_id']/'checkpoint.json')
                charges=[e for e in state['ledger']['entries'] if e['kind']=='constrained_decoding']
                self.assertEqual(len(charges),1)
                self.assertEqual(charges[0]['work'],300)
                self.assertTrue(charges[0]['uncertain'])
                self.assertFalse(state['store']['artifacts'])

    def test_incomplete_generation_is_charged_without_executing_partial_action(self):
        class Truncated(ConstrainedScript):
            def generate(self, messages, max_new_tokens, seed):
                return Generation('{"tool":"run_read_query",', max_new_tokens, 1600,
                    diagnostics={"action_constraint": contract(), "constraint_complete": False,
                                 "constraint_cpu_seconds": 0.1, "finish_reason": "length_limit"})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            results = run_manifest(build_manifest(self.config(), ROOT), root, ROOT, backend=Truncated())
            self.assertTrue(all(not r['success'] for r in results))
            for result in results:
                state = read_json(root/'episodes'/result['episode_id']/'checkpoint.json')
                entries = state['ledger']['entries']
                models = [e for e in entries if e['kind']=='model']
                self.assertEqual(len(models), 3)
                self.assertTrue(all(e['output_tokens']==2048 and e['reasoning_tokens']==1600 for e in models))
                self.assertFalse(any(e['kind']=='sql_execution' for e in entries))
                self.assertFalse(state['store']['artifacts'])


if __name__ == '__main__':
    unittest.main()
