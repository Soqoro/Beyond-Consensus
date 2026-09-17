"""Allocation explanations and ledger reconciliation, without model execution."""
from collections import Counter, defaultdict
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
    reports, totals = [], defaultdict(list)
    for row in manifest["episodes"]:
        path = output / "episodes" / row["episode_id"]
        result_path, costs_path = path / "result.json", path / "costs.json"
        if not result_path.exists():
            reports.append({"episode_id": row["episode_id"], "status": "result_unavailable"})
            continue
        result = read_json(result_path)
        if "costs" in result:
            ledger = result["costs"]
        elif costs_path.exists():
            ledger = read_json(costs_path)
        elif (path / "checkpoint.json").exists():
            ledger = read_json(path / "checkpoint.json")["ledger"]
        else:
            reports.append({"episode_id": row["episode_id"], "status": "ledger_unavailable"})
            continue
        detail = reconcile(ledger, result, manifest["config"]["budget"])
        trace = path / "allocation-diagnostic.json"
        reports.append({"episode_id": row["episode_id"], "policy": row["policy"], "condition": row["attack"]["family"],
            "ledger_hash": digest(ledger), "reconciliation": detail,
            "recorded_plan": result.get("provenance", {}).get("plan"),
            "recorded_cost_estimates": result.get("provenance", {}).get("calibration"),
            "allocation": read_json(trace) if trace.exists() else None,
            "allocation_status": "recorded" if trace.exists() else "candidate_trace_not_recorded"})
        totals[(row["policy"], row["attack"]["family"])].append(detail)
    return {"schema": "bc-allocation-analysis-v1", "derived": True, "manifest_hash": digest(manifest),
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
