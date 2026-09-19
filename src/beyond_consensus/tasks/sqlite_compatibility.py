"""Four synthetic, schema-supplied tool probes; never native benchmark data.

No solution tree is provided to workers. Terminal expectations are computed
independently in Python and are never used for public monitoring or repair.
"""
from pathlib import Path
import sqlite3

from ..schemas import TaskInstance
from ..util import BCError, canonical, digest
from ..runtime.sqlite_executor import DEFAULT_LIMITS, POLICY
from .sqlite_tasks import read_query

SUITE = "tool_compatibility_v1"
SCHEMA = {"departments": ["id", "name"], "entries": ["id", "department_id", "amount"]}
DEPARTMENTS = ((1, "Amber"), (2, "Blue"), (3, "Cedar"))
ENTRIES = ((1, 1, 4), (2, 1, 6), (3, 2, -2), (4, 2, 2), (5, 3, 0))
REQUIREMENTS = {
    "aggregate": "Return one row per department_id in entries. Output department_id, the sum of amount AS total_amount, and the count of entry IDs AS entry_count. Order by department_id ascending.",
    "join": "Join entries to departments using entries.department_id = departments.id. Return entries.id AS entry_id, departments.name AS department_name, and entries.amount AS amount, ordered by entry_id ascending.",
    "case": "For every row of entries return id and a CASE classification AS sign_label: 'positive' when amount > 0, 'negative' when amount < 0, otherwise 'zero'. Order by id ascending.",
    "view": "Create the view entry_adjusted with columns id and adjusted_amount, where adjusted_amount is entries.amount + 3. Include every entry. Finish by submitting the created view's artifact ID.",
}


def tasks():
    result = []
    for probe, requirement in REQUIREMENTS.items():
        unit = "sqlite-tools-" + probe
        contract = {"kind": "view" if probe == "view" else "query", "requirement": requirement,
            "schema": SCHEMA, "relationships": ["entries.department_id = departments.id"],
            **({"name": "entry_adjusted"} if probe == "view" else {})}
        specification = ("Synthetic SQLite tool-compatibility diagnostic, not a benchmark task. "
            "All schema and relationship information is supplied here; no document discovery is needed. "
            "Read the assigned contract, construct the requested artifact, then submit its returned artifact ID. "
            "Schema: " + canonical(SCHEMA) + ". Relationship: entries.department_id = departments.id. "
            "Requirement: " + requirement)
        result.append(TaskInstance(unit, "sqlite_fixture", "sqlite-tool-compatibility-source-v1",
            specification, {unit: contract}, (unit,), (), {
                "adaptation": "bc_sqlite_tool_compatibility_v1", "scorer": "bc-sqlite-tools-v1",
                "tool_policy": POLICY, "access_regime": "synthetic_schema_supplied",
                "diagnostic_mode": "tool_compatibility", "sqlite_fixture_suite": SUITE,
                "probe": probe, "synthetic": True, "readiness": "fixture",
                "base_hash": digest([SCHEMA, DEPARTMENTS, ENTRIES]), "source_ids": ["sqlite-tools-v1"],
                "harness": {"tables": list(SCHEMA), "schema": SCHEMA,
                    "documents": {}, "limits": dict(DEFAULT_LIMITS)}}))
    return result


def database(path):
    """Fixed trusted synthetic setup, not model-generated SQL."""
    path = Path(path)
    if not path.exists():
        con = sqlite3.connect(path)
        try:
            con.execute("CREATE TABLE departments(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            con.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, department_id INTEGER NOT NULL, amount INTEGER NOT NULL)")
            con.executemany("INSERT INTO departments VALUES (?,?)", DEPARTMENTS)
            con.executemany("INSERT INTO entries VALUES (?,?,?)", ENTRIES)
            con.commit()
        finally:
            con.close()
    return path


def view_check():
    query = read_query("entry_adjusted", ["id", "adjusted_amount"])
    query["order_by"] = [{"expr": {"column": "id"}, "direction": "asc"}]
    return query


def expected(probe):
    if probe == "aggregate":
        rows = [[d, sum(a for _, dept, a in ENTRIES if dept == d),
                 sum(dept == d for _, dept, _ in ENTRIES)] for d in sorted({d for _, d, _ in ENTRIES})]
        return ["department_id", "total_amount", "entry_count"], rows
    if probe == "join":
        names = dict(DEPARTMENTS)
        return ["entry_id", "department_name", "amount"], [[i, names[d], a] for i, d, a in ENTRIES]
    if probe == "case":
        return ["id", "sign_label"], [[i, "positive" if a > 0 else "negative" if a < 0 else "zero"] for i, _, a in ENTRIES]
    if probe == "view":
        return ["id", "adjusted_amount"], [[i, a+3] for i, _, a in ENTRIES]
    raise BCError("Unknown tool compatibility probe")


def score(probe, output):
    columns, rows = expected(probe)
    return output["columns"] == columns and output["rows"] == rows
