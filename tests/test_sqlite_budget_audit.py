"""Budget audit is descriptive and cannot execute or publish reference answers."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("budget_audit",
    Path(__file__).resolve().parents[1] / "scripts/audit_sqlite_budget.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def task(kind="query", docs=None):
    artifact = {"kind": kind, "select": {
        "columns": [{"expr": {"column": "secret_column"}}], "from": {"table": "demo"}}}
    if kind == "view":
        artifact["name"] = "secret_view"
    return SimpleNamespace(id="demo-task", kind="sqlite_native", required_outputs=("unit",),
        metadata={"evaluation": {"unit": {"artifact": artifact}},
            "harness": {"tables": ["demo"], "documents": docs or {}}})


class BudgetAuditTests(unittest.TestCase):
    def test_reference_envelopes_and_report_separation(self):
        with patch("sqlite3.connect", side_effect=AssertionError("No SQL execution")):
            rows, texts = audit.inspect_tasks([task(), task("view")], 12)
        query, view = map(json.loads, texts)
        self.assertEqual(query["tool"], "run_read_query")
        self.assertEqual(view["tool"], "submit_view_definition")
        self.assertEqual(view["artifact_name"], "secret_view")
        self.assertEqual(view["permitted_artifact_versions"], {})
        self.assertLess(texts[1].index('"permitted_artifact_versions"'), texts[1].index('"select_sql"'))
        self.assertNotIn("secret_column", json.dumps(rows))
        self.assertNotIn("secret_view", json.dumps(rows))
        self.assertNotIn("reference_action_tokens", rows[0])

    def test_character_paging_and_catalogue_overhead(self):
        docs = {"schema": "é" * 4000, "columns": "x" * 4001,
            **{f"kb-{i}": "x" for i in range(63)}}
        rows, _ = audit.inspect_tasks([task(docs=docs)], 12)
        row = rows[0]
        self.assertEqual(row["public_document_pages"]["schema"], 1)
        self.assertEqual(row["public_document_pages"]["columns"], 2)
        self.assertEqual(row["full_catalogue_actions"], 2)
        self.assertEqual(row["document_page_slots_after_full_catalogue"], 6)
        self.assertEqual(row["actions_reading_schema_and_columns_once"], 9)

    def test_default_cli_stdlib_report_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp)/"data.json", Path(temp)/"audit.json"
            source.write_text("{}")
            argv = ["audit", "--data-manifest", str(source), "--output", str(output)]
            with patch.object(audit, "validate_data", return_value=[task()]), \
                    patch.object(audit.subprocess, "run", side_effect=AssertionError("No tokenizer by default")), \
                    patch("sys.argv", argv), patch("builtins.print"), patch("sys.stderr", new_callable=io.StringIO):
                audit.main()
                report = json.loads(output.read_text())
                self.assertEqual(report["token_measurement"], "unmeasured")
                self.assertFalse(report["sql_executed"])
                self.assertFalse(report["model_executed"])
                before = output.read_bytes()
                with self.assertRaises(SystemExit):
                    audit.main()
                self.assertEqual(output.read_bytes(), before)

    def test_optional_tokenizer_boundary_and_offline_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output, lock_path = [folder/name for name in ("data.json", "audit.json", "lock.json")]
            source.write_text("{}")
            hashes = {}
            for name in ("tokenizer.json", "tokenizer_config.json"):
                (folder/name).write_text("{}")
                hashes[name] = audit.file_hash(folder/name)
            lock_path.write_text(json.dumps({"revision": "demo", "tokenizer_revision": "demo",
                "model_path": temp, "tokenizer_path": temp, "metadata_hashes": hashes}))
            argv = ["audit", "--data-manifest", str(source), "--output", str(output),
                "--model-lock", str(lock_path), "--tokenizer-python", "/example/python"]
            result = SimpleNamespace(returncode=0, stdout=json.dumps({"counts": [767, 768], "cpu_seconds": 0.1}))
            with patch.object(audit, "validate_data", return_value=[task(), task("view")]), \
                    patch.object(audit.subprocess, "run", return_value=result) as run, \
                    patch("sys.argv", argv), patch("builtins.print"):
                audit.main()
            report = json.loads(output.read_text())
            self.assertEqual([r["content_plus_one_stop_fits"] for r in report["tasks"]], [True, False])
            self.assertEqual(report["tokenizer_process_cpu_seconds"], 0.1)
            self.assertEqual(run.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
            self.assertEqual(run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
            self.assertNotIn("secret_column", output.read_text())
            (folder/"tokenizer.json").write_text("changed")
            argv[argv.index("--output")+1] = str(folder/"second.json")
            with patch.object(audit, "validate_data", return_value=[task()]), \
                    patch.object(audit.subprocess, "run", side_effect=AssertionError("Must reject changed metadata")), \
                    patch("sys.argv", argv):
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    audit.main()


if __name__ == "__main__":
    unittest.main()
