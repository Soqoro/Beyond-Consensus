# Public SQLite interface audit — 2026-09-22

## Evidence and accounting

Historical native experiment
`13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981`
remains **0/2**, with **171715** charged work. The user subsequently supplied
an offline replay report: both failed solar_2 queries were `unresolved_column`;
the solar_M_3 selected bundle and candidate/reference checks executed but both
exact and native comparisons failed. Five bounded child invocations charged
**150 separate replay work**. No historical scores changed or worker feedback
was issued. These are user-reported cluster observations, not local execution.

The subsequent public-only candidate export shows:

- solar_2 generations 15/16 repeat the same tree with qualified column names but
  no FROM or joins to define their aliases. It also gives SUM two arguments and
  omits required metrics, classification and sorting. The column names exist in
  the public schema. Missing bindings explain the unresolved-column failure;
  fixing that alone would not establish task correctness.
- solar_M_3 multiplies measured power by rated power in PPR, whereas the public
  definition divides. That error propagates into TAPR. TPCI matches its public
  formula. The temperature correction in TAPR is algebraically consistent with
  TPCI/rated power for nonzero rated power. The environment-to-panel primary-key
  join is not a declared relationship; both tables have separate plant foreign
  keys. Its actual contribution to result differences was not measured.

This interpretation uses public requirements, schema, documents and generated
candidates. It neither constructs corrected native submissions nor reads hidden
reference bodies. It cannot isolate model ability from representation difficulty.

## Interface and feedback findings

`runtime/data_domain.py:SQL_INSTRUCTIONS` already demonstrates FROM and a full
query action, permits qualified column names, lists join syntax and arithmetic
operators, and describes explicit final artifact submission. It does not give a
worked aliased join, explain function arities, or explain division operand order.
An example's presence does not prove a model can reliably use it.

The compiler deliberately separates syntax from SQLite name/type resolution:
FROM is optional (constant SELECTs are valid), column references are resolved by
SQLite, and function arguments are bounded in count but not checked against each
function's arity. A JSON-schema-complete action can therefore still fail execution.
Blanket rejection of every SELECT without FROM would incorrectly reject constants.

The executor exports sanitized `semantic_error` / `query_execution`, without raw
SQLite errors. DataDomain raises a BCError; WorkerLoop reduces it to the generic
`Action rejected by the restricted tool contract`. Events retain the execution
status. The more specific view-validation hint applies to a separate validation
path. Neither unresolved aliases nor function arity receives a targeted worker
hint through this generic query failure path. Rejections consume the same retry
counter as malformed actions, and their work remains charged.

The audit identifies a feedback limitation, not proof that richer feedback would
have corrected either task. Successful execution cannot diagnose an incorrect
but legal multiplication expression without consulting the public requirement or
terminal scorer. The scorer must not become worker feedback.

## Local controls and decision

`tests/test_sqlite_interface_audit.py` adds trusted synthetic controls for:

1. Unbound qualified names fail; explicitly bound names and constant SELECTs work.
2. Two-argument SUM compiles but fails execution; a one-argument control works.
3. Division retains its meaning; multiplication gives different results despite
   identical output shape and successful execution.

These tests use temporary synthetic data and the existing restricted CPU executor.
They are engineering checks, not model results or historical episode work.
No runtime, prompt, grammar, scorer, budget or configuration changed in this audit.

The next implementation candidate is generic, sanitized execution-category
feedback, with tests for privacy, retry limits and charging. It would require a
fresh labelled condition and manifest; any compiler, schema or prompt changes
must be disclosed separately. Test on synthetic inputs first. Do not automatically
repair trees, prescribe native answers, reinterpret old scores, increase limits,
or launch another GPU campaign. Native clean competence and the separate research
comparison gate remain unmet.
