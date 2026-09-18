"""Allocation explanations and ledger reconciliation, without model execution."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from ..planning.costs import compatibility
from ..util import digest, read_json


def calibration_metadata(config, task):
    data = read_json(config.calibration_file) if config.calibration_file else {}
    return {"id": data.get("id"), "origin": data.get("origin", "uncalibrated_allowance_surrogate"),
        "units": "token_tool_surrogate_v1", "convention": "arithmetic mean" if data else "equal capped allowances; no preparation discount",
        "confidence_interval": None, "quantile": None, "sample_count": data.get("sample_count"),
        "compatibility": data.get("compatibility"), "expected_compatibility": compatibility(config, task),
        "compatible": data.get("compatibility") == compatibility(config, task) if data else None,
        "missing_calibration": not bool(data), "confirmatory": False}


def reconcile(ledger, result=None, rules=None):
    """Summing stage totals again would double count. Only entries are charges."""
    entries = ledger.get("entries", [])
    stages, kinds = defaultdict(float), defaultdict(float)
    for entry in entries:
        stages[entry["stage"]] += entry["work"]
        kinds[entry["kind"]] += entry["work"]
    total = sum(e["work"] for e in entries)
    ids = [e["entry_id"] for e in entries if "entry_id" in e]
    duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)
    # Equal tool/model charges can be legitimate repeated work. Do not delete them.
    identical = sum(n-1 for n in Counter(digest(e) for e in entries).values() if n > 1)
    expected = (result or {}).get("costs", {}).get("spent")
    model_mismatches = []
    if rules:
        for index, entry in enumerate(entries):
            if entry["kind"] != "model" or entry.get("input_tokens") is None:
                continue
            generated = entry.get("output_tokens")
            if generated is None:
                generated = entry.get("reserved_output_tokens")
            if generated is None:
                continue
            predicted = entry["input_tokens"]*rules["input_weight"]+generated*rules["output_weight"]
            if abs(predicted-entry["work"]) > 1e-9:
                model_mismatches.append({"entry_index": index, "recorded_work": entry["work"], "token_formula_work": predicted})
    return {"entry_count": len(entries), "entry_total": total, "stages": dict(stages), "kinds": dict(kinds),
        "stage_entries": {stage: [{"entry_index": i, **entry} for i, entry in enumerate(entries) if entry["stage"] == stage]
                          for stage in stages},
        "summary_total_matches": total == ledger["spent"] if "spent" in ledger else None,
        "stage_totals_match": dict(stages) == ledger["stages"] if "stages" in ledger else None,
        "result_total": expected, "result_total_matches": total == expected if expected is not None else None,
        "historical_total": sum(e["work"] for e in ledger.get("historical_entries", ledger.get("historical", []))),
        "duplicate_entry_ids": duplicates, "identical_entries": identical,
        "model_charge_mismatches": model_mismatches, "model_charge_formula_checked": rules is not None,
        "duplicate_accounting_status": "duplicate_ids" if duplicates else "not_detected_with_ids" if len(ids) == len(entries) else "identity_unavailable",
        "identity_note": "Identical charges are not proof of duplicate execution/accounting; legacy entries lack unique operation IDs.",
        "planner_charges": [{"entry_index": i, **e} for i, e in enumerate(entries) if e["stage"] == "planning"]}


def inspect_output(output):
    output = Path(output)
    manifest = read_json(output / "manifest.json")
    from ..experiments.manifest import validate_manifest
    validate_manifest(manifest)
    reports, totals = [], defaultdict(list)
    for row in manifest["episodes"]:
        path = output / "episodes" / row["episode_id"]
        result_path, costs_path = path / "result.json", path / "costs.json"
        if not result_path.exists():
            reports.append({"episode_id": row["episode_id"], "status": "result_unavailable"})
            continue
        result = read_json(result_path)
        checkpoint = read_json(path/"checkpoint.json") if (path/"checkpoint.json").exists() else {}
        if isinstance(result.get("costs", {}).get("entries"), list):
            ledger = result["costs"]
        elif costs_path.exists():
            ledger = read_json(costs_path)
        elif checkpoint:
            ledger = checkpoint["ledger"]
        else:
            reports.append({"episode_id": row["episode_id"], "status": "ledger_unavailable"})
            continue
        if not isinstance(ledger.get("entries"), list):
            reports.append({"episode_id": row["episode_id"], "status": "ledger_entries_unavailable",
                "reported_total": result.get("costs", {}).get("spent"), "reconciliation": None})
            continue
        detail = reconcile(ledger, result, manifest["config"]["budget"])
        trace = path / "allocation-diagnostic.json"
        plan = result.get("provenance", {}).get("plan") or checkpoint.get("plan")
        events = []
        if (path/"events.jsonl").exists():
            events = [json.loads(line) for line in (path/"events.jsonl").read_text().splitlines() if line.strip()]
        allocation = read_json(trace) if trace.exists() else None
        observed_search = sum(e["work"] for e in ledger["entries"] if e["stage"] == "planning" and e["kind"] == "finite_search")
        checks = {"episode_manifest": result.get("provenance", {}).get("manifest_hash") == digest(row),
            "source": result.get("provenance", {}).get("source_revision") == manifest["source_revision"]}
        reports.append({"episode_id": row["episode_id"], "task_id": row["task_id"], "seed": row["seed"],
            "policy": row["policy"], "condition": row["attack"]["family"],
            "ledger_hash": digest(ledger), "reconciliation": detail,
            "identity_checks": checks, "result_hash": digest(result),
            "recorded_plan": plan,
            "recorded_cost_estimates": result.get("provenance", {}).get("calibration") or checkpoint.get("costs"),
            "ledger_schema": ledger.get("observation_schema"), "config_hash": manifest["config_hash"],
            "source_revision": manifest["source_revision"], "calibration_hash": manifest.get("calibration_hash"),
            "observed_search_work": observed_search,
            "recorded_search_states": plan.get("search_states") if plan else None,
            "search_charge_matches_recorded_states": observed_search == plan["search_states"] if plan and "search_states" in plan else None,
            "candidate_count": allocation.get("candidate_count") if allocation else None,
            "executed_preparation_replication": [{k: e.get(k) for k in ("key", "unit", "executor", "operation", "measured_work", "outcome")}
                for e in events if e["type"] == "operation" and e.get("operation") in ("prepare", "replicate")]
                if (path/"events.jsonl").exists() else None,
            "stage_preparation_work": detail["stages"].get("preparation", 0),
            "stage_replication_work": detail["stages"].get("replication", 0),
            "allocation": allocation,
            "allocation_status": "recorded" if trace.exists() else "candidate_trace_not_recorded"})
        totals[(row["policy"], row["attack"]["family"])].append(detail)
    paired = []
    indexed = {(r["task_id"], r["seed"], r["condition"], r["policy"]): r for r in reports if r.get("reconciliation")}
    for key, recovery in indexed.items():
        if key[-1] != "recovery":
            continue
        jit = indexed.get((*key[:-1], "jit"))
        if not jit:
            paired.append({"task_id": key[0], "seed": key[1], "condition": key[2], "status": "missing_jit_ledger"})
            continue
        rd, jd = recovery["reconciliation"], jit["reconciliation"]
        delta = rd["entry_total"]-jd["entry_total"]
        stages = {s: rd["stages"].get(s, 0)-jd["stages"].get(s, 0) for s in rd["stages"].keys() | jd["stages"].keys()}
        search_delta = recovery["observed_search_work"]-jit["observed_search_work"]
        verified = all(all(r["identity_checks"].values()) and r["search_charge_matches_recorded_states"] is True
            and r["reconciliation"]["result_total_matches"] is True
            and r["reconciliation"]["stage_totals_match"] is True
            and not r["reconciliation"]["duplicate_entry_ids"] and not r["reconciliation"]["model_charge_mismatches"]
            for r in (recovery, jit))
        paired.append({"task_id": key[0], "seed": key[1], "condition": key[2],
            "total_work_difference": delta, "stage_differences": stages,
            "finite_search_difference": search_delta, "non_search_residual": delta-search_delta,
            "status": "reconciled" if verified else "incomplete_or_inconsistent_evidence",
            "entire_gap_matches_search": verified and delta == search_delta and stages.get("planning", 0) == search_delta
                and all(v == 0 for s, v in stages.items() if s != "planning")})
    return {"schema": "bc-allocation-analysis-v1", "derived": True, "manifest_hash": digest(manifest),
        "experiment_id": manifest["experiment_id"], "source_revision": manifest["source_revision"],
        "mode": manifest["config"].get("model", {}).get("backend"),
        "evidence_origin": "saved episode ledgers; mock runs remain mock evidence",
        "config_hash": manifest["config_hash"], "calibration_hash": manifest.get("calibration_hash"),
        "recovery_jit_pairs": paired,
        "missing_evidence_note": "Absent candidate traces/calibration origin/operation events remain unknown; planned preparation is not proof of execution.",
        "original_charges_modified": False, "episodes": reports,
        "groups": {"/".join(k): {"episodes_with_ledgers": len(v),
            "mean_total_work": sum(r["entry_total"] for r in v)/len(v),
            "mean_planning_work": sum(r["stages"].get("planning", 0) for r in v)/len(v)} for k, v in totals.items()}}


def reproduce(config, task, costs, policies=("jit", "recovery", "replication")):
    from ..policies.core import choose_plan
    from ..tasks.data_manifest import policy_view
    result = {}
    task = policy_view(task)
    for policy in policies:
        trace = {}
        plan = choose_plan(policy, task, config, costs, config.budget.total-1, trace=trace)
        trace["calibration"] = calibration_metadata(config, task)
        trace["planning_ledger_prediction"] = {"catalogue_setup": 1, "finite_search": plan.search_states}
        result[policy] = trace
    return {"schema": "bc-allocation-reproduction-v1", "evidence": "current-code finite-search reproduction, not historical execution",
        "task_id": task.id, "task_group": task.group, "conditions": result, "model_executed": False}
