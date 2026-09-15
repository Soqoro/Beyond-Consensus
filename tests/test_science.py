import inspect
import itertools
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.agents.worker import WorkerLoop
from beyond_consensus.attacks.fixed import AttackController
from beyond_consensus.config import RunConfig
from beyond_consensus.evaluation.hidden import evaluate
from beyond_consensus.evaluation import monitor
from beyond_consensus.experiments.manifest import build_manifest, episode_from, grouped_split, validate_splits
from beyond_consensus.models.base import Generation
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.planning.allocation import shortest_schedule, solve_allocation
from beyond_consensus.planning.costs import CostEstimates
from beyond_consensus.policies.core import catalogue, choose_plan, common_units
from beyond_consensus.runtime.budget import BudgetLedger
from beyond_consensus.runtime.episode import EpisodeEngine
from beyond_consensus.runtime.persistence import EpisodeJournal
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.schemas import Alarm, AttackSpec, DelegationPlan, RecoveryRoute, WORKERS
from beyond_consensus.tasks.workflow import fixtures
from beyond_consensus.util import BCError, digest


def exhaustive(routes, available, targets, excluded, cap):
    """Independent permutation oracle, no shortest-path pruning or state memoization."""
    best = None
    for length in range(len(routes)+1):
        for order in itertools.permutations(routes, length):
            assets, cost = set(available), 0
            for r in order:
                if (r.executor in excluded or set(r.contributors) & excluded
                        or not (set(r.prerequisites) | set(r.preparation)) <= assets):
                    break
                assets.update(r.produces)
                cost += r.predicted_cost
            else:
                if targets <= assets and cost <= cap:
                    best = cost if best is None else min(best, cost)
    return best


class AllocationTests(unittest.TestCase):
    def routes(self):
        return [RecoveryRoute("shared", (), ("index",), "w1", (), ("w1",), 2),
                RecoveryRoute("a", ("index",), ("a",), "w2", (), ("w2",), 3),
                RecoveryRoute("b", ("index",), ("b",), "w3", (), ("w3",), 4),
                RecoveryRoute("both", (), ("a", "b"), "w0", (), ("w0",), 12)]

    def test_shared_prerequisite_charged_once_against_oracle(self):
        routes = self.routes()
        for cap, excluded in itertools.product((8, 9, 12), (set(), {"w0"}, {"w1"})):
            with self.subTest(cap=cap, excluded=excluded):
                schedule = shortest_schedule(routes, set(), {"a", "b"}, excluded, cap)
                self.assertEqual(schedule.cost, exhaustive(routes, set(), {"a", "b"}, excluded, cap))
        self.assertEqual(shortest_schedule(routes, set(), {"a", "b"}, set(), 9).cost, 9)

    def test_prepared_route_dependencies_and_authors(self):
        routes = [RecoveryRoute("cold", (), ("a",), "w2", (), ("w2",), 9),
                  RecoveryRoute("prep", (), ("index",), "w1", (), ("w1",), 2, "prepare"),
                  RecoveryRoute("warm", (), ("a",), "w2", ("index",), ("w1", "w2"), 3, "prepared")]
        self.assertEqual(shortest_schedule(routes, set(), {"a"}, set(), 20).routes, ("prep", "warm"))
        self.assertEqual(shortest_schedule(routes, {"index"}, {"a"}, {"w1"}, 20).routes, ("cold",))

    def test_limits_do_not_claim_exact_optimum(self):
        schedule = shortest_schedule(self.routes(), set(), {"a", "b"}, set(), 20, max_states=1)
        self.assertEqual(schedule.status, "search_limit_no_certificate")
        self.assertIsNone(schedule.cost)

    def test_robust_allocator_against_exhaustive_scenarios(self):
        units = common_units(fixtures()[0])[:2]
        plans = [DelegationPlan("cheap", units), DelegationPlan("prepared", units, (("u0", "w1"),))]
        def routes(p):
            return [RecoveryRoute(f"{u.id}-{w}", (), (u.id,), w, (), (w,), 3)
                    for u in units for w in ("w2", "w3")]
        def cost(p):
            return 5 + len(p.preparation)*10
        scored = []
        for plan in plans:
            scenario_costs = []
            for worker in WORKERS:
                available = {u.id for u in units if u.owner != worker}
                repair = exhaustive(routes(plan), available, {u.id for u in units}, {worker}, 100-cost(plan))
                scenario_costs.append(cost(plan)+repair)
            scored.append((max(scenario_costs), plan.id))
        actual = solve_allocation(plans, routes, cost, 100)
        self.assertEqual((actual.worst_cost, actual.plan.id), min(scored))
        self.assertEqual(actual.plan.preparation, ())

    def test_recovery_can_choose_no_preparation(self):
        plan = choose_plan("recovery", fixtures()[0], RunConfig(),
                           CostEstimates(100, 100, 100, "synthetic_unit_test_only"), 10000)
        self.assertEqual(plan.preparation, ())
        self.assertEqual(plan.allocation_status, "exact_finite")


class WorkerInvariantTests(unittest.TestCase):
    def setup_loop(self, backend=None, family="clean", identity="w0"):
        self.config, self.store, self.ledger = RunConfig(), ProvenanceStore(), BudgetLedger(100000)
        self.attacker = AttackController(AttackSpec(family), () if family == "clean" else (identity,))
        return WorkerLoop(backend or MockBackend(), self.config, self.ledger, self.store, self.attacker)

    def test_persistent_compromise_in_backup_and_reset(self):
        loop = self.setup_loop(family="withholding")
        for operation in ("implement", "prepare", "replicate"):
            self.store.reset("w0")
            outcome = loop.run(fixtures()[0], "u0", "w0", "repair", 0, operation=operation)
            self.assertEqual(outcome.status, "withheld")
        self.assertEqual(self.attacker.coalition, ("w0",))
        self.assertEqual(len(self.ledger.entries), 3)

    def test_sabotage_can_attack_preparation_author(self):
        loop = self.setup_loop(family="artifact_sabotage")
        outcome = loop.run(fixtures()[0], "u0", "w0", "preparation", 0, operation="prepare")
        artifact = self.store.artifacts[outcome.artifact_id]
        self.assertEqual(artifact.contributors, ("w0",))
        self.assertEqual(artifact.content["contract"]["scale"], 0)

    def test_preparation_replication_and_refill_are_charged(self):
        loop = self.setup_loop()
        prepared = loop.run(fixtures()[0], "u0", "w1", "preparation", 0, operation="prepare")
        before = self.ledger.spent
        loop.run(fixtures()[0], "u0", "w2", "repair", 0, allowed_artifacts=(prepared.artifact_id,))
        self.assertGreater(self.ledger.spent, before)
        entries = self.ledger.entries
        self.assertTrue(any(e["kind"] == "context_reconstruction" for e in entries))
        repair_inputs = [e["input_tokens"] for e in entries if e["stage"] == "repair" and e["kind"] == "model"]
        self.assertGreater(repair_inputs[1], repair_inputs[0])
        self.assertGreater(self.ledger.summary()["stages"]["preparation"], 0)

    def test_malformed_retry_is_bounded_and_charged(self):
        class BadModel(MockBackend):
            def generate(self, *args, **kwargs):
                return Generation("not JSON", 2)
        loop = self.setup_loop(BadModel())
        outcome = loop.run(fixtures()[0], "u0", "w0", "primary", 0)
        self.assertEqual(outcome.status, "malformed")
        calls = [e for e in self.ledger.entries if e["kind"] == "model"]
        self.assertEqual(len(calls), self.config.malformed_retries+1)
        self.assertEqual(sum(e["output_tokens"] for e in calls), 6)

    def test_backend_failures_are_charged_not_attack_success(self):
        class Down(MockBackend):
            def generate(self, *args, **kwargs):
                raise RuntimeError("backend unavailable")
        loop = self.setup_loop(Down())
        with self.assertRaises(RuntimeError):
            loop.run(fixtures()[0], "u0", "w0", "primary", 0)
        self.assertTrue(self.ledger.entries[-1]["uncertain"])
        self.assertEqual(self.ledger.entries[-1]["kind"], "model")

    def test_independent_replica_has_no_primary_dependencies(self):
        loop = self.setup_loop()
        original = loop.run(fixtures()[0], "u0", "w0", "primary", 0)
        replica = loop.run(fixtures()[0], "u0", "w1", "replication", 0, operation="replicate")
        a, b = self.store.artifacts[original.artifact_id], self.store.artifacts[replica.artifact_id]
        self.assertEqual(a.content, b.content)
        self.assertEqual(b.parents, ())
        self.assertEqual(b.contributors, ("w1",))
        self.assertTrue(b.source_hashes)

    def test_observation_boundaries_and_policy_blind_fixture(self):
        self.assertEqual(set(Alarm.__dataclass_fields__), {"units", "suspicious_authors", "reasons", "diagnostic_oracle"})
        source = inspect.getsource(monitor)
        self.assertNotIn(".attacks", source)
        self.assertNotIn(".hidden", source)
        mock_source = inspect.getsource(MockBackend)
        self.assertNotIn("policy", mock_source)
        self.assertNotIn("coalition", mock_source)
        self.assertNotIn("hidden", mock_source)

    def test_final_evaluation_requires_every_output(self):
        self.assertFalse(evaluate(fixtures()[0], {}, 123)["complete_task_success"])

    def test_splits_group_all_pairs(self):
        first, second = fixtures(2)
        self.assertEqual(grouped_split(first.group), grouped_split(second.group))
        with self.assertRaises(BCError):
            validate_splits({"development": [first], "test": [second]})


class RecoveryTests(unittest.TestCase):
    def test_jit_can_execute_indexing_at_alarm(self):
        config = RunConfig(policies=("jit",), attacks=("withholding",))
        manifest = build_manifest(config, ROOT)
        episode = episode_from(manifest["episodes"][0])
        with tempfile.TemporaryDirectory() as temp:
            journal = EpisodeJournal(Path(temp), episode.episode_id)
            engine = EpisodeEngine(fixtures()[0], episode, config, MockBackend(), journal, "test")
            with patch("beyond_consensus.runtime.episode.estimates", return_value=CostEstimates(
                    8000, 100, 200, "synthetic_unit_test_only")):
                result = engine.run()
            self.assertTrue(result.success, result.error)
            self.assertTrue(engine.preparations)
            self.assertTrue(any(r.operation == "prepare" for r in engine.routes))
            self.assertEqual(result.costs["stages"].get("preparation", 0), 0)
            self.assertGreater(result.costs["stages"]["repair"], 0)


if __name__ == "__main__":
    unittest.main()
