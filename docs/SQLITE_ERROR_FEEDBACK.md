# Opt-in SQLite execution feedback — 2026-09-22

## Scope

`sqlite_error_feedback: "sqlite-errors-v1"` enables fixed execution-error categories
and generic construction hints during primary/repair tool use. The default is
`generic`, preserving existing worker observations. Initially the option is gated
to the existing four single/clean synthetic tool-compatibility probes (seed 0,
Protocol A). Native, paired, SILO and recovery campaigns are not enabled by this
change. No GPU run has been performed.

Prepared config: `configs/qwen27b-sql-error-feedback.json`, copied from the pinned
27B synthetic competence config. It changes the feedback option and condition
labels only: 8192 context, 2048 output including reasoning, 12 actions, two malformed
retries, 100000 work, one shard and the model/decoder settings remain the same.
No new tasks, task-specific instructions, expected values or native repairs are
introduced. Passing these probes again would not establish native competence;
if no SQL errors occur, the new feedback path receives no model-level test.

## Boundary and accounting

The fixed executor classifies semantic SQLite exceptions into an allowlist:
unresolved/ambiguous column, unresolved table/function, aggregate misuse,
function arity, SQL syntax, or generic execution error. Only constant category
strings leave the child; raw exception messages, names, values and paths do not.
Unknown categories are mapped to the generic category again in the parent.
Policy rejections and infrastructure/resource failures retain their old handling.
View execution errors use the same opt-in feedback; public output-shape validation
retains its existing hint. Syntax/schema failures outside SQLite execution are
not newly classified.

Feedback includes `feedback_policy: sqlite-errors-v1`, an `error_code`, and a
fixed hint. It creates no artifact, repairs no action, performs no extra query
and reads no evaluator material. It does not state whether a mathematically legal
expression satisfies the task. Terminal evaluation and integration do not request
this feedback. The existing retry counter still includes these rejected actions.
Every failed execution retains its normal bounded SQL charge, the tool call and
model generation are charged, and the next model call pays for the added feedback
in its input. There is no free correction call or increased allowance.

The config/manifest identity, result and aggregate condition, and calibration
compatibility distinguish the opt-in mode. Existing archived runs remain under
their historical source; do not resume them with modified source or relabel their
scores. The changed executor source also means that exact-source offline native
replays must continue using their matching historical audit snapshot.

## Validation and next step

Local tests exercise real restricted synthetic execution for missing aliases and
function arity through the worker loop, scripted correction and retry exhaustion,
legacy feedback parity, full tool/model/execution charging, allowlist privacy,
terminal-path isolation, all four positive controls and aggregation's refusal to
mix feedback conditions. These are CPU engineering controls, not LLM results.

The user can review and push this bounded change. A future browser-terminal run
must use a new manifest and output directory, the existing qualified 27B lock and
shared Slurm registry/preflight guards. No automatic submission or native rerun
is part of this implementation. Preserve the previous 4/4 synthetic result and
0/2 native result as separate historical observations.
