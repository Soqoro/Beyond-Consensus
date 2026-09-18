"""Research gates use labelled exact fixtures, never fabricated native evidence."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from tests.support import ROOT
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.diagnostics.planning import inventory
from beyond_consensus.diagnostics.allocation import inspect_output
from beyond_consensus.policies.core import candidate_plans, catalogue, choose_plan, boundary_plans
from beyond_consensus.planning.allocation import shortest_schedule
from beyond_consensus.planning.costs import CostEstimates, compatibility
from beyond_consensus.tasks.workflow import fixtures
from beyond_consensus.tasks.sqlite_tasks import fixtures as sqlite_fixtures
from beyond_consensus.tasks.silo import task as silo_task
from beyond_consensus.tasks.silo_diagnostics import full_control, data_manifest
from beyond_consensus.experiments.manifest import build_manifest, task_from
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.util import BCError, atomic_json, plain, read_json, digest, file_hash


class ResearchGateTests(unittest.TestCase):
    def test_counts_separate_backup_masks_from_actual_workflows(self):
        cfg = RunConfig()
        for task, graphs in ((fixtures(2)[0], 1), (fixtures(2)[1], 2), (sqlite_fixtures()[0], 1), (silo_task(seed=1), 1)):
            report = inventory(task, cfg)
            self.assertEqual(report["candidate_count"], 32)
            counts = report["distinct"]
            self.assertEqual(counts["preparation_selections"], 16)
            self.assertEqual(counts["dependency_graphs"], graphs)
            self.assertEqual(counts["material_plans_including_preparation"], 16*graphs)
            for key in ("owner_assignments", "unit_boundaries", "terminal_obligation_sets", "primary_execution_orders", "reserve_values"):
                self.assertEqual(counts[key], 1)
            self.assertFalse(report["reserve"]["optimized"])
            self.assertIsNone(report["objective"]["checking"])
            self.assertIsNone(report["objective"]["integration"])

    def test_existing_boundaries_change_charged_versioned_primary_reads(self):
        task = fixtures(2)[1]
        records = {}
        with tempfile.TemporaryDirectory() as temporary:
            for organization in ("fixed_isolated", "fixed_linked", "select_boundary"):
                cfg = RunConfig(task_count=1, policies=("jit",), attacks=("clean",), organization=organization)
                manifest = build_manifest(cfg, ROOT, [task])
                out = Path(temporary)/organization
                result = run_manifest(manifest, out, ROOT)[0]
                self.assertTrue(result["success"])
                self.assertEqual(result["provenance"]["condition"]["organization"], organization)
                cp = read_json(out/"episodes"/result["episode_id"]/"checkpoint.json")
                self.assertEqual(set(cp["selected"]), set(task.required_outputs))
                plan = result["provenance"]["plan"]
                self.assertEqual(plan["reserve"], cfg.budget.total*cfg.budget.reserve_fraction)
                self.assertEqual(plan["preparation"], [])
                self.assertEqual(len({u["owner"] for u in plan["units"]}), 4)
                reconstruction = [e for e in result["costs"]["entries"] if e["kind"] == "context_reconstruction"]
                records[organization] = (manifest["experiment_id"], reconstruction)
                if organization == "fixed_linked":
                    version = cp["selected"]["u0"]
                    store = ProvenanceStore.restore(cp["store"])
                    self.assertIn(version, store.artifacts[cp["selected"]["u2"]].parents)
                    store.invalidate({version})
                    self.assertFalse(store.artifacts[cp["selected"]["u2"]].valid)
                    self.assertFalse(store.artifacts[cp["selected"]["u3"]].valid)
                    self.assertTrue(store.artifacts[cp["selected"]["u1"]].valid)
                aggregate(manifest, out)
            self.assertFalse(records["fixed_isolated"][1])
            self.assertEqual(len(records["fixed_linked"][1]), 2)
            self.assertEqual(len({v[0] for v in records.values()}), 3)

    def test_common_jit_catalogue_reserve_and_missing_native_variation(self):
        task, costs = fixtures(2)[1], CostEstimates(100, 5, 10, "constructed-test")
        cfg = RunConfig(policies=("jit",), organization="fixed_isolated")
        selected = choose_plan("jit", task, replace(cfg, organization="select_boundary"), costs, 99999)
        fixed = choose_plan("jit", task, cfg, costs, 99999)
        self.assertEqual(selected.units, fixed.units)
        self.assertEqual(catalogue(selected, costs), catalogue(fixed, costs))
        self.assertEqual(selected.reserve, fixed.reserve)
        self.assertEqual(compatibility(cfg), compatibility(replace(cfg, organization="select_boundary")))
        self.assertTrue(any(r.operation == "prepare" for r in catalogue(fixed, costs)))
        for task in (sqlite_fixtures()[0], silo_task(seed=1)):
            with self.assertRaisesRegex(BCError, "readiness gap"):
                choose_plan("jit", task, cfg, costs, 99999)
        with self.assertRaisesRegex(BCError, "common JIT"):
            replace(cfg, policies=("recovery",))

    def test_exact_deferral_cost_argument_per_scenario(self):
        task = fixtures()[0]
        for costs in (CostEstimates(20, 2, 3, "constructed"), CostEstimates(2, 20, 3, "constructed")):
            for plan in candidate_plans("recovery", task, 0)[::2]:
                for bad in ("w0", "w1", "w2", "w3"):
                    targets = {u.id for u in plan.units}
                    available = {u.id for u in plan.units if u.owner != bad}
                    prep = {f"prep:{u}:{w}" for u, w in plan.preparation if w != bad}
                    routes = catalogue(plan, costs)
                    jit = shortest_schedule(routes, available, targets, {bad}, 1000)
                    warm = shortest_schedule(routes, available | prep, targets, {bad}, 1000)
                    self.assertEqual(jit.status, "exact_finite")
                    self.assertLessEqual(jit.cost, len(plan.preparation)*costs.prepare + warm.cost)

    def test_public_only_structure_does_not_consult_hidden_material(self):
        original = sqlite_fixtures()[0]
        tampered = deepcopy(original)
        tampered.metadata["evaluation"] = {"reference": "GOLD_SENTINEL"}
        tampered.metadata["harness"]["private_tests"] = "PRIVATE_SENTINEL"
        self.assertEqual(inventory(original, RunConfig()), inventory(tampered, RunConfig()))
        self.assertEqual(candidate_plans("recovery", original, 100), candidate_plans("recovery", tampered, 100))

    def test_saved_ledger_pairs_confirm_only_observed_charges_and_preserve_files(self):
        cfg = RunConfig(task_count=1, policies=("jit", "recovery"), attacks=("clean",),
                        allocation_diagnostics=True)
        manifest = build_manifest(cfg, ROOT, fixtures())
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            run_manifest(manifest, out, ROOT)
            paths = list(out.rglob("result.json"))
            before = [file_hash(p) for p in paths]
            report = inspect_output(out)
            pair = report["recovery_jit_pairs"][0]
            self.assertEqual(pair["finite_search_difference"], 256)
            self.assertEqual(pair["status"], "reconciled")
            self.assertTrue(pair["entire_gap_matches_search"])
            self.assertEqual(before, [file_hash(p) for p in paths])
            self.assertTrue(all(e["candidate_count"] in (1,32) for e in report["episodes"]))
            path = paths[0]
            data = read_json(path)
            data["costs"]["entries"].append(data["costs"]["entries"][0])
            atomic_json(path, data)
            pair = inspect_output(out)["recovery_jit_pairs"][0]
            self.assertFalse(pair["entire_gap_matches_search"])
            self.assertEqual(pair["status"], "incomplete_or_inconsistent_evidence")

    def test_summary_only_ledger_is_unknown_not_zero(self):
        cfg = RunConfig(task_count=1, policies=("jit",), attacks=("clean",))
        manifest = build_manifest(cfg, ROOT, fixtures())
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            atomic_json(out/"manifest.json", manifest)
            path = out/"episodes"/manifest["episodes"][0]["episode_id"]
            atomic_json(path/"result.json", {"costs": {"spent": 42}})
            report = inspect_output(out)
            self.assertEqual(report["episodes"][0]["status"], "ledger_unavailable")
            self.assertEqual(report["groups"], {})

    def test_eight_full_only_and_reuse_preserve_frozen_sources(self):
        controls = full_control()
        self.assertEqual(set(controls), {"full", "plan"})
        self.assertEqual(controls["plan"]["planned_executions"], 8)
        self.assertFalse(controls["plan"]["automatic_followup"])
        cfg = load_config(ROOT/"configs/validation/qwen35-4b-control.json")
        manifest = build_manifest(cfg, ROOT, [task_from(t) for t in controls["full"]["tasks"]])
        self.assertEqual(manifest["planned_episodes"], 8)
        self.assertEqual({e["policy"] for e in manifest["episodes"]}, {"single"})
        self.assertEqual({e["attack"]["family"] for e in manifest["episodes"]}, {"clean"})
        self.assertFalse(manifest["config"]["model"]["thinking"])
        self.assertEqual(manifest["config"]["silo_interface"], "original")
        with tempfile.TemporaryDirectory() as temporary:
            frozen = Path(temporary)/"full.json"
            atomic_json(frozen, controls["full"])
            reused = full_control(reuse=frozen)
            self.assertEqual(reused["full"]["tasks"], controls["full"]["tasks"])
            with self.assertRaisesRegex(BCError, "overlap"):
                full_control(reuse=frozen, exclusions=[frozen])
            atomic_json(frozen, data_manifest([silo_task(seed=1)]*8))
            with self.assertRaises(BCError): full_control(reuse=frozen)
            from beyond_consensus.experiments import cluster
            from tests.test_cluster import site_config
            from unittest.mock import patch
            def scheduler(argv):
                if argv[0] == "squeue": return ""
                if argv[0] == "sinfo": return "131072"
                if argv[:3] == ["scontrol", "show", "partition"]:
                    return "PartitionName=NH100q MaxTime=02:00:00"
                self.fail("Only fake scheduler inspection permitted")
            with patch.object(cluster, "registry_root", return_value=Path(temporary)/"registry"), patch.object(cluster, "command", side_effect=scheduler):
                dry = cluster.submit(ROOT, site_config(Path(temporary)), manifest, {"revision": cfg.model.revision}, 1, dry_run=True)
            self.assertFalse(dry["submitted"])
            self.assertIn("--gres=gpu:1", dry["argv"])
            self.assertIn("--array=0-3%1", dry["argv"])

    def test_documented_generated_bash_is_parsed_separately(self):
        from scripts.check_docs_shell import check
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"example.md"
            path.write_text("```bash\ncat > /tmp/not-executed.sh <<'SH'\n#!/usr/bin/env bash\nif then\nSH\n```\n")
            import subprocess
            with self.assertRaises(subprocess.CalledProcessError): check([path])


if __name__ == "__main__":
    unittest.main()
