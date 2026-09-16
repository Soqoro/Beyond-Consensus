"""Restricted data API, not an OS sandbox. Also the fixed stdlib CPU child entrypoint.

No raw candidate SQL, executable, path, environment, or Python expression is a
worker input. Every candidate connection has an authorizer, including scoring.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

POLICY = "bc-select-tree-v1"
FUNCTIONS = frozenset({"abs", "coalesce", "ifnull", "nullif", "round", "length",
    "lower", "upper", "substr", "trim", "replace", "min", "max", "sum", "avg",
    "count", "total", "json_extract", "json_array_length", "json_type"})
DEFAULT_LIMITS = {"seconds": 5, "cpu_seconds": 3, "memory_bytes": 536870912,
    "max_rows": 1000, "max_output_bytes": 262144, "max_steps": 200000,
    "max_database_bytes": 1073741824}


class SQLRejected(ValueError):
    pass


def keys(obj, allowed, required=()):
    if not isinstance(obj, dict) or set(obj) - set(allowed) or set(required) - set(obj):
        raise SQLRejected("Invalid structured query fields")


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
        raise SQLRejected("Invalid identifier")
    if value.lower().startswith("sqlite_"):
        raise SQLRejected("Protected identifier")
    return '"' + value + '"'


class Compiler:
    """Complete recursive validation of the v1 JSON SELECT grammar.

    Aliases and column references are resolved by SQLite under the authorizer;
    all table/view objects are checked here and again by the authorizer.
    """
    def __init__(self, objects):
        self.objects, self.references, self.nodes = set(objects), set(), 0
        for name in self.objects:
            identifier(name)

    def tick(self, depth):
        self.nodes += 1
        if self.nodes > 400 or depth > 12:
            raise SQLRejected("Query tree exceeds node/depth limit")

    def expr(self, obj, depth=0):
        self.tick(depth)
        if not isinstance(obj, dict) or len(obj) != 1:
            raise SQLRejected("Expressions must have exactly one operator")
        kind, value = next(iter(obj.items()))
        if kind == "column":
            if not isinstance(value, str) or len(value.split(".")) not in (1, 2):
                raise SQLRejected("Invalid column")
            return ".".join(identifier(p) for p in value.split("."))
        if kind == "literal":
            if value is None:
                return "NULL"
            if type(value) in (int, float):
                if not math.isfinite(value) or abs(value) > 1e15:
                    raise SQLRejected("Numeric literal exceeds bounds")
                return str(value)
            if isinstance(value, str) and len(value) <= 4096 and "\x00" not in value:
                return "'" + value.replace("'", "''") + "'"
            raise SQLRejected("Invalid literal")
        if kind == "binary":
            if not isinstance(value, list) or len(value) != 3 or value[0] not in (
                    "+", "-", "*", "/", "%", "=", "!=", "<", "<=", ">", ">=", "and", "or", "is", "is not", "like"):
                raise SQLRejected("Unsupported binary operation")
            return f"({self.expr(value[1], depth+1)} {value[0]} {self.expr(value[2], depth+1)})"
        if kind == "call":
            keys(value, {"name", "args", "distinct"}, {"name", "args"})
            if value["name"] not in FUNCTIONS or not isinstance(value["args"], list) or len(value["args"]) > 8:
                raise SQLRejected("Unsupported function")
            if "distinct" in value and type(value["distinct"]) is not bool:
                raise SQLRejected("Invalid distinct flag")
            args = ",".join(self.expr(a, depth+1) for a in value["args"])
            return value["name"] + "(" + ("DISTINCT " if value.get("distinct") else "") + args + ")"
        if kind == "select":
            return "(" + self.select(value, depth+1) + ")"
        if kind == "case":
            keys(value, {"when", "else"}, {"when", "else"})
            if not isinstance(value["when"], list) or not 1 <= len(value["when"]) <= 8:
                raise SQLRejected("Invalid CASE")
            clauses = []
            for pair in value["when"]:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise SQLRejected("Invalid CASE branch")
                clauses.append("WHEN " + self.expr(pair[0], depth+1) + " THEN " + self.expr(pair[1], depth+1))
            return "(CASE " + " ".join(clauses) + " ELSE " + self.expr(value["else"], depth+1) + " END)"
        raise SQLRejected("Unsupported expression; raw SQL is not accepted")

    def source(self, obj, depth):
        self.tick(depth)
        keys(obj, {"table", "as", "select"})
        if ("table" in obj) == ("select" in obj):
            raise SQLRejected("Source needs exactly one table or subquery")
        if "table" in obj:
            name = obj["table"]
            identifier(name)
            if name not in self.objects:
                raise SQLRejected("Undeclared database object")
            self.references.add(name)
            text = identifier(name)
        else:
            text = "(" + self.select(obj["select"], depth+1) + ")"
        return text + (" AS " + identifier(obj["as"]) if "as" in obj else "")

    def select(self, obj, depth=0):
        self.tick(depth)
        keys(obj, {"columns", "from", "joins", "where", "group_by", "having", "order_by", "distinct", "limit"}, {"columns"})
        if not isinstance(obj["columns"], list) or not 1 <= len(obj["columns"]) <= 32:
            raise SQLRejected("Invalid SELECT columns")
        if "distinct" in obj and type(obj["distinct"]) is not bool:
            raise SQLRejected("Invalid distinct flag")
        columns = []
        for item in obj["columns"]:
            keys(item, {"expr", "as"}, {"expr"})
            columns.append(self.expr(item["expr"], depth+1) + (" AS " + identifier(item["as"]) if "as" in item else ""))
        text = "SELECT " + ("DISTINCT " if obj.get("distinct") else "") + ",".join(columns)
        if "from" in obj:
            text += " FROM " + self.source(obj["from"], depth+1)
        joins = obj.get("joins", [])
        if not isinstance(joins, list) or len(joins) > 8 or (joins and "from" not in obj):
            raise SQLRejected("Invalid joins")
        for join in joins:
            keys(join, {"kind", "source", "on"}, {"kind", "source"})
            if join["kind"] not in ("inner", "left", "cross") or (join["kind"] != "cross" and "on" not in join):
                raise SQLRejected("Unsupported join")
            text += " " + join["kind"].upper() + " JOIN " + self.source(join["source"], depth+1)
            if "on" in join:
                text += " ON " + self.expr(join["on"], depth+1)
        for key, word in (("where", " WHERE "), ("having", " HAVING ")):
            if key == "having" and "group_by" in obj:
                group = obj["group_by"]
                if not isinstance(group, list) or not 1 <= len(group) <= 16:
                    raise SQLRejected("Invalid GROUP BY")
                text += " GROUP BY " + ",".join(self.expr(e, depth+1) for e in group)
            if key in obj:
                text += word + self.expr(obj[key], depth+1)
        if "order_by" in obj:
            order = obj["order_by"]
            if not isinstance(order, list) or not 1 <= len(order) <= 16:
                raise SQLRejected("Invalid ORDER BY")
            parts = []
            for item in order:
                keys(item, {"expr", "direction"}, {"expr"})
                if item.get("direction", "asc") not in ("asc", "desc"):
                    raise SQLRejected("Invalid ordering")
                parts.append(self.expr(item["expr"], depth+1) + " " + item.get("direction", "asc"))
            text += " ORDER BY " + ",".join(parts)
        if "limit" in obj:
            if type(obj["limit"]) is not int or not 0 <= obj["limit"] <= 1000:
                raise SQLRejected("Invalid explicit LIMIT")
            text += " LIMIT " + str(obj["limit"])
        return text


def compile_select(tree, objects):
    compiler = Compiler(objects)
    sql = compiler.select(tree)
    if len(sql) > 65536:
        raise SQLRejected("Statement length limit")
    return sql, sorted(compiler.references)


def capabilities():
    result = {"sqlite": sqlite3.sqlite_version, "python": sys.version.split()[0],
        "policy": POLICY, "authorizer": hasattr(sqlite3.Connection, "set_authorizer"),
        "defensive": False, "trusted_schema_off": False, "process_limits": False,
        "extension_loading_disabled": False, "table_inventory": False}
    with sqlite3.connect(":memory:") as con:
        try:
            if hasattr(con, "enable_load_extension"):
                con.enable_load_extension(False)
            result["extension_loading_disabled"] = True  # Also safe when compiled out.
        except sqlite3.Error:
            pass
        if hasattr(con, "setconfig") and hasattr(sqlite3, "SQLITE_DBCONFIG_DEFENSIVE"):
            con.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            result["defensive"] = con.getconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE)
        con.execute("PRAGMA trusted_schema=OFF")
        result["trusted_schema_off"] = con.execute("PRAGMA trusted_schema").fetchone() == (0,)
        result["table_inventory"] = bool(con.execute("PRAGMA table_list").fetchall())
    try:
        import resource
        result["process_limits"] = all(hasattr(resource, x) for x in ("RLIMIT_AS", "RLIMIT_CPU", "RLIMIT_FSIZE")) and hasattr(signal, "setitimer")
    except ImportError:
        pass
    return result


def authorizer(objects, creating=None):
    def allow(action, arg1, arg2, db, trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        # SQLite also reports table-only reads (COUNT/cross-join cardinality)
        # with an empty column and no database argument. Attach is always denied.
        if action == sqlite3.SQLITE_READ and arg1 in objects and (db == "main" or db is None and arg2 == ""):
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in FUNCTIONS:
            return sqlite3.SQLITE_OK
        # Only the compiler's CREATE VIEW wrapper enters this short-lived path.
        if creating and db == "main":
            if action == sqlite3.SQLITE_CREATE_VIEW and arg1 == creating:
                return sqlite3.SQLITE_OK
            if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_READ) and arg1 == "sqlite_master":
                return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return allow


def _child(request):
    limits = {**DEFAULT_LIMITS, **request["limits"]}
    caps = capabilities()
    if not all(caps[k] for k in ("authorizer", "trusted_schema_off", "defensive", "process_limits", "extension_loading_disabled", "table_inventory")):
        return {"status": "blocked_capability", "capabilities": caps}
    import resource
    # Covers copying/startup as well as SQLite execution if the parent exits.
    signal.setitimer(signal.ITIMER_REAL, limits["seconds"])
    resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"]))
    resource.setrlimit(resource.RLIMIT_AS, (limits["memory_bytes"], limits["memory_bytes"]))
    resource.setrlimit(resource.RLIMIT_FSIZE, (limits["max_database_bytes"]*2, limits["max_database_bytes"]*2))
    source = Path(request["database"])
    if any(Path(str(source)+suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        return {"status": "blocked_prerequisite", "reason": "active_source_database"}
    if source.stat().st_size > limits["max_database_bytes"]:
        return {"status": "execution_limit", "reason": "database_size"}
    with tempfile.TemporaryDirectory(prefix="bc-sql-") as temporary:
        target = Path(temporary) / "state.sqlite"
        shutil.copyfile(source, target)
        if request.get("source_hash"):
            with target.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != request["source_hash"]:
                    return {"status": "blocked_prerequisite", "reason": "source_integrity"}
        con = sqlite3.connect(target, isolation_level=None)
        try:
            if hasattr(con, "enable_load_extension"):
                con.enable_load_extension(False)
            con.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            for pragma in ("trusted_schema=OFF", "temp_store=MEMORY", "mmap_size=0", "cache_size=-2048"):
                con.execute("PRAGMA " + pragma)
            con.execute("PRAGMA hard_heap_limit=" + str(limits["memory_bytes"]//2))
            for name, value in (("SQLITE_LIMIT_LENGTH", 1048576), ("SQLITE_LIMIT_SQL_LENGTH", 65536),
                    ("SQLITE_LIMIT_COLUMN", 64), ("SQLITE_LIMIT_EXPR_DEPTH", 32),
                    ("SQLITE_LIMIT_ATTACHED", 0), ("SQLITE_LIMIT_COMPOUND_SELECT", 1),
                    ("SQLITE_LIMIT_VDBE_OP", 100000), ("SQLITE_LIMIT_FUNCTION_ARG", 8)):
                con.setlimit(getattr(sqlite3, name), value)
            # Originals must be offline reviewed ordinary tables. No executable
            # views/triggers/virtual tables from an unreviewed source schema.
            schema = con.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            inventory = con.execute("PRAGMA table_list").fetchall()
            if any(t not in ("table", "index") for t, n, s in schema) or any(row[2] in ("virtual", "shadow") for row in inventory):
                raise SQLRejected("Unsupported source schema objects")
            tables = {n for t, n, s in schema if t == "table"}
            if tables != set(request["tables"]):
                raise SQLRejected("Source schema differs from approved objects")
            ticks = 0
            start = time.monotonic()
            def progress():
                nonlocal ticks
                ticks += 100
                return int(ticks > limits["max_steps"] or time.monotonic()-start > limits["seconds"])
            con.set_progress_handler(progress, 100)
            objects = set(tables)
            if len(request["views"]) > 16:
                raise SQLRejected("View count limit")
            for view in request["views"]:
                name = view["name"]
                identifier(name)
                if name.lower() in {n.lower() for n in objects}:
                    raise SQLRejected("Object shadowing is prohibited")
                sql, _ = compile_select(view["select"], objects)
                con.set_authorizer(authorizer(objects, creating=name))
                con.execute("CREATE VIEW " + identifier(name) + " AS " + sql)
                objects.add(name)
            con.set_authorizer(authorizer(objects))
            outputs = []
            size = 0
            for tree in request["queries"]:
                sql, refs = compile_select(tree, objects)
                cursor = con.execute(sql)
                rows = []
                for row in cursor:
                    if any(isinstance(v, bytes) or isinstance(v, float) and not math.isfinite(v) for v in row):
                        raise SQLRejected("Unsupported result value")
                    size += len(json.dumps(row, allow_nan=False).encode())
                    if len(rows) >= limits["max_rows"] or size > limits["max_output_bytes"]:
                        return {"status": "execution_limit", "reason": "full_output_capacity", "steps": ticks}
                    rows.append(row)
                outputs.append({"rows": rows, "columns": [c[0] for c in cursor.description], "references": refs})
            return {"status": "ok", "outputs": outputs, "steps": ticks, "capabilities": caps}
        finally:
            con.close()


def execute(database, tables, views, queries, limits=None, *, source_hash=None):
    """Harness API; callers must charge every invocation, including replay/scoring."""
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    if set(limits) != set(DEFAULT_LIMITS) or any(type(v) is not int or v < 1 for v in limits.values()):
        raise SQLRejected("Invalid harness limits")
    request = {"database": str(Path(database).resolve()), "tables": list(tables),
        "views": views, "queries": queries, "limits": limits, "source_hash": source_hash}
    raw = json.dumps(request, allow_nan=False)
    if len(raw.encode()) > 2097152 or len(queries) > 32:
        raise SQLRejected("Executor request limit")
    start = time.monotonic()
    # An owned temporary parent also cleans up if CPU/deadline termination kills
    # the child before its finally block. No candidate API can fork descendants.
    with tempfile.TemporaryDirectory(prefix="bc-sql-child-") as parent:
        env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR") if k in os.environ}
        env.update({"TMPDIR": parent, "TEMP": parent, "TMP": parent})
        process = subprocess.Popen([sys.executable, "-I", "-S", str(Path(__file__).resolve())],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=parent)
        try:
            out, err = process.communicate(raw, timeout=limits["seconds"])
        except BaseException:
            process.kill()
            process.communicate()
            if sys.exc_info()[0] is subprocess.TimeoutExpired:
                return {"status": "execution_limit", "reason": "deadline", "wall_seconds": time.monotonic()-start}
            raise
    if process.returncode:
        return {"status": "execution_limit" if process.returncode < 0 else "infrastructure_failed",
                "reason": "executor_terminated", "wall_seconds": time.monotonic()-start}
    try:
        result = json.loads(out)
    except ValueError:
        result = {"status": "infrastructure_failed", "reason": "invalid_executor_response"}
    result["wall_seconds"] = time.monotonic()-start
    return result


if __name__ == "__main__":
    try:
        value = _child(json.loads(sys.stdin.read(2097153)))
    except SQLRejected:
        value = {"status": "prohibited_operation", "reason": "structured_policy"}
    except sqlite3.DatabaseError as exc:
        code = getattr(exc, "sqlite_errorcode", None)
        status = "execution_limit" if code in (sqlite3.SQLITE_INTERRUPT, sqlite3.SQLITE_NOMEM, sqlite3.SQLITE_TOOBIG, sqlite3.SQLITE_FULL) else (
            "prohibited_operation" if code == sqlite3.SQLITE_AUTH else "semantic_error")
        value = {"status": status, "reason": "query_execution"}
    except (MemoryError, OverflowError):
        value = {"status": "execution_limit", "reason": "memory_or_value"}
    except Exception:
        value = {"status": "infrastructure_failed", "reason": "executor_failure"}
    print(json.dumps(value, allow_nan=False))
