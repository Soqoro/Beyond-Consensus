"""Public view resolution must precede artifact creation; no gold feedback."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from tests.test_sqlite_compatibility import ScriptedWorker, controls
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.models.base import Generation
from beyond_consensus.planning.costs import compatibility
from beyond_consensus.runtime.sqlite_executor import capabilities, execute
from beyond_consensus.tasks.sqlite_compatibility import database, tasks
from beyond_consensus.util import canonical, read_json, file_hash


class BadViewWorker(ScriptedWorker):
    def __init__(self, defect):
        super().__init__()
        self.defect = defect

    def generate(self, messages, max_new_tokens, seed):
        answer = super().generate(messages, max_new_tokens, seed)
        action = json.loads(answer.text)
        if action["tool"] == "submit_view_definition":
            if self.defect == "missing_from":
                action["select_sql"].pop("from")
            elif self.defect == "wrong_value":
                action["select_sql"]["columns"][0] = {"expr": {"literal": 999}, "as": "id"}
            else:
                action["select_sql"]["columns"][-1].pop("as")
            text = canonical(action)
            return Generation(text, (len(text)+3)//4)
        return answer


class ViewValidationTests(unittest.TestCase):
    def test_reasoning_config_is_bounded_and_executor_fingerprint_changes(self):
        old = load_config(ROOT/"configs/sqlite-tool-compatibility.json")
        new = load_config(ROOT/"configs/sqlite-tool-compatibility-reasoning.json")
        self.assertEqual(replace(new.model, thinking=False, max_new_tokens=768), old.model)
        self.assertEqual(new.model.max_new_tokens, 2048)
        self.assertTrue(new.model.thinking)
        self.assertEqual(replace(new, model=old.model, name=old.name,
                                 development_profile=old.development_profile), old)
        self.assertEqual((new.task_count, new.shards, new.max_actions, new.budget.total), (4,1,12,100000))
        self.assertEqual(capabilities()["view_validation"], "zero-row-v1")
        before = compatibility(new, tasks()[-1])
        with patch("beyond_consensus.runtime.sqlite_executor.VIEW_VALIDATION", "other-version"):
            self.assertNotEqual(before, compatibility(new, tasks()[-1]))

    @unittest.skipUnless(capabilities()["defensive"], "SQLite defensive controls required")
    def test_create_only_resolves_views_without_forbidding_constant_selects(self):
        with tempfile.TemporaryDirectory() as temp:
            path = database(Path(temp)/"source.sqlite")
            original = file_hash(path)
            for defect in ("missing_from", "unknown_column"):
                tree = copy.deepcopy(controls()["view"])
                if defect == "missing_from":
                    tree.pop("from")
                else:
                    tree["columns"][0]["expr"] = {"column": "entries.absent"}
                with self.subTest(defect=defect):
                    result = execute(path, ["departments", "entries"], [{"name": "v", "select": tree}], [])
                    self.assertEqual(result["status"], "semantic_error")
            for tree in (controls()["view"], {"columns": [{"expr": {"literal": "absent"}, "as": "constant"}]}):
                self.assertEqual(execute(path, ["departments", "entries"],
                    [{"name": "v", "select": tree}], [])["status"], "ok")
            self.assertEqual(file_hash(path), original)

    @unittest.skipUnless(capabilities()["defensive"], "SQLite defensive controls required")
    def test_missing_from_or_public_alias_rejected_charged_and_not_submitted(self):
        config = replace(load_config(ROOT/"configs/sqlite-tool-compatibility.json"), model=RunConfig().model)
        manifest = build_manifest(config, ROOT)
        for defect in ("missing_from", "missing_alias"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                results = run_manifest(manifest, root, ROOT, backend=BadViewWorker(defect))
                view = next(r for r in results if r["task_id"] == "sqlite-tools-view")
                self.assertEqual(view["status"], "completed")
                self.assertFalse(view["success"])
                self.assertTrue(all(r["success"] for r in results if r is not view))
                state = read_json(root/"episodes"/view["episode_id"]/"checkpoint.json")
                self.assertFalse(state["store"]["artifacts"])
                messages = state["store"]["contexts"]["w0"]["messages"]
                errors = [json.loads(m["content"]) for m in messages if m["role"] == "user"]
                errors = [e for e in errors if e.get("error_code") == "invalid_view"]
                self.assertEqual(len(errors), 3)
                self.assertNotIn("expected", canonical(errors))
                self.assertNotIn("rows", canonical(errors))
                charges = [e for e in state["ledger"]["entries"] if e["kind"] == "sql_execution"]
                self.assertEqual(len(charges), 3)
                self.assertTrue(all(e["work"] > 0 for e in charges))

    @unittest.skipUnless(capabilities()["defensive"], "SQLite defensive controls required")
    def test_public_validation_does_not_reveal_wrong_values(self):
        config = replace(load_config(ROOT/"configs/sqlite-tool-compatibility.json"), model=RunConfig().model)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            results = run_manifest(build_manifest(config, ROOT), root, ROOT, backend=BadViewWorker("wrong_value"))
            view = next(r for r in results if r["task_id"] == "sqlite-tools-view")
            self.assertFalse(view["success"])
            store = read_json(root/"episodes"/view["episode_id"]/"checkpoint.json")["store"]
            self.assertTrue(store["artifacts"])
            messages = store["contexts"]["w0"]["messages"]
            self.assertNotIn("invalid_view", canonical(messages))
            self.assertTrue(any('"submit_required_artifact"' in m["content"] for m in messages if m["role"] == "assistant"))
