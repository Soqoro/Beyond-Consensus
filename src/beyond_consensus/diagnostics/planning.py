"""Read-only structural inventory of the actual legacy candidate catalogue."""
from ..policies.core import candidate_plans
from ..tasks.data_manifest import policy_view
from ..util import digest, plain


def structure(plan):
    # Boundary/plan names and ownership alone are not new decompositions.
    return [{"id": u.id, "outputs": list(u.outputs), "inputs": list(u.inputs)} for u in plan.units]


def inventory(task, config):
    task = policy_view(task)
    plans = candidate_plans("recovery", task, config.budget.total*config.budget.reserve_fraction)
    def distinct(fn):
        return len({digest(fn(p)) for p in plans})
    examples = {}
    for plan in plans:
        key = digest(structure(plan))
        if key not in examples:
            examples[key] = {"boundary_label": plan.units[0].boundary, "units": structure(plan),
                "owners": {u.id: u.owner for u in plan.units}, "primary_order": [u.id for u in plan.units],
                "preparation": plain(plan.preparation), "reserve": plan.reserve}
    return {"task_id": task.id, "task_kind": task.kind, "group": task.group,
        "public_task_hash": digest(task), "candidate_count": len(plans),
        "required_terminal_obligations": list(task.required_outputs),
        "terminal_obligation_count": len(task.required_outputs),
        "distinct": {
            "terminal_obligation_sets": distinct(lambda p: sorted(o for u in p.units for o in u.outputs)),
            "unit_boundaries": distinct(lambda p: [(u.id, u.outputs) for u in p.units]),
            "dependency_graphs": distinct(lambda p: [(u.id, u.inputs) for u in p.units]),
            "primary_execution_orders": distinct(lambda p: [u.id for u in p.units]),
            "primary_workflows_including_reads": distinct(structure),
            "owner_assignments": distinct(lambda p: [(u.id, u.owner) for u in p.units]),
            "preparation_selections": distinct(lambda p: p.preparation),
            "reserve_values": distinct(lambda p: p.reserve),
            "material_plans_including_preparation": distinct(lambda p: [structure(p), p.preparation])},
        "introduced_intermediate_units": [],
        "terminal_artifacts_also_used_as_inputs": sorted({d for p in plans for u in p.units for d in u.inputs}),
        "examples": list(examples.values()),
        "reserve": {"optimized": False, "configured_fraction": config.budget.reserve_fraction,
            "recovery_replication": plans[0].reserve, "legacy_jit": 0,
            "opt_in_organization_arms": "same configured fraction for fixed and selected boundaries"},
        "candidate_meaning": "Two exposure boundaries times all preparation masks; owners and unit outputs fixed. Replication uses the same masks for duplicates.",
        "objective": {"recovery": "min max_identity(base + predicted repair); both weights 1",
            "replication": "lexicographic worst exposed cold work, then base; different objective",
            "normal": "unit count * cold", "preparation": "mask count * prepare",
            "checking": None, "integration": None, "search_overhead": None,
            "legacy_recovery_feasibility": "base <= cap and base + scenario repair <= cap; reserve not a solve_allocation constraint",
            "legacy_replication_feasibility": "base <= cap - configured reserve",
            "runtime": "all actual charges share cap; primary/preparation/replication floor at plan.reserve; audit/repair/integration consume remaining cap",
            "can_exhaust_despite_predicted_feasibility": True},
        "legality": "Structural inventory only; no semantic equivalence or model competence claim",
        "native_selection_readiness": "blocked: no validated native material alternative/calibrated operation model" if task.kind != "workflow_fixture" else "existing fixture dependency exposure alternatives only"}


def audit(tasks, config):
    return {"schema": "bc-planning-structure-v1", "evidence": "current code and public task structure; not historical allocation traces",
        "model_executed": False, "config_hash": digest(config), "tasks": [inventory(t, config) for t in tasks],
        "source_paths": ["policies/core.py:candidate_plans/common_units", "planning/allocation.py:solve_allocation/shortest_schedule",
            "runtime/episode.py:primary/public_audit/repair", "agents/worker.py:allowed_artifacts"]}
