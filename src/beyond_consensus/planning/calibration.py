"""Measure the shared operation catalogue on development workflow groups."""

from __future__ import annotations

from statistics import mean
from pathlib import Path
import tempfile
from types import SimpleNamespace
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
    if any(t.kind == "cooperbench" for t in tasks):
        raise BCError("Legacy repository calibration requires its approved sandbox adapter")
    if not tasks or len({compatibility(config, t) for t in tasks}) != 1:
        raise BCError("Calibration tasks must share environment/scorer/access/limit rules")
    measurements = []
    for task in tasks:
        with tempfile.TemporaryDirectory(prefix="bc-calibration-") as temporary:
            store, ledger = ProvenanceStore(), BudgetLedger(config.budget.total, config.budget)
            attacker = AttackController.after_allocation(AttackSpec("clean"), DelegationPlan("calibration", common_units(task)))
            domain = None
            if task.kind != "workflow_fixture":
                from ..runtime.data_domain import DataDomain
                engine = SimpleNamespace(task=task, config=config, ledger=ledger, store=store,
                    journal=SimpleNamespace(path=Path(temporary)), plan=DelegationPlan("calibration", common_units(task)),
                    selected={}, candidates={}, alarm=None, calibrating=True)
                domain = DataDomain(engine)
            loop = WorkerLoop(backend, config, ledger, store, attacker, domain=domain)
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
    data = {"compatibility": compatibility(config, tasks[0]), "groups": sorted({t.group for t in tasks}),
            "costs": costs, "origin": "mock-measured" if config.model.backend == "mock" else "development-measured",
            "sample_count": len(measurements)}
    data["id"] = digest([data, measurements])
    return {"calibration": data, "measurements": measurements}
