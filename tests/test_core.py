import copy
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tests.support import ROOT
from beyond_consensus.config import BudgetConfig, RunConfig, ModelConfig, from_dict
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.runtime.budget import BudgetLedger, BudgetExceeded
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.runtime.persistence import EpisodeJournal
from beyond_consensus.runtime.episode import EpisodeEngine
from beyond_consensus.experiments.manifest import build_manifest, episode_from
from beyond_consensus.tasks.workflow import fixtures, interpret
from beyond_consensus.util import BCError, digest


class BudgetTests(unittest.TestCase):
    def test_all_work_and_uncertain_retries(self):
        ledger = BudgetLedger(1000)
        ledger.charge("preparation", 100, kind="tool")
        first = ledger.reserve_call("primary", 50, 100)
        self.assertEqual(ledger.remaining, 750)
        ledger.reconcile(first, output_tokens=20, reasoning_tokens=10)
        second = ledger.reserve_call("repair", 50, 100)
        ledger.reconcile(second, output_tokens=None, failed=True)
        self.assertEqual(ledger.spent, 320)
        self.assertTrue(ledger.summary()["uncertain_work"])
        unprepared = BudgetLedger(1000)
        self.assertEqual(unprepared.remaining-ledger.remaining, 320)

    def test_total_cap_and_protocol_b_history(self):
        ledger = BudgetLedger(100)
        ledger.charge("preparation", 75, kind="tool")
        with self.assertRaises(BudgetExceeded):
            ledger.reserve_call("repair", 10, 20)
        ledger.start_repair_diagnostic(100)
        self.assertEqual(ledger.remaining, 100)
        self.assertEqual(ledger.summary()["historical_work"], 75)

    def test_strict_config(self):
        for data in ({"typo": 1}, {"shards": True}, {"protocol": "B"},
                     {"policies": ["single"], "attacks": ["withholding"]},
                     {"model": {"revision": "main"}}, {"confirmatory": True}):
            with self.subTest(data=data), self.assertRaises(BCError):
                from_dict(data)


class ProvenanceTests(unittest.TestCase):
    def test_message_rewrite_and_descendants(self):
        store = ProvenanceStore()
        store.save_context("w1")
        first = store.submit("w0", "u0", {"text": "outline"})
        store.message("w0", "w1", "rewrite this outline")
        second = store.submit("w1", "u1", "rewritten")
        store.read("w2", second.id)
        third = store.submit("w2", "u2", "later")
        unrelated = store.submit("w3", "u3", "unrelated")
        self.assertIn("w0", second.contributors)
        self.assertEqual(store.invalidate({first.id}), {first.id, second.id, third.id})
        self.assertTrue(unrelated.valid)
        self.assertEqual(store.contexts["w1"].reads, set())

    def test_missing_records_fail(self):
        store = ProvenanceStore()
        with self.assertRaises(BCError):
            store.declared_reads("w0", None)
        with self.assertRaises(BCError):
            store.submit("w0", "u", {})


class EpisodeTests(unittest.TestCase):
    def test_clean_single_agent_retains_one_full_context(self):
        config = RunConfig(policies=("single",), attacks=("clean",))
        row = episode_from(build_manifest(config, ROOT)["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            journal = EpisodeJournal(Path(temp), row.episode_id)
            engine = EpisodeEngine(fixtures()[0], row, config, MockBackend(), journal, "single")
            result = engine.run()
            self.assertTrue(result.success, result.error)
            self.assertEqual({a.author for a in engine.store.artifacts.values()}, {"w0"})
            assignments = [m for m in engine.store.contexts["w0"].messages if m["content"].startswith('{"assignment":')]
            self.assertEqual(len(assignments), 4)

    def test_complete_episodes_all_policies_and_attacks(self):
        config = RunConfig(task_count=1, attacks=("clean", "withholding", "artifact_sabotage"))
        manifest = build_manifest(config, ROOT)
        with tempfile.TemporaryDirectory() as temp:
            for row in manifest["episodes"]:
                with self.subTest(policy=row["policy"], attack=row["attack"]["family"]):
                    episode = episode_from(row)
                    journal = EpisodeJournal(Path(temp), episode.episode_id)
                    engine = EpisodeEngine(fixtures()[0], episode, config, MockBackend(), journal, journal.begin(digest(episode)))
                    result = engine.run()
                    self.assertEqual(result.status, "completed", result.error)
                    self.assertIs(result.success, True, result.error)
                    self.assertGreater(result.costs["spent"], 0)

    def test_interpreter_rejects_code(self):
        for value in ("__import__('os')", {"steps": [{"op": "shell", "value": 1}]},
                      {"steps": [{"op": "mul", "value": float("inf")}]},
                      {"steps": [{"op": "add", "value": True}]}):
            with self.subTest(value=value), self.assertRaises((BCError, ValueError)):
                interpret(value, 1)


if __name__ == "__main__":
    unittest.main()
