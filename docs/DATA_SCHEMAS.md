# Restricted data record versions

These schemas extend the existing records; v1 numeric/legacy results remain
readable. New artifacts and private input manifests must stay outside Git.

| Record/version | Required interpretation |
| --- | --- |
| `bc-sqlite-stage-v1` | Exact audited release, public metadata hash, registered local database/document paths and hashes; optional author material and review pins. Registration is not scored readiness. |
| `bc-sqlite-reviewed-evaluation-v1` | Reviewer and per-task exact public/material hashes, reviewed requirement support, typed reference artifact and nonempty read comparisons, schema/tables, limits, and empty v1 setup/cleanup. No Python test execution. |
| `bc-data-v2` | One environment, task records, validation reports/rejections or deterministic SILO generator metadata. A validated task is bound to its report and complete task content. |
| `bc-manifest-v2` | Existing full planned grid and hashes plus a single `data_regime`. SQL tasks bind executor/runtime capabilities. Environments, releases, scorer/tool policies and access regimes cannot mix. |
| `bc-result-v2` | Recorded in result provenance with the data regime. Existing budget/provenance/result structure remains; final diagnostics do not feed policy execution. |
| `bc-summary-v2` | All planned statuses and source-group counts; native diagnostics are not pooled as joint-completion accuracy. No episode-independent confidence intervals. |
| `bc-native-readiness-v1` | Sanitized file/material/review support status. Not a validation approval or model score. |
| `bc-observations-v1` | Separate tri-state public coverage/shape/integration, missing obligations, evaluator, final semantics and execution status. Historical unknowns are null. |
| `bc-ledger-observations-v2` | Additive charge IDs; same `token_tool_surrogate_v1` accounting. Entries, not sums of entries plus stage summaries, define spent work. |
| `bc-allocation-trace-v1` | Optional private trace of the unchanged finite candidate/scenario search. Predicted costs and unknown cost components remain explicit. |
| `bc-silo-battery-v1` | Frozen selection/count plan for eight full, 32 local, up to 24 actual-boundary executions and two separate confirmation sources. |
| `bc-actual-predecessor-v1` | Actual baseline version/content, submission sequence, parent closure and baseline manifest/episode/checkpoint/condition pins. Hash validation rejects replacing content under the old version. No gold substitution. |
| `bc-silo-attribution-v1` | Offline evaluator-only global/incoming/local error attribution. Never a public monitor observation. |
| `bc-operation-cost-validation-v1` | Labelled mock/real operation measurements and disjoint holdout errors, not automatically deployable allocator calibration. |

SILO local/boundary tasks remain `bc-data-v2` with distinct adaptation/scorer and
`diagnostic_mode`. Their exact derivation is checked against original generated
inputs; original source groups remain shared across modes. Config fields
`silo_interface`, `development_profile`, `operation_measurement` and
`allocation_diagnostics` are explicit opt-ins. Changed conditions get new
manifests; mode/interface/measurement differences cannot pool in aggregation.

## Result statuses

`ResultStatus` in `schemas.py` declares the supported status vocabulary.

| Status | Success field and aggregation |
| --- | --- |
| `completed` | Boolean full joint/segment completion; semantic failures count. Labelled operation-only measurements use null success and no accuracy denominator. |
| `budget_exhausted` | False; all prior work retained and counted. |
| `scoring_unavailable` | Null; missing reviewed evaluation is excluded from semantic accuracy. |
| `blocked_prerequisite` | Null; staged source missing/changed/active. |
| `blocked_capability` | Null; required fixed-executor capability/runtime unavailable or changed. |
| `execution_limit` | Null; declared full-output, VM-step, CPU, memory or deadline capacity reached. Never a partial success. |
| `interrupted` | Null; eligible for conservative resume with prior/uncertain work charged. |
| `infrastructure_failed` | Null; eligible for retry, kept separate from semantic failures. |
| `blocked_sandbox`, `ineligible` | Retained legacy statuses. |
| `missing` | Aggregation-only: no result exists for a planned episode. |

Tool rejections are charged events and counted in `metrics.tool_rejections`.
Private rejection events include assignment and `error_code`: `invalid_json`,
`invalid_action_fields`, `unknown_source`, or `restricted_action_rejected`.
JSON parser locations describe only the worker's generated text. Public field
guidance does not contain query values, references or private exception text.
Invalid JSON never dispatches a tool; its model generation and re-prefill remain
charged. Parsed-but-rejected tool actions also incur the normal tool charge.
The worker may correct an action; exhausting its action/retry limit can leave
an incomplete `completed` episode. A known execution limit ends with its own
status and does not silently restart under increased limits.

SQL implementation content stores a SELECT tree, exact name-to-version
`bindings`, and kind (`query` or `view`). Query results store full bounded rows
and an execution-binding hash; tool observations are labelled previews. Optional
query templates are separate provenance versions and are reusable only while
valid. SILO implementation content stores `answer`, the entire original segment.
The four original obligations survive reassignment and compromised identities.

Private checkpoints retain existing contexts, artifacts, public events, budgets,
selected candidates and persistent compromise. Public v2 exports omit those
checkpoints, evaluator records, private paths, raw failures and tracebacks; they
include aggregate coverage and bounded cost summaries. Full schema behavior is
validated by the standard-library tests, not by an external schema package.
