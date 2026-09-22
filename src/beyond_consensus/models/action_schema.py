"""Public SQL action syntax only: no task, artifact, reference or model inputs.

Objects use the declared key order during constrained generation. Runtime SQL
validation remains authoritative for identifiers, bindings, depth and semantics.
"""
from __future__ import annotations

import json
import math
import re

from ..util import BCError, digest
from ..runtime.sqlite_executor import FUNCTIONS

MODE = "sqlite-json-schema-v1"
XGRAMMAR_VERSION = "0.1.32"
DECODER_CPU_SECONDS = 30


def obj(properties, required=None, additional=False):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": additional}


def array(items, maximum, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


def ref(name):
    return {"$ref": "#/$defs/"+name}


def enum(*values):
    return {"enum": list(values)}


def action_schema(mode=MODE):
    if mode not in (MODE, "sqlite-sql-text-v1"):
        raise BCError("Unknown action representation")
    name = {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]{0,62}$"}
    column = {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]{0,62}(\\.[A-Za-z][A-Za-z0-9_]{0,62})?$"}
    text = {"type": "string", "maxLength": 4096}
    offset = {"type": "integer", "minimum": 0, "maximum": 2147483647}
    expr = ref("expr")
    select = {"type": "string", "maxLength": 16384} if mode == "sqlite-sql-text-v1" else ref("select")
    def tuple_schema(*items):
        return {"type": "array", "prefixItems": list(items), "items": False,
                "minItems": len(items), "maxItems": len(items)}
    defs = {
        "expr": {"anyOf": [
            obj({"column": column}),
            obj({"literal": {"anyOf": [{"type": "null"}, {"type": "number", "minimum": -1e15, "maximum": 1e15}, text]}}),
            obj({"binary": tuple_schema(enum("+", "-", "*", "/", "%", "=", "!=", "<", "<=", ">", ">=", "and", "or", "is", "is not", "like"), expr, expr)}),
            obj({"call": obj({"name": enum(*sorted(FUNCTIONS)), "args": array(expr, 8), "distinct": {"type": "boolean"}}, ["name", "args"])}),
            obj({"case": obj({"when": array(tuple_schema(expr, expr), 8, 1), "else": expr})}),
            obj({"select": select}),
        ]},
        "source": {"anyOf": [obj({"table": name, "as": name}, ["table"]),
                                obj({"select": select, "as": name}, ["select"])]},
        "select": obj({
            "columns": array(obj({"expr": expr, "as": name}, ["expr"]), 32, 1),
            "from": ref("source"),
            "joins": array({"anyOf": [
                obj({"kind": enum("inner", "left"), "source": ref("source"), "on": expr}),
                obj({"kind": enum("cross"), "source": ref("source"), "on": expr}, ["kind", "source"]),
            ]}, 8),
            "where": expr, "group_by": array(expr, 16, 1), "having": expr,
            "order_by": array(obj({"expr": expr, "direction": enum("asc", "desc")}, ["expr"]), 16, 1),
            "distinct": {"type": "boolean"}, "limit": {"type": "integer", "minimum": 0, "maximum": 1000},
        }, ["columns"]),
    }
    bindings = {"type": "object", "additionalProperties": text}
    def action(tool, fields, required=None):
        return obj({"tool": enum(tool), **fields}, None if required is None else ["tool", *required])
    actions = [
        action("read_source", {"name": text}),
        action("inspect_schema", {"database_id": text}),
        action("list_documents", {"offset": offset}, []),
        action("read_document", {"document_id": text, "offset": offset}, ["document_id"]),
        action("read_artifact", {"version": text, "row_offset": offset}, ["version"]),
        action("message", {"recipient": text, "text": text}),
        action("run_read_query", {"permitted_artifact_versions": bindings, "select_sql": select}),
        action("submit_view_definition", {"artifact_name": name, "permitted_artifact_versions": bindings, "select_sql": select}),
        action("submit_required_artifact", {"artifact_id": text}),
        action("submit_query_template", {"view_names": array(name, 16), "select_sql": select}),
        action("replay_query", {"template_id": text, "permitted_artifact_versions": bindings}),
    ]
    # Preparation is not available in this implementation-only diagnostic.
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$defs": defs, "anyOf": actions}


def decoder_schema(mode=MODE):
    """Decoder syntax projection; runtime action_schema remains authoritative.

    XGrammar 0.1.32's bounded-string production rejects JSON escapes. Use its
    normal JSON-string production for SQL only; validate_action and the compiler
    still enforce character and UTF-8 byte limits before any SQL execution.
    """
    schema = action_schema(mode)
    if mode == "sqlite-sql-text-v1":
        for branch in schema["anyOf"]:
            payload = branch["properties"].get("select_sql")
            if payload is not None:
                payload.pop("maxLength", None)
    return schema


def contract(mode=MODE):
    result = {"mode": mode, "schema_sha256": digest(action_schema(mode)), "xgrammar_version": XGRAMMAR_VERSION,
            "object_key_order": "schema_declared", "reasoning": "unconstrained_until_think_close",
            "decoder_cpu_allowance_seconds_per_call": DECODER_CPU_SECONDS,
            "decoder_charge": "ceil_process_cpu_seconds_times_tool_charge"}
    if mode == "sqlite-sql-text-v1":
        result.update(decoder_schema_sha256=digest(decoder_schema(mode)),
                      sql_string_length_enforcement="runtime-characters-and-utf8-bytes-v1")
    return result


def validate_action(text, mode=MODE):
    """Stdlib structural check of this schema subset, independent of GPU imports.

    This checks shape only. It never fixes text, resolves names or executes SQL.
    """
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BCError("Duplicate action key")
            result[key] = value
        return result
    def nonfinite(_):
        raise BCError("Nonfinite JSON")
    try:
        value = json.loads(text, object_pairs_hook=pairs,
                           parse_constant=nonfinite)
    except (ValueError, RecursionError) as exc:
        raise BCError("Incomplete or invalid constrained action JSON") from exc
    schema = action_schema(mode)
    def matches(value, rule, depth=0):
        if depth > 128:
            return False
        if rule is False:
            return False
        if "$ref" in rule:
            return matches(value, schema["$defs"][rule["$ref"].split("/")[-1]], depth+1)
        if "anyOf" in rule:
            return any(matches(value, branch, depth+1) for branch in rule["anyOf"])
        if "enum" in rule:
            return value in rule["enum"]
        kind = rule.get("type")
        if kind == "object":
            if not isinstance(value, dict) or not set(rule.get("required", ())) <= set(value):
                return False
            props = rule.get("properties", {})
            return all(matches(v, props.get(k, rule.get("additionalProperties", False)), depth+1) for k, v in value.items())
        if kind == "array":
            if not isinstance(value, list) or not rule.get("minItems", 0) <= len(value) <= rule.get("maxItems", 100000):
                return False
            prefix = rule.get("prefixItems", [])
            return all(matches(v, prefix[i] if i < len(prefix) else rule["items"], depth+1) for i,v in enumerate(value))
        if kind == "string":
            return isinstance(value, str) and len(value) <= rule.get("maxLength", 100000) and ("pattern" not in rule or re.fullmatch(rule["pattern"], value) is not None)
        if kind in ("number", "integer"):
            return (type(value) in ((int,) if kind == "integer" else (int,float))
                    and rule.get("minimum", -math.inf) <= value <= rule.get("maximum", math.inf)
                    and (type(value) is int or math.isfinite(value)))
        if kind == "boolean":
            return type(value) is bool
        return kind == "null" and value is None
    if not matches(value, schema):
        raise BCError("Action does not match public SQL action schema")
    return value
