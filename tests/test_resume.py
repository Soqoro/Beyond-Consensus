import copy
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import RunConfig
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.experiments.manifest import build_manifest, episode_from, validate_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.runtime.episode import EpisodeEngine
from beyond_consensus.runtime.persistence import EpisodeJournal
from beyond_consensus.tasks.workflow import fixtures
from beyond_consensus.util import BCError, atomic_json, digest, read_json


class ResumeTests(unittest.TestCase):
    def test_grid_320_is_planned_only(self):
        config = RunConfig(task_count=20, seeds=(0, 1), shards=20)
        manifest = build_manifest(config, ROOT)
        self.assertEqual(manifest["planned_episodes"], 320)
        self.assertTrue(manifest["planned_only"])
        self.assertEqual(len({r["episode_id"] for r in manifest["episodes"]}), 320)
        self.assertEqual({r["shard"] for r in manifest["episodes"]}, set(range(20)))

    def test_manifest_rejects_modified_seed_and_shard(self):
        config = RunConfig(task_count=2, shards=2)
        original = build_manifest(config, ROOT)
        for name, value in (("evaluation_seed", 3), ("shard", 1), ("mode", "real_development")):
            bad = copy.deepcopy(original)
            bad["episodes"][0][name] = value
            with self.subTest(name=name), self.assertRaises(BCError):
                validate_manifest(bad)

    def test_sharding_completed_resume_and_missing_report(self):
        config = RunConfig(task_count=4, policies=("ordinary",), attacks=("clean",), shards=4)
        manifest = build_manifest(config, ROOT)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            rows = run_manifest(manifest, output, ROOT, shard=1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(aggregate(manifest, output)["statuses"]["missing"], 3)
            episode = output / "episodes" / rows[0]["episode_id"]
            events = (episode / "events.jsonl").read_bytes()
            class NoCalls(MockBackend):
                def generate(self, *args, **kwargs):
                    raise AssertionError("Completed episode reran")
            run_manifest(manifest, output, ROOT, shard=1, backend=NoCalls())
            self.assertEqual(events, (episode / "events.jsonl").read_bytes())
            self.assertEqual(len(list((episode / "attempts").glob("*.json"))), 1)

    def test_active_resume_preserves_budget_and_coalition(self):
        config = RunConfig(policies=("jit",), attacks=("withholding",))
        row = episode_from(build_manifest(config, ROOT)["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            journal = EpisodeJournal(Path(temp), row.episode_id)
            stop = [False]
            engine = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "first", lambda: stop[0])
            original = engine.boundary
            def interrupt(name):
                if name == "model_complete":
                    stop[0] = True
                original(name)
            engine.boundary = interrupt
            first = engine.run()
            self.assertEqual(first.status, "interrupted")
            checkpoint = read_json(journal.path / "checkpoint.json")
            next_engine = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "second")
            second = next_engine.run()
            self.assertTrue(second.success, second.error)
            self.assertGreater(second.costs["spent"], first.costs["spent"])
            self.assertEqual(list(next_engine.attacker.coalition), checkpoint["attacker"]["coalition"])

    def test_protocol_b_common_primary_and_equal_allowance(self):
        config = RunConfig(policies=("jit",), attacks=("withholding",))
        original = build_manifest(config, ROOT)
        row = episode_from(original["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = EpisodeJournal(root / "capture", row.episode_id)
            engine = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "capture")
            frozen = engine.freeze_primary()
            path = root / "fixed.json"
            atomic_json(path, frozen)
            diagnostic = replace(config, policies=("jit", "recovery"), protocol="B", fixed_state_file=str(path))
            manifest = build_manifest(diagnostic, ROOT)
            results = run_manifest(manifest, root / "diagnostic", ROOT)
            self.assertTrue(all(r["success"] for r in results))
            self.assertEqual({r["costs"]["cap"] for r in results}, {config.budget.repair_allowance})
            self.assertGreater(results[1]["costs"]["historical_work"], results[0]["costs"]["historical_work"])
            self.assertEqual(results[0]["provenance"]["plan"], results[1]["provenance"]["plan"])
            self.assertEqual(aggregate(manifest, root / "diagnostic")["interpretation"],
                             "equal_remaining_diagnostic_not_total_efficiency")
            self.assertGreater(aggregate(manifest, root / "diagnostic")["groups"]["recovery/withholding"]["historical_preparation_work"], 0)
            bad_path = root / "diagnostic/episodes" / results[0]["episode_id"] / "result.json"
            bad = read_json(bad_path)
            bad["protocol"] = "A"
            atomic_json(bad_path, bad)
            with self.assertRaises(BCError):
                aggregate(manifest, root / "diagnostic")

    def test_crash_inflight_charged_conservatively(self):
        config = RunConfig(policies=("ordinary",), attacks=("clean",))
        row = episode_from(build_manifest(config, ROOT)["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            journal = EpisodeJournal(Path(temp), row.episode_id)
            engine = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "first")
            engine.plan_primary()
            engine.ledger.reserve_call("primary", 100, 500)
            journal.checkpoint(engine.state("model_inflight"))
            restored = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "second")
            result = restored.run()
            self.assertTrue(result.success)
            self.assertTrue(result.costs["uncertain_work"])
            self.assertTrue(any(e.get("reserved_output_tokens") == 500 for e in result.costs["entries"]))

    def test_protocol_b_resume_during_preparation_keeps_repair_cap(self):
        config = RunConfig(policies=("jit",), attacks=("withholding",))
        row = episode_from(build_manifest(config, ROOT)["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = EpisodeJournal(root / "primary", row.episode_id)
            primary = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "capture")
            path = root / "fixed.json"
            atomic_json(path, primary.freeze_primary())
            diagnostic = replace(config, policies=("recovery",), protocol="B", fixed_state_file=str(path))
            diagnostic_row = episode_from(build_manifest(diagnostic, ROOT)["episodes"][0])
            journal = EpisodeJournal(root / "diagnostic", diagnostic_row.episode_id)
            stop = [False]
            engine = EpisodeEngine(fixtures()[0], diagnostic_row, diagnostic, MockBackend(), journal, "first", lambda: stop[0])
            original_boundary = engine.boundary
            def interrupted(name):
                if name == "model_complete" and engine.phase == "diagnostic_preparation":
                    stop[0] = True
                original_boundary(name)
            engine.boundary = interrupted
            self.assertEqual(engine.run().status, "interrupted")
            resumed = EpisodeEngine(fixtures()[0], diagnostic_row, diagnostic, MockBackend(), journal, "second")
            result = resumed.run()
            self.assertTrue(result.success, result.error)
            self.assertEqual(result.costs["cap"], config.budget.repair_allowance)
            self.assertGreater(result.costs["historical_work"], 0)
