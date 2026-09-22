# Beyond Consensus — progress and results for review

**Date:** 2026-09-22  
**Current decision:** pause further submissions for the user's review.  
**Coverage:** project history plus results received since the September 20 audit.

## 1. Executive summary

The research question is whether recovery-aware delegation improves complete-task
success after contributor compromise **at the same total work allowance**.
**We have not demonstrated that advantage.**

We have built and exercised a substantial execution, accounting and diagnostic
system. Corrected engineering fixtures passed, and the 27B model passed all four
simple SQL tool probes. However, the native solar tasks still fail, the tested
SILO controls have no complete-task successes, and the meaningful decomposition /
fair policy-comparison problem remains unresolved.

The most recent completed feedback-enabled run passed **4/4 at 21327 work**, with
**zero rejected actions**. It reproduces the earlier 27B synthetic result and
therefore does not demonstrate a benefit from richer error feedback.

The latest implemented experiment deliberately supplies two invalid synthetic
query drafts and compares generic with categorized feedback. Its code passed
local tests and the user reports pushing it. **No cluster submission or result
for this paired correction diagnostic has been reported.** Commands were supplied,
but the user requested this review before continuing. Prepared code is not a result.

### Current evidence at a glance

| Area | Latest evidence | What it supports |
| --- | --- | --- |
| Numeric workflow engineering | Two reported 32/32 campaigns | Bounded workflow plumbing, not native performance |
| Arithmetic SQLite policy fixtures | Corrected pilot 32/32 | Fixture execution/recovery paths; no recovery advantage |
| SILO clean controls | Original 0/8; actual-carry interface 0/8 | Tested setup lacks complete-task competence |
| 4B synthetic SQL probes | Best reported condition 1/4 | Syntax constraints alone did not solve the tasks |
| 27B synthetic SQL probes | Original 4/4; feedback-enabled 4/4 | Basic tool competence on four inspected synthetic tasks |
| 27B native solar, latest condition | 0/2, 171715 work | Real construction and semantic failures remain |
| Offline native failure replay | Two unresolved-column failures; incorrect view comparison | Diagnostic attribution, not a rescore |
| Paired correction diagnostic | Implemented and locally tested; GPU results pending | No empirical feedback-effect result yet |

## 2. Evidence and interpretation rules

Cluster results below come from the user's pasted outputs and uploaded reports.
The assistant has not accessed the cluster directly or independently rehashed all
remote inputs. Local code tests are separate software evidence; scripted workers
are not model experiments. This report adds no model/SQL execution or new scores.

- **Completed** means execution finished; **success** means the terminal task
  checks passed. They are not interchangeable.
- Work is the configured token/tool surrogate, not GPU-hours, FLOPs, money or
  end-to-end latency. Reasoning and failed attempts remain charged.
- Protocol A uses equal total allowances. Protocol B is a separate equal-remainder
  diagnostic; results are not pooled across them.
- Repeated conditions on the same tasks are not new independent tasks. The four
  tool probes share one synthetic group; solar uses one database group.
- These are development observations after repeated inspection and modification,
  not held-out confirmation. Before/after comparisons often changed several things.
- Restricted SQLite tools are not an OS sandbox. Reference validation is not
  worker competence. Public shape/integration is not semantic correctness.
- `missing_artifact_observations` is not the missing-required-artifact count.
  Legacy `integration_failures` means unsuccessful completed episodes; consult
  the separate public-integration and semantic-correctness observations.

The [September 20 report](PROGRESS_REPORT_2026-09-20.md) remains a historical
checkpoint. Its statements that 27B was unselected/unexecuted are superseded here.

## 3. What has been built and why the task environment changed

### Execution and provenance

The repository implements frozen manifests and source snapshots, pinned model
staging, guarded Slurm submission, per-episode results/checkpoints, resume rules,
public monitoring, terminal evaluation, and explicit model/tool/planning charges.
Four persistent worker identities share one frozen model per allocated GPU.
Single-worker competence controls do not test four-worker cooperation.
The shared submission registry enforces one active campaign and at most four GPUs;
the recent competence/correction configurations use one GPU shard.

### CooperBench blocker and data-path migration

Basic private Apptainer namespace, network and file-visibility probes passed.
The full repository-execution boundary did not qualify: delegation was absent,
and the inspected Slurm allocation did not show finite inherited memory/swap/PID
limits despite its memory request. These observations describe the tested setup,
not every node or all possible scheduler configurations.

The approved direction changed to restricted SQLite data tools and a labelled
SILO recoverable-contributor adaptation on the existing Slurm cluster. CooperBench
remains optional legacy and has not produced a qualified model result. PBS,
Colab, personal-PC and rented-GPU alternatives were discussed, not deployed.
The active data path does not require those environments or cgroup delegation.

### SQLite, SILO and model-interface work

Implemented restricted SELECT/view trees, exact artifact version bindings, copied
SQLite execution, public schema/document access, complete-output checks, and
separate fixture/native/pair/SILO provenance. Private author solutions/test material
remain evaluator-only; arbitrary upstream test Python is not executed.

Successive diagnostics addressed invalid JSON examples, incorrect source IDs,
repeated reads, document discovery, tokenizer turn-ending, view resolution,
required public aliases, reasoning budgets and schema-constrained decoding.
Later changes added 16K context qualification, explicit action-limit conditions,
private diagnostic context archives, offline failure replay and sanitized SQL
error categories. None of these guarantees the intended SQL calculation is right.

## 4. Earlier results: fixtures, policy costs and SILO

### Policy fixtures

After initial smoke/interface failures, numeric workflow campaigns reported 32/32
for clean/withholding and 32/32 for clean/sabotage. These are engineering fixtures.
The first arithmetic SQLite pilot had mixed outcomes; after shared source/assignment
instruction corrections, its second 32-episode pilot passed every episode.

Second SQLite pilot, four episodes per table cell:

| Policy | Clean success | Withholding success | Mean clean work | Mean withholding work |
| --- | ---: | ---: | ---: | ---: |
| Ordinary | 4/4 | 4/4 | 22111 | 21715.5 |
| JIT | 4/4 | 4/4 | 22111 | 21711.5 |
| Recovery | 4/4 | 4/4 | 22367 | 21967.5 |
| Replication | 4/4 | 4/4 | 37470.75 | 26682 |

No advance preparations were selected. Replication's extra total cost bought no
success improvement in this corrected fixture pilot. The saved-ledger audit
attributed the **256-work recovery/JIT difference entirely to finite-search
charges**, with zero non-search residual in the audited pairs. This is not proof
that recovery is generally inferior; its intended preparation benefit was not
shown in these conditions.

### SILO

| Measure | Original interface | Submitted actual-carry interface |
| --- | ---: | ---: |
| Complete-task successes | 0/8 | 0/8 |
| Correct values | 101/480 | 101/480 |
| Public integration passes | 8/8 | 8/8 |
| Within-segment increment errors | 21/448 | 7/448 |
| Charged work | 173439 | 185156 |

The carry interface used actual predecessor output, including errors, not a gold
carry. Local consistency improved without complete-task or total-value improvement.
These clean controls do not establish SILO recovery efficacy; further runs of this
setting were paused.

## 5. SQL competence progression

### Synthetic tools

| Model/condition | Correct tasks | Total work | Main interpretation |
| --- | ---: | ---: | --- |
| 4B, no thinking / 768 output | 0/4 | 23786 | Basic construction/submission failures |
| 4B, thinking / 2048 output | 1/4 | 30715 | View passed; protocol/construction failures persisted |
| 4B, constrained / 2048 output | 1/4 | 28649 | Public integration 3/4, but only view fully correct |
| 27B, constrained / 2048 output | 4/4 | 21327 | All four simple probes passed without rejections |
| 27B, categorized-feedback enabled | 4/4 | 21327 | Same outcome/cost; no feedback was triggered |

The 4B transitions also involved interface/validation changes; the 4B/27B history
is not a clean causal estimate of model size. Fixed key order, decoding, prompts,
hardware and runtime provenance must be considered. Four inspected tasks are
insufficient for a general SQL competence claim.

Most recent 27B feedback-enabled result:

| Task | Success | Work | Model calls | Rejections |
| --- | --- | ---: | ---: | ---: |
| Aggregate | Yes | 5263 | 3 | 0 |
| Join | Yes | 5660 | 3 | 0 |
| CASE | Yes | 5363 | 3 | 0 |
| View | Yes | 5041 | 3 | 0 |

All twelve generations completed their constrained actions and ended at EOS.
All ledgers reconcile; no episodes or required artifacts are missing. There was
no repair work. Enabling a dormant feedback path is a regression check, not an
observed error-correction improvement.

## 6. Native LiveSQLBench solar controls

Public metadata was pinned at
`0664a2f28555faa0dd2947c8c23288df79bcc06b`. Its 270 records lacked solutions/tests;
private author material was obtained separately. Two individual solar tasks and
one joint pair passed reported CPU positive/reset/source-integrity and
missing/corrupt-obligation controls, including later renewed controls.

Scoring is the reviewed **bc_livesql_native_v1 adaptation**, not full upstream
Python evaluator parity. Only one database group and one reviewed pair have been
validated. Reference successes establish the implemented checks can accept the
reviewed solution and reject the chosen negative controls—not broad scorer
completeness or model competence.

### Model results

| Condition | Outcome | Work | Main limitation |
| --- | --- | ---: | --- |
| 4B initial native control | 0/2 | 56867 | Repeated contract reads; no final artifacts |
| 4B catalogue correction | 0/2 | 71489 | Discovery did not yield submissions |
| 4B EOS correction | 0/2 | 73320 | Malformed attempts and reading loops |
| 4B 24-action condition | 0/2 | 131348 | More actions did not solve construction/submission |
| 27B 8K context / 12 actions | Both unscored | 62465 | Context guard stopped both executions |
| 27B 16K context / 12 actions | 0/2 | 113123 | Both exhausted actions; no final selected artifact |
| 27B 16K context / 24 actions | 0/2 | 171715 | Query construction failure and incorrect submitted view |

The 8K run's stored status was `infrastructure_failed`, with success null. Its
explicit cause was the context-limit guard. It must not be described as two
terminally scored wrong answers or a transient failure that merits unchanged retry.

The final 24-action condition did not hit the context or action limit. Therefore
those limits alone cannot explain its remaining failures.

### Latest failure attribution

**solar_2:** 16 model calls, 88562 total work, three rejections. One capped response
was followed by two complete but unsuccessful query actions. CPU replay classified
both as unresolved columns. Public candidate inspection showed undefined table
aliases: qualified references without FROM/joins to bind them. Both attempts
repeated the same tree; it also had two arguments to SUM and omitted required
metrics, classification and ordering. Correcting one alias would not prove success.

**solar_M_3:** 13 model calls, 83153 work. A view was selected and passed public
integration but failed terminal comparisons. Public-document inspection showed
multiplication by rated power where the required PPR divides by rated power; the
error propagated into TAPR. TPCI matched its documented formula. The selected
environment-to-panel primary-key join was not a declared relationship; its exact
contribution to result differences was not measured.

Offline replay executed five bounded child calls, charging **150 separate replay
work**. Candidate and reference checks ran, but exact/native comparisons did not
match. Historical results and the **171715 episode work** remain unchanged.
No native answer was repaired and fed back for rescoring.

## 7. Hardware and qualification established

The pinned 27B model/tokenizer revision is
`fc05daec18b0a78c049392ed2e771dde82bdf654`. Reported stack includes Python 3.12.10,
torch 2.10.0+cu126, Transformers 5.3.0 and XGrammar 0.1.32. GPU preflights used
full A100 80GB devices; actual preflight hardware does not prove every campaign's
node assignment or current partition availability.

Latest feedback preflight **1080375** reported command_failed=false, matching
CPU qualification, valid short/long constrained completions and SQLite status ok.
The long probe used 6144 input tokens and generated 99 tokens. Peak reserved memory
was 58143539200 bytes (about 54.2 GiB). Early EOS leaves full-cap memory fit untested.
Earlier 16K preflights likewise establish observed lengths, not every worst case.
The lock's stored staging label is not automatically rewritten by a GPU preflight;
use its separate runtime qualification evidence.

## 8. Latest implementation: what is ready but unmeasured

### Categorized SQL feedback

`sqlite-errors-v1` returns fixed categories and generic construction hints, with
no raw SQLite exception text, identifiers, paths, expected rows or hidden results.
Legacy feedback remains the default. Failures retain ordinary tool/SQL/model
charges and retry limits. This is opt-in synthetic functionality; native feedback
runs and recovery campaigns have not been enabled by these changes.

### Paired supplied-draft correction diagnostic

Prepared configs compare generic versus categorized feedback on the same two
invalid drafts: wrong SUM arity and an undefined qualifier. Same source, model,
seed, task data, 8192 context, 2048 output cap, 12 actions and 100000 work.
Each condition has two episodes; both together would be four executions.

The harness executes the draft before the first model turn. It is labelled a
supplied input, not a fabricated model generation. The initial tool/SQL work is
charged (40 with current defaults), consumes one action and one rejected attempt,
and its text/feedback is charged in subsequent model inputs. No free retries are
added. The model may rewrite the draft and must submit a complete artifact.

The paired audit checks matched inputs and separates draft rejections from model
rejections. This is a **near-complete supplied-draft correction test**. Even success
would not establish end-to-end native generation, general self-correction, or
recovery under contributor compromise. Both conditions passing would show no
observed success advantage for categorized feedback on these two cases.

**Status at review:** implemented, tested and reportedly pushed; no paired GPU
result or submission reported. Further commands are paused by this review request.
See [the diagnostic design](SQLITE_CORRECTION_DIAGNOSTIC.md).

## 9. Main unresolved research questions

1. **Clean native competence (gate A):** synthetic success has not transferred to
   solar; SILO complete-task success is also absent. The evidence identifies
   specific failures in the tested model/interface combination, not intrinsic
   inability of the model in every interface.
2. **Meaningful policy comparison (gate B):** the current finite catalogue uses
   fixed owners/obligations and a small set of boundary/backup choices. Independent
   tasks can collapse to the same workflow. It is not general task decomposition.
3. **Advance preparation versus JIT:** under the limited additive-cost catalogue,
   JIT may perform the same preparation after the alarm. No preparation can be
   the valid optimum. A research benefit cannot be manufactured by assumed cheap
   warm costs or by forcing nonzero preparation.
4. **Evaluation scope:** reviewed native scoring and adapted SILO access/scheduling
   differ from upstream settings. Intended paper claims must match those changes.
5. **Fairness and generalization:** repeated development task inspection, model
   changes and interface tuning prevent simple causal conclusions. A later claim
   needs a prospectively frozen design and additional independent task groups.
6. **Cost interpretation:** surrogate-work accounting is implemented and latest
   ledgers reconcile, but hardware/time/cost comparisons require separate evidence.
7. **Research focus:** much recent work has become model/interface debugging.
   More successful diagnostics alone will not answer the recovery question.

## 10. Review decisions, without presuming the answer

| Choice | What it could resolve | What it would not resolve |
| --- | --- | --- |
| Run the prepared two-condition correction test | Whether categories help on two controlled errors | Native competence or recovery benefit |
| Audit/simplify the task interface prospectively | Whether representation obstructs task construction | Requires a new labelled condition and fresh evaluation |
| Revisit task decomposition and policy mechanism first | Whether the proposed comparison can exercise recoverability | Does not fix current worker errors |
| Pause or change task scope | Avoid further tuning on the same two failed native tasks | Requires new task/scorer/data validation |

Before resuming, decide which uncertainty matters most and what result would stop
or justify the next bounded step. No further experiment is authorized merely by
this report. Do not increase limits, retry unchanged semantic failures or expand
into a policy campaign automatically.

## 11. Provenance and local verification

Latest experiment identifiers (older IDs are indexed in the September 20 report):

| Condition | Experiment ID |
| --- | --- |
| 27B original synthetic | `2529aacf278226f8fa77195f1a7280913e6e7be6b12fb2d41ebe9f22e72cf10c` |
| 27B native 8K | `15465896c46c6daedf3098ef3200c696331cd6bdbcd2996996de72152a84ec4e` |
| 27B native 16K / 12 actions | `64b9dbbf253cfec70c4c12fe4ce1efa5fcf297e8044ca91caa1549931bfd699e` |
| 27B native 16K / 24 actions | `13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981` |
| 27B feedback-enabled synthetic | `ef260dc917102ddb9c1684f008622ce50918616a6f99a0bcb42f20cda193ca20` |

Latest feedback setup/report directory:
`/dataset/suaq0001/beyond-consensus/diagnostics/sqlite-feedback.JeJ2Ju`.
Preserve manifests, qualified locks, frozen snapshots, preflight/runtime reports,
per-episode results/checkpoints/events, raw ledgers and derived immutable reports.
Preserve private reviews and author material privately; do not commit their contents.

The latest implementation verification recorded **214 local tests: 213 passed,
one opt-in legacy skip**, plus nine shell files and documentation/CLI checks.
These are engineering controls, not model task successes. See
[VALIDATION.md](VALIDATION.md) for exact commands and timings.

This report is a documentation-only consolidation. It does not change runtime,
scoring, budgets, historical outputs or task data, and launches no jobs or downloads.
