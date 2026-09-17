"""Additive observations; legacy semantic failures never imply a public alarm."""
from collections import Counter


def observations(status, final, integration=None, required=None, selected=None, shape=None):
    missing = sorted(set(required)-set(selected)) if required is not None and selected is not None else None
    semantic = final.get("complete_task_success") if isinstance(final, dict) else None
    evaluator = ("available" if type(semantic) is bool else
                 "unavailable" if status in ("scoring_unavailable", "blocked_prerequisite", "blocked_capability") else
                 "not_run" if status != "completed" else "unknown")
    return {"schema": "bc-observations-v1", "public_integration": integration,
            "public_coverage": not missing if missing is not None else None,
            "public_shape_valid": shape,
            "missing_required_artifacts": missing, "evaluator_status": evaluator,
            "final_semantic_correctness": semantic, "execution_status": status,
            "budget_exhausted": status == "budget_exhausted",
            "infrastructure_failed": status == "infrastructure_failed", "interrupted": status == "interrupted"}


def from_result(row):
    metrics = row.get("metrics", {})
    if "observations" in metrics:
        return metrics["observations"]
    # No artifact-coverage reconstruction from success or legacy integration_failure.
    return observations(row["status"], metrics.get("final_evaluation"),
                        metrics.get("joint_public_integration"))


def summarize(rows):
    values = [from_result(r) for r in rows]
    result = {name: {"passed": sum(v.get(name) is True for v in values),
                     "failed": sum(v.get(name) is False for v in values),
                     "unknown": sum(v.get(name) is None for v in values)}
              for name in ("public_coverage", "public_shape_valid", "public_integration", "final_semantic_correctness")}
    result["evaluator_statuses"] = dict(Counter(v["evaluator_status"] for v in values))
    result["missing_artifact_observations"] = sum(v["missing_required_artifacts"] is not None for v in values)
    result["missing_required_artifacts"] = sum(len(v["missing_required_artifacts"] or []) for v in values)
    result["execution_statuses"] = dict(Counter(r["status"] for r in rows))
    return result
