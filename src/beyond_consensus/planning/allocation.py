"""Finite robust allocation and exact shortest reconstruction in a monotone DAG.

Optimality is only over the supplied finite catalogue and predicted additive costs.
Shared prerequisites are assets in a state, so they are purchased once.
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass
from typing import Callable

from ..schemas import DelegationPlan, RecoveryRoute, WORKERS
from ..util import plain


@dataclass(frozen=True)
class Schedule:
    routes: tuple[str, ...]
    cost: float | None
    status: str
    states: int


def shortest_schedule(routes: list[RecoveryRoute], available: set[str], targets: set[str],
                      excluded: set[str], cap: float, max_states: int = 10000,
                      trace: dict | None = None) -> Schedule:
    original = routes
    if trace is not None:
        trace.update(available=sorted(available), targets=sorted(targets), excluded=sorted(excluded),
                     allowance=cap, state_limit=max_states)
    if cap < 0:
        return Schedule((), None, "infeasible", 0)
    # Safe dominance pruning: a route with weaker prerequisites, no additional
    # contributors, identical outputs/executor and no greater cost supersedes it.
    routes = [r for r in routes if not any(
        q.id != r.id and q.produces == r.produces and q.executor == r.executor
        and q.predicted_cost <= r.predicted_cost
        and set(q.contributors) <= set(r.contributors)
        and (set(q.prerequisites) | set(q.preparation)) < (set(r.prerequisites) | set(r.preparation))
        for q in routes)]
    needed = set(targets)
    while True:
        previous = set(needed)
        for route in routes:
            if set(route.produces) & needed:
                needed.update(route.prerequisites)
                needed.update(route.preparation)
        if previous == needed:
            break
    routes = [r for r in routes if set(r.produces) & needed]
    if trace is not None:
        active = {r.id for r in routes}
        trace["routes"] = [{**plain(r), "structural_validation": "valid_schema",
            "eligibility": "contributor_conflict" if r.executor in excluded or set(r.contributors) & excluded else
                           "predicted_dominated_or_irrelevant" if r.id not in active else
                           "requires_prerequisite" if not (set(r.prerequisites)|set(r.preparation)) <= available else "available"}
                          for r in original]
    serial = itertools.count()
    initial = frozenset(available)
    queue = [(0.0, next(serial), initial, ())]
    best = {initial: 0.0}
    states = 0
    while queue:
        cost, _, assets, path = heapq.heappop(queue)
        if cost > best[assets]:
            continue
        if states >= max_states:
            return Schedule((), None, "search_limit_no_certificate", states)
        states += 1
        if targets <= assets:
            return Schedule(path, cost, "exact_finite", states)
        for route in routes:
            if route.executor in excluded or set(route.contributors) & excluded:
                continue
            if not (set(route.prerequisites) | set(route.preparation)) <= assets:
                continue
            added = assets | frozenset(route.produces)
            new_cost = cost + route.predicted_cost
            if added == assets or new_cost > cap or new_cost >= best.get(added, float("inf")):
                continue
            best[added] = new_cost
            heapq.heappush(queue, (new_cost, next(serial), added, path + (route.id,)))
    return Schedule((), None, "infeasible", states)


@dataclass(frozen=True)
class Allocation:
    plan: DelegationPlan | None
    worst_cost: float | None
    status: str
    states: int


def solve_allocation(plans: list[DelegationPlan], routes_for: Callable[[DelegationPlan], list[RecoveryRoute]],
                     cost_for: Callable[[DelegationPlan], float], cap: float,
                     max_states: int = 100000, trace: list | None = None) -> Allocation:
    winner, best_cost, states, limited = None, float("inf"), 0, False
    for plan in plans:
        base = cost_for(plan)
        record = {"plan_id": plan.id, "base_cost": base, "scenarios": [], "worst_total": None,
                  "reason": "over_budget" if base > cap else "evaluating"}
        if trace is not None:
            trace.append(record)
        if base > cap:
            continue
        worst, feasible = base, True
        for compromised in WORKERS:
            affected = {u.id for u in plan.units if u.owner == compromised}
            changed = True
            while changed:
                previous = set(affected)
                affected.update(u.id for u in plan.units if set(u.inputs) & affected)
                changed = affected != previous
            available = {u.id for u in plan.units} - affected
            available.update(u for u, author in plan.replicas if author != compromised)
            available.update(f"prep:{u}:{author}" for u, author in plan.preparation if author != compromised)
            if states >= max_states:
                limited, feasible = True, False
                break
            detail = {} if trace is not None else None
            schedule = shortest_schedule(routes_for(plan), available,
                                         {u.id for u in plan.units}, {compromised}, cap-base,
                                         max_states=max_states-states, trace=detail)
            if trace is not None:
                record["scenarios"].append({"excluded_identity": compromised,
                    "affected_units": sorted(affected), "schedule": plain(schedule), **detail})
            states += schedule.states
            if schedule.cost is None:
                feasible = False
                limited |= schedule.status != "infeasible"
                break
            worst = max(worst, base + schedule.cost)
        if feasible and worst < best_cost:
            winner, best_cost = plan, worst
        record.update(worst_total=worst if feasible else None,
                      reason="feasible" if feasible else "search_limit" if limited else "no_feasible_schedule")
        if limited:
            break
    status = ("heuristic_search_limit" if winner else "search_limit_no_certificate") if limited else (
        "exact_finite" if winner else "infeasible")
    if trace is not None:
        for record in trace:
            if winner and record["plan_id"] == winner.id:
                record["reason"] = "selected_no_preparation" if not winner.preparation else "selected"
            elif record["reason"] == "feasible":
                record["reason"] = ("objective_tie" if record["worst_total"] == best_cost else
                                    "predicted_dominated" if not limited else "not_selected_limited_search")
    return Allocation(winner, best_cost if winner else None, status, states)
