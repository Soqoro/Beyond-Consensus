# Beyond Consensus / RepoRecourse — Consolidated Audit

**Evidence cutoff: 16 October 2026**  
**Purpose: review completed work, assess results, and choose the next experiments.**

## 1. Executive summary

We have implemented a restricted artifact execution and recovery system, extended
it to generated planning and assignment-scoped execution, and exercised it with
CPU controls, GPU qualification probes, synthetic demonstrations and development
task cohorts. Workers publish validated SQL, schemas and mappings; they do not
execute arbitrary repository code.

The strongest positive task evidence is successful clean execution and persistent
worker-loss recovery on the synthetic-stock demonstrations, plus a successful
Jaffle smoke. The richer development cohorts show much lower complete success:
**1/16, 3/16 and 2/16 scheduled branches** across successive interface versions.
Those versions are not controlled replications of one intervention.

The latest organization-characterization run used six authored plans across two
tasks, with no model planner: **clean 3/6; loss 2/6**. Only **one of the three
clean-success configurations also succeeded under loss**. All six losses
triggered; all twelve conditions were reported conformant. Valid execution and
conformance therefore remain distinct from task correctness.

The latest three-call synthetic diagnostic produced:

- **Order granularity: semantic pass.**
- **Unpaid boundary: compiler rejection; semantic correctness unmeasured.**
- **Mapping output names: public-monitor pass but semantic failure.**

The compiler rejection is explained by the saved `case_else_required` diagnostic:
the generated CASE expressions omitted the explicit ELSE required by the public
contract. The mapping used `label`/`bytes` instead of `labels`/`size_bytes`.

The decoder now has an opt-in duplicate-key guard. CPU qualification and later
normal-mode GPU probes passed, but the original AcceleratorError remains
unexplained. No controlled task comparison establishes that the guard improves
task success.

**Overall assessment:** engineering feasibility is demonstrated in bounded cases;
reliable semantic task completion and general recovery effectiveness are not.
There is no established planner superiority, calibrated B0 result, or confirmatory
population estimate. No new experiment is authorized or launched by this report.

## 2. Evidence and audit boundaries

This report consolidates repository records and user-supplied cluster outputs.
It is not an independent inspection of the remote cluster. No model, task SQL,
or evaluator was run to write it. Historical results were not repaired, promoted,
rescored or replaced.

Evidence classes must remain separate:

| Evidence | Supports | Does not establish |
|---|---|---|
| Unit and CPU integration tests | Tested implementation behavior | Model competence |
| Authored reference executions | Feasibility of particular programs/organizations | Generated-planner quality |
| Grammar/tokenizer checks | Acceptance/rejection of tested representations | Semantic task correctness |
| Synthetic GPU preflights | Observed model/runtime behavior | Universal memory fit or broad reliability |
| Model task branches | Recorded outcomes under their specific contracts | Independent population estimates |
| Offline trace inspection | Explanations supported by saved artifacts | Unobserved counterfactual outcomes or causal attribution |

The newest semantic paste starts inside the first case's evaluator ledger and
is not a complete JSON archive. Its trace fields support the reported findings;
the full cluster report, manifest and snapshot should remain the archival source.
Its SHA256 is recorded in [the detailed semantic audit](SEMANTIC_DIAGNOSTIC_RESULTS.md).
Normal qualification's internal-binding audit checks file consistency, not
independent authenticity of the scheduler, hardware or environment.

Older status entries saying an adapter or experiment was pending describe their
original evidence cutoff. Later completed results below supersede those pending
states without rewriting their history.

## 3. System implemented

### Execution and isolation

- Restricted SQL text lowers through pinned SQLGlot into the existing approved IR,
  then runs through the fixed trusted SQLite child executor.
- Unsupported SQL is rejected, not silently rewritten. Worker SQL and downloaded
  repository code are not executed directly on the host.
- Schema and mapping artifacts have validated formats, exact version bindings
  and explicit terminal obligations.
- Public monitoring and hidden semantic evaluation remain separate. Self-declared
  schema validity is not a guarantee of public-task correctness.

### Planning, scopes and recovery

- RepoRecourse v0.2 supports 2–8 logical identities, including seven, sharing one
  frozen model on one allocated GPU. This is not seven independent model copies.
- Plans are frozen before target selection. Authored organizations, generated
  plans and fixed-plan recovery references remain distinct conditions.
- AssignmentScopes mediate observations, tools, artifact registries, messages
  and restored histories. Declared imports are permissions, not proof of reads.
- New units receive fresh contexts; identity loss persists. Common public JIT
  records admitted scope overlays and exact artifact rebinding.

### Accounting and operation

- Input/output tokens, model-side CPU, compiler/decoder/tool work, failures and
  uncertain interrupted usage are recorded. Private terminal evaluation has a
  separate ledger where required by the protocol.
- Planning is charged logically per branch even when physically reused. Logical
  branch totals cannot be summed and labelled physical GPU consumption.
- Frozen source, model/grammar locks, shared registry and scheduler inspection
  guard submissions. Qualification uses one GPU; total physical concurrency is
  bounded. No batch self-submission or silent retry is permitted.
- Read-only exports preserve failed, invalid, incomplete and unrun conditions.

These controls are implemented boundaries, not evidence of a general OS sandbox,
arbitrary-code agent, completed task-rights review or trained recovery controller.

## 4. Early development results

These stages have different tasks, interfaces and budgets. Do not pool them into
one success rate or interpret them as a continuous controlled improvement curve.

| Stage | Recorded result | Interpretation |
|---|---|---|
| Earlier 4B synthetic probes | Initially 0/4; reasoning and constrained conditions 1/4 | Tool formatting alone did not establish competence |
| Earlier 27B synthetic probes | 4/4 | Small compatibility probes passed |
| Matched Solar JSON-tree arm | 0/2 | Native tasks failed under that interface |
| Matched Solar SQL-text arm | 1/2 | Local success on two repeatedly inspected tasks |
| Later Solar SQL-text follow-up | 1/2 | Failure persisted despite further interface work |
| Synthetic aggregation | 1/2 | Independent-detail join multiplication caused inflated aggregates |
| Initial Jaffle smoke | 0/1 | Published artifacts failed execution; recovery did not complete |
| Corrected Jaffle smoke | 1/1 | Both obligations passed; 29,745 tokens, about 404.79 CPU seconds |
| v0.2 scripted reference matrix | 188/188 branches across 56 conditions | Reference/harness evidence across pools 2–8 and four organizations |

Solar audits separately identified unresolved columns, missing obligations and
incorrect executable candidates. An unsubmitted candidate replay matched its
recorded rows but failed reference comparisons. It remained invalid/unsubmitted;
offline replay did not change the historical score.

## 5. Synthetic-stock planning and loss recovery

| Run / branch | Outcome | Logical tokens | CPU debit seconds |
|---|---|---:|---:|
| Open clean `151721…` | Passed, conformant | 7,476 | 208.01 |
| Conditional F(w0), `f6066e…` | Passed, conformant | 9,949 | 232.30 |
| Conditional F(w1), `f6066e…` | Passed, conformant | 10,802 | 245.37 |
| Prospective stock clean `e10d7f…` | Passed | 9,120 | 169.30 |
| Prospective stock F(w0) | Passed | 11,849 | 196.63 |
| Prospective stock F(w1) | Passed | 12,723 | 211.66 |

Both conditional losses triggered and both obligations passed. Trace inspection
distinguished reconstruction with exact-version consumption after w0 loss from
source-based repair after w1 loss. A read event alone is not executable reuse.

Conditional fault branches were selected after clean success. The later
prospective stock protocol avoids treating that selection as an unselected
robustness estimate, but still covers one synthetic request. Its 3,005 planning
tokens are already included in each branch's logical total.

Earlier adaptive stock success also showed that actual artifact dependencies
could differ from an authored plan; this motivated explicit plan-scoped execution.
That historical success remains valid under its original adaptive contract.

## 6. Richer four-task cohorts

Tasks: Jaffle payment release, Energy single-indicator release, GitHub topics
client package, and GitHub multioperation integration. These are **four requests
from three source groups**, not four independent repositories.

Runs used the explicitly labelled `rich_development_unreviewed` lane after the
user deferred reviews. Independent task and rights reviews remain deferred;
execution approval is not a claim those reviews occurred.

| Cohort | Requirement clean | Requirement F | Prompted-open clean | Prompted-open F | Scheduled successes |
|---|---:|---:|---:|---:|---:|
| Initial `b9f84b…` | 1/4 | 0/4 | 0/4 | 0/4 | 1/16 |
| Interface reliability `5b2323…` | 0/4 | 2/4 | 1/4 | 0/4 | 3/16 |
| Assignment interface `dd7f95…` | 1/4 | 1/4 | 0/4 | 0/4 | 2/16 |

These denominators retain invalid planning and unexecuted scheduled branches.
They are not executed-only success rates. The requirement-level condition uses
a reference decomposition; it is not an independently successful model planner.

### Findings and changes

1. Initial planning repeatedly placed helper/artifact names in terminal outputs.
   Public field explanations, helper/terminal examples and feedback were clarified.
2. Of 69 initial schema/mapping contract failures, 68 supplied JSON strings where
   objects were required. Format-specific guidance and diagnostics were improved.
3. Energy repeatedly used unsupported IN/NOT IN/BETWEEN. The public SQL subset
   and bounded rejection feedback were made explicit.
4. Assignment-specific publication guidance reduced observed denied publications
   from 84 to 7 between the latter cohorts, but success fell from 3/16 to 2/16.

The assignment cohort reported all sixteen branches conformant and all eight
fault interventions triggered. Two Jaffle/open branches exhausted token admission.
Its logical total was 816,353 tokens and about 9,386.02 charged CPU seconds.
These are not physical GPU wall-time totals.

Semantic failures included order-count fanout, wrong exclusion labels, extra
mapping fields and `name` instead of `names`. Thus clearer interfaces and valid
artifacts did not establish semantic competence. Repeatedly inspected development
cohorts do not support causal estimates of individual interface changes.

## 7. Qualification and decoder investigation

### Planner capacity

A representative 24-unit plan needed 2,125 action-plus-stop tokens, exceeding
the initial 2,048 cap before reasoning. After a role-admission correction,
4,096 still truncated the model response. At 6,144, the observed case passed:
4,377 output tokens including 2,252 reasoning tokens. Worker output stayed 2,048;
context stayed 16,384. Passing observed probes is not worst-case-fit evidence.

### Duplicate-key boundary

Response inspection found malformed JSON at normal EOS as well as length limits.
A reconstructed-input probe produced a `duplicate_object_key` rejection, but was
not exact historical replay. CPU matcher/mask checks then showed that the native
grammar accepted nested and escaped-equivalent duplicate keys that the strict
parser correctly rejected. Envelope duplicates and incomplete JSON were blocked.

Implemented opt-in `reporecourse-json-unique-v1-pool-7`: a byte-prefix key guard
intersected with the native grammar before token selection. It preserves strict
parsing and does not delete keys, apply last-key-wins, normalize runtime keys,
repair outputs, or force reasoning termination.

A synthetic positive test initially failed because tokenizer NFC normalization
collapsed a decomposed literal key. Encoding the combining mark as a JSON escape
made the control stable without changing runtime key semantics. Cluster CPU
qualification subsequently reported 151 controls and 44/44 native cases passed.

### GPU sequence

| Experiment | Observation | Limit |
|---|---|---|
| Initial guarded preflight `a3aadd…` | Nested case passed; escaped-key call raised AcceleratorError; long-context unrun | 692 known tokens plus 2,143 uncertain reservation; qualification failed |
| Matched debug diagnostic `7755a2…` | Native and guarded arms each passed two cases; 4,692 tokens total, zero uncertain | Fresh process per arm, launch blocking enabled; no task execution |
| Normal guarded qualification `5dd357…` | 3/3 passed; 17,521 tokens, zero uncertain; 318.633 seconds | Observed synthetic qualification only |

The debug run used two sequential model instances and reported matched arm
inputs and hardware. Both arms completed without an accelerator exception.
Normal qualification then passed nested, escaped and 14,335-input-token mapping
cases on A100-SXM4-80GB. All reached EOS with strict-parser-valid output.

**The original AcceleratorError remains unexplained.** Empty stderr and an
exception-class-only record do not establish OOM, a kernel defect or a guard bug.
Later success does not erase that failed attempt or its uncertain usage.

The normal evidence audit reported compatible code/model bindings and verified
snapshot inventory. It does not independently establish environment authenticity
or reparse responses saved only as hashes. There is no measured causal task gain
from the guard: the later task design also differs from earlier cohorts.

## 8. Latest authored-organization experiment

Experiment:
`a6b820857f765fb3a4841b696e120f00e662c523be31744e5ed3cc6452d97ba4`.
Jobs 1097647_0 through 1097647_5 reported COMPLETED/0:0.

Six CPU-qualified authored organizations were selected for two tasks, with clean
and one seeded meaningful-owner F branch each. There were **zero generated
planner calls**. Offline catalog expense remains separate; actual receipt and
validation work is logically charged in branches.

| Task | Organization | Clean | F |
|---|---|---|---|
| Jaffle | Independent | Failed | Failed |
| Jaffle | Grouped | Failed | Resource exhausted |
| Jaffle | Shared | Passed | Failed |
| GitHub multioperation | Independent | Passed | Failed |
| GitHub multioperation | Grouped | Passed | Passed |
| GitHub multioperation | Shared | Failed | Passed |

All twelve conditions were represented/conformant; all six losses triggered;
reported uncertain tokens/CPU were zero. Eleven branch executions completed and
one exhausted resources. Scheduler success does not mean task success.

### What the traces show

- Five failed Jaffle branches counted orders after joining raw payments, causing
  fanout. Shared clean used COUNT(DISTINCT order.id) and passed.
- Independent F also counted the outer-join null row as an unpaid order.
- Grouped F lacked reconciliation after truncations/rejection and could not
  reserve another call: 11,958 requested tokens versus 11,941 remaining. Recorded
  task usage was 88,059 tokens and 1,150.545 CPU seconds.
- GitHub independent F used errors/errors_2 rather than topics/language_bytes,
  and name rather than names. Shared clean repair used errors/errors_bytes.
  Self-declared schemas repeated incorrect keys.

Clean success was 3/6, F success 2/6. Among the three clean successes, only one
also passed F. GitHub shared's failed-clean/passed-F pair does not prove loss
helps. Organizations within two selected tasks are correlated; these are not
independent trials or evidence of organization superiority.

## 9. Synthetic semantic follow-up

### CPU feasibility and negative controls

Job 1098418, source `82cd822fa80ff427cbb8d4101af98819d30ecd19`, reported
seven production controls passed using Python 3.12.10, SQLGlot 27.28.1,
jsonschema 4.25.1 and referencing 0.36.2. Three positives passed independent
semantic checks; four deliberately wrong artifacts passed public monitoring but
failed those checks. This demonstrates the intended distinction, not seven
successful model tasks.

Fresh runner preparation, job 1098499, source
`a3a457760b4d77f963429835b78133562a362a25`, passed 24 tests without skips and
all prompt-footprint checks. The exact three-call proposal was subsequently
approved by the user.

### Model results

Experiment:
`254b92bc02c5733cfeff6e0b4d46fca608b0aeba01228e9390a192f22b2cbdf5`.
Runtime records job 1098514, array task 0. One fresh scoped assignment and one
publication call per invented case; no planner, repair or retry.

| Case | Input tokens | Output tokens | Public result | Semantic result |
|---|---:|---:|---|---|
| order_grain | 2428 | 772 | Passed | Correct |
| unpaid_boundary | 2433 | 958 | Not reached: compiler rejected | Unmeasured |
| mapping_keys | 2221 | 625 | Passed | Incorrect |

Total task usage: **9,437 tokens**, about **227.400 CPU debit seconds**, zero
recorded uncertain tokens. Wall time: **313.112 seconds**. All three responses
reached EOS with complete constrained output; all cases were represented.
Terminal evaluation has separate ledgers and is not worker feedback.

The order query counted distinct orders and every payment, with correct totals.
This shows capability on this particular instance, not immunity to fanout.

The unpaid query omitted ELSE in both searched CASE expressions. Saved feedback
explicitly reports `case_else_required`, operator Case, path sql.ast. Source and
existing regression coverage match this restriction. No compiler fix or silent
query repair is justified. The rejected query has no measured semantic result.

The mapping produced label/bytes rather than labels/size_bytes, and declared the
same wrong names in its schema. This is a concrete example of public-valid but
task-incorrect output even with duplicate-free constrained decoding.

### Prompt audit

Static prompt construction includes both the explicit-ELSE rule and the exact
mapping-key request. There is no missing task requirement in the inspected code.
However, generic schema/mapping syntax examples use label, overlapping one wrong
generated key. This supports an example-copying hypothesis, not a conclusion.
The second wrong key bytes is not explained by that overlap. Saved-token/snapshot
reconstruction has not been independently performed in this audit.

## 10. Operational fixes and evidence preservation

Repeated preparation failures were distinct from model failures: Slurm copied
scripts into spool directories; source directories or manifests were missing;
terminal variables were unset; untracked exports prevented source freezing;
cross-filesystem rename failed; exclusive output creation stopped duplicate
writes; scheduler array/accounting visibility blocked submissions; large offline
records exceeded the worker-oriented JSON loader limit.

Fixes introduced frozen source working directories, explicit environment/path
setup, separate bounded operator-record loading, precise role admission and
record compatibility checks. Slurm test-environment handling was corrected while
retaining the batch-self-submission guard. Historical failed preparations and
uncertain submissions must remain visible, rather than being edited into passes.

GPU partition changes required hardware qualification/compatibility evidence.
Old occupancy tables do not establish current availability. GPU accounting
guards have not been treated as authorization to cancel unrelated jobs or bypass
the shared registry.

## 11. Validation and remaining limitations

Latest local suite: **592 tests run, 557 passed, 35 optional-dependency skips**;
ten shell files validated. These counts are implementation checks, not model
performance. The no-skip cluster semantic preparation passed 24 scoped tests.
Local missing optional libraries prevent claiming a fresh local production SQL
replay; the compiler finding rests on saved exact feedback and source inspection.

Still unresolved:

1. General task reliability and recovery effectiveness across independent groups.
2. Generated-planner superiority under a controlled, equal-budget comparison.
3. Independent task/evaluator and rights-review completion for deferred tasks.
4. Compatible B0 calibration; 100k/1200 branch caps remain engineering limits.
5. Worst-case memory/output feasibility under current contracts.
6. Root cause of the original AcceleratorError.
7. Causal attribution of wrong mapping keys or task outcomes to a decoder mode.
8. Full archival verification of the latest fragment-based semantic result.

Do not pool probe, control, branch, obligation and source-group counts. Do not
exclude invalid planning or resource-exhausted branches to inflate success. Do
not infer no usage from a missing generation record. Repeatedly inspected tasks
are development material, not untouched confirmation data.

## 12. Decisions for the next experiments

### Recommended immediate option: narrow mapping-example diagnostic

Prepare two new mapping-only calls: current prompt as baseline versus the same
prompt with generic example key label consistently renamed neutral_example_field.
Keep actual task keys and values, decoder, model, budgets, evaluator and monitor
unchanged. Record token lengths and hashes; do not assume identical tokenization.
Use a fresh baseline, no repair and no historical rescore.

This is currently **a design only**: no adapter, manifest or submission exists.
It would test response sensitivity to that edit on one selected case, not prove
the cause of the historical error or establish a population effect.

### Separate choices

| Question | Appropriate next design | What to avoid |
|---|---|---|
| SQL contract adherence | Prospective public-syntax diagnostic with fixed scope | Auto-correcting the rejected historical query |
| Mapping-key adherence | Isolated example/wording comparison | Changing prompts, decoder and scorer together |
| Recovery contribution | Fixed-plan matched recovery/no-recovery or restart lane | Calling clean/F alone a recovery-benefit estimate |
| Planner quality | Prespecified planner comparison with common workers/JIT and charged planning | Treating authored reference plans as generated planners |
| Generalization | Additional independently reviewed source groups and held-out split | Reusing inspected tasks as confirmation |

The immediate decision is which question matters most. Another broad cohort run
without isolating a question would add cost while leaving attribution difficult.

## 13. Source index

- [Implementation status](STATUS.md) and [research protocol](RESEARCH_PROTOCOL.md).
- [14 October audit, including initial GPU-failure addendum](AUDIT_REPORT_2026-10-14.md).
- [12 October richer-cohort trace audit](RICH_COHORT_TRACE_AUDIT_2026-10-12.md).
- [Decoder and organization workstreams](DECODER_AND_ORGANIZATION_WORKSTREAMS.md).
- [Sampled organization runbook](SAMPLED_ORGANIZATION_RUNBOOK.md).
- [Sampled artifact findings and synthetic controls](SAMPLED_SEMANTIC_FOLLOWUP.md).
- [Three-call run contract and preparation](SEMANTIC_DIAGNOSTIC_RUNBOOK.md).
- [Latest semantic trace and prompt audit](SEMANTIC_DIAGNOSTIC_RESULTS.md).

This report summarizes recorded evidence; those linked records retain detailed
contracts, versioned limitations and the history of each stopping point.
