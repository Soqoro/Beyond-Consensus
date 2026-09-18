"""Policies use public alarms, permitted sources, and a common operation catalogue."""

from __future__ import annotations

import itertools
from dataclasses import replace

from ..config import RunConfig
from ..planning.allocation import solve_allocation
from ..planning.costs import CostEstimates
from ..schemas import Alarm, DelegationPlan, RecoveryRoute, RecoveryUnit, TaskInstance, WORKERS
from ..tasks.workflow import dependencies, ordered_units
from ..util import BCError, digest, plain


def common_units(task: TaskInstance, boundary: str = "isolated_contract") -> tuple[RecoveryUnit, ...]:
    return tuple(RecoveryUnit(u, f"Implement the permitted contract for {u}", WORKERS[i % 4],
                              dependencies(task, u) if boundary == "context_linked" or task.kind == "silo" else (),
                              (u,), boundary) for i, u in enumerate(ordered_units(task)))


def candidate_plans(policy: str, task: TaskInstance, reserve: float) -> list[DelegationPlan]:
    """Legacy ordered catalogue: two exposure boundaries times backup masks.

    Unit boundaries, terminal obligations, primary order and owners stay fixed.
    Boundary labels need not denote different dependency graphs.
    """
    candidates = []
    for boundary in ("isolated_contract", "context_linked"):
        units = common_units(task, boundary)
        for mask in itertools.product((False, True), repeat=len(units)):
            choices = tuple((u.id, WORKERS[(WORKERS.index(u.owner)+1) % 4])
                            for u, chosen in zip(units, mask) if chosen)
            candidates.append(DelegationPlan(digest([boundary, choices])[:16], units,
                choices if policy == "recovery" else (),
                choices if policy == "replication" else (), reserve))
    return candidates


def boundary_plans(task: TaskInstance, reserve: float) -> list[DelegationPlan]:
    """Existing primary-read alternatives only; no generated native view plans."""
    return [DelegationPlan("boundary-jit-v1:"+boundary, common_units(task, boundary), reserve=reserve)
            for boundary in ("isolated_contract", "context_linked")]


def require_boundary_variation(task: TaskInstance) -> None:
    plans = boundary_plans(task, 0)
    if tuple(u.inputs for u in plans[0].units) == tuple(u.inputs for u in plans[1].units):
        raise BCError("Decomposition readiness gap: existing boundaries have identical primary dependency structures")
    # Native independence/semantic equivalence is not established by structural checks.
    if task.kind != "workflow_fixture":
        raise BCError("Decomposition readiness gap: native alternative legality and calibrated operation costs are unvalidated")


def catalogue(plan: DelegationPlan, costs: CostEstimates) -> list[RecoveryRoute]:
    routes = []
    for unit in plan.units:
        for worker in WORKERS:
            prep = f"prep:{unit.id}:{worker}"
            routes.append(RecoveryRoute(f"index:{unit.id}:{worker}", (), (prep,), worker, (),
                                        (worker,), costs.prepare, "prepare"))
            routes.append(RecoveryRoute(f"cold:{unit.id}:{worker}", unit.inputs, (unit.id,), worker,
                                        (), (worker,), costs.cold, "cold"))
            for author in WORKERS:
                prep = f"prep:{unit.id}:{author}"
                routes.append(RecoveryRoute(f"prepared:{unit.id}:{worker}:{author}", unit.inputs,
                                            (unit.id,), worker, (prep,), (worker, author),
                                            costs.prepared, "prepared"))
    return routes


def choose_plan(policy: str, task: TaskInstance, config: RunConfig,
                costs: CostEstimates, cap: float, max_search_states: int = 10000,
                trace: dict | None = None) -> DelegationPlan:
    if config.organization != "legacy":
        require_boundary_variation(task)
        if config.model.backend != "mock" and costs.status != "development-calibrated":
            raise BCError("Decomposition readiness gap: real organization selection requires compatible measured calibration")
        reserve = config.budget.total * config.budget.reserve_fraction
        candidates = boundary_plans(task, reserve)
        if config.organization != "select_boundary":
            plan = candidates[config.organization == "fixed_linked"]
            plan.allocation_status = "prespecified_boundary"
        else:
            # Same JIT catalogue, owners and reserve rule in all organization arms.
            # Unlike legacy recovery, both arms enforce the same primary reserve gate.
            eligible = [p for p in candidates if len(p.units)*costs.cold <= cap-reserve]
            allocation = solve_allocation(eligible, lambda p: catalogue(p, costs),
                lambda p: len(p.units)*costs.cold, cap, max_states=max_search_states,
                trace=trace.setdefault("evaluations", []) if trace is not None else None)
            plan = allocation.plan or candidates[0]
            plan.allocation_status, plan.predicted_cost, plan.search_states = allocation.status, allocation.worst_cost, allocation.states
        if trace is not None:
            trace.update(schema="bc-boundary-jit-v1", organization=config.organization,
                candidate_count=len(candidates) if config.organization == "select_boundary" else 1,
                candidates=[plain(p) for p in candidates], selected=plain(plan),
                reserve_rule="configured_fraction_same_across_organization_arms", reserve=reserve,
                preparation_permission="identical JIT catalogue after alarm; no advance preparation",
                unmodeled_costs={"checking": None, "integration": None, "planner_search_overhead": None},
                semantic_equivalence="fixture obligations unchanged; not inferred from structural validation")
        return plan
    reserve = config.budget.total * config.budget.reserve_fraction if policy in ("recovery", "replication") else 0
    basic = DelegationPlan("common", common_units(task), reserve=reserve)
    if trace is not None:
        trace.update(schema="bc-allocation-trace-v1", policy=policy, task_id=task.id, group=task.group,
            costs=plain(costs), cap=cap, reserve=reserve, state_limit=max_search_states,
            work_unit="token_tool_surrogate_v1", candidates=[], evaluations=[],
            unmodeled_costs=["checking", "integration", "planner_search_overhead"],
            calibration_warning="missing_calibration" if not costs.calibration_id else None,
            scope="finite boundary/subset catalogue; single-identity public-detection scenarios, not attacker truth")
    if policy in ("ordinary", "jit", "single"):
        if policy == "single":
            basic.units = tuple(replace(u, owner="w0") for u in basic.units)
        if trace is not None:
            trace.update(selected=plain(basic), decision="fixed_policy_no_advance_search", candidate_count=1,
                         candidates=[{"plan": plain(basic), "routes": plain(catalogue(basic, costs))}])
        return basic
    candidates = candidate_plans(policy, task, reserve)
    if trace is not None:
        trace["candidate_count"] = len(candidates)
        trace["preparation_candidates"] = sum(bool(p.preparation) for p in candidates)
        trace["candidates"] = [{"plan": plain(p), "routes": plain(catalogue(p, costs)),
            "normal": len(p.units)*costs.cold, "preparation": len(p.preparation)*costs.prepare,
            "replication": len(p.replicas)*costs.cold, "checking": None, "integration": None,
            "primary_allowance_feasible": (len(p.units)+len(p.replicas))*costs.cold+len(p.preparation)*costs.prepare <= cap-reserve,
            "candidate_generation": "generated", "structural_validation": "valid_schema"} for p in candidates]
    def base_cost(plan: DelegationPlan) -> float:
        return len(plan.units)*costs.cold + len(plan.preparation)*costs.prepare + len(plan.replicas)*costs.cold
    if policy == "replication":
        # Minimize exposed work left at the alarm subject to a primary cap and a
        # tunable repair reserve. All duplicates execute independently later.
        evaluated = candidates[:max_search_states // len(WORKERS)]
        feasible = [p for p in evaluated if base_cost(p) <= cap-reserve]
        if not feasible:
            basic.allocation_status = "infeasible" if len(evaluated) == len(candidates) else "search_limit_no_certificate"
            basic.search_states = len(evaluated)*len(WORKERS)
            if trace is not None:
                trace.update(selected=plain(basic), decision=basic.allocation_status)
            return basic
        def score(p: DelegationPlan) -> tuple[float, float]:
            worst = max(sum(costs.cold for u in p.units if u.owner == compromised
                            and not any(k == u.id and a != compromised for k, a in p.replicas))
                        for compromised in WORKERS)
            return worst, base_cost(p)
        plan = min(feasible, key=score)
        plan.predicted_cost = sum(score(plan))
        plan.search_states = len(evaluated)*len(WORKERS)
        plan.allocation_status = "exact_finite_replication_objective" if len(evaluated) == len(candidates) else "heuristic_search_limit"
        if trace is not None:
            trace.update(selected=plain(plan), decision="selected_replication" if plan.replicas else "selected_no_replication")
            trace["evaluations"] = [{"plan_id": p.id, "objective": score(p),
                "reason": "selected" if p.id == plan.id else "over_budget" if p not in feasible else "not_selected",
                "scenarios": [{"excluded_identity": w, "exposed_reconstruction": sum(costs.cold for u in p.units
                    if u.owner == w and not any(k == u.id and a != w for k,a in p.replicas))} for w in WORKERS]}
                for p in evaluated]
        return plan
    allocation = solve_allocation(candidates, lambda p: catalogue(p, costs), base_cost, cap, max_states=max_search_states,
                                  trace=trace["evaluations"] if trace is not None else None)
    plan = allocation.plan or basic
    plan.allocation_status = allocation.status
    plan.predicted_cost, plan.search_states = allocation.worst_cost, allocation.states
    if trace is not None:
        trace.update(selected=plain(plan), decision=allocation.status if allocation.plan is None else
                     "selected_no_preparation" if not plan.preparation else "selected_preparation")
        evaluated_ids = {e["plan_id"] for e in trace["evaluations"]}
        trace["evaluations"].extend({"plan_id": p.id, "reason": "unavailable_search_limit"}
                                    for p in candidates if p.id not in evaluated_ids)
    return plan


def ordinary_routes(plan: DelegationPlan, alarm: Alarm, missing: set[str], costs: CostEstimates) -> list[RecoveryRoute]:
    """Documented fallback: one fresh next-eligible identity per affected unit."""
    routes = []
    for unit in plan.units:
        if unit.id not in missing:
            continue
        eligible = [WORKERS[(WORKERS.index(unit.owner)+offset) % 4] for offset in range(1, 5)
                    if WORKERS[(WORKERS.index(unit.owner)+offset) % 4] not in alarm.suspicious_authors]
        if eligible:
            routes.append(RecoveryRoute(f"ordinary:{unit.id}", unit.inputs, (unit.id,), eligible[0],
                                        (), (eligible[0],), costs.cold, "cold"))
    return routes
