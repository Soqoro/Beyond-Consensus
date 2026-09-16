"""CPU tests use fabricated data and injected sandbox responses, never host code."""
import base64
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.agents.coding import CodingWorker
from beyond_consensus.config import RunConfig, BudgetConfig
from beyond_consensus.models.base import Generation
from beyond_consensus.runtime.apptainer import (ApptainerSandbox, SandboxProfile, SandboxFailure,
    CHECKS, SCHEMA, approve, qualify, runtime_hash)
from beyond_consensus.runtime.budget import BudgetLedger, BudgetExceeded
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.runtime.repository import (CodingEnvironment, RepositorySession, apply_changes,
    copy_tree, inventory, relative)
from beyond_consensus.runtime.coding_episode import require_coding_e0
from beyond_consensus.schemas import TaskInstance
from beyond_consensus.util import BCError, atomic_json, digest, file_hash, plain


def change(text, executable=False):
    return {"data": base64.b64encode(text.encode()).decode(), "executable": executable}


@unittest.skipUnless(os.name == "posix", "Linux/POSIX repository sandbox filesystem checks")
class RepositoryTests(unittest.TestCase):
    def test_paths_links_special_files_and_git_history_rejected(self):
        for name in ("../home", "/home", "a/../b", ".git/config", "a/.git/objects/x", "a//b", "a\\b", ".env", "", "."):
            with self.subTest(name=name), self.assertRaises(BCError):
                relative(name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "normal").write_text("plain")
            (root / "link").symlink_to("normal")
            with self.assertRaises(BCError):
                inventory(root)
            (root / "link").unlink()
            os.link(root / "normal", root / "hard")
            with self.assertRaises(BCError):
                inventory(root)
            (root / "hard").unlink()
            os.mkfifo(root / "fifo")
            with self.assertRaises(BCError):
                inventory(root)

    def test_data_only_copy_and_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base"
            base.mkdir()
            (base / "program.py").write_text("THIS IS DATA; NEVER EXECUTE")
            before = inventory(base)
            with patch("subprocess.Popen", side_effect=AssertionError("host execution")):
                copy_tree(base, root / "candidate")
                apply_changes(root / "candidate", {"program.py": None, "src/new.py": change("also data", True)})
            self.assertEqual(inventory(base), before)
            self.assertEqual((root / "candidate/src/new.py").read_text(), "also data")
            self.assertTrue(inventory(root / "candidate")["src/new.py"]["executable"])

    def test_invalid_wire_changes_do_not_partially_mutate_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "keep").write_text("original")
            for invalid in ({"keep": change("changed"), "../escape": change("bad")},
                            {"keep": change("changed"), "new": {"data": "!!!", "executable": False}},
                            {"keep": change("changed"), "keep/child": change("bad")},
                            {"keep": {"data": "AA==", "executable": "yes"}}):
                with self.subTest(invalid=invalid), self.assertRaises((BCError, ValueError)):
                    apply_changes(root, invalid)
                self.assertEqual((root / "keep").read_text(), "original")


@unittest.skipUnless(os.name == "posix", "Linux/POSIX Apptainer profile checks")
class SandboxTests(unittest.TestCase):
    def setup_profile(self, root):
        runtime = root / "runtime"
        (runtime / "bin").mkdir(parents=True)
        (runtime / "bin/apptainer").write_text("UNIT TEST DATA - NOT AN EXECUTABLE")
        (runtime / "helper").write_text("helper")
        image = root / "unit-test.sif"
        image.write_text("UNIT TEST DATA - NOT A CONTAINER")
        return SandboxProfile(str(runtime), runtime_hash(runtime), str(image), file_hash(image), str(root / "scratch"))

    def test_only_readonly_explicit_mounts_and_no_gpu_or_host_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sandbox = ApptainerSandbox(self.setup_profile(root))
            argv = sandbox.argv(root / "request", root / "candidate")
            for flag in ("--userns", "--containall", "--cleanenv", "--no-home", "--no-eval", "--net", "--drop-caps"):
                self.assertIn(flag, argv)
            binds = [argv[i+1] for i, a in enumerate(argv) if a == "--bind"]
            self.assertTrue(all(b.endswith(":ro") for b in binds))
            self.assertFalse(any("evaluator" in b for b in binds))
            self.assertNotIn("--nv", argv)
            self.assertNotIn("--writable", argv)
            self.assertEqual(argv[-4:], [sandbox.profile.python, "-I", "-S", "/bc/guest.py"])
            eval_argv = sandbox.argv(root / "request", root / "candidate", root / "private")
            self.assertIn(f"{root}/private:/bc/evaluator:ro", eval_argv)

    def test_no_process_without_approval_and_no_qualification_command_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sandbox = ApptainerSandbox(self.setup_profile(root))
            with patch("subprocess.Popen", side_effect=AssertionError("must not launch")):
                with self.assertRaisesRegex(BCError, "approval"):
                    sandbox.run({"operation": "command", "argv": ["false"]}, root)
                with self.assertRaisesRegex(BCError, "fixed trusted probes"):
                    sandbox.run({"operation": "command", "argv": ["false"]}, root, qualification=True)

    def test_runtime_helper_and_image_changes_revoke_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self.setup_profile(root)
            profile.identity()
            (root / "runtime/helper").write_text("changed")
            with self.assertRaisesRegex(BCError, "runtime changed"):
                profile.identity()
            profile = replace(profile, runtime_sha256=runtime_hash(root / "runtime"))
            (root / "unit-test.sif").write_text("changed")
            with self.assertRaisesRegex(BCError, "image changed"):
                profile.identity()

    def test_approval_requires_every_check_and_explicit_review_and_matching_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self.setup_profile(root)
            report = {"schema": SCHEMA, "identity": profile.identity(), "checks": {k: True for k in CHECKS}, "passed": True}
            path = root / "report.json"
            atomic_json(path, report)
            with self.assertRaises(BCError):
                approve([path], "unit-test-reviewer", False, root / "approval.json")
            report["checks"]["descendant_cleanup"] = False
            atomic_json(path, report)
            with self.assertRaises(BCError):
                approve([path], "unit-test-reviewer", True, root / "approval.json")
            report["checks"]["descendant_cleanup"] = True
            atomic_json(path, report)
            approve([path], "unit-test-reviewer", True, root / "approval.json")
            sandbox = ApptainerSandbox(profile, root / "approval.json")
            with patch("beyond_consensus.runtime.apptainer.cgroup_parent", return_value=root):
                sandbox.require_approval()
                with patch("platform.node", return_value="different-node"), self.assertRaises(BCError):
                    sandbox.require_approval()

    def test_missing_cgroup_delegation_produces_failed_unapproved_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = self.setup_profile(root)
            with patch("beyond_consensus.runtime.apptainer.cgroup_parent", side_effect=BCError("no delegation")), \
                 patch("subprocess.Popen", side_effect=AssertionError("must not launch")):
                report = qualify(profile, root / "report.json")
            self.assertFalse(report["passed"])
            self.assertFalse(report["approved"])
            self.assertIn("no delegation", report["error"])

    def test_profile_rejects_bind_injection_and_unbounded_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.setup_profile(Path(tmp))
            for changes in ({"image": "/tmp/image,/home:/leak"}, {"pids": True}, {"memory_bytes": 0},
                            {"timeout_seconds": 999999}, {"runtime_sha256": "missing"}):
                with self.subTest(changes=changes), self.assertRaises(BCError):
                    replace(p, **changes)


class WorkerTests(unittest.TestCase):
    def task(self):
        return TaskInstance("unit-test-pair", "cooperbench", "group", "Two fabricated test features",
                            {"feature1": "public one", "feature2": "public two"}, ("feature1", "feature2"), ())

    def worker(self, texts, total=100000):
        class FakeBackend:
            def __init__(self):
                self.seen = []
            def count_input(self, messages):
                return len(json.dumps(messages))
            def generate(self, messages, max_new_tokens, seed):
                self.seen.append(json.dumps(messages))
                return Generation(texts[len(self.seen)-1], 10)
        class FakeProfile:
            timeout_seconds = 10
        class FakeEnvironment:
            profile = FakeProfile()
        class FakeSession:
            environment = FakeEnvironment()
            last_usage = {"input_tree_hash": "unit-test-base", "output_tree_hash": "unit-test-tree"}
            def __init__(self):
                self.calls = []
            def invoke(self, op, **args):
                self.calls.append((op, args))
                return {"public": "tool output"}
        config = RunConfig(policies=("single",), attacks=("clean",), budget=BudgetConfig(total=total))
        backend, session, store = FakeBackend(), FakeSession(), ProvenanceStore()
        ledger = BudgetLedger(total, config.budget)
        return CodingWorker(backend, config, ledger, store, session), backend, session

    def test_coding_actions_charged_and_both_public_features_in_one_context(self):
        worker, backend, session = self.worker(['{"tool":"list"}', '{"tool":"submit"}'])
        self.assertEqual(worker.run(self.task(), 2), ("submitted", True))
        self.assertEqual([x[0] for x in session.calls], ["list", "submit"])
        self.assertIn("public one", backend.seen[0])
        self.assertIn("public two", backend.seen[0])
        self.assertNotIn("unit-test-reviewer", backend.seen[0])
        self.assertEqual(set(worker.store.contexts), {"w0", "w1", "w2", "w3"})
        self.assertEqual(sum(e.get("model_calls", 0) for e in worker.ledger.entries), 2)
        self.assertEqual(sum(e["kind"] == "sandbox_tool" for e in worker.ledger.entries), 2)
        self.assertEqual(len(worker.store.artifacts), 1)

    def test_malformed_actions_charged_and_bounded_without_execution(self):
        worker, _, session = self.worker(['{tool:submit}']*3)
        self.assertEqual(worker.run(self.task(), 2), ("malformed", False))
        self.assertFalse(session.calls)
        self.assertGreater(worker.ledger.spent, 0)

    def test_budget_stops_before_model_or_container(self):
        worker, backend, session = self.worker(['{"tool":"submit"}'], total=1)
        with self.assertRaises(BudgetExceeded):
            worker.run(self.task(), 0)
        self.assertEqual(backend.seen, [])
        self.assertEqual(session.calls, [])

    def test_infrastructure_failure_not_swallowed_as_model_error(self):
        worker, backend, session = self.worker(['{"tool":"list"}'])
        with patch.object(session, "invoke", side_effect=SandboxFailure("cgroup failed")), self.assertRaises(SandboxFailure):
            worker.run(self.task(), 0)
        self.assertTrue(worker.ledger.entries[-1]["uncertain"])
        self.assertEqual(len(backend.seen), 1)

    def test_coding_policy_grid_cannot_silently_use_fixture_planner(self):
        with self.assertRaisesRegex(BCError, "clean single-agent"):
            require_coding_e0(RunConfig(task_kind="cooperbench"))


@unittest.skipUnless(os.name == "posix", "Linux/POSIX coding sandbox integration mocks")
class CodingIntegrationTests(unittest.TestCase):
    def setup_environment(self, root):
        from tests.test_adapters import CooperBenchTests
        from beyond_consensus.tasks.cooperbench import import_dataset
        from beyond_consensus.experiments.manifest import task_from
        from beyond_consensus.evaluation.cooperbench import validation_identity
        source = root / "dataset"
        source.mkdir()
        subset = CooperBenchTests().dataset(source)
        data = import_dataset(source, subset, "b"*40, "c"*40)
        data_path = root / "data.json"
        atomic_json(data_path, data)
        task = task_from(data["tasks"][0])
        profile = SandboxTests().setup_profile(root)
        Path(profile.scratch_root).mkdir()
        base = root / "base"
        base.mkdir()
        (base / "public.txt").write_text("fabricated source; never execute")
        env_path = root / "environment.json"
        unit_approval = {"unit_test_only": "not a real approval"}
        atomic_json(root / "approval.json", unit_approval)
        atomic_json(env_path, {"schema": "cooper-e0-environment-v1", "task_id": task.id,
            "task_hash": task.source_hash, "base_root": str(base), "base_files": inventory(base),
            "profile": plain(profile), "approval": str(root / "approval.json"), "reviewer": "unit-test-only",
            "approval_hash": digest(unit_approval),
            "source_review": True, "suites": {f: ["/bin/false"] for f in task.required_outputs}})
        environment = CodingEnvironment(env_path)
        validation_path = root / "validation.json"
        report = {"schema": "cooper-e0-validation-v1", **validation_identity(environment, task), "passed": True,
                  "baseline": {"feature_suites": {f: {"passed": False, "returncode": 1} for f in task.required_outputs}},
                  "positive": {"feature_suites": {f: {"passed": True, "returncode": 0} for f in task.required_outputs}}}
        atomic_json(validation_path, report)
        config = RunConfig(task_kind="cooperbench", policies=("single",), attacks=("clean",),
            monitor_id="coding-structure-v1",
            data_manifest=str(data_path), coding_environment=str(env_path), coding_environment_hash=environment.hash,
            coding_validation=str(validation_path), coding_validation_hash=digest(report))
        return environment, task, config

    def test_joint_evaluation_hidden_files_never_in_worker_mount_and_terminal_resume(self):
        from beyond_consensus.experiments.manifest import build_manifest
        from beyond_consensus.experiments.runner import run_manifest
        class Backend:
            def count_input(self, messages):
                assert "SECRET" not in json.dumps(messages)
                return 100
            def generate(self, *args):
                return Generation('{"tool":"submit"}', 10)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, task, config = self.setup_environment(root)
            manifest = build_manifest(config, ROOT, [task])
            calls = []
            def execute(request, input_tree, evaluator=None, **kwargs):
                calls.append(request["operation"])
                self.assertEqual(set(inventory(input_tree)), {"public.txt"})
                if request["operation"] == "evaluate":
                    self.assertIsNotNone(evaluator)
                    names = set(inventory(evaluator))
                    self.assertEqual(names, {"feature1.patch", "feature2.patch", "run_tests.sh", "runner.sh"})
                    self.assertEqual(set(request["suites"]), {"feature1", "feature2"})
                    self.assertEqual(request["reference_patches"], [])
                    payload = {"evaluation": {"feature1": {"returncode": 0}, "feature2": {"returncode": 1}}}
                else:
                    self.assertIsNone(evaluator)
                    payload = {"observation": {"submitted": True}, "changes": {}}
                return {"returncode": 0, "failure": None, "stdout": json.dumps(payload), "stderr": "",
                        "wall_seconds": 0.25, "limits": {}, "cleanup": True}
            with patch.object(ApptainerSandbox, "require_approval"), patch.object(ApptainerSandbox, "run", side_effect=execute):
                results = run_manifest(manifest, root / "run", ROOT, backend=Backend())
                self.assertEqual(results[0]["status"], "completed")
                self.assertIs(results[0]["success"], False)
                self.assertEqual(calls, ["submit", "evaluate"])
                self.assertTrue(results[0]["metrics"]["final_evaluation"]["joint_candidate"])
                self.assertGreater(results[0]["costs"]["stages"]["evaluation"], 0)
                run_manifest(manifest, root / "run", ROOT, backend=Backend())
                self.assertEqual(calls, ["submit", "evaluate"])

    def test_evaluator_failure_retry_never_returns_to_model(self):
        from beyond_consensus.experiments.manifest import build_manifest
        from beyond_consensus.experiments.runner import run_manifest
        class Backend:
            calls = 0
            def count_input(self, messages):
                return 100
            def generate(self, *args):
                self.calls += 1
                return Generation('{"tool":"submit"}', 10)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, task, config = self.setup_environment(root)
            manifest = build_manifest(config, ROOT, [task])
            backend = Backend()
            evaluations = []
            def execute(request, *_args, **_kwargs):
                if request["operation"] == "evaluate":
                    evaluations.append(request)
                    if len(evaluations) == 1:
                        raise SandboxFailure("unit-test interrupted evaluation")
                    payload = {"evaluation": {f: {"returncode": 0} for f in task.required_outputs}}
                else:
                    payload = {"observation": {}, "changes": {}}
                return {"returncode": 0, "failure": None, "stdout": json.dumps(payload), "stderr": "",
                        "wall_seconds": 0.25, "limits": {}, "cleanup": True}
            with patch.object(ApptainerSandbox, "require_approval"), patch.object(ApptainerSandbox, "run", side_effect=execute):
                first = run_manifest(manifest, root / "run", ROOT, backend=backend)[0]
                self.assertEqual(first["status"], "infrastructure_failed")
                self.assertIsNone(first["success"])
                second = run_manifest(manifest, root / "run", ROOT, backend=backend, retry_failures=True)[0]
                self.assertTrue(second["success"])
                self.assertEqual(backend.calls, 1)
                self.assertGreater(second["costs"]["spent"], first["costs"]["spent"])

    def test_validation_rejects_vacuous_test_driver_and_stale_environment(self):
        from beyond_consensus.evaluation.cooperbench import validate_environment, require_environment_validation
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, task, config = self.setup_environment(root)
            always_passes = {"complete_task_success": True,
                             "feature_suites": {f: {"passed": True} for f in task.required_outputs}}
            with patch("beyond_consensus.evaluation.cooperbench.evaluate", return_value=always_passes):
                report = validate_environment(env, task, config.data_manifest, root / "vacuous.json")
            self.assertFalse(report["passed"])
            with self.assertRaises(BCError):
                require_environment_validation(root / "vacuous.json", digest(report), env, task)
            (env.base / "public.txt").write_text("modified")
            with self.assertRaisesRegex(BCError, "base tree changed"):
                CodingEnvironment(env.path, env.hash)

    def test_renamed_reference_patch_cannot_enter_worker_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, task, _ = self.setup_environment(Path(tmp))
            (env.base / "innocent.txt").write_text("SECRET_REFERENCE")
            data = json.loads(env.path.read_text())
            data["base_files"] = inventory(env.base)
            atomic_json(env.path, data)
            with self.assertRaisesRegex(BCError, "hidden test/reference"):
                CodingEnvironment(env.path).validate_task(task)

    def test_infrastructure_recheck_is_fatal_not_a_model_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _, _ = self.setup_environment(root)
            session = RepositorySession(env, root / "candidate")
            session.initialize()
            with patch.object(ApptainerSandbox, "run", side_effect=BCError("image changed")), self.assertRaises(SandboxFailure):
                session.invoke("list")

    def test_older_serialized_fixture_manifests_remain_readable(self):
        from beyond_consensus.experiments.manifest import build_manifest, validate_manifest
        from beyond_consensus.tasks.workflow import fixtures
        config = RunConfig()
        manifest = build_manifest(config, ROOT, fixtures(1))
        for field in ("coding_environment", "coding_environment_hash", "coding_validation", "coding_validation_hash"):
            manifest["config"].pop(field)
        manifest["config_hash"] = digest(manifest["config"])
        manifest["experiment_id"] = digest([manifest["source_revision"], manifest["config_hash"], manifest["data_hash"],
            manifest["model_hash"], manifest["fixed_state_hash"], manifest["calibration_hash"]])
        for row in manifest["episodes"]:
            row["config_hash"] = manifest["config_hash"]
            row["experiment_id"] = manifest["experiment_id"]
            row["episode_id"] = digest([manifest["experiment_id"], digest(manifest["tasks"][0]), row["policy"], row["attack"]["family"], row["seed"]])
        validate_manifest(manifest)


@unittest.skipUnless(os.environ.get("BC_SANDBOX_TEST_PROFILE"),
                     "Real container/cgroup qualification requires explicit BC_SANDBOX_TEST_PROFILE")
class RealSandboxTests(unittest.TestCase):
    def test_actual_isolation_and_cleanup(self):
        profile = SandboxProfile.load(Path(os.environ["BC_SANDBOX_TEST_PROFILE"]))
        with tempfile.TemporaryDirectory() as tmp:
            report = qualify(profile, Path(tmp) / "report.json")
            self.assertTrue(report["passed"], json.dumps(report))
