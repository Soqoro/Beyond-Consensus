import copy
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import ModelConfig, RunConfig
from beyond_consensus.experiments.export import export_bundle, sanitize
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.models.staging import stage_model, resolve_model_config
from beyond_consensus.models.transformers_backend import TransformersBackend, require_allocation
from beyond_consensus.planning.calibration import calibrate
from beyond_consensus.planning.costs import estimates
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.runtime.sandbox import capabilities, require_repository_sandbox
from beyond_consensus.tasks.cooperbench import import_dataset, validate_manifest
from beyond_consensus.tasks.workflow import fixtures
from beyond_consensus.util import BCError, atomic_json


class CooperBenchTests(unittest.TestCase):
    def dataset(self, root):
        # Schema-only fabricated content, explicitly a unit-test fixture. The adapter
        # derives every ID/path from this input; this is never shipped as real data.
        task = root / "schema_fixture/task7"
        task.mkdir(parents=True)
        (task / "setup.sh").write_text('BASE_COMMIT="'+"a"*40+'"\ngit clone https://github.com/example/schema-fixture "$REPO_NAME"\n')
        for name in ("Dockerfile", "runner.sh", "run_tests.sh"):
            (task / name).write_text("NEVER EXECUTE - schema unit test\n")
        for number in (1, 2, 3):
            feature = task / f"feature{number}"
            feature.mkdir()
            (feature / "feature.md").write_text(f"Public contract {number}")
            (feature / "feature.patch").write_text("SECRET_REFERENCE")
            (feature / "tests.patch").write_text("SECRET_TEST")
        subset = root / "subset.json"
        atomic_json(subset, {"name": "schema_test", "tasks": [
            {"repo": "schema_fixture", "task_id": 7, "pairs": [[1, 2], [1, 3]]}]})
        return subset

    def test_actual_schema_both_features_and_hidden_separation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subset = self.dataset(root)
            with patch("subprocess.run", side_effect=AssertionError("No repository code execution")):
                data = import_dataset(root, subset, "b"*40, "c"*40)
            self.assertEqual(len(data["tasks"]), 2)
            first, second = data["tasks"]
            self.assertEqual(first["group"], second["group"])
            self.assertEqual(first["required_outputs"], ["feature1", "feature2"])
            self.assertNotIn("SECRET", json.dumps(first["sources"]))
            self.assertEqual(first["metadata"]["base_commit"], "a"*40)
            path = root / "manifest.json"
            atomic_json(path, data)
            self.assertEqual(len(validate_manifest(path)), 2)
            (root / "schema_fixture/task7/feature2/tests.patch").write_text("changed")
            with self.assertRaisesRegex(BCError, "changed"):
                validate_manifest(path)

    def test_missing_feature_unknown_base_and_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subset = self.dataset(root)
            for entry in ({"repo": "../escape", "task_id": 7, "pairs": [[1, 2]]},
                          {"repo": "schema_fixture", "task_id": 7, "pairs": [[1, 99]]},
                          {"repo": "schema_fixture", "task_id": 7, "pairs": [[1, 1]]}):
                atomic_json(subset, {"tasks": [entry]})
                with self.subTest(entry=entry), self.assertRaises(BCError):
                    import_dataset(root, subset, "b"*40, "c"*40)


class SafetyAndModelTests(unittest.TestCase):
    def test_repository_execution_fails_closed_despite_container_command(self):
        with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run", side_effect=AssertionError("host fallback")):
            self.assertFalse(capabilities()["repository_execution"])
            with self.assertRaisesRegex(BCError, "No approved repository sandbox"):
                require_repository_sandbox()

    @unittest.skip("Repository isolation integration unavailable: no approved sandbox adapter or site isolation attestation exists")
    def test_real_sandbox_network_home_credentials_mount_and_evaluator_isolation(self):
        # This integration cannot honestly certify isolation by mocking a capability flag.
        require_repository_sandbox()

    def test_gpu_loading_blocked_before_torch_import(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(BCError, "Slurm GPU allocation"):
                TransformersBackend(ModelConfig(backend="transformers"), None)
        self.assertNotIn("torch", sys.modules)

    def test_backend_initialization_failure_is_an_infrastructure_row(self):
        from dataclasses import replace
        config = RunConfig(policies=("ordinary",), attacks=("clean",), model=ModelConfig(
            backend="transformers", revision="a"*40, tokenizer_revision="a"*40))
        manifest = build_manifest(config, ROOT)
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            rows = run_manifest(manifest, Path(temp), ROOT)
            self.assertEqual(rows[0]["status"], "infrastructure_failed")
            self.assertIsNone(rows[0]["success"])
            self.assertIn("Slurm GPU allocation", rows[0]["error"])

    def test_explicit_staging_dry_run_does_not_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "models"
            result = stage_model(ModelConfig(), root, dry_run=True)
            self.assertFalse(result["downloaded"])
            self.assertFalse(root.exists())

    def test_revision_lock_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "model-lock.json"
            atomic_json(path, {"schema": "bc-model-lock-v1", "checkpoint": "Qwen/Qwen3.5-4B",
                               "revision": "a"*40, "tokenizer_revision": "b"*40})
            resolved = resolve_model_config(ModelConfig(), path)
            self.assertEqual(resolved.revision, "a"*40)
            self.assertEqual(resolved.tokenizer_revision, "b"*40)
            with self.assertRaises(BCError):
                resolve_model_config(ModelConfig(revision="c"*40), path)

    def test_cli_without_site_packages_or_gpu_libraries(self):
        result = subprocess.run([sys.executable, "-I", "-S", str(ROOT / "scripts/bc.py"), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Beyond Consensus", result.stdout)


class CalibrationAndExportTests(unittest.TestCase):
    def test_measured_calibration_and_group_disjointness(self):
        config = RunConfig()
        measured = calibrate(config, MockBackend(), fixtures())
        self.assertEqual(measured["calibration"]["sample_count"], 12)
        self.assertGreater(measured["calibration"]["costs"]["prepared"], measured["calibration"]["costs"]["cold"])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "calibration.json"
            atomic_json(path, measured["calibration"])
            from dataclasses import replace
            configured = replace(config, calibration_file=str(path))
            with self.assertRaisesRegex(BCError, "overlap"):
                estimates(configured, MockBackend(), fixtures()[0])
            self.assertEqual(estimates(configured, MockBackend(), fixtures(3)[2]).calibration_id,
                             measured["calibration"]["id"])

    def test_sanitized_allowlist_export_excludes_raw_state_and_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "run"
            config = RunConfig(policies=("ordinary",), attacks=("clean",))
            manifest = build_manifest(config, ROOT)
            run_manifest(manifest, output, ROOT)
            (output / ".env").write_text("HF_TOKEN=hf_credential_should_not_leave")
            bundle = root / "bundle.tar.gz"
            export_bundle(output, bundle)
            with tarfile.open(bundle) as archive:
                self.assertEqual(set(archive.getnames()), {"summary.json", "manifest.json", "results.json", "failures.json"})
                raw = b"".join(archive.extractfile(member).read() for member in archive.getmembers())
                self.assertNotIn(b"credential_should_not_leave", raw)
                self.assertNotIn(b"lower_bound", raw)
            self.assertEqual(sanitize({"authorization": "anything"})["authorization"], "[REDACTED]")
            self.assertNotIn("secretvalue", sanitize("token=secretvalue"))
            self.assertNotIn("credential", sanitize("hf_credential"))
