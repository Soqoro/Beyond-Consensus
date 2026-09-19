"""Independent SQL tree controls; scripted CPU workers are not model results."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from tests.support import ROOT
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.models.base import Generation
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.runtime.sqlite_executor import capabilities
from beyond_consensus.tasks.sqlite_compatibility import tasks, expected
from beyond_consensus.util import BCError, canonical, read_json


def col(name):
    return {"column": name}


def controls():
    order = lambda name: [{"expr": col(name), "direction": "asc"}]
    return {
        "aggregate": {"columns": [{"expr": col("department_id")},
            {"expr": {"call": {"name": "sum", "args": [col("amount")]}}, "as": "total_amount"},
            {"expr": {"call": {"name": "count", "args": [col("id")]}}, "as": "entry_count"}],
            "from": {"table": "entries"}, "group_by": [col("department_id")], "order_by": order("department_id")},
        "join": {"columns": [{"expr": col("e.id"), "as": "entry_id"},
            {"expr": col("d.name"), "as": "department_name"}, {"expr": col("e.amount"), "as": "amount"}],
            "from": {"table": "entries", "as": "e"},
            "joins": [{"kind": "inner", "source": {"table": "departments", "as": "d"},
                "on": {"binary": ["=", col("e.department_id"), col("d.id")]}}], "order_by": order("e.id")},
        "case": {"columns": [{"expr": col("id")}, {"expr": {"case": {"when": [
            [{"binary": [">", col("amount"), {"literal": 0}]}, {"literal": "positive"}],
            [{"binary": ["<", col("amount"), {"literal": 0}]}, {"literal": "negative"}]],
            "else": {"literal": "zero"}}}, "as": "sign_label"}],
            "from": {"table": "entries"}, "order_by": order("id")},
        "view": {"columns": [{"expr": col("id")},
            {"expr": {"binary": ["+", col("amount"), {"literal": 3}]}, "as": "adjusted_amount"}],
            "from": {"table": "entries"}},
    }


class ScriptedWorker(MockBackend):
    def __init__(self, mutation=None):
        self.mutation = mutation

    def generate(self, messages, max_new_tokens, seed):
        observations = []
        for message in messages:
            if message["role"] == "user":
                observations.append(json.loads(message["content"]))
        request = next(o for o in observations if "assignment" in o)
        unit = request["assignment"]
        created = next((o for o in observations if "artifact_id" in o), None)
        if not any(o.get("tool") == "read_source" for o in observations):
            action = {"tool": "read_source", "name": unit}
        elif created:
            action = ({"tool": "read_source", "name": unit} if self.mutation == "no_submission" else
                {"tool": "submit_required_artifact", "artifact_id": created["artifact_id"]})
        else:
            probe = unit.removeprefix("sqlite-tools-")
            tree = copy.deepcopy(controls()[probe])
            if self.mutation == "wrong_value":
                tree["columns"][0]["expr"] = {"literal": 999}
            if self.mutation == "wrong_alias":
                tree["columns"][-1]["as"] = "incorrect"
            action = {"tool": "submit_view_definition" if probe == "view" else "run_read_query",
                "permitted_artifact_versions": {}, "select_sql": tree}
            if probe == "view":
                action["artifact_name"] = "entry_adjusted"
        text = canonical(action)
        return Generation(text, (len(text)+3)//4)


class SuiteTests(unittest.TestCase):
    def config(self):
        return replace(load_config(ROOT/"configs/sqlite-tool-compatibility.json"), model=RunConfig().model)

    def test_bounded_conditions_and_separate_regime(self):
        config = self.config()
        manifest = build_manifest(config, ROOT)
        self.assertEqual(len(manifest["episodes"]), 4)
        self.assertEqual(manifest["data_regime"]["adaptation"], "bc_sqlite_tool_compatibility_v1")
        self.assertEqual(manifest["data_regime"]["access_regime"], "synthetic_schema_supplied")
        for change in ({"task_count": 8}, {"attacks": ("clean", "withholding")},
                       {"policies": ("recovery",)}, {"seeds": (0,1)}, {"task_kind": "sqlite_native"}):
            with self.subTest(change=change), self.assertRaises(BCError):
                replace(config, **change)
        for task in tasks():
            self.assertFalse(task.metadata["harness"]["documents"])
            self.assertNotIn("select", task.sources[task.id])
            self.assertNotIn("evaluation", task.metadata)
            self.assertIn("Schema:", task.specification)
        self.assertEqual(expected("aggregate")[1], [[1,10,2],[2,0,2],[3,0,1]])
        # Existing arithmetic fixture configuration and contents still load.
        old = build_manifest(RunConfig(task_kind="sqlite_fixture", monitor_id="data-structure-v1"), ROOT)
        self.assertEqual(old["data_regime"]["adaptation"], "bc_sqlite_fixture_v1")

    @unittest.skipUnless(capabilities()["defensive"], "SQLite defensive controls required")
    def test_complete_episodes_positive_negative_and_submission_gate(self):
        manifest = build_manifest(self.config(), ROOT)
        for mutation in (None, "wrong_value", "wrong_alias", "no_submission"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                results = run_manifest(manifest, root, ROOT, backend=ScriptedWorker(mutation))
                self.assertEqual(len(results), 4)
                self.assertTrue(all(r["status"] == "completed" for r in results), results)
                self.assertEqual([r["success"] for r in results], [mutation is None]*4)
                self.assertTrue(all(r["costs"]["spent"] > 0 for r in results))
                report = aggregate(manifest, root)
                self.assertEqual(report["groups"]["single/clean"]["successes"], 4 if mutation is None else 0)
                for result in results:
                    checkpoint = read_json(root/"episodes"/result["episode_id"]/"checkpoint.json")
                    self.assertEqual(set(checkpoint["store"]["contexts"]), {"w0","w1","w2","w3"})
                    worker_text = canonical(checkpoint["store"]["contexts"])
                    self.assertNotIn("complete_task_success", worker_text)
                    self.assertNotIn("expected_rows", worker_text)
                    self.assertTrue(all(e.get("stage") != "final_evaluation"
                        for e in checkpoint["store"]["events"] if e["type"] == "generation_metadata"))


if __name__ == "__main__":
    unittest.main()
