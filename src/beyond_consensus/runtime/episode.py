"""Complete episodes. Public policy and terminal scoring run at distinct boundaries."""

from __future__ import annotations

import random
import traceback
from typing import Any

from ..agents.worker import WorkerLoop, WorkerOutcome
from ..attacks.fixed import AttackController
from ..config import RunConfig
from ..evaluation.monitor import Audit, audit
from ..models.base import Backend
from ..planning.allocation import shortest_schedule
from ..planning.costs import CostEstimates, estimates
from ..policies.core import catalogue, choose_plan, ordinary_routes
from ..schemas import (Alarm, AttackSpec, DelegationPlan, EpisodeManifest, EpisodeResult,
                       PreparationItem, RecoveryRoute, RecoveryUnit, TaskInstance)
from ..util import BCError, digest, plain, read_json
from .budget import BudgetExceeded, BudgetLedger
from .persistence import EpisodeJournal
from .provenance import ProvenanceStore


class Interrupted(BCError):
    pass


def plan_from(data: dict[str, Any]) -> DelegationPlan:
    values = dict(data)
    values["units"] = tuple(RecoveryUnit(**{**u, "inputs": tuple(u["inputs"]), "outputs": tuple(u["outputs"])})
                            for u in values["units"])
    for key in ("preparation", "replicas"):
        values[key] = tuple(tuple(p) for p in values[key])
    return DelegationPlan(**values)


class EpisodeEngine:
    def __init__(self, task: TaskInstance, manifest: EpisodeManifest, config: RunConfig,
                 backend: Backend, journal: EpisodeJournal, attempt_id: str,
                 stop_requested=lambda: False) -> None:
        self.task, self.manifest, self.config = task, manifest, config
        from ..planning.decomposition import resolve
        self.task, self.finite_candidate, self.finite_selection = resolve(task, config)
        self.backend, self.journal, self.attempt_id = backend, journal, attempt_id
        self.stop_requested = stop_requested
        self.ledger = BudgetLedger(config.budget.total, config.budget)
        if self.finite_candidate:
            self.ledger.charge("planning", config.budget.tool_charge, kind="finite_graph_validation", cpu_limit_seconds=1)
        self.store = ProvenanceStore()
        self.plan: DelegationPlan | None = None
        self.attacker: AttackController | None = None
        self.costs: CostEstimates | None = None
        self.candidates: dict[str, list[str]] = {}
        self.preparations: list[PreparationItem] = []
        self.completed: list[str] = []
        self.routes: list[RecoveryRoute] = []
        self.alarm: Alarm | None = None
        self.selected: dict[str, str] = {}
        self.phase = "planning"
        self.rng = random.Random(manifest.seed)
        self.retained = 0
        self.integration_passed: bool | None = None
        self.error: str | None = None
        from .data_domain import DataDomain, DATA_KINDS
        self.domain = DataDomain(self) if task.kind in DATA_KINDS else None

    def state(self, boundary: str) -> dict[str, Any]:
        return plain({"manifest_hash": digest(self.manifest), "boundary": boundary,
                      "plan": self.plan, "attacker": self.attacker, "costs": self.costs,
                      "ledger": self.ledger, "store": self.store.export(), "phase": self.phase,
                      "candidates": self.candidates, "preparations": self.preparations,
                      "completed": self.completed, "routes": self.routes, "alarm": self.alarm,
                      "selected": self.selected, "rng": self.rng.getstate(), "retained": self.retained,
                      "integration_passed": self.integration_passed})

    def boundary(self, name: str) -> None:
        self.journal.checkpoint(self.state(name))
        self.journal.event("boundary", name=name, phase=self.phase, attempt_id=self.attempt_id,
                           work=self.ledger.spent)
        if self.stop_requested() and name != "model_inflight":
            raise Interrupted("Termination requested; checkpoint saved at a safe model/tool boundary")

    def restore(self, state: dict[str, Any]) -> None:
        self.plan = plan_from(state["plan"]) if state["plan"] else None
        attack = state["attacker"]
        self.attacker = AttackController(AttackSpec(**attack["spec"]), tuple(attack["coalition"]),
                                         attack["selection_work"]) if attack else None
        self.costs = CostEstimates(**state["costs"]) if state["costs"] else None
        ledger = state["ledger"]
        self.ledger = BudgetLedger(ledger["cap"], self.config.budget, ledger["entries"],
                                   ledger["reservations"], ledger["historical"])
        self.ledger.uncertain_inflight()
        if self.finite_candidate:
            self.ledger.charge("planning", self.config.budget.tool_charge, kind="finite_graph_revalidation", cpu_limit_seconds=1)
            if self.finite_selection:
                self.ledger.charge("planning", self.finite_selection["search_states"], kind="finite_selector_revalidation")
        self.store = ProvenanceStore.restore(state["store"])
        for key in ("phase", "candidates", "completed", "selected", "retained", "integration_passed"):
            setattr(self, key, state[key])
        self.preparations = [PreparationItem(**p) for p in state["preparations"]]
        self.routes = [RecoveryRoute(**r) for r in state["routes"]]
        self.alarm = Alarm(**state["alarm"]) if state["alarm"] else None
        def tuples(x: Any) -> Any:
            return tuple(tuples(y) for y in x) if isinstance(x, list) else x
        self.rng.setstate(tuples(state["rng"]))
        self.journal.event("resumed", attempt_id=self.attempt_id, prior_boundary=state["boundary"],
                           semantics="completed operations retained; interrupted operation restarted and prior work charged")

    def worker(self) -> WorkerLoop:
        assert self.attacker is not None
        return WorkerLoop(self.backend, self.config, self.ledger, self.store, self.attacker, self.boundary, self.domain)

    def operation(self, key: str, unit: str, worker: str, stage: str, operation: str,
                  reads: tuple[str, ...] = (), floor: float = 0) -> str | None:
        if key in self.completed:
            return None
        before = self.ledger.spent
        if self.domain and self.task.kind == "silo" and stage == "primary":
            missing_inputs = [d for d in self.task.metadata.get("dependencies", {}).get(unit, []) if not self.candidates.get(d)]
            if missing_inputs:
                self.store.events.append({"type": "blocked_primary_input", "unit": unit, "worker": worker,
                                          "missing": missing_inputs})
        generation_seed = int(digest([self.manifest.seed, unit, worker, operation, "generation"])[:8], 16)
        replayed = None
        if self.domain and stage == "repair" and operation == "implement" and not self.attacker.withholds(worker):
            replayed = self.domain.try_replay(unit, worker, stage, floor)
        outcome = WorkerOutcome("replayed", replayed.id, 0) if replayed else self.worker().run(self.task, unit, worker, stage, generation_seed,
                                    operation=operation, allowed_artifacts=reads, floor=floor,
                                    fresh_context=stage != "primary" and self.manifest.policy != "single")
        if self.domain and outcome.status == "withheld":
            self.store.events.append({"type": "public_timeout", "unit": unit, "worker": worker})
        if outcome.artifact_id:
            if operation == "prepare":
                self.preparations.append(PreparationItem(f"prep:{unit}:{worker}", unit, worker,
                    outcome.artifact_id, "source_index_outline", self.ledger.spent-before))
            else:
                self.candidates.setdefault(unit, []).append(outcome.artifact_id)
        self.completed.append(key)
        self.journal.event("operation", key=key, unit=unit, executor=worker, operation=operation,
                           measured_work=self.ledger.spent-before, outcome=outcome.status)
        self.boundary("operation_complete")
        return outcome.artifact_id

    def public_audit(self, stage: str) -> Audit:
        assert self.plan is not None
        candidate_count = sum(self.store.artifacts[k].valid for values in self.candidates.values() for k in values)
        checks = len(self.plan.units) + candidate_count * max(1 if self.domain else 0, len(self.task.public_cases))
        self.ledger.charge(stage, self.config.budget.tool_charge * checks,
                           kind="public_audit", tool_calls=checks, cpu_limit_seconds=1)
        if self.domain:
            return self.domain.audit(self.plan.units,
                {u: [self.store.artifacts[k] for k in keys] for u, keys in self.candidates.items()})
        return audit(self.task, self.plan.units,
                     {u: [self.store.artifacts[k] for k in keys] for u, keys in self.candidates.items()})

    def plan_primary(self) -> None:
        self.ledger.charge("planning", 1, kind="catalogue_setup")
        from ..tasks.data_manifest import policy_view
        planning_task = policy_view(self.task) if self.domain else self.task
        self.costs = estimates(self.config, self.backend, planning_task)
        # Planning is a finite deterministic protected operation, charged by visited states.
        cap = self.ledger.remaining
        limit = min(10000, int(cap))
        if limit < 1:
            raise BudgetExceeded("No allowance left for planning")
        reservation = self.ledger.reserve_work("planning", limit, "finite_search")
        self.boundary("planning_inflight")
        try:
            allocation_trace = {} if self.config.allocation_diagnostics else None
            if self.finite_candidate:
                from ..planning.decomposition import delegation
                self.plan = delegation(self.finite_candidate, self.config.budget.total*self.config.budget.reserve_fraction)
                if self.finite_selection:
                    self.plan.search_states = self.finite_selection['search_states']
                    self.journal.event("finite_selection", **self.finite_selection)
            else:
                self.plan = choose_plan(self.manifest.policy, planning_task, self.config, self.costs, cap,
                                        max_search_states=limit, trace=allocation_trace)
            self.ledger.reconcile_work(reservation, self.plan.search_states)
            if allocation_trace is not None:
                from ..util import atomic_json
                from ..diagnostics.allocation import calibration_metadata
                allocation_trace["calibration"] = calibration_metadata(self.config, planning_task)
                atomic_json(self.journal.path / "allocation-diagnostic.json", allocation_trace)
        except Exception:
            if reservation in self.ledger.reservations:
                self.ledger.reconcile_work(reservation, None)
            raise
        self.attacker = AttackController.after_allocation(self.manifest.attack, self.plan)
        if self.finite_candidate and self.manifest.attack.family != "clean":
            from ..planning.decomposition import affected
            from ..schemas import WORKERS
            # Public-plan-aware structural attacker, fixed before execution.
            # No detector sees this coalition; all units by the identity count.
            selected_identity = max(WORKERS, key=lambda w: len(affected(self.finite_candidate, w)))
            self.attacker = AttackController(self.manifest.attack, (selected_identity,))
            self.journal.event("finite_attacker_rule", rule="largest_declared_identity_closure_before_execution")
        frozen = self.task.metadata.get("harness", {}).get("predecessor")
        if self.task.metadata.get("diagnostic_mode") == "boundary" and frozen:
            from ..tasks.silo_diagnostics import validate_predecessor
            validate_predecessor(frozen, self.task.metadata["original_unit"])
            from ..schemas import ArtifactVersion
            for key, record in frozen["artifacts"].items():
                self.store.artifacts[key] = ArtifactVersion(**record)
            self.store.events.append({"type": "frozen_baseline_import", "version": frozen["version"],
                "baseline_manifest_hash": frozen["baseline_manifest_hash"], "checkpoint_hash": frozen["checkpoint_hash"]})
        self.journal.event("allocation_published", plan=self.plan, calibration=self.costs.status)
        self.journal.event("coalition_committed", selection_hash=digest(self.attacker.coalition),
                           attacker_work=self.attacker.selection_work)
        self.phase = "primary"
        self.boundary("allocation_complete")

    def primary(self) -> None:
        assert self.plan is not None
        try:
            for unit, author in self.plan.preparation:
                self.operation(f"prepare:{unit}:{author}", unit, author, "preparation", "prepare", floor=self.plan.reserve)
            for unit in self.plan.units:
                reads = tuple(self.candidates[d][-1] for d in unit.inputs if self.candidates.get(d))
                if self.task.metadata.get("diagnostic_mode") == "boundary":
                    reads = (self.task.metadata["harness"]["predecessor"]["version"],)
                self.operation(f"primary:{unit.id}", unit.id, unit.owner, "primary", "implement", reads,
                               floor=self.plan.reserve)
            for unit, author in self.plan.replicas:
                self.operation(f"replica:{unit}:{author}", unit, author, "replication", "replicate", floor=self.plan.reserve)
        except BudgetExceeded as exc:
            self.error = f"Primary allowance exhausted; auditing partial work and using budgeted repair: {exc}"
            self.journal.event("primary_budget_fallback", reason=self.error)
        observed = self.public_audit("monitoring")
        self.alarm, self.selected = observed.alarm, observed.selected
        self.phase = "alarm"
        self.boundary("primary_complete")

    def freeze_primary(self) -> dict[str, Any]:
        if self.phase == "planning":
            self.plan_primary()
        if self.phase == "primary":
            self.primary()
        if self.phase != "alarm":
            raise BCError("Fixed state can only be captured immediately after the common primary audit")
        return {"schema": "fixed-primary-v1", "task_hash": self.task.source_hash,
                "source_revision": self.manifest.source_revision, "model_hash": self.manifest.model_hash,
                "seed": self.manifest.seed, "selection_seed": self.manifest.attack.selection_seed,
                "budget_rules": plain(self.config.budget), "state": self.state("fixed_alarm")}

    def load_fixed(self) -> None:
        frozen = read_json(self.config.fixed_state_file)
        if frozen["schema"] != "fixed-primary-v1" or frozen["task_hash"] != self.task.source_hash:
            raise BCError("Protocol B task/common decomposition mismatch")
        if frozen["model_hash"] != self.manifest.model_hash or frozen["source_revision"] != self.manifest.source_revision:
            raise BCError("Protocol B source/model mismatch")
        if frozen["budget_rules"] != plain(self.config.budget):
            raise BCError("Protocol B budget-rule mismatch")
        self.restore(frozen["state"])
        if (self.attacker.spec.family != self.manifest.attack.family or
                self.manifest.seed != frozen["seed"] or
                self.manifest.attack.selection_seed != frozen["selection_seed"]):
            raise BCError("Protocol B attack differs from frozen primary")
        # Preparation is deliberately executed from immutable sources in independent
        # contexts AFTER capture but before starting the diagnostic allowance. It is
        # historical work, never a mutation of the common primary trace or alarm.
        self.phase = "diagnostic_preparation"
        self.boundary("diagnostic_base_loaded")

    def diagnostic_preparation(self) -> None:
        if self.manifest.policy in ("recovery", "replication"):
            for i, unit in enumerate(self.plan.units):
                author = ("w0", "w1", "w2", "w3")[(i+1) % 4]
                operation = "replicate" if self.manifest.policy == "replication" else "prepare"
                self.operation(f"diagnostic-prep:{unit.id}", unit.id, author, "preparation", operation)
        self.ledger.start_repair_diagnostic(self.config.budget.repair_allowance)
        self.phase = "alarm"
        self.journal.event("protocol_b", fixed_state_hash=self.manifest.fixed_state_hash,
                           interpretation="equal remaining repair allowance; historical preparation charged separately")
        self.boundary("diagnostic_ready")

    def repair(self) -> None:
        assert self.plan is not None and self.alarm is not None and self.costs is not None
        if self.phase == "alarm":
            invalid = {k for u in self.alarm.units for k in self.candidates.get(u, [])}
            self.store.invalidate(invalid, set(self.alarm.suspicious_authors))
            self.selected = {u: k for u, k in self.selected.items() if self.store.artifacts[k].valid}
            if self.alarm.units or self.alarm.suspicious_authors:
                # All methods may retain alternate valid candidates after invalidation.
                # This also audits historical independent replicas in Protocol B.
                self.selected = self.public_audit("repair_monitoring").selected
            self.retained = len(self.selected)
            self.phase = "repair"
            self.boundary("invalidation_complete")
        available = set(self.selected)
        prep_lookup = {p.id: p.artifact_version for p in self.preparations
                       if self.store.artifacts[p.artifact_version].valid}
        available.update(prep_lookup)
        missing = {u.id for u in self.plan.units} - available
        if not missing or self.manifest.policy == "single":
            return
        routes = catalogue(self.plan, self.costs)
        if self.manifest.policy == "ordinary":
            routes = ordinary_routes(self.plan, self.alarm, missing, self.costs)
        # All practical repair information comes from public suspicion, never truth.
        cap = self.ledger.remaining
        limit = min(10000, int(cap))
        if limit < 1:
            raise BudgetExceeded("No allowance for repair planning")
        reservation = self.ledger.reserve_work("repair_planning", limit, "finite_search")
        self.boundary("repair_planning_inflight")
        try:
            schedule = shortest_schedule(routes, available, {u.id for u in self.plan.units},
                                         set(self.alarm.suspicious_authors), cap, max_states=limit)
            self.ledger.reconcile_work(reservation, schedule.states)
        except Exception:
            if reservation in self.ledger.reservations:
                self.ledger.reconcile_work(reservation, None)
            raise
        self.journal.event("repair_schedule", schedule=schedule)
        if schedule.cost is None:
            # Keep infeasibility observed. Budgeted fallback attempts cold reconstruction
            # in dependency order until the cap stops it; it does not drop the task.
            self.error = f"Predicted schedule {schedule.status}; used budgeted cold fallback"
            chosen = ordinary_routes(self.plan, self.alarm, missing, self.costs)
        else:
            chosen = [next(r for r in routes if r.id == key) for key in schedule.routes]
        for route in chosen:
            if f"route:{route.id}" in self.completed:
                continue
            assets = set(self.selected) | set(prep_lookup)
            if not (set(route.prerequisites) | set(route.preparation)) <= assets:
                route.measured_outcome = {"status": "prerequisite_failed", "work": 0, "artifact": None}
                self.routes.append(route)
                continue
            reads = tuple(prep_lookup[p] for p in route.preparation if p in prep_lookup)
            reads += tuple(self.selected[u] for u in route.prerequisites if u in self.selected)
            unit = route.produces[0].split(":")[1] if route.operation == "prepare" else route.produces[0]
            before = self.ledger.spent
            artifact = self.operation(f"route:{route.id}", unit, route.executor, "repair",
                                      "prepare" if route.operation == "prepare" else "implement", reads)
            route.measured_outcome = {"artifact": artifact, "work": self.ledger.spent-before,
                "prediction_error": self.ledger.spent-before-route.predicted_cost}
            self.routes.append(route)
            if artifact and route.operation == "prepare":
                prep_lookup[f"prep:{unit}:{route.executor}"] = artifact
            elif artifact:
                self.selected[unit] = artifact
            self.boundary("route_complete")

    def run(self, resume: bool = True) -> EpisodeResult:
        previous = self.journal.previous(digest(self.manifest)) if resume else None
        status, success, final = "completed", None, {}
        try:
            if previous:
                self.restore(previous)
            elif self.manifest.protocol == "B":
                self.load_fixed()
            if self.phase == "diagnostic_preparation":
                self.diagnostic_preparation()
            if self.phase == "planning":
                self.plan_primary()
            if self.phase == "primary":
                self.primary()
            if self.phase in ("alarm", "repair"):
                self.repair()
                self.phase = "integration"
                self.boundary("repair_complete")
            if self.phase == "integration":
                if self.finite_candidate:
                    from ..planning.decomposition import dependency_report
                    self.ledger.charge("integration", self.config.budget.tool_charge, kind="finite_dependency_audit", cpu_limit_seconds=1)
                    self.journal.event("finite_observed_dependencies", **dependency_report(self.finite_candidate, self.store))
                observed = self.public_audit("integration")
                self.selected = observed.selected
                from ..tasks.workflow import run_outputs, expected
                programs = {u: self.store.artifacts[k].content for u, k in self.selected.items()}
                self.ledger.charge("integration", self.config.budget.tool_charge * len(self.task.public_cases),
                                   kind="joint_public_check", tool_calls=len(self.task.public_cases), cpu_limit_seconds=1)
                try:
                    self.integration_passed = self.domain.integrate() if self.domain else all(
                        run_outputs(self.task, programs, x) == expected(self.task, x) for x in self.task.public_cases)
                except BCError as exc:
                    from .data_domain import TaskUnavailable
                    if isinstance(exc, TaskUnavailable):
                        raise
                    self.integration_passed = False
                self.phase = "evaluation"
                self.boundary("integration_complete")
            # Terminal evaluation has no return edge into policy/worker execution.
            from ..evaluation.hidden import evaluate
            final = self.domain.evaluate() if self.domain else evaluate(self.task, {u: self.store.artifacts[k].content for u, k in self.selected.items()},
                             self.manifest.evaluation_seed)
            success = final["complete_task_success"] and self.integration_passed is True
        except BudgetExceeded as exc:
            status, success, self.error = "budget_exhausted", False, str(exc)
        except Interrupted as exc:
            status, self.error = "interrupted", str(exc)
        except Exception as exc:
            from .data_domain import TaskUnavailable
            status = exc.status if isinstance(exc, TaskUnavailable) else "infrastructure_failed"
            self.error = str(exc) if isinstance(exc, TaskUnavailable) else ("Restricted data episode failed; inspect private journal" if self.domain else f"{type(exc).__name__}: {exc}")
            self.journal.event("failure", error=self.error, traceback=traceback.format_exc())
        alarmed = bool(self.alarm and (self.alarm.units or self.alarm.suspicious_authors))
        cumulative, violations = 0.0, 0
        for entry in self.ledger.historical + self.ledger.entries:
            cumulative += entry["work"]
            if (self.plan and entry["stage"] in ("preparation", "primary", "replication") and
                    self.config.budget.total - cumulative < self.plan.reserve - 1e-9):
                violations += 1
        result = EpisodeResult(self.manifest.episode_id, self.attempt_id, self.manifest.experiment_id,
            self.manifest.protocol, self.manifest.mode, status, success, self.task.id, self.task.group,
            self.manifest.policy, self.manifest.attack.family, self.manifest.seed, self.ledger.summary(),
            {"alarmed": alarmed, "detected_but_unfinished": alarmed and success is False,
             "false_alarm": alarmed and self.manifest.attack.family == "clean",
             "unaffected_work_retained": self.retained, "integration_failure": status == "completed" and not success,
             "reserve_violations": violations, "final_evaluation": final,
             "joint_public_integration": self.integration_passed,
             "attacker_search_work": self.attacker.selection_work if self.attacker else 0,
             "allocation_status": self.plan.allocation_status if self.plan else "not_planned",
             "prediction_errors": [r.measured_outcome for r in self.routes]},
            {"manifest_hash": digest(self.manifest), "source_revision": self.manifest.source_revision,
             "model_hash": self.manifest.model_hash, "data_hash": self.manifest.data_hash,
             "calibration": plain(self.costs), "plan": plain(self.plan),
             "fixed_state_hash": self.manifest.fixed_state_hash, "import_path": __file__,
             "backend_runtime": getattr(self.backend, "runtime", {"backend": "deterministic-mock-v1"})},
            ["Development only; confirmatory claims disabled", ("Restricted data-workflow adaptation; not repository coding evidence" if self.domain else "Workflow fixtures are synthetic, not CooperBench"),
             "Costs use an explicit token/tool surrogate, not measured FLOPs",
             "Interrupted worker operations restart with all prior and uncertain work charged"], self.error)
        if self.domain:
            from ..tasks.data_manifest import regime
            result.provenance.update({"result_schema": "bc-result-v2", "data_regime": regime(self.task)})
            result.metrics["tool_rejections"] = sum(e["type"] == "prohibited_or_malformed_action" for e in self.store.events)
            result.metrics["query_replays"] = sum(e["type"] == "query_replay" for e in self.store.events)
            result.metrics["shard_transfers"] = sum(e["type"] == "shard_transfer" for e in self.store.events)
        from ..evaluation.metrics import observations
        result.metrics["observations"] = observations(status, final, self.integration_passed,
            self.task.required_outputs if self.phase == "evaluation" else None,
            self.selected if self.phase == "evaluation" else None,
            not set(self.task.required_outputs)-set(self.selected) if self.domain and self.phase == "evaluation" else None)
        result.provenance["condition"] = {"profile": self.config.development_profile,
            "silo_interface": self.config.silo_interface,
            "diagnostic_mode": self.task.metadata.get("diagnostic_mode", "full"),
            "operation_measurement": self.config.operation_measurement}
        if self.config.organization != "legacy":
            result.provenance["condition"]["organization"] = self.config.organization
        if self.config.sqlite_error_feedback != "generic":
            result.provenance["condition"]["sqlite_error_feedback"] = self.config.sqlite_error_feedback
        if self.config.model.action_constraint != "none":
            result.provenance["condition"]["action_constraint"] = self.config.model.action_constraint
        self.journal.result(result)
        return result
