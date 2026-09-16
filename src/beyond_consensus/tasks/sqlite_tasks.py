"""Explicit public/harness/evaluator views and reviewed SQLite task registration."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sqlite3

from ..schemas import TaskInstance
from ..util import BCError, atomic_json, digest, file_hash, plain, read_json
from ..runtime.sqlite_executor import POLICY, DEFAULT_LIMITS, compile_select, identifier

DATA_REVISION = "0664a2f28555faa0dd2947c8c23288df79bcc06b"
CODE_REVISION = "abd11b6db92a1c9f809b32f7564c7c71b34d67f0"
SCORER = "bc-sqlite-joint-v1"
DATA_FILE = "livesqlbench_data_sqlite.jsonl"
PUBLIC_SHA256 = "2b964165a6cda878a4e4d4de9ccef1c6ad623b96e5215b522d81be284c9fcebc"


def column(name):
    return {"column": name}


def read_query(table, fields):
    return {"columns": [{"expr": column(f)} for f in fields], "from": {"table": table}}


def fixtures(count=1):
    if not 1 <= count <= 4:
        raise BCError("There are four labelled SQLite engineering fixtures; do not inflate their count")
    result = []
    for n in range(count):
        sources = {f"u{i}": {"requirement": f"Return id and value multiplied by {i+1+n} from measurements, ordered by id.",
            "kind": "query", "table": "measurements", "factor": i+1+n} for i in range(4)}
        result.append(TaskInstance(f"sqlite-fixture-{n}", "sqlite_fixture", f"sqlite-fixture-source-{n}",
            "Labelled engineering fixture. Submit all four required reports. Read each assigned contract and schema. "
            "Use the restricted SELECT tree tools. All four reports must be present and correct.",
            sources, tuple(sources), (), {"adaptation": "bc_sqlite_fixture_v1", "tool_policy": POLICY,
                "scorer": SCORER, "access_regime": "all_approved_public_documents",
                "fixture_seed": n, "synthetic": True, "readiness": "fixture",
                "base_hash": digest(["sqlite_fixture", n]), "source_ids": [f"fixture-{n}"],
                "harness": {"tables": ["measurements"], "schema": {"measurements": ["id", "value"]},
                    "documents": {}, "limits": dict(DEFAULT_LIMITS)}}))
    return result


def fixture_database(path, seed):
    path = Path(path)
    if not path.exists():
        con = sqlite3.connect(path)
        try:
            con.execute("CREATE TABLE measurements(id INTEGER PRIMARY KEY,value INTEGER)")
            con.executemany("INSERT INTO measurements VALUES(?,?)", [(1, 2+seed), (2, -3-seed), (3, 0)])
            con.commit()
        finally:
            con.close()
    return path


def compare_rows(actual, expected, ordered=False, native=False):
    """Versioned comparison diagnostics, not upstream Python-test execution.

    Inspected native ex_base: Python round(float,2), exact ordered lists or
    unordered sets, empty result fails. Joint v1 preserves duplicate counts,
    NULLs and ordering; requires exact numeric values (no rounding tolerance).
    """
    def rows(values):
        return [tuple(round(v, 2) if native and isinstance(v, float) else v for v in row) for row in values]
    a, b = rows(actual), rows(expected)
    if native and (not a or not b):
        return False
    if ordered:
        return a == b
    return set(a) == set(b) if native else Counter(a) == Counter(b)


def _outside_git(path):
    path = Path(path).resolve()
    root = Path(__file__).resolve().parents[3]
    if path == root or root in path.parents:
        raise BCError("Register staged data and evaluation material outside the Git checkout")
    return path


def pinned_file(path):
    path = _outside_git(path)
    if not path.is_file():
        raise BCError("Staged prerequisite file is missing")
    return {"path": str(path), "sha256": file_hash(path)}


def verify_file(record):
    path = _outside_git(record["path"])
    if not path.is_file() or file_hash(path) != record["sha256"]:
        raise BCError("Staged prerequisite integrity mismatch")
    return path


def records(path):
    result = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {"instance_id", "selected_database", "query", "preprocess_sql", "clean_up_sqls", "category", "conditions", "sol_sql", "test_cases"}
    if any(not required <= set(r) for r in result) or len({r["instance_id"] for r in result}) != len(result):
        raise BCError("Unexpected LiveSQLBench record interface or duplicate IDs")
    return result


def stage(root, output, materials=None, review=None):
    """Register already staged local files. No network, SQL setup, or test exec."""
    root = _outside_git(root)
    _outside_git(output)
    raw = records(root / DATA_FILE)
    databases = {}
    for name in sorted({r["selected_database"] for r in raw}):
        identifier(name)
        # These names are from the pinned release tree. Missing files stay missing.
        directory = root / name
        db = directory / (name + "_template.sqlite")
        entry = {"status": "missing_database", "documents": {}}
        if db.is_file():
            if any(Path(str(db)+suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
                raise BCError("Database is active or has sidecars; stage an immutable closed source")
            entry = {"status": "staged", "database": pinned_file(db), "documents": {}}
        for suffix, label in (("_schema.txt", "schema"), ("_column_meaning_base.json", "columns"), ("_kb.jsonl", "knowledge")):
            path = directory / (name + suffix)
            if path.is_file():
                entry["documents"][label] = pinned_file(path)
        databases[name] = entry
    result = {"schema": "bc-sqlite-stage-v1", "dataset_revision": DATA_REVISION,
        "upstream_commit": CODE_REVISION, "metadata": pinned_file(root / DATA_FILE),
        "databases": databases, "materials": pinned_file(materials) if materials else None,
        "review": pinned_file(review) if review else None}
    if Path(output).exists():
        raise BCError("Use a new staging manifest path")
    atomic_json(output, result)
    return inspect(result)


def inspect(staged):
    if staged.get("schema") != "bc-sqlite-stage-v1" or staged["dataset_revision"] != DATA_REVISION or staged["upstream_commit"] != CODE_REVISION:
        raise BCError("Unreviewed SQLite release/schema")
    if staged["metadata"]["sha256"] != PUBLIC_SHA256:
        raise BCError("Public metadata differs from the audited release hash")
    public = records(verify_file(staged["metadata"]))
    full = {r["instance_id"]: r for r in records(verify_file(staged["materials"]))} if staged.get("materials") else {}
    review = read_json(verify_file(staged["review"])) if staged.get("review") else {}
    statuses = []
    for record in public:
        key = record["instance_id"]
        private = full.get(key, {})
        reasons = []
        if not private.get("sol_sql") or not private.get("test_cases"):
            reasons.append("scoring_unavailable: missing nonempty author solution/test material")
        approved = review.get("tasks", {}).get(key)
        if not approved:
            reasons.append("blocked: requirement/setup/test translation has not been reviewed")
        db = staged["databases"][record["selected_database"]]
        if db["status"] != "staged":
            reasons.append("blocked: database missing")
        if set(db["documents"]) != {"schema", "columns", "knowledge"}:
            reasons.append("blocked: approved public documents missing")
        statuses.append({"id": key, "category": record["category"], "database": record["selected_database"],
            "status": "candidate_requires_validation" if not reasons else "blocked", "reasons": reasons})
    return {"dataset_revision": DATA_REVISION, "tasks": statuses,
            "scored_ready": False, "material_access": "author email request; see MIGRATION_SQLITE_SILO.md"}


def native_tasks(staged):
    inspection = inspect(staged)
    public = {r["instance_id"]: r for r in records(verify_file(staged["metadata"]))}
    if not staged.get("materials") or not staged.get("review"):
        return [], inspection["tasks"]
    private = {r["instance_id"]: r for r in records(verify_file(staged["materials"]))}
    reviewed = read_json(verify_file(staged["review"]))
    if reviewed.get("schema") != "bc-sqlite-reviewed-evaluation-v1" or not isinstance(reviewed.get("reviewer"), str) or not reviewed["reviewer"].strip():
        raise BCError("Evaluation review schema/reviewer required")
    result, excluded = [], []
    for status in inspection["tasks"]:
        if status["status"] == "blocked":
            excluded.append(status)
            continue
        key, raw = status["id"], public[status["id"]]
        approval, gold = reviewed["tasks"][key], private[key]
        try:
            if any(gold[k] != raw[k] for k in ("instance_id", "selected_database", "query", "preprocess_sql", "clean_up_sqls", "category", "conditions")):
                raise BCError("Public/private requirement or setup mismatch")
            if approval.get("record_hash") != digest(raw) or approval.get("material_hash") != digest(gold):
                raise BCError("Evaluation review does not bind these exact records")
            if approval.get("test_translation_reviewed") is not True or not isinstance(approval.get("review_notes"), str) or not approval["review_notes"].strip():
                raise BCError("Python tests must be manually reviewed and ported, not executed")
            if raw["preprocess_sql"] or raw["clean_up_sqls"] or approval.get("setup") or approval.get("cleanup"):
                raise BCError("v1 supports empty setup/cleanup only; nonempty plans require an audited extension")
            kind = approval["artifact"]["kind"]
            if kind not in ("query", "view") or approval.get("supported_requirement") is not True:
                raise BCError("Only reviewed SELECT/CREATE VIEW requirements are supported")
            if raw["category"] != ("Query" if kind == "query" else "Management"):
                raise BCError("Artifact does not preserve the native task category")
            database = staged["databases"][raw["selected_database"]]
            verify_file(database["database"])
            tables = approval["tables"]
            for name in tables:
                identifier(name)
            compile_select(approval["artifact"]["select"], tables)
            if not approval.get("checks"):
                raise BCError("Reviewed nonempty evaluation checks required")
            if kind == "view":
                identifier(approval["artifact"]["name"])
            for check in approval["checks"]:
                if set(check) - {"select", "reference", "submitted_report", "order"}:
                    raise BCError("Unknown evaluation operation; only reviewed read comparisons are supported")
                if any(key in check and type(check[key]) is not bool for key in ("order", "submitted_report")):
                    raise BCError("Evaluation order/report flags must be booleans")
                compile_select(check["reference"], tables)
                if kind == "query" and not check.get("submitted_report"):
                    raise BCError("Query tests must evaluate the submitted report")
                if kind == "view":
                    if check.get("submitted_report"):
                        raise BCError("View evaluation requires an explicit read of the submitted view")
                    _, refs = compile_select(check["select"], set(tables) | {approval["artifact"]["name"]})
                    if approval["artifact"]["name"] not in refs:
                        raise BCError("View check does not consume the submitted view")
            docs = {}
            for label, entry in database["documents"].items():
                text = verify_file(entry).read_text(encoding="utf-8")
                if len(text) > 1000000:
                    raise BCError("Document capacity exceeded")
                if label == "knowledge":
                    for line in text.splitlines():
                        doc = json.loads(line)
                        docs["kb-"+str(doc["id"])] = {k: doc[k] for k in ("knowledge", "description", "definition", "type", "children_knowledge")}
                else:
                    # Source documents only: never include gold-selected knowledge IDs.
                    docs[label] = text
            contract = {"requirement": raw["query"], "kind": kind,
                **({"name": approval["artifact"]["name"]} if kind == "view" else {})}
            task = TaskInstance(key, "sqlite_native", "database:"+raw["selected_database"], raw["query"],
                {key: contract}, (key,), (), {"adaptation": "bc_livesql_native_v1", "tool_policy": POLICY,
                "scorer": SCORER, "access_regime": "all_approved_public_documents", "upstream_commit": CODE_REVISION,
                "dataset_revision": DATA_REVISION, "database_id": raw["selected_database"],
                "source_ids": [key], "base_hash": database["database"]["sha256"], "record_hashes": [digest(raw)],
                "requirement_hashes": [digest(" ".join(raw["query"].lower().split()))],
                "readiness": "reviewed_pending_reference_validation", "review_hash": staged["review"]["sha256"],
                "harness": {"database": database["database"], "tables": tables, "schema": approval["schema"],
                    "documents": docs, "limits": {**DEFAULT_LIMITS, **approval.get("limits", {})}, "setup": [], "cleanup": []},
                "evaluation": {key: {"artifact": approval["artifact"], "checks": approval["checks"],
                    "conditions": raw["conditions"], "material_hash": digest(gold),
                    "native_semantics": "reviewed-tree-result-comparison-diagnostic-v1"}}})
            result.append(task)
        except (BCError, ValueError, KeyError, TypeError) as exc:
            excluded.append({"id": key, "status": "blocked", "reasons": [str(exc)]})
    return result, excluded


def review_template(staged, ids):
    """Scaffold exact-record hashes; never invent a reference or approval."""
    inspect(staged)
    public = {r["instance_id"]: r for r in records(verify_file(staged["metadata"]))}
    private = {r["instance_id"]: r for r in records(verify_file(staged["materials"]))} if staged.get("materials") else {}
    if not ids or not set(ids) <= public.keys():
        raise BCError("Select actual public task IDs")
    return {"schema": "bc-sqlite-reviewed-evaluation-v1", "reviewer": "", "tasks": {key: {
        "record_hash": digest(public[key]), "material_hash": digest(private[key]) if key in private else None,
        "supported_requirement": False, "test_translation_reviewed": False, "review_notes": "",
        "tables": [], "schema": {}, "artifact": None, "checks": [], "setup": [], "cleanup": []}
        for key in ids}}


def pair(left, right, rationale):
    if left.kind != "sqlite_native" or right.kind != "sqlite_native" or left.id == right.id:
        raise BCError("Pair needs two distinct native tasks")
    if not rationale.strip():
        raise BCError("Pair compatibility rationale required")
    for key in ("database_id", "base_hash", "dataset_revision", "scorer", "access_regime"):
        if left.metadata[key] != right.metadata[key]:
            raise BCError("Pair does not share a compatible initial state/release/scorer")
    if left.metadata["harness"] != right.metadata["harness"]:
        raise BCError("Pair setup/cleanup/schema/limits conflict")
    names = [s.get("name") for t in (left, right) for s in t.sources.values() if s["kind"] == "view"]
    if len(names) != len(set(names)):
        raise BCError("Pair artifacts collide")
    from copy import deepcopy
    metadata = deepcopy(left.metadata)
    for key in ("validation_hash", "validated_sqlite_runtime", "executor_runtime"):
        metadata.pop(key, None)
    metadata.update({"adaptation": "bc_livesql_pairs_v1", "source_ids": [left.id, right.id],
        "record_hashes": left.metadata["record_hashes"] + right.metadata["record_hashes"],
        "requirement_hashes": left.metadata["requirement_hashes"] + right.metadata["requirement_hashes"],
        "compatibility_rationale": rationale, "validation_status": "candidate_pending_joint_reference",
        "readiness": "reviewed_pending_reference_validation",
        "evaluation": {**left.metadata["evaluation"], **right.metadata["evaluation"]}})
    return TaskInstance("pair-"+digest([left.id, right.id])[:16], "sqlite_pair", left.group,
        left.specification + "\n\n" + right.specification,
        {**left.sources, **right.sources}, left.required_outputs + right.required_outputs, (), metadata)
