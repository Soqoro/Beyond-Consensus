"""Terminal joint-candidate scoring with evaluator-only test patches.

No output from this module is an observation for the coding worker.
"""
import json
from pathlib import Path
import tempfile

from ..runtime.apptainer import SandboxFailure
from ..tasks.cooperbench import safe_file
from ..util import BCError, atomic_json, digest, file_hash, read_json


def evaluate(task, environment, workspace, data_manifest, ledger, *, reference_features=(),
             validation_control=False, boundary=lambda _: None, cancelled=lambda: False):
    environment.validate_task(task)
    data = read_json(data_manifest)
    root = Path(data["root"])
    prefix = task.metadata["pair_id"].split("/features_")[0]
    with tempfile.TemporaryDirectory(prefix="evaluation-", dir=environment.profile.scratch_root) as tmp:
        private = Path(tmp)
        patches = []
        reference_patches = []
        if not set(reference_features) <= set(task.required_outputs):
            raise BCError("Unknown reference feature in environment validation")
        for feature in reference_features:
            name = f"{prefix}/{feature}/feature.patch"
            path = safe_file(root, name)
            if file_hash(path) != task.metadata["source_hashes"][name]:
                raise BCError("Reference patch changed since task import")
            filename = feature + ".reference.patch"
            (private / filename).write_bytes(path.read_bytes())
            reference_patches.append(filename)
        for feature in task.required_outputs:
            name = f"{prefix}/{feature}/tests.patch"
            path = safe_file(root, name)
            if file_hash(path) != task.metadata["source_hashes"][name]:
                raise BCError("Hidden tests changed since task import")
            filename = feature + ".patch"
            (private / filename).write_bytes(path.read_bytes())
            patches.append(filename)
        # Reviewed upstream test drivers, copied as data and executed only inside
        # the evaluator container. Never copy setup scripts or feature.patch.
        for name in ("run_tests.sh", "runner.sh"):
            path = safe_file(root, f"{prefix}/{name}")
            if file_hash(path) != task.metadata["environment_requirements"][name]:
                raise BCError("Evaluator driver changed since task import")
            (private / name).write_bytes(path.read_bytes())
        maximum = environment.profile.timeout_seconds * ledger.rules.timeout_charge_per_second
        key = ledger.reserve_work("evaluation", maximum, "joint_hidden_evaluation")
        boundary("hidden_evaluation_inflight")
        try:
            result = environment.sandbox().run({"operation": "evaluate", "patches": patches,
                "reference_patches": reference_patches,
                "suites": environment.data["suites"],
                "seconds": max(1, (environment.profile.timeout_seconds-5)//(len(patches)*2+len(reference_patches)))},
                workspace, private, cancelled=cancelled)
            ledger.reconcile_work(key, min(maximum, result["wall_seconds"]*ledger.rules.timeout_charge_per_second))
            ledger.entries[-1].update(wall_seconds=result["wall_seconds"], limits=result["limits"], cleanup=result["cleanup"])
            boundary("hidden_evaluation_complete")
        except Exception:
            if key in ledger.reservations:
                ledger.reconcile_work(key, None)
            raise
        if result.get("failure") == "interrupted":
            from ..runtime.episode import Interrupted
            raise Interrupted("Hidden evaluation cancelled; no worker feedback")
        if result.get("failure") or result["returncode"]:
            raise SandboxFailure("Joint evaluator infrastructure failed")
        try:
            payload = json.loads(result["stdout"])
            if "evaluation_error" in payload:
                if validation_control:
                    raise SandboxFailure(payload["evaluation_error"])
                # Environment controls have already established patch applicability
                # on the base/reference. Candidate-induced conflicts are failures
                # of that candidate, not infrastructure rows excluded from scoring.
                return {"complete_task_success": False, "joint_candidate": True,
                        "reason": payload["evaluation_error"], "feature_suites": {
                            f: {"passed": False, "returncode": None, "status": "not_run_patch_conflict"}
                            for f in task.required_outputs}}
            suites = payload["evaluation"]
            if set(suites) != set(task.required_outputs) or any(
                    type(v.get("returncode")) is not int and not (v.get("returncode") is None and v.get("timeout") is True)
                    for v in suites.values()):
                raise ValueError("Missing feature suite results")
        except (ValueError, KeyError, TypeError) as exc:
            raise SandboxFailure("Invalid evaluator response") from exc
        return {"complete_task_success": all(v["returncode"] == 0 for v in suites.values()),
                "feature_suites": {k: {"passed": v["returncode"] == 0, "returncode": v["returncode"],
                                       "timeout": v.get("timeout", False)} for k, v in suites.items()},
                "test_patch_hashes": {k: file_hash(private / k) for k in patches},
                "evaluation_output_hash": digest(payload), "joint_candidate": True}


def validation_identity(environment, task):
    from ..runtime.apptainer import GUEST
    return {"environment_hash": environment.hash, "task_hash": task.source_hash,
            "evaluator_hash": file_hash(Path(__file__)), "guest_hash": file_hash(GUEST)}


def validate_environment(environment, task, data_manifest, output):
    """Baseline and positive control in separate evaluator invocations, no worker."""
    from ..runtime.budget import BudgetLedger
    environment.validate_task(task)
    ledger = BudgetLedger(100000)
    report = {"schema": "cooper-e0-validation-v1", **validation_identity(environment, task), "passed": False}
    try:
        baseline = evaluate(task, environment, environment.base, data_manifest, ledger, validation_control=True)
        positive = evaluate(task, environment, environment.base, data_manifest, ledger,
                            reference_features=task.required_outputs, validation_control=True)
        report.update(baseline=baseline, positive=positive)
        # Reject vacuous commands that pass an unchanged base, missing tests, and
        # incompatible reference patch application rather than redefining scoring.
        report["passed"] = (all(not s["passed"] for s in baseline["feature_suites"].values()) and
                            positive["complete_task_success"] is True)
    except (BCError, OSError, ValueError) as exc:
        report["error"] = str(exc)
    report["costs"] = ledger.summary()
    report["command_failed"] = not report["passed"]
    atomic_json(output, report)
    return report


def require_environment_validation(path, expected_hash, environment, task):
    report = read_json(path)
    if (digest(report) != expected_hash or report.get("schema") != "cooper-e0-validation-v1" or
            report.get("passed") is not True or any(report.get(k) != v for k, v in validation_identity(environment, task).items())):
        raise BCError("Missing or stale joint evaluator baseline/reference validation")
    baseline = report.get("baseline", {}).get("feature_suites", {})
    positive = report.get("positive", {}).get("feature_suites", {})
    if (set(baseline) != set(task.required_outputs) or set(positive) != set(task.required_outputs) or
            any(s.get("passed") is not False or type(s.get("returncode")) is not int or s["returncode"] == 0
                for s in baseline.values()) or
            any(s.get("passed") is not True or type(s.get("returncode")) is not int or s.get("returncode") != 0 for s in positive.values())):
        raise BCError("Missing actual baseline and positive feature-suite results")
