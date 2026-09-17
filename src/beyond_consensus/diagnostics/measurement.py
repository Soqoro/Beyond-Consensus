"""Held-out cost summaries; estimates remain labelled measured predictions."""
from collections import defaultdict
from pathlib import Path
from statistics import mean

from ..util import BCError, digest, read_json


def collect(output):
    root = Path(output)
    manifest = read_json(root/"manifest.json")
    if not manifest["config"].get("operation_measurement"):
        raise BCError("Expected an operation measurement manifest")
    rows, missing = [], []
    task_sizes = {t["id"]: len(t["required_outputs"]) for t in manifest["tasks"]}
    for episode in manifest["episodes"]:
        path = root/"episodes"/episode["episode_id"]/"result.json"
        if not path.exists():
            missing.append(episode["episode_id"])
            continue
        result = read_json(path)
        if result["provenance"]["manifest_hash"] != digest(episode):
            raise BCError("Measurement result provenance mismatch")
        if result["status"] != "completed" or len(result["metrics"].get("measurements", [])) != 6*task_sizes[episode["task_id"]]:
            missing.append(episode["episode_id"]+":incomplete_operations")
        for measurement in result["metrics"].get("measurements", []):
            rows.append({**measurement, "group": episode["group"], "task_id": episode["task_id"],
                "origin": result["provenance"]["measurement_origin"],
                "compatibility": result["provenance"]["calibration_compatibility"]})
    return manifest, rows, missing


def compare(training, holdout):
    train, values, missing = collect(training)
    held, checks, missing_held = collect(holdout)
    groups = {e["group"] for e in train["episodes"]}
    held_groups = {e["group"] for e in held["episodes"]}
    if groups & held_groups:
        raise BCError("Cost calibration and holdout source groups overlap")
    conditions = {(r["compatibility"], r["origin"]) for r in values+checks}
    if len(conditions) != 1 or not values or not checks:
        raise BCError("Missing or incompatible measured model/interface/operation conditions")
    by_op = defaultdict(list)
    for r in values:
        by_op[r["operation"]].append(r["work"])
    predictions = {key: mean(v) for key, v in by_op.items()}
    errors = [{"group": r["group"], "unit": r["unit"], "operation": r["operation"],
        "status": r["status"], "measured": r["work"], "predicted": predictions.get(r["operation"]),
        "error": r["work"]-predictions[r["operation"]] if r["operation"] in predictions else None} for r in checks]
    complete = not missing and not missing_held and all(r["status"] == "submitted" and r["source_grounded"] for r in values+checks)
    report = {"schema": "bc-operation-cost-validation-v1", "training_manifest_hash": digest(train),
        "holdout_manifest_hash": digest(held), "training_groups": sorted(groups), "holdout_groups": sorted(held_groups),
        "origin": values[0]["origin"], "convention": "arithmetic mean; no quantile/confidence guarantee",
        "work_unit": "token_tool_surrogate_v1", "missing_training": missing, "missing_holdout": missing_held,
        "all_operations_submitted_and_grounded": complete, "means": predictions, "holdout_prediction_errors": errors,
        "preparation_plus_execution": {style: predictions.get(style, 0)+predictions.get("after_"+style, 0) for style in ("index", "outline")},
        "activation": "diagnostic only; operation-specific prompts differ from the allocator's combined index/outline operation; no automatic calibration activation",
        "confirmatory": False, "selection_pass_condition": "none; nonzero preparation is not required"}
    report["id"] = digest(report)
    return report
