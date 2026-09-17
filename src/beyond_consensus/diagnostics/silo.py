"""Offline prefix diagnostics. No import into workers, monitor or route search."""
import json
from collections import Counter
from pathlib import Path

from ..tasks.silo import solve
from ..util import BCError, digest, read_json


def bounded_answer(value, length):
    return isinstance(value, list) and len(value) == length and all(type(v) is int and abs(v) <= 10**9 for v in value)


def attribution(shards, answers, visible):
    """visible[unit] must come from observed artifact reads, never expected_output."""
    expected = solve("II-11", shards)
    report = []
    for i, (inputs, reference) in enumerate(zip(shards, expected)):
        unit = f"u{i}"
        answer = answers.get(unit)
        valid = bounded_answer(answer, len(inputs))
        predecessor = visible.get(unit)
        carry = 0 if i == 0 else predecessor.get("submitted_final_value") if predecessor else None
        boundary = answer[0] == carry+inputs[0] if valid and type(carry) is int else None
        increments = [answer[j]-answer[j-1] == inputs[j] for j in range(1, len(inputs))] if valid else None
        true_carry = 0 if i == 0 else expected[i-1][-1]
        wrong_carry = carry != true_carry if type(carry) is int else None
        local = boundary and all(increments) if boundary is not None else None
        report.append({"unit": unit, "present": unit in answers, "shape_valid": valid,
            "global_correct": answer == reference if valid else False,
            "correct_values": sum(a == b for a, b in zip(answer, reference)) if valid else 0,
            "required_values": len(reference), "visible_predecessor": predecessor,
            "incoming_consistent": boundary, "local_increment_checks": increments,
            "local_increment_errors": sum(not v for v in increments) if increments is not None else None,
            "locally_consistent": local, "inherited_wrong_state": wrong_carry,
            "inherited_only": bool(wrong_carry and local) if wrong_carry is not None and local is not None else None,
            "additional_worker_error": not local if local is not None else None})
    return {"schema": "bc-silo-attribution-v1", "offline_evaluator_only": True, "segments": report,
        "correct_values": sum(r["correct_values"] for r in report), "required_values": sum(map(len, shards)),
        "complete_task_success": all(r["global_correct"] for r in report)}


def visible_predecessors(checkpoint):
    """Bind the last actual read before each submission, including its content."""
    artifacts = checkpoint["store"]["artifacts"]
    observed, by_unit = {}, {}
    for event in checkpoint["store"]["events"]:
        if event["type"] in ("context_reset", "context_restore"):
            # Legacy restore events do not name the restored snapshot/read set.
            # Leave it unknown until a subsequent explicit artifact read.
            observed.pop(event["identity"], None)
        if event["type"] == "artifact_read":
            observed.setdefault(event["identity"], []).append(event["version"])
        if event["type"] == "submit":
            version = event["version"]
            unit = event["unit"]
            if not unit.startswith("u") or not unit[1:].isdigit() or int(unit[1:]) == 0:
                continue
            previous = f"u{int(unit[1:])-1}"
            candidates = [v for v in observed.get(event["author"], []) if artifacts.get(v, {}).get("unit") == previous]
            if not candidates:
                continue
            v = candidates[-1]
            value = artifacts[v].get("content", {}).get("answer")
            if bounded_answer(value, 15):
                by_unit[version] = {"predecessor_artifact_id": v, "submitted_final_value": value[-1],
                    "author": artifacts[v]["author"], "content_hash": digest(artifacts[v]["content"])}
    return by_unit


def analyze_output(output):
    output = Path(output)
    manifest = read_json(output / "manifest.json")
    if manifest["config"].get("operation_measurement"):
        raise BCError("Operation measurements have no selected task submission; use measurement-report, not task-accuracy analysis")
    tasks = {t["id"]: t for t in manifest["tasks"]}
    reports = []
    for row in manifest["episodes"]:
        task = tasks[row["task_id"]]
        if task["kind"] != "silo" or task["metadata"]["family"] != "II-11":
            raise BCError("Offline attribution currently supports SILO Prefix Sum only")
        path = output / "episodes" / row["episode_id"] / "checkpoint.json"
        if not path.exists():
            reports.append({"episode_id": row["episode_id"], "status": "trace_unavailable"})
            continue
        cp = read_json(path)
        result_path = path.parent/"result.json"
        runtime = read_json(result_path).get("provenance", {}).get("backend_runtime", {}) if result_path.exists() else {}
        arts, selected = cp["store"]["artifacts"], cp["selected"]
        mode = task["metadata"].get("diagnostic_mode", "full")
        if mode == "full":
            answers = {u: arts[v]["content"].get("answer") for u, v in selected.items()}
            reads = visible_predecessors(cp)
            visible = {u: reads[v] for u, v in selected.items() if v in reads}
            analysis = attribution(list(task["metadata"]["harness"]["shards"].values()), answers, visible)
        else:
            # Derived modes preserve original inputs in evaluator-only metadata.
            meta = task["metadata"]
            index = meta["original_unit"]
            answer = arts[selected["u0"]]["content"].get("answer") if "u0" in selected else None
            original = meta["harness"]["original_shards"]
            if mode == "local":
                analysis = attribution([original[index]], {"u0": answer} if answer is not None else {}, {})
            else:
                frozen = meta["harness"]["predecessor"]
                value = frozen["artifacts"][frozen["version"]]["content"]["answer"][-1]
                full = attribution(original, {f"u{index}": answer} if answer is not None else {},
                    {f"u{index}": {"predecessor_artifact_id": frozen["version"], "submitted_final_value": value}})
                analysis = {"offline_evaluator_only": True, "segment": full["segments"][index]}
        messages = [m for c in cp["store"]["contexts"].values() for m in c["messages"]]
        generation_events = [e for e in cp["store"]["events"] if e["type"] == "generation_metadata"]
        duplicate_messages = {h: n for h, n in Counter(digest(m) for m in messages).items() if n>1}
        reports.append({"episode_id": row["episode_id"], "group": task["group"], "diagnostic_mode": mode,
            "checkpoint_hash": digest(cp), "analysis": analysis,
            "interface_audit": {"message_count": len(messages), "current_code_context_policy": "persistent identity; no implicit truncation",
                "declared_model": manifest["config"]["model"], "declared_interface": manifest["config"].get("silo_interface", "original"),
                "recorded_backend": {k: runtime.get(k) for k in ("dependencies", "checkpoint_revision", "tokenizer_revision", "chat_template", "loader", "slurm_job_id", "snapshot_id", "hardware")},
                "selected_bindings": {u: {"artifact_id": v, "artifact_unit": arts[v]["unit"], "author": arts[v]["author"]} for u,v in selected.items()},
                "repeated_message_hashes": duplicate_messages, "repetition_interpretation": "Not evidence of answer-cache reuse",
                "generation_events": generation_events,
                "limit_events": [e for e in cp["store"]["events"] if e["type"] in ("context_limit", "observation_limit")],
                "historical_missing_generation_metadata": not bool(generation_events),
                "historical_truncation_status": "recorded_per_call" if generation_events else "unknown",
                "current_code_answer_cache": "no cross-call cache in repository backend; KV cache exists within each generate call only"}})
    return {"schema": "bc-silo-analysis-v1", "derived": True, "manifest_hash": digest(manifest), "episodes": reports,
        "feedback_to_runtime": False, "aggregation": "separate by model/interface/mode/group; no independent seed inference"}
