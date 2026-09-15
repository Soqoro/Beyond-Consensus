"""Policies use public alarms, permitted sources, and a common operation catalogue."""

from __future__ import annotations

import itertools
from dataclasses import replace

from ..config import RunConfig
from ..planning.allocation import solve_allocation
from ..planning.costs import CostEstimates
from ..schemas import Alarm, DelegationPlan, RecoveryRoute, RecoveryUnit, TaskInstance, WORKERS
from ..tasks.workflow import dependencies, ordered_units
from ..util import digest


def common_units(task: TaskInstance, boundary: str = "isolated_contract") -> tuple[RecoveryUnit, ...]:
    return tuple(RecoveryUnit(u, f"Implement the permitted contract for {u}", WORKERS[i % 4],
                              dependencies(task, u) if boundary == "context_linked" else (),
                              (u,), boundary) for i, u in enumerate(ordered_units(task)))


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
                costs: CostEstimates, cap: float, max_search_states: int = 10000) -> DelegationPlan:
    reserve = config.budget.total * config.budget.reserve_fraction if policy in ("recovery", "replication") else 0
    basic = DelegationPlan("common", common_units(task), reserve=reserve)
    if policy in ("ordinary", "jit", "single"):
        if policy == "single":
            basic.units = tuple(replace(u, owner="w0") for u in basic.units)
        return basic
    candidates = []
    for boundary in ("isolated_contract", "context_linked"):
        units = common_units(task, boundary)
        # Every subset, including no preparation/replication. Backup authors rotate;
        # the catalogue permits every identity during later reconstruction.
        for mask in itertools.product((False, True), repeat=len(units)):
            choices = tuple((u.id, WORKERS[(WORKERS.index(u.owner)+1) % 4])
                            for u, chosen in zip(units, mask) if chosen)
            candidate = DelegationPlan(digest([boundary, choices])[:16], units,
                                        choices if policy == "recovery" else (),
                                        choices if policy == "replication" else (), reserve)
            candidates.append(candidate)
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
        return plan
    allocation = solve_allocation(candidates, lambda p: catalogue(p, costs), base_cost, cap, max_states=max_search_states)
    plan = allocation.plan or basic
    plan.allocation_status = allocation.status
    plan.predicted_cost, plan.search_states = allocation.worst_cost, allocation.states
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
