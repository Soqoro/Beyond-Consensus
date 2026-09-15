import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import ModelConfig, RunConfig
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot
from beyond_consensus.util import BCError, atomic_json, plain


def site_config(root):
    return cluster.ClusterConfig("NH100q", "01:00:00", 32, sys.executable,
        str(root / "storage"), str(root / "cache"), str(root / "snapshots"), str(root / "outputs"))


class GuardTests(unittest.TestCase):
    def test_resource_arguments_and_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = site_config(root)
            args = cluster.sbatch_arguments(config, root / "snapshot space", root / "output space", [0, 1, 2, 3], 4)
            for value in ("--partition=NH100q", "--nodes=1", "--ntasks=1", "--cpus-per-task=4",
                          "--gres=gpu:1", "--array=0-3%4", "--mem=32G"):
                self.assertIn(value, args)
            self.assertTrue(any("%A_%a.out" in x for x in args))
            self.assertFalse(any("nodelist" in x for x in args))
            self.assertIn(str(root / "snapshot space/experiments/run_shard.sbatch"), args)
            for concurrency in (0, 5, True):
                with self.assertRaises(BCError):
                    cluster.sbatch_arguments(config, root, root, [0], concurrency)

    def test_overlap_unknown_and_explicit_serialization(self):
        with patch.object(cluster, "active_gpu_jobs", return_value={"12_0": 1}), patch.object(cluster, "terminal_accounting", return_value=False):
            registry = {"jobs": [{"job_id": "12"}]}
            with self.assertRaisesRegex(BCError, "Overlapping"):
                cluster.guard(registry)
            self.assertEqual(cluster.guard(registry, serialize=True), ["12"])
            with self.assertRaisesRegex(BCError, "Other/unknown"):
                cluster.guard({"jobs": []}, serialize=True)
        with self.assertRaisesRegex(BCError, "uncertain"):
            cluster.guard({"uncertain_submission": True})

    def test_unknown_tres_fails_closed(self):
        def fake(argv):
            return "12" if argv[0] == "squeue" else "JobId=12 JobState=RUNNING"
        with patch.object(cluster, "command", side_effect=fake), self.assertRaisesRegex(BCError, "Unknown GPU accounting"):
            cluster.active_gpu_jobs()

    def test_typed_gpu_tres_not_double_counted(self):
        def fake(argv):
            return "12" if argv[0] == "squeue" else "JobId=12 ReqTRES=cpu=4,mem=32G,gres/gpu=1,gres/gpu:h100=1"
        with patch.object(cluster, "command", side_effect=fake):
            self.assertEqual(cluster.active_gpu_jobs(), {"12": 1})

    def test_cpu_jobs_are_accounted_without_blocking(self):
        def fake(argv):
            return "12" if argv[0] == "squeue" else "JobId=12 ReqTRES=cpu=4,mem=32G,node=1"
        with patch.object(cluster, "command", side_effect=fake):
            self.assertEqual(cluster.active_gpu_jobs(), {})

    def test_site_limits_are_not_invented(self):
        with tempfile.TemporaryDirectory() as temp:
            config = site_config(Path(temp))
            with patch.object(cluster, "command", return_value="PartitionName=NH100q MaxTime=00:30:00"):
                with self.assertRaisesRegex(BCError, "time exceeds"):
                    cluster.validate_site(config)
            with patch.object(cluster, "command", side_effect=["PartitionName=NH100q MaxTime=02:00:00", "16000"]):
                with self.assertRaisesRegex(BCError, "host RAM"):
                    cluster.validate_site(config)

    def test_batch_preserves_visibility_and_removes_editable_import_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            atomic_json(root / "resolved/cluster.json", site_config(root))
            atomic_json(root / "resolved/environment.json", {})
            with patch.object(cluster, "verify_snapshot"), patch.dict(os.environ, {
                "SLURM_JOB_ID": "123", "SLURM_ARRAY_TASK_ID": "2", "CUDA_VISIBLE_DEVICES": "GPU-assigned-uuid",
                "PYTHONPATH": "/mutable/checkout"}), patch.object(cluster, "environment_inventory", return_value={}), \
                patch.object(os, "execvpe", side_effect=RuntimeError("exec intercepted")) as execute:
                with self.assertRaisesRegex(RuntimeError, "intercepted"):
                    cluster.batch(root, root / "out", "run", False)
                executable, argv, env = execute.call_args.args
                self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "GPU-assigned-uuid")
                self.assertNotIn("PYTHONPATH", env)
                self.assertIn("-I", argv)
                self.assertIn(str(root / "scripts/bc.py"), argv)
                self.assertEqual(env["HF_HUB_OFFLINE"], "1")

    def test_shared_registry_rejects_second_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = site_config(root)
            run_config = RunConfig(model=ModelConfig(backend="transformers", revision="a"*40, tokenizer_revision="a"*40))
            manifest = build_manifest(run_config, ROOT)
            lock = {"revision": "a"*40}
            submitted = [False]
            def fake(argv):
                if argv[0] == "squeue":
                    return "123_0" if submitted[0] else ""
                if argv[:3] == ["scontrol", "show", "job"]:
                    return "JobId=123_0 ReqTRES=cpu=4,gres/gpu=1"
                if argv[:3] == ["scontrol", "show", "partition"]:
                    return "PartitionName=NH100q MaxTime=02:00:00"
                if argv[0] == "sinfo":
                    return "131072"
                if argv[0] == "sbatch":
                    if "--test-only" in argv:
                        return ""
                    submitted[0] = True
                    return "123"
                raise AssertionError(argv)
            with patch.object(cluster, "registry_root", return_value=root / "registry"), \
                 patch.object(cluster, "command", side_effect=fake), \
                 patch.object(cluster, "create_snapshot", return_value=root / "snapshot"), \
                 patch.dict(os.environ, {}, clear=True):
                first = cluster.submit(ROOT, config, manifest, lock, 4)
                self.assertTrue(first["submitted"])
                with self.assertRaisesRegex(BCError, "Overlapping"):
                    cluster.submit(ROOT, config, manifest, lock, 4)
                self.assertTrue((Path(first["output"]) / "logs").is_dir())


@unittest.skipUnless(shutil.which("git"), "Git executable missing; immutable archive tests require Git")
class SnapshotTests(unittest.TestCase):
    def test_commit_archive_survives_checkout_changes_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            (repo / "src").mkdir(parents=True)
            (repo / "src/example.py").write_text("version = 1\n")
            for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                          "commit", "-qm", "test snapshot"]):
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
            manifest = build_manifest(RunConfig(), repo)
            snapshot = create_snapshot(repo, root / "snapshots", manifest, {}, {})
            self.assertTrue(verify_snapshot(snapshot)["commit"])
            (repo / "src/example.py").write_text("version = 2\n")
            self.assertEqual((snapshot / "src/example.py").read_text(), "version = 1\n")
            verify_snapshot(snapshot)
            path = snapshot / "src/example.py"
            path.chmod(0o644)
            path.write_text("version = 3\n")
            with self.assertRaisesRegex(BCError, "changed"):
                verify_snapshot(snapshot)
            # Restore permissions for portable TemporaryDirectory cleanup.
            snapshot.chmod(0o755)
            for path in snapshot.rglob("*"):
                path.chmod(0o755 if path.is_dir() else 0o644)


@unittest.skipUnless(shutil.which("bash") and os.name != "nt", "POSIX Bash scheduler-command fixture requires Linux/WSL")
class ShellTests(unittest.TestCase):
    def test_all_help_and_shell_syntax(self):
        paths = [*ROOT.glob("experiments/*.sh"), *ROOT.glob("experiments/*.sbatch"), *ROOT.glob("scripts/*.sh")]
        for path in paths:
            with self.subTest(script=path.name):
                subprocess.run(["bash", "-n", str(path)], check=True)
                output = subprocess.check_output(["bash", str(path), "--help"], text=True)
                self.assertIn("Usage:", output)

    def test_submission_dry_run_with_mock_scheduler_and_quoted_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mock_bin = root / "bin"
            mock_bin.mkdir()
            for name, output in {"squeue": "", "scontrol": "PartitionName=NH100q MaxTime=02:00:00", "sinfo": "131072"}.items():
                path = mock_bin / name
                path.write_text("#!/bin/sh\nprintf '%s\\n' '" + output + "'\n")
                path.chmod(0o755)
            config = replace(site_config(root), output_root=str(root / 'output spaces $(touch SHOULD_NOT_EXIST)'))
            config_path = root / "cluster settings.json"
            atomic_json(config_path, config)
            run_config = RunConfig(shards=4, model=ModelConfig(backend="transformers", revision="a"*40, tokenizer_revision="a"*40))
            manifest = build_manifest(run_config, ROOT)
            atomic_json(root / "manifest.json", manifest)
            atomic_json(root / "model.json", {"revision": "a"*40})
            bootstrap = root / "isolated-test-python"
            bootstrap.write_text(f'#!{sys.executable}\nimport sys, os\nfrom pathlib import Path\n'
                f'sys.path.insert(0, {str(ROOT / "src")!r})\n'
                'from beyond_consensus.experiments import cluster\n'
                'cluster.registry_root = lambda: Path(os.environ["BC_TEST_REGISTRY"])\n'
                'from beyond_consensus.cli import main\nraise SystemExit(main(sys.argv[2:]))\n')
            bootstrap.chmod(0o755)
            env = {**os.environ, "PATH": str(mock_bin)+os.pathsep+os.environ["PATH"], "BC_PYTHON": str(bootstrap),
                   "BC_TEST_REGISTRY": str(root / "registry")}
            env.pop("SLURM_JOB_ID", None)
            result = subprocess.run(["bash", str(ROOT / "experiments/submit_pilot.sh"), "--cluster", str(config_path),
                "--manifest", str(root / "manifest.json"), "--model-lock", str(root / "model.json"),
                "--concurrency", "4", "--dry-run"], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertFalse(data["submitted"])
            self.assertIn("--array=0-3%4", data["argv"])
            self.assertFalse((root / "output spaces $(touch SHOULD_NOT_EXIST)").exists())
            self.assertFalse((ROOT / "SHOULD_NOT_EXIST").exists())

    def test_batch_dry_run_and_nonzero_exit(self):
        result = subprocess.run(["bash", str(ROOT / "experiments/run_shard.sbatch"), "/snapshot with spaces",
            "/output with spaces", "run", "resume", sys.executable, "--dry-run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("preserved", result.stdout)
        bad = subprocess.run(["bash", str(ROOT / "experiments/run_shard.sbatch"), "/s", "/o", "bad", "resume", sys.executable], capture_output=True)
        self.assertNotEqual(bad.returncode, 0)
