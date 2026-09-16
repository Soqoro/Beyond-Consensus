"""Versioned data manifests and offline reference controls; no model execution."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace

from ..config import RunConfig
from ..runtime.budget import BudgetLedger
from ..runtime.data_domain import DataDomain, TaskUnavailable
from ..runtime.provenance import ProvenanceStore
from ..util import BCError, digest, plain, read_json


def policy_view(task):
    """The planner receives no harness paths, shards or evaluation material."""
    from dataclasses import replace
    allowed = {"adaptation", "dependencies", "source_ids", "base_hash", "tool_policy", "access_regime",
        "family", "workers", "communication", "backup_access", "scorer", "synthetic", "upstream_commit", "dataset_revision"}
    metadata = {k: deepcopy(v) for k, v in task.metadata.items() if k in allowed}
    if task.metadata.get("harness", {}).get("limits"):
        metadata["execution_limits"] = deepcopy(task.metadata["harness"]["limits"])
    return replace(task, sources=deepcopy(task.sources), metadata=metadata)


def regime(task):
    return {"environment": task.kind, **{k: task.metadata.get(k) for k in (
        "adaptation", "tool_policy", "scorer", "access_regime", "upstream_commit", "dataset_revision")}}


def validation_subject(task):
    data = plain(task)
    for key in ("readiness", "validation_status", "validation_hash", "validated_sqlite_runtime", "executor_runtime"):
        data["metadata"].pop(key, None)
    return digest(data)


def validate_data(path):
    from ..experiments.manifest import task_from, validate_splits
    data = read_json(path)
    if data.get("schema") != "bc-data-v2":
        raise BCError("Expected bc-data-v2")
    tasks = [task_from(t) for t in data["tasks"]]
    seen = set()
    for task in tasks:
        if task.kind != data["environment"] or task.id in seen:
            raise BCError("Data manifest environment/identity mismatch")
        seen.add(task.id)
        if task.kind == "silo":
            from .silo import task as regenerate
            original = regenerate(task.metadata["family"], task.metadata["generator_seed"] or 0, task.metadata["access_regime"])
            if original.source_hash != task.source_hash:
                raise BCError("SILO generated data/source/protocol mismatch")
        elif task.kind in ("sqlite_native", "sqlite_pair"):
            if task.metadata.get("readiness") != "reference_validated" or not task.metadata.get("validation_hash"):
                raise BCError("SQLite scored tasks require recorded positive and negative reference controls")
            report = next((r for r in data.get("reports", []) if r.get("task_id") == task.id), None)
            if (report is None or digest(report) != task.metadata["validation_hash"] or report["status"] != "validated"
                    or report.get("subject_hash") != validation_subject(task)):
                raise BCError("Reference validation report identity mismatch")
            from .sqlite_tasks import verify_file
            verify_file(task.metadata["harness"]["database"])
        else:
            raise BCError("Unexpected data adapter")
    if len({digest(regime(t)) for t in tasks}) > 1:
        raise BCError("Cannot mix environments, tool policies, scorers, access regimes or releases")
    by_split = {}
    from ..experiments.manifest import grouped_split
    for task in tasks:
        by_split.setdefault(grouped_split(task.group), []).append(task)
    validate_splits(by_split)
    return tasks


def validate_reference(task):
    """Reviewed typed references only. The upstream exec(test_code) is not used."""
    config = RunConfig(task_kind=task.kind, monitor_id="data-structure-v1")
    with tempfile.TemporaryDirectory(prefix="bc-reference-") as temporary:
        engine = SimpleNamespace(task=task, config=config, ledger=BudgetLedger(config.budget.total, config.budget),
            journal=SimpleNamespace(path=Path(temporary)), store=ProvenanceStore(), selected={})
        domain = DataDomain(engine)
        for unit in task.required_outputs:
            content = deepcopy(task.metadata["evaluation"][unit]["artifact"])
            content.setdefault("bindings", {})
            engine.selected[unit] = engine.store.submit("w0", unit, content).id
        original = dict(engine.selected)
        try:
            positive = domain.integrate() and domain.evaluate()["complete_task_success"]
            missing, corrupt = {}, {}
            for unit in task.required_outputs:
                engine.selected = {u: k for u, k in original.items() if u != unit}
                missing[unit] = domain.evaluate()["complete_task_success"] is False
                engine.selected = dict(original)
                content = deepcopy(engine.store.artifacts[original[unit]].content)
                # Shape-preserving constant replacement tests whether this
                # obligation actually affects its reviewed evaluation checks.
                for item in content["select"]["columns"]:
                    if content["kind"] == "view" and "as" not in item:
                        if "column" not in item["expr"]:
                            raise BCError("Reviewed view expressions need explicit column aliases for semantic controls")
                        item["as"] = item["expr"]["column"].split(".")[-1]
                    item["expr"] = {"literal": -987654321}
                engine.selected[unit] = engine.store.submit("w1", unit, content).id
                corrupt[unit] = domain.evaluate()["complete_task_success"] is False
            passed = positive and all(missing.values()) and all(corrupt.values())
            report = {"task_id": task.id, "task_hash": task.source_hash, "subject_hash": validation_subject(task),
                "status": "validated" if passed else "reference_validation_failed",
                "positive_joint": positive, "missing_obligation_controls": missing,
                "corrupt_obligation_controls": corrupt, "work": engine.ledger.summary(),
                "semantics": "reviewed AST adaptation; upstream arbitrary Python evaluator not run"}
        except (TaskUnavailable, BCError, ValueError, KeyError) as exc:
            report = {"task_id": task.id, "task_hash": task.source_hash,
                "status": exc.status if isinstance(exc, TaskUnavailable) else "reference_validation_failed",
                "reason": "Restricted reference execution unavailable or failed", "work": engine.ledger.summary()}
        if report["status"] == "validated":
            from ..runtime.sqlite_executor import capabilities
            report["sqlite_runtime"] = capabilities()
            task.metadata["readiness"] = "reference_validated"
            task.metadata["validation_status"] = "joint_reference_validated"
            task.metadata["validation_hash"] = digest(report)
            task.metadata["validated_sqlite_runtime"] = report["sqlite_runtime"]
        return report


def validate_native(staged, ids, count):
    from .sqlite_tasks import native_tasks
    tasks, excluded = native_tasks(staged)
    chosen = [t for t in tasks if not ids or t.id in ids]
    if len(chosen) != count or ids and set(ids) != {t.id for t in chosen}:
        return {"schema": "bc-data-v2", "environment": "sqlite_native", "tasks": [],
            "status": "scoring_unavailable", "requested": count, "available_reviewed": len(chosen),
            "excluded": excluded, "command_failed": True}
    reports = [validate_reference(t) for t in chosen]
    return {"schema": "bc-data-v2", "environment": "sqlite_native",
        "tasks": plain([t for t, r in zip(chosen, reports) if r["status"] == "validated"]),
        "reports": reports, "excluded": excluded,
        "command_failed": any(r["status"] != "validated" for r in reports)}


def validate_pairs(staged, candidates):
    from .sqlite_tasks import native_tasks, pair
    if not isinstance(candidates, list) or not candidates:
        raise BCError("Pair validation requires nonempty explicit candidates")
    natives, excluded = native_tasks(staged)
    available = {t.id: t for t in natives}
    tasks, reports = [], []
    for candidate in candidates:
        ids = candidate["source_ids"]
        try:
            if len(ids) != 2 or not set(ids) <= available.keys():
                raise BCError("Pair material/review prerequisites missing")
            task = pair(available[ids[0]], available[ids[1]], candidate["rationale"])
            report = validate_reference(task)
            report["source_ids"] = ids
            if report["status"] == "validated":
                task.metadata["validation_hash"] = digest(report)
            reports.append(report)
            if report["status"] == "validated":
                tasks.append(task)
        except BCError as exc:
            reports.append({"source_ids": ids, "status": "rejected_or_blocked", "reason": str(exc)})
    return {"schema": "bc-data-v2", "environment": "sqlite_pair", "tasks": plain(tasks),
        "status": "validated" if len(tasks) == len(candidates) else "blocked_or_rejected",
        "pair_selection_hash": digest(candidates), "reports": reports, "excluded_native": excluded,
        "command_failed": len(tasks) != len(candidates)}
