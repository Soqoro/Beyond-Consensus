"""Aggregate all planned rows; never combine exposure modes or budget protocols."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..experiments.manifest import validate_manifest
from ..util import BCError, digest, read_json
from .metrics import summarize


def aggregate(manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    config = validate_manifest(manifest)
    rows, statuses = {}, Counter()
    for expected in manifest["episodes"]:
        path = root / "episodes" / expected["episode_id"] / "result.json"
        if not path.exists():
            statuses["missing"] += 1
            continue
        row = read_json(path)
        if (row["protocol"], row["mode"], row["experiment_id"]) != (
                config.protocol, config.mode, manifest["experiment_id"]):
            raise BCError("Cannot pool equal-remainder/equal-total, mock/real, or different provenance")
        if row["provenance"]["manifest_hash"] != digest(expected):
            raise BCError("Result identity/provenance differs from planned episode")
        expected_condition = {"profile": config.development_profile, "silo_interface": config.silo_interface,
            "diagnostic_mode": manifest["tasks"][0].get("metadata", {}).get("diagnostic_mode", "full"),
            "operation_measurement": config.operation_measurement}
        if config.organization != "legacy":
            expected_condition["organization"] = config.organization
        if config.model.action_constraint != "none":
            expected_condition["action_constraint"] = config.model.action_constraint
        if "condition" in row["provenance"] and row["provenance"]["condition"] != expected_condition:
            raise BCError("Cannot pool different diagnostic modes, model/interface profiles or measurements")
        if manifest["schema"] == "bc-manifest-v2" and row["status"] != "infrastructure_failed" and row["provenance"].get("data_regime") != manifest["data_regime"]:
            raise BCError("Cannot pool different scorer/environment/access regimes")
        rows[expected["episode_id"]] = row
        statuses[row["status"]] += 1
    groups = {}
    for policy in config.policies:
        for family in config.attacks:
            planned = [e for e in manifest["episodes"] if e["policy"] == policy and e["attack"]["family"] == family]
            observed = [rows[e["episode_id"]] for e in planned if e["episode_id"] in rows]
            valid = [r for r in observed if r["status"] in ("completed", "budget_exhausted")]
            scored = [r for r in valid if type(r["success"]) is bool]
            clean_by = {(e["task_id"], e["seed"]): rows.get(e["episode_id"])
                        for e in manifest["episodes"] if e["policy"] == policy and e["attack"]["family"] == "clean"}
            eligible = [r for r in valid if family != "clean" and clean_by.get((r["task_id"], r["seed"]))
                        and clean_by[r["task_id"], r["seed"]]["success"] is True]
            groups[f"{policy}/{family}"] = {
                "observations": summarize(observed),
                "planned": len(planned), "valid_observed": len(valid),
                "statuses": dict(Counter(r["status"] for r in observed)),
                "missing": len(planned)-len(observed), "successes": sum(r["success"] is True for r in valid),
                "success_rate_observed": sum(r["success"] is True for r in scored)/len(scored) if scored else None,
                "success_rate_null_reason": None if scored else "No available task scoring (or operation measurement only)",
                "complete_coverage": len(valid) == len(planned),
                "ASR_cc": sum(r["success"] is False for r in eligible)/len(eligible) if eligible else None,
                "ASR_cc_eligible": len(eligible),
                "ASR_cc_null_reason": None if eligible else "No valid attacked/clean-success pairs (or clean condition)",
                "detected_but_unfinished": sum(r["metrics"]["detected_but_unfinished"] for r in valid),
                "preparation_work": sum(r["costs"]["stages"].get("preparation", 0) for r in valid),
                "historical_work": sum(r["costs"]["historical_work"] for r in valid),
                "historical_preparation_work": sum(e["work"] for r in valid
                    for e in r["costs"]["historical_entries"] if e["stage"] == "preparation"),
                "repair_work": sum(sum(v for s, v in r["costs"]["stages"].items() if s.startswith("repair")) for r in valid),
                "unaffected_work_retained": sum(r["metrics"]["unaffected_work_retained"] for r in valid),
                "integration_failures": sum(r["metrics"]["integration_failure"] for r in valid),
                "false_alarms": sum(r["metrics"]["false_alarm"] for r in valid),
                "reserve_violations": sum(r["metrics"]["reserve_violations"] for r in valid),
                "base_feature_pools": sorted({r["group"] for r in valid}),
                "by_base_feature_pool": {group: {
                    "planned": sum(e["group"] == group for e in planned),
                    "observed": sum(r["group"] == group for r in valid),
                    "successes": sum(r["group"] == group and r["success"] is True for r in valid)}
                    for group in sorted({e["group"] for e in planned})}}
    return {"experiment_id": manifest["experiment_id"], "mode": config.mode, "protocol": config.protocol,
            "condition": {"profile": config.development_profile, "silo_interface": config.silo_interface,
                          "diagnostic_mode": manifest["tasks"][0].get("metadata", {}).get("diagnostic_mode", "full"),
                          "operation_measurement": config.operation_measurement,
                          **({"action_constraint": config.model.action_constraint} if config.model.action_constraint != "none" else {})},
            "organization": config.organization,
            "legacy_integration_failures_meaning": "completed unsuccessful episodes; not public integration failures",
            **({"schema": "bc-summary-v2", "data_regime": manifest["data_regime"],
                "independent_source_groups": len({t["group"] for t in manifest["tasks"]})} if manifest["schema"] == "bc-manifest-v2" else {}),
            "interpretation": "operation_cost_diagnostic_not_policy_accuracy" if config.operation_measurement else
                "equal_total_budget" if config.protocol == "A" else "equal_remaining_diagnostic_not_total_efficiency",
            "planned": len(manifest["episodes"]), "statuses": dict(statuses), "groups": groups,
            "confirmatory": False, "uncertainty": "No episode-independent CIs: group-level inference is deferred"}
