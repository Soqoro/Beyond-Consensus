"""Legacy instructions and qualification for the shared restricted SQL compiler."""
from pathlib import Path
from restricted_artifacts.sql_text import *
from restricted_artifacts.sql_text import _lower

def instructions(original):
    start = original.index('select_sql is a JSON tree')
    end = original.index('permitted_artifact_versions is an object')
    return original[:start] + '''select_sql is a SQL SELECT string, encoded as a JSON string. Keep permitted_artifact_versions
and select_sql as sibling top-level action fields. For views supply the separate artifact_name;
do not write CREATE VIEW. Close the quoted SELECT string and the outer JSON object.
Syntax example ONLY: suppose a different task had a table demo_rows(item_key,amount) and asked for
item_key and amount plus 7, ordered by item_key. Its query action would be:
{"tool":"run_read_query","permitted_artifact_versions":{},"select_sql":"SELECT item_key, amount + 7 AS adjusted FROM demo_rows ORDER BY item_key ASC"}
This example is not your assignment. Obtain actual table/column names and requirements through the source/schema tools.
Supported: SELECT columns, numeric/string/NULL literals, + - * / % = != < <= > >= AND OR IS IS NOT LIKE,
searched CASE WHEN ... THEN ... ELSE ... END, scalar subqueries, FROM tables or subqueries,
INNER/LEFT/CROSS JOIN with ON (optional for CROSS), WHERE, GROUP BY, HAVING, ORDER BY ASC/DESC,
DISTINCT and integer LIMIT 0..1000. Computed output expressions require explicit aliases.
Functions: abs coalesce ifnull nullif round length lower upper substr trim replace min max sum avg count total json_extract json_array_length json_type.
Only identifiers accepted by the original tool policy; quoting does not expand the name alphabet.
One statement only. No wildcards, CTEs, windows, set operations, casts, DML/DDL, PRAGMA,
external files or extensions. Unsupported syntax is rejected; queries are never auto-corrected.
''' + original[end:]


def require_qualification(lock):
    from beyond_consensus.util import BCError, file_hash
    report = lock.get('sql_frontend_qualification', {})
    root = Path(__file__).resolve().parents[3]
    names = ('src/beyond_consensus/runtime/sql_text.py', 'src/beyond_consensus/runtime/sqlite_executor.py', 'tests/test_sql_text.py', 'src/restricted_artifacts/sql_text.py', 'src/restricted_artifacts/sqlite_executor.py')
    if (report.get('status') != 'passed' or report.get('skipped') != 0 or
            report.get('contract') != contract() or report.get('inputs') != 'synthetic_only' or
            report.get('model_executed') is not False or report.get('sql_executed') is not True or
            report.get('implementation_hashes') != {n:file_hash(root/n) for n in names}):
        raise BCError('SQL text requires current separate CPU compiler qualification in its new lock')
    return report
