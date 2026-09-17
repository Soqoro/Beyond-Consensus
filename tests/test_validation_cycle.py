"""Bounded validation behavior; constructed data/costs are not model evidence."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import RunConfig, ModelConfig, load_config
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.models.base import Generation
from beyond_consensus.models.transformers_backend import verify_thinking_template, stopping_reason
from beyond_consensus.planning.costs import CostEstimates, compatibility
from beyond_consensus.policies.core import choose_plan, catalogue
from beyond_consensus.planning.allocation import shortest_schedule
from beyond_consensus.experiments.manifest import build_manifest, episode_from, task_from, grouped_split
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.runtime.episode import EpisodeEngine
from beyond_consensus.runtime.persistence import EpisodeJournal
from beyond_consensus.runtime.budget import BudgetLedger
from beyond_consensus.runtime.provenance import ProvenanceStore
from beyond_consensus.tasks.sqlite_tasks import fixtures, native_tasks, pair
from beyond_consensus.tasks.silo import task as silo_task, solve
from beyond_consensus.tasks.silo_diagnostics import battery, derived, data_manifest, freeze_boundaries, validate_predecessor
from beyond_consensus.tasks.data_manifest import validate_data, validate_reference, validate_native, regime
from beyond_consensus.diagnostics.allocation import reconcile, inspect_output
from beyond_consensus.diagnostics.native import readiness, scorer_parity
from beyond_consensus.diagnostics.silo import attribution, analyze_output
from beyond_consensus.diagnostics.measurement import compare
from beyond_consensus.evaluation.aggregate import aggregate
from beyond_consensus.evaluation.metrics import from_result
from beyond_consensus.util import BCError, plain, read_json, atomic_json, digest, file_hash


def config_for(tasks, **extra):
    return RunConfig(task_kind=tasks[0].kind, task_count=len(tasks), policies=("single",), attacks=("clean",),
        seeds=(0,), monitor_id="data-structure-v1", max_actions=12, **extra)


class NativeReadinessTests(unittest.TestCase):
    def fixture(self):
        from tests.test_data_workflows import NativeFixtureTests
        fixture = NativeFixtureTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_missing_staging_and_materials_are_unavailable_without_gold_or_paths(self):
        self.assertEqual(readiness()["status"], "scoring_unavailable")
        f = self.fixture()
        report = readiness({**f.staged, "materials": None, "review": None})
        self.assertEqual(report["status"], "scoring_unavailable")
        self.assertEqual(len(report["tasks"]), 2)
        self.assertTrue(all(t["native_scoring"] == "scoring_unavailable" for t in report["tasks"]))
        for marker in (str(f.root), "GOLD_SQL_SENTINEL", "HIDDEN_TEST_SENTINEL"):
            self.assertNotIn(marker, json.dumps(report))

    def test_private_integrity_and_unsupported_operations_have_sanitized_reasons(self):
        f = self.fixture()
        report = readiness(f.staged)
        self.assertTrue(all(t["reference"]["exact_record_binding"] for t in report["tasks"]))
        f.review["tasks"]["fixture_view"]["artifact"]["select"]["columns"][0]["expr"] = {"call": {"name": "load_extension", "args": [{"literal": "PRIVATE_PATH_SENTINEL"}]}}
        atomic_json(f.review_path, f.review)
        f.staged["review"]["sha256"] = file_hash(f.review_path)
        report = readiness(f.staged)
        self.assertTrue(any(t["status"] == "blocked" for t in report["tasks"]))
        self.assertNotIn("PRIVATE_PATH_SENTINEL", json.dumps(report))
        f.staged["review"]["sha256"] = "0"*64
        self.assertEqual(readiness(f.staged)["status"], "blocked_prerequisite")

    def test_positive_negative_joint_reset_and_comparison_parity(self):
        f = self.fixture()
        tasks, _ = native_tasks(f.staged)
        paired = pair(*tasks, "labelled synthetic shared-state check")
        report = validate_reference(paired)
        self.assertEqual(report["status"], "validated")
        self.assertTrue(report["positive_joint"])
        self.assertTrue(report["source_integrity_after_controls"])
        self.assertTrue(report["reset_repeat_identical"])
        self.assertEqual(report["evaluated_obligations"], 2)
        self.assertTrue(all(report["missing_obligation_controls"].values()))
        self.assertTrue(all(report["corrupt_obligation_controls"].values()))
        self.assertTrue(all(c["passed"] for c in scorer_parity()))

    def test_up_to_deterministic_and_not_ten_fabricated_tasks(self):
        f = self.fixture()
        with patch("beyond_consensus.experiments.manifest.grouped_split", return_value="development"):
            report = validate_native(f.staged, None, 10, up_to=True)
        self.assertEqual(report["evaluated"], 2)
        self.assertEqual([t["id"] for t in report["tasks"]], ["fixture_report", "fixture_view"])

    def test_missing_second_pair_and_reversed_duplicate_are_not_two_pairs(self):
        from beyond_consensus.tasks.data_manifest import validate_pairs
        f = self.fixture()
        candidate = {"source_ids": ["fixture_report", "fixture_view"], "rationale": "synthetic shared-state pair"}
        report = validate_pairs(f.staged, [candidate], 2)
        self.assertEqual(report["missing_candidate_slots"], 1)
        self.assertTrue(report["command_failed"])
        reversed_pair = {**candidate, "source_ids": list(reversed(candidate["source_ids"]))}
        report = validate_pairs(f.staged, [candidate, reversed_pair], 2)
        self.assertEqual(len(report["tasks"]), 1)
        self.assertTrue(report["command_failed"])
        self.assertIn("Duplicate pair", report["reports"][1]["reason"])

    def test_empty_reference_containers_do_not_pass_presence_gate(self):
        from beyond_consensus.tasks.sqlite_tasks import nonempty_material
        for value in (None, [], [""], ["   "], [[]], {}, {"test": []}):
            self.assertFalse(nonempty_material(value))


class AllocationAuditTests(unittest.TestCase):
    def test_trace_does_not_change_choice_and_exposes_zero_preparation(self):
        task, config, costs = fixtures()[0], RunConfig(), CostEstimates(2000, 2000, 2000, "constructed")
        trace = {}
        plain_plan = choose_plan("recovery", task, config, costs, 99999)
        traced = choose_plan("recovery", task, config, costs, 99999, trace=trace)
        self.assertEqual(plain(plain_plan), plain(traced))
        self.assertEqual(traced.search_states, 256)
        self.assertEqual(traced.preparation, ())
        self.assertEqual(len(trace["candidates"]), 32)
        self.assertTrue(any(c["plan"]["preparation"] for c in trace["candidates"]))
        self.assertEqual(trace["decision"], "selected_no_preparation")
        scenario = trace["evaluations"][0]["scenarios"][0]
        self.assertEqual(scenario["schedule"]["status"], "exact_finite")
        self.assertTrue(any(r["eligibility"] == "contributor_conflict" for r in scenario["routes"]))
        self.assertEqual(choose_plan("jit", task, config, costs, 99999).search_states, 0)

    def test_search_limit_never_claims_global_dominance(self):
        trace = {}
        plan = choose_plan("recovery", fixtures()[0], RunConfig(), CostEstimates(100, 1, 2, "constructed"),
            99999, max_search_states=1, trace=trace)
        self.assertIn("search_limit", plan.allocation_status)
        self.assertNotIn("predicted_dominated", [e["reason"] for e in trace["evaluations"]])
        self.assertTrue(any(e["reason"] == "unavailable_search_limit" for e in trace["evaluations"]))

    def test_jit_equivalent_catalogue_explains_no_upfront_prep_even_with_cheaper_warm_cost(self):
        for cold, prep, warm in ((100, 1, 2), (100, 5, 20), (100, 150, 100)):
            plan = choose_plan("recovery", fixtures()[0], RunConfig(), CostEstimates(cold, prep, warm, "constructed"), 99999)
            self.assertEqual(plan.preparation, ())
        replica = choose_plan("replication", fixtures()[0], RunConfig(), CostEstimates(100, 1, 2, "constructed"), 99999)
        self.assertEqual(len(replica.replicas), 4)

    def test_charge_ids_detect_duplicate_and_preserve_legitimate_equal_costs(self):
        ledger = BudgetLedger(1000)
        ledger.charge("planning", 256, kind="finite_search")
        ledger.charge("primary", 10, kind="tool")
        ledger.charge("primary", 10, kind="tool")
        report = reconcile(ledger.summary())
        self.assertEqual(report["entry_total"], 276)
        self.assertTrue(report["stage_totals_match"])
        self.assertEqual(report["duplicate_entry_ids"], [])
        duplicate = deepcopy(ledger.summary())
        duplicate["entries"].append(duplicate["entries"][1])
        bad = reconcile(duplicate)
        self.assertFalse(bad["summary_total_matches"])
        self.assertEqual(bad["duplicate_entry_ids"], ["charge-1"])
        legacy = {"entries": [{"stage": "primary", "kind": "tool", "work": 10}]*2}
        self.assertEqual(reconcile(legacy)["duplicate_accounting_status"], "identity_unavailable")
        wrong_formula = {"entries": [{"stage": "primary", "kind": "model", "work": 60,
            "input_tokens": 20, "output_tokens": 10, "reasoning_tokens": 4}]}
        report = reconcile(wrong_formula, rules={"input_weight": 1, "output_weight": 1})
        self.assertEqual(report["model_charge_mismatches"][0]["token_formula_work"], 30)

    def test_preparation_is_executable_and_eligible_repair_reads_are_charged(self):
        # Explicit constructed behavioral plan: does not claim choose_plan prefers it.
        tasks = fixtures()
        config = replace(config_for(tasks), policies=("recovery",), attacks=("withholding",))
        manifest = build_manifest(config, ROOT, tasks)
        with tempfile.TemporaryDirectory() as temp:
            row = episode_from(manifest["episodes"][0])
            journal = EpisodeJournal(Path(temp), row.episode_id)
            engine = EpisodeEngine(tasks[0], row, config, MockBackend(), journal, journal.begin(digest(row)))
            engine.plan_primary()
            engine.costs = CostEstimates(100, 1, 2, "constructed")
            owner = engine.attacker.coalition[0]
            unit = next(u for u in engine.plan.units if u.owner == owner)
            author = next(w for w in ("w0", "w1", "w2", "w3") if w != owner)
            engine.plan.preparation = ((unit.id, author),)
            engine.primary()
            prep = engine.preparations[0]
            self.assertTrue(engine.store.artifacts[prep.artifact_version].source_hashes)
            engine.repair()
            self.assertIn(unit.id, engine.selected)
            self.assertTrue(any(e["kind"] == "context_reconstruction" and e["stage"] == "repair" for e in engine.ledger.entries))
            self.assertTrue(any(e["kind"] == "model" and e["stage"] == "repair" and e["input_tokens"]>0 for e in engine.ledger.entries))
            self.assertTrue(any(r.operation == "prepared" for r in engine.routes))
            schedule = shortest_schedule(catalogue(engine.plan, engine.costs), {prep.id}, {unit.id}, {author}, 9999)
            self.assertNotIn(f"prepared:{unit.id}:{author}:{author}", schedule.routes)
            self.assertFalse(any(r.endswith(":"+author) and r.startswith("prepared:") for r in schedule.routes))


class SILOCycleTests(unittest.TestCase):
    def test_context_limit_is_observed_without_model_execution_or_truncation(self):
        tasks = [silo_task(seed=1)]
        config = replace(config_for(tasks), model=ModelConfig(context_limit=32, max_new_tokens=16))
        manifest = build_manifest(config, ROOT, tasks)
        backend = MockBackend()
        with tempfile.TemporaryDirectory() as temp, patch.object(backend, "generate", side_effect=AssertionError("generation forbidden")):
            row = run_manifest(manifest, Path(temp), ROOT, backend=backend)[0]
            self.assertEqual(row["status"], "infrastructure_failed")
            cp = read_json(Path(temp)/"episodes"/row["episode_id"]/"checkpoint.json")
            event = next(e for e in cp["store"]["events"] if e["type"] == "context_limit")
            self.assertFalse(event["history_truncated"])
            self.assertGreater(event["input_tokens"], event["context_limit"])

    def test_boundary_empty_or_malformed_predecessor_is_unavailable(self):
        store = ProvenanceStore()
        artifact = store.submit("w0", "u0", {"answer": []})
        frozen = {"schema": "bc-actual-predecessor-v1", "artifacts": plain(store.artifacts), "version": artifact.id,
            "baseline_manifest_hash": "test-only-baseline", "checkpoint_hash": "test-only-checkpoint"}
        with self.assertRaises(BCError): validate_predecessor(frozen, 1)

    def test_supplied_excerpt_attributes_boundary_and_increment_errors(self):
        fixture = read_json(ROOT/"tests/fixtures/silo-v3-user-excerpt.json")
        task = silo_task(seed=fixture["generator_seed"])
        self.assertEqual(task.group, fixture["source_group"])
        result = attribution(list(task.metadata["harness"]["shards"].values()), fixture["answers"], fixture["visible"])
        self.assertEqual(result["correct_values"], 15)
        self.assertTrue(all(s["shape_valid"] for s in result["segments"]))
        self.assertEqual([s["incoming_consistent"] for s in result["segments"]], [True, False, False, False])
        self.assertEqual([s["local_increment_errors"] for s in result["segments"]], [0, 1, 1, 0])

    def test_inherited_error_is_separate_from_additional_worker_error(self):
        shards = [[1, 2], [3, 4]]
        result = attribution(shards, {"u0": [0, 2], "u1": [5, 9]},
            {"u1": {"predecessor_artifact_id": "wrong-submitted-version", "submitted_final_value": 2}})
        segment = result["segments"][1]
        self.assertFalse(segment["global_correct"])
        self.assertTrue(segment["inherited_only"])
        self.assertFalse(segment["additional_worker_error"])

    def test_fresh_counts_dedup_splits_and_confirmation(self):
        data = battery()
        full = [task_from(t) for t in data["full"]["tasks"]]
        local = [task_from(t) for t in data["local"]["tasks"]]
        self.assertEqual((len(full), len(local)), (8, 32))
        self.assertEqual(data["plan"]["total_maximum_per_condition"], 64)
        self.assertTrue(all(grouped_split(t.group) == "development" for t in full))
        self.assertNotIn(silo_task(seed=1).group, {t.group for t in full})
        self.assertFalse({t.group for t in full} & {t["group"] for t in data["confirmation"]["tasks"]})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"prior.json"
            atomic_json(path, data["full"])
            again = battery(exclusions=[path])
            self.assertFalse({t.group for t in full} & {t["group"] for t in again["full"]["tasks"]})
            atomic_json(path, data["local"])
            self.assertEqual(len(validate_data(path)), 32)

    def test_shape_valid_all_wrong_passes_monitor_fails_final_without_feedback(self):
        class Wrong(MockBackend):
            def generate(self, messages, max_new_tokens, seed):
                action = {"tool": "submit_result", "answer": [0]*15}
                return Generation(json.dumps(action), 80)
        tasks = [silo_task(seed=1)]
        config = config_for(tasks)
        manifest = build_manifest(config, ROOT, tasks)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            row = run_manifest(manifest, output, ROOT, backend=Wrong())[0]
            self.assertEqual(row["status"], "completed")
            self.assertFalse(row["success"])
            self.assertTrue(row["metrics"]["joint_public_integration"])
            obs = row["metrics"]["observations"]
            self.assertTrue(obs["public_shape_valid"])
            self.assertTrue(obs["public_coverage"])
            self.assertFalse(obs["final_semantic_correctness"])
            self.assertFalse(row["metrics"]["alarmed"])
            cp = read_json(output/"episodes"/row["episode_id"]/"checkpoint.json")
            self.assertNotIn("incoming_consistent", json.dumps(cp["store"]["contexts"]))
            self.assertEqual(len([e for e in cp["store"]["events"] if e["type"] == "submit"]), 4)
            analysis = analyze_output(output)
            self.assertFalse(analysis["feedback_to_runtime"])
            frozen = freeze_boundaries(output)
            self.assertEqual((frozen["planned"], frozen["denominator"]), (3, 3))
            for t in frozen["tasks"]:
                predecessor = t["metadata"]["harness"]["predecessor"]
                self.assertEqual(predecessor["artifacts"][predecessor["version"]]["content"]["answer"][-1], 0)
            forged = deepcopy(frozen["tasks"][0]["metadata"]["harness"]["predecessor"])
            forged["artifacts"][forged["version"]]["content"]["answer"][-1] = 386
            with self.assertRaisesRegex(BCError, "submitted version"):
                validate_predecessor(forged, 1)
            # Wrong predecessor remains wrong in actual worker-visible serialization.
            boundary = task_from(frozen["tasks"][0])
            cfg = config_for([boundary], silo_interface="submitted_final_value_v1")
            run = build_manifest(cfg, ROOT, [boundary])
            out2 = output/"boundary"
            result = run_manifest(run, out2, ROOT)[0]
            self.assertFalse(result["success"])
            cp2 = read_json(out2/"episodes"/result["episode_id"]/"checkpoint.json")
            observations = [json.loads(m["content"]) for m in cp2["store"]["contexts"]["w0"]["messages"] if m["role"] == "user"]
            carry = next(o for o in observations if "submitted_final_value" in o)
            self.assertEqual(carry["submitted_final_value"], 0)
            self.assertEqual(carry["predecessor_artifact_id"], boundary.metadata["harness"]["predecessor"]["version"])
            forbidden = {"incoming_consistent", "global_correct", "expected_output"}
            self.assertFalse(any(forbidden & o.keys() for o in observations))
            report = analyze_output(out2)["episodes"][0]["analysis"]["segment"]
            self.assertTrue(report["locally_consistent"])
            self.assertFalse(report["global_correct"])

    def test_missing_baseline_keeps_denominator_and_no_gold_substitution(self):
        tasks = [silo_task(seed=1)]
        manifest = build_manifest(config_for(tasks), ROOT, tasks)
        with tempfile.TemporaryDirectory() as temp:
            atomic_json(Path(temp)/"manifest.json", manifest)
            result = freeze_boundaries(temp)
            self.assertEqual(result["denominator"], 3)
            self.assertEqual(result["planned"], 0)
            self.assertEqual(result["unavailable"], 3)

    def test_local_mode_is_changed_task_and_tampered_data_rejected(self):
        original = silo_task(seed=1)
        local = derived(original, 2, "local")
        self.assertNotEqual(regime(local), regime(original))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"local.json"
            atomic_json(path, data_manifest([local]))
            self.assertEqual(len(validate_data(path)), 1)
            local.metadata["harness"]["shards"]["u0"][0] += 1
            atomic_json(path, data_manifest([local]))
            with self.assertRaises(BCError):
                validate_data(path)

    def test_generation_metadata_context_cap_and_profile_grouping(self):
        tasks = [silo_task(seed=1)]
        config = config_for(tasks)
        manifest = build_manifest(config, ROOT, tasks)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            row = run_manifest(manifest, out, ROOT)[0]
            path = out/"episodes"/row["episode_id"]
            cp = read_json(path/"checkpoint.json")
            events = [e for e in cp["store"]["events"] if e["type"] == "generation_metadata"]
            self.assertEqual({e["unit"] for e in events}, {"u0", "u1", "u2", "u3"})
            self.assertTrue(all(e["history_truncated"] is False and e["input_tokens"]>0 for e in events))
            self.assertTrue(all(e["details"] == {} for e in events))  # mock never invents hardware/finish reason
            row["provenance"]["condition"]["silo_interface"] = "submitted_final_value_v1"
            atomic_json(path/"result.json", row)
            with self.assertRaises(BCError): aggregate(manifest, out)


class ProfileAndMeasurementTests(unittest.TestCase):
    def test_measurement_resume_keeps_discarded_operation_work(self):
        from beyond_consensus.runtime.measurement import MeasurementEngine
        tasks = [derived(silo_task(seed=1), 0, "local")]
        config = config_for(tasks, operation_measurement=True)
        manifest = build_manifest(config, ROOT, tasks)
        class Counting(MockBackend):
            calls = 0
            def generate(self, *args):
                self.calls += 1
                return super().generate(*args)
        backend = Counting()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            atomic_json(out/"manifest.json", manifest)
            row = episode_from(manifest["episodes"][0])
            journal = EpisodeJournal(out, row.episode_id)
            engine = MeasurementEngine(tasks[0], row, config, backend, journal, journal.begin(digest(row)),
                stop_requested=lambda: backend.calls >= 2)
            stopped = engine.run()
            self.assertEqual(stopped.status, "interrupted")
            discarded = stopped.costs["stages"]["calibration"]
            resumed = run_manifest(manifest, out, ROOT, retry_failures=True)[0]
            self.assertEqual(resumed["status"], "completed")
            cold = resumed["metrics"]["measurements"][0]
            self.assertGreater(cold["work"], discarded)
            entries = resumed["costs"]["entries"][cold["start_entry"]:cold["end_entry"]]
            self.assertEqual(cold["work"], sum(e["work"] for e in entries))
            self.assertEqual(len([e for e in entries if e["kind"] == "model"]), 5)

    def test_export_records_allowlisted_runtime_and_no_private_paths(self):
        from beyond_consensus.experiments.export import export_bundle
        import tarfile
        tasks = [silo_task(seed=1)]
        config = config_for(tasks)
        manifest = build_manifest(config, ROOT, tasks)
        backend = MockBackend()
        backend.runtime = {"hardware": "TEST_FIXTURE_DEVICE", "slurm_job_id": "TEST_ONLY",
            "model_lock_hash": "test-only-hash", "model_path": "/dataset/PRIVATE_PATH_SENTINEL",
            "import_path": "/home/PRIVATE_PATH_SENTINEL", "snapshot_id": "test-only-snapshot",
            "settings": plain(config.model), "api_key": "SECRET_SENTINEL"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_manifest(manifest, root/"run", ROOT, backend=backend)
            export_bundle(root/"run", root/"bundle.tar.gz")
            with tarfile.open(root/"bundle.tar.gz") as archive:
                text = archive.extractfile("results.json").read().decode()
            self.assertNotIn("PRIVATE_PATH_SENTINEL", text)
            self.assertNotIn("SECRET_SENTINEL", text)
            self.assertIn("TEST_FIXTURE_DEVICE", text)
            self.assertIn("generation_diagnostics", text)

    def test_stopping_cause_is_explicit_and_9b_requires_pin(self):
        self.assertEqual(stopping_reason([7, 2], 2, 2), "eos")
        self.assertEqual(stopping_reason([7, 8], [1, 2], 2), "length_limit")
        self.assertEqual(stopping_reason([7], 2, 2), "other_or_unknown")
        with self.assertRaisesRegex(BCError, "Resolve"):
            load_config(ROOT/"configs/validation/qwen35-9b-later.json")

    def test_silo_diagnostic_snapshot_and_guarded_dry_run(self):
        from beyond_consensus.experiments import cluster
        from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot
        from tests.test_cluster import site_config
        import subprocess
        tasks = [derived(silo_task(seed=1), 0, "local")]
        cfg = config_for(tasks, model=ModelConfig(backend="transformers", revision="a"*40, tokenizer_revision="a"*40))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root/"repo"
            (repo/"src").mkdir(parents=True)
            (repo/"src/test.txt").write_text("test-only immutable source")
            for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"]):
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
            manifest = build_manifest(cfg, repo, tasks)
            snapshot = create_snapshot(repo, root/"snapshots", manifest, {}, {})
            verify_snapshot(snapshot)
            self.assertEqual(read_json(snapshot/"resolved/manifest.json")["tasks"], manifest["tasks"])
            def scheduler_read(argv):
                if argv[0] == "squeue":
                    return ""
                if argv[0] == "sinfo":
                    return "131072"
                if argv[:3] == ["scontrol", "show", "partition"]:
                    return "PartitionName=NH100q MaxTime=02:00:00"
                raise AssertionError("Only scheduler inspection is permitted in this dry run")
            with patch.object(cluster, "registry_root", return_value=root/"registry"), patch.object(cluster, "command", side_effect=scheduler_read):
                dry = cluster.submit(repo, site_config(root), manifest, {"revision": "a"*40}, 1, dry_run=True)
            self.assertFalse(dry["submitted"])
            self.assertIn("--gres=gpu:1", dry["argv"])
            self.assertIn("--array=0-0%1", dry["argv"])

    def test_default_unchanged_and_variant_calibration_provenance_differs(self):
        control = load_config(ROOT/"configs/validation/qwen35-4b-control.json")
        thinking = load_config(ROOT/"configs/validation/qwen35-4b-reasoning.json")
        self.assertFalse(ModelConfig().thinking)
        self.assertFalse(control.model.thinking)
        self.assertEqual(control.model.dtype, "bfloat16")
        self.assertEqual(control.silo_interface, "original")
        self.assertEqual(control.model.revision, "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
        self.assertTrue(thinking.model.thinking)
        self.assertEqual(replace(thinking.model, thinking=False), control.model)
        self.assertNotEqual(compatibility(control), compatibility(thinking))
        self.assertNotEqual(compatibility(control), compatibility(replace(control, silo_interface="submitted_final_value_v1")))

    def test_unsupported_reasoning_template_fails_explicitly(self):
        class Tokenizer:
            chat_template = "a template without the switch"
            unk_token_id = 0
            def apply_chat_template(self, messages, **kwargs):
                return "<think>" if kwargs["enable_thinking"] else "<think></think>"
            def convert_tokens_to_ids(self, token):
                return 42
        tokenizer = Tokenizer()
        self.assertFalse(verify_thinking_template(tokenizer, False)["reasoning_support_verified"])
        with self.assertRaises(BCError): verify_thinking_template(tokenizer, True)
        tokenizer.chat_template = "enable_thinking"
        self.assertTrue(verify_thinking_template(tokenizer, True)["reasoning_support_verified"])
        tokenizer.apply_chat_template = lambda *a, **k: "same prompt"
        with self.assertRaises(BCError): verify_thinking_template(tokenizer, True)

    def test_measurements_use_actual_loop_charges_and_disjoint_holdout(self):
        # Synthetic mock data demonstrate mechanics, not model cost calibration.
        groups = battery(start=2500)["full"]["tasks"][:2]
        tasks = [derived(task_from(t), 0, "local") for t in groups]
        with tempfile.TemporaryDirectory() as temp:
            outputs = []
            for i, task in enumerate(tasks):
                out = Path(temp)/str(i)
                config = config_for([task], operation_measurement=True)
                manifest = build_manifest(config, ROOT, [task])
                row = run_manifest(manifest, out, ROOT)[0]
                self.assertEqual(row["status"], "completed")
                self.assertIsNone(row["success"])
                self.assertEqual(len(row["metrics"]["measurements"]), 6)
                self.assertTrue(all(m["work"]>0 and m["status"] == "submitted" for m in row["metrics"]["measurements"]))
                self.assertIsNone(aggregate(manifest, out)["groups"]["single/clean"]["success_rate_observed"])
                self.assertTrue(inspect_output(out)["episodes"][0]["reconciliation"]["result_total_matches"])
                with self.assertRaisesRegex(BCError, "no selected task submission"):
                    analyze_output(out)
                outputs.append(out)
            report = compare(*outputs)
            self.assertEqual(report["origin"], "mock-measured")
            self.assertTrue(report["all_operations_submitted_and_grounded"])
            self.assertEqual(len(report["holdout_prediction_errors"]), 6)
            self.assertFalse(report["confirmatory"])
            with self.assertRaises(BCError): compare(outputs[0], outputs[0])

    def test_legacy_unknown_public_metrics_are_not_inferred_from_failure(self):
        result = {"status": "completed", "success": False, "metrics": {"integration_failure": True}}
        obs = from_result(result)
        self.assertIsNone(obs["public_integration"])
        self.assertIsNone(obs["public_shape_valid"])
        self.assertIsNone(obs["missing_required_artifacts"])
        self.assertIsNone(obs["final_semantic_correctness"])


if __name__ == "__main__":
    unittest.main()
