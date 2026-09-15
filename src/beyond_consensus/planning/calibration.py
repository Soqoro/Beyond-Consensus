"""Measure the shared operation catalogue on development workflow groups."""

from __future__ import annotations

from statistics import mean
from typing import Any

from ..agents.worker import WorkerLoop
from ..attacks.fixed import AttackController
from ..config import RunConfig
from ..models.base import Backend
from ..policies.core import common_units
from ..runtime.budget import BudgetLedger
from ..runtime.provenance import ProvenanceStore
from ..schemas import AttackSpec, DelegationPlan, TaskInstance
from ..util import BCError, digest
from .costs import compatibility


def calibrate(config: RunConfig, backend: Backend, tasks: list[TaskInstance]) -> dict[str, Any]:
    if any(t.kind != "workflow_fixture" for t in tasks):
        raise BCError("Repository calibration requires the missing approved sandbox adapter")
    measurements = []
    for task in tasks:
        store, ledger = ProvenanceStore(), BudgetLedger(config.budget.total, config.budget)
        attacker = AttackController.after_allocation(AttackSpec("clean"), DelegationPlan("calibration", common_units(task)))
        loop = WorkerLoop(backend, config, ledger, store, attacker)
        for unit in task.required_outputs:
            prepared_id = None
            for operation, identity, label in (("implement", "w0", "cold"), ("prepare", "w1", "prepare"),
                                                ("implement", "w2", "prepared")):
                before = ledger.spent
                outcome = loop.run(task, unit, identity, "calibration", 0, operation=operation,
                    allowed_artifacts=(prepared_id,) if label == "prepared" and prepared_id else ())
                if label == "prepare":
                    prepared_id = outcome.artifact_id
                measurements.append({"group": task.group, "task_id": task.id, "unit": unit,
                    "operation": label, "work": ledger.spent-before, "status": outcome.status})
                if outcome.status != "submitted":
                    raise BCError("Calibration operation did not submit; inspect model/tool competence before using estimates")
    costs = {op: mean(m["work"] for m in measurements if m["operation"] == op)
             for op in ("cold", "prepare", "prepared")}
    data = {"compatibility": compatibility(config), "groups": sorted({t.group for t in tasks}),
            "costs": costs, "origin": "mock-measured" if config.model.backend == "mock" else "development-measured",
            "sample_count": len(measurements)}
    data["id"] = digest([data, measurements])
    return {"calibration": data, "measurements": measurements}
