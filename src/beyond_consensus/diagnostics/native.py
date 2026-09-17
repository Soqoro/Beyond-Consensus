"""Sanitized readiness; private material is read only by this offline audit."""
from collections import Counter

from ..experiments.manifest import grouped_split
from ..runtime.sqlite_executor import POLICY, capabilities
from ..tasks.sqlite_tasks import (DATA_REVISION, CODE_REVISION, inspect, native_tasks,
    records, verify_file, compare_rows, nonempty_material)
from ..util import BCError, digest, read_json


def asset(record):
    if not record:
        return {"present": False, "sha256": None, "integrity": "missing"}
    from pathlib import Path
    present = Path(record["path"]).is_file()
    try:
        verify_file(record)
        integrity = "verified"
    except (BCError, OSError):
        integrity = "mismatch" if present else "missing"
    return {"present": present, "sha256": record.get("sha256"), "integrity": integrity}


def readiness(staged=None):
    report = {"schema": "bc-native-readiness-v1", "dataset_revision": DATA_REVISION,
        "upstream_commit": CODE_REVISION, "tool_policy": POLICY, "executor": capabilities(),
        "model_executed": False, "sql_executed": False, "tasks": [], "scored_tasks": 0,
        "full_upstream_native_partial_score": {"status": "unavailable_untranslated_python_scorer", "value": None},
        "support_boundary": {"artifacts": ["reviewed SELECT tree", "reviewed view definition"],
            "unsupported_constructs": ["raw SQL", "write statements", "triggers", "nonempty setup/cleanup", "CTEs", "window expressions", "functions outside the fixed allowlist"],
            "setup_cleanup": "empty only", "tests": "reviewed nonempty read comparisons; upstream Python is not executed",
            "native_score": "round2/set/empty-fails result comparison subset; not full upstream Python scorer"}}
    if staged is None:
        return {**report, "status": "scoring_unavailable", "reason": "staging_manifest_not_supplied",
            "next_action": "Register existing public database/documents and author materials with sqlite-stage; obtain and review missing materials manually.",
            "summary": "No local staging manifest supplied; native readiness and counts are unknown."}
    report["staging_hash"] = digest(staged)
    # Never include private paths, raw exceptions, SQL or evaluator contents.
    try:
        statuses = inspect(staged)["tasks"]
        public = {r["instance_id"]: r for r in records(verify_file(staged["metadata"]))}
        full = {r["instance_id"]: r for r in records(verify_file(staged["materials"]))} if staged.get("materials") else {}
        review = read_json(verify_file(staged["review"])) if staged.get("review") else {}
        supported, rejected = native_tasks(staged)
    except (BCError, OSError, ValueError, KeyError, TypeError):
        return {**report, "status": "blocked_prerequisite", "reason": "staging_release_integrity_or_review_invalid",
            "next_action": "Verify the pinned staging manifest and exact-record material/review hashes in the private workspace.",
            "summary": "Pinned staging or review is invalid; no tasks admitted."}
    supported = {t.id: t for t in supported}
    rejected = {r["id"]: r for r in rejected}
    for status in statuses:
        key = status["id"]
        raw, gold, approval = public[key], full.get(key, {}), review.get("tasks", {}).get(key, {})
        db = staged["databases"][raw["selected_database"]]
        bindings = bool(gold and approval.get("record_hash") == digest(raw) and approval.get("material_hash") == digest(gold))
        approved = bool(bindings and nonempty_material(gold.get("sol_sql")) and nonempty_material(gold.get("test_cases"))
            and review.get("reviewer") and approval.get("test_translation_reviewed") is True
            and approval.get("supported_requirement") is True and approval.get("review_notes"))
        reasons = []
        if not nonempty_material(gold.get("sol_sql")) or not nonempty_material(gold.get("test_cases")):
            reasons.append("missing_nonempty_author_solution_or_tests")
        if not approved:
            reasons.append("missing_or_unbound_private_review")
        database = asset(db.get("database"))
        documents = {label: asset(db.get("documents", {}).get(label)) for label in ("schema", "columns", "knowledge")}
        if database["integrity"] != "verified" or any(v["integrity"] != "verified" for v in documents.values()):
            reasons.append("missing_or_changed_database_or_documents")
        empty_setup = not raw["preprocess_sql"] and not raw["clean_up_sqls"] and not approval.get("setup") and not approval.get("cleanup")
        if not empty_setup:
            reasons.append("unsupported_nonempty_setup_or_cleanup")
        if key not in supported and not reasons:
            reasons.append("unsupported_or_invalid_reviewed_requirement")
        # Messages in the native adapter are fixed diagnoses except compiler messages,
        # which can embed private identifiers; expose an allowlisted category only.
        private_reasons = rejected.get(key, {}).get("reasons", [])
        boundary = []
        for message in private_reasons:
            lower = message.lower()
            if "select" in lower or "expression" in lower or "operator" in lower or "function" in lower:
                boundary.append("select_tree_construct_or_reference_unsupported")
            if "setup" in lower or "cleanup" in lower:
                boundary.append("nonempty_setup_cleanup")
            if "check" in lower or "test" in lower:
                boundary.append("evaluation_translation_or_obligation_binding")
        entry = {"task_id": key, "database_id": raw["selected_database"], "group": "database:"+raw["selected_database"],
            "split": grouped_split("database:"+raw["selected_database"]), "category": raw["category"],
            "dataset_revision": DATA_REVISION, "upstream_commit": CODE_REVISION, "public_record_hash": digest(raw),
            "database": database, "documents": documents,
            "reference": {"present": nonempty_material(gold.get("sol_sql")), "provenance": "author-material record" if gold else None,
                "record_hash": digest(gold) if gold else None, "approved": approved, "exact_record_binding": bindings},
            "hidden_tests": {"present": nonempty_material(gold.get("test_cases")), "provenance": "author-material record" if gold else None,
                "approved": approved, "review_hash": staged.get("review", {}).get("sha256") if staged.get("review") else None},
            "tool_support": "supported_reviewed_tree" if key in supported else "blocked_or_unassessed",
            "unsupported_capability_categories": sorted(set(boundary)), "setup_cleanup_supported": empty_setup,
            "native_scoring": "pending_reference_controls" if key in supported else "scoring_unavailable",
            "joint_state": "candidate_requires_joint_reference" if key in supported else "unavailable",
            "status": "ready_for_reference_validation" if key in supported else "blocked",
            "blocking_reasons": reasons,
            "next_action": "Run sqlite-validate --up-to --count 10 in a CPU allocation." if key in supported else
                "Stage missing pinned files; privately review exact author records and supported tree translations. Unsupported constructs require a reviewed extension."}
        report["tasks"].append(entry)
    counts = dict(Counter(t["status"] for t in report["tasks"]))
    report.update(status="reference_validation_required" if supported else "scoring_unavailable", counts=counts,
        summary=f"{len(statuses)} metadata records; {len(supported)} supported reviewed candidates; 0 scored by this read-only audit.")
    return report


def scorer_parity():
    cases = [("ordering", [[2], [1]], [[1], [2]], True, False, False),
             ("duplicates", [[1], [1]], [[1]], False, False, True),
             ("null", [[None]], [[None]], False, True, True),
             ("tolerance", [[1.001]], [[1.002]], True, False, True),
             ("empty", [], [], False, True, False)]
    return [{"case": name, "strict": compare_rows(a, b, order), "native_subset": compare_rows(a, b, order, True),
        "expected_strict": strict, "expected_native_subset": native,
        "passed": compare_rows(a, b, order) == strict and compare_rows(a, b, order, True) == native}
        for name, a, b, order, strict, native in cases]
