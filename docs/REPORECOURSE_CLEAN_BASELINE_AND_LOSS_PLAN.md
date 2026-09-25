# RepoRecourse clean baseline and proposed contributor-loss diagnostic

Recorded 2026-09-25. Evidence below is user-supplied cluster output, not a local
rerun or independently retrieved cluster record. Historical scores are unchanged.

## Observed engineering results

| Condition | Experiment | Complete success | Logical tokens | CPU seconds |
| --- | --- | --- | --- | --- |
| Original finish behavior | 855edc500f48ec01eb9674e48bb6c2b9d7f59caa11fd218f5a41ab35da72bdcb | 0/1 | 18,302 | approximately 372.72 |
| Assignment-local finish and clarified public contract | b9492f9028928218e190cf0441956d681cecb524b824505d551047f55757a9f9 | 1/1 | 29,745 | 404.791043613 |

Both are Jaffle recorded-payments, independent outline, delegation_jit, clean
development episodes in one source group. Neither is confirmatory.
The corrected episode is a9cfd17e2a30080a28a15d5c2e985502a129f8742a2753730cb440282921beaa.
It reports no uncertain tokens, missing episodes or infrastructure failures.

The original saved queries referenced nonexistent source columns:
customers.customer_id (actual id), orders.customer_id (actual user_id),
orders.order_id (actual id), and payments.payment_id (actual id).
These are static artifact/schema findings, not new SQL executions. Structural
compilation accepted the queries; recorded execution returned semantic_error.
Repair rebound an unchanged invalid artifact, then worker finish closed the
shared episode and a subsequent worker call failed with episode_closed.

In the corrected run, w0 published customer_summary and w1 published
method_summary. Both final obligations passed the available finite evaluator.
w1 incurred one sql_rejected compiler event, read another source and published
successfully within its primary assignment. Both public executions passed.
There was no public alarm, repair stage, explicit rebind, or use of w2/w3.
Both primary versions were retained. Task costs were 12,970 tokens for the
customer assignment and 16,775 for the method assignment. Caps were 100,000
logical tokens and 1,200 CPU seconds under rr-logical-tokens-cpu-v1.

This shows clean engineering feasibility on one repeatedly inspected task.
It does not demonstrate contributor recovery, a policy advantage, general
competence, or causal benefit of the finish fix. The public instructions changed
too, and the corrected GPU run did not exercise finish during repair.
Regression tests, not this GPU observation, exercise the corrected finish path.

## Proposed bounded plan: not executable or submitted

Status: REVIEW PLAN ONLY. No manifest or fabricated qualification is attached.
Current require_run permits one clean engineering smoke only. Non-smoke runs
raise development_review_competence_calibration_gates_pending; an F row cannot
be placed in an engineering smoke to bypass that gate.

Proposed scope: exactly three fresh episodes, one seed (0), one task
(jaffle-recorded-payments), one independent outline and delegation_jit only.

| Episode | Track | Target | Intended check |
| --- | --- | --- | --- |
| Fresh control | clean | none | Competence under the exact new frozen implementation |
| Loss of customer contributor | F | w0 | Missing assigned customer output and eligible reconstruction |
| Loss of method contributor | F | w1 | Missing assigned method output and retention of unrelated work |

Use the actual active assigned workers, not w2/w3 or a fifth identity. The current
F mechanism marks the target unavailable at its first assigned publication
attempt, before publication, retaining prior other publications and original
sources. It is an injected handoff loss, not a real process kill or adaptive
attack. If the handoff is never reached, report no_intervention rather than
claiming a tested loss. All four identities share one frozen model/backend.

Freeze the same public task/source hashes, prompt/tool contract, model/tokenizer
revision, exact budgets, seed and runtime for all three episodes. Do not reuse
the historical successful smoke as the matched control. Do not give workers
the diagnosed query corrections, hidden checks or reference answers.

Proposed engineering caps remain 100,000 logical tokens and 1,200 CPU seconds
per episode, equal-total track A, including pre-loss work and all reconstruction.
These are uncalibrated engineering caps, not measured B0. Keep terminal evaluator
CPU separate. Preserve full actual/uncertain work on infrastructure resume.
No terminal-failure retries or repeated seeds chosen after outcomes.
No policy sweep, plan search, sabotage track S or equal-remaining track R.

## Gate decision and work needed before execution

The successful smoke does not automatically open the gate. Independent review,
broader competence and compatible calibration remain unresolved. The eventual
balanced twelve-task thresholds cannot be applied to this one-task result.

Two possible protocol routes require a concrete decision:
1. Meet the existing review/competence/calibration gates before non-smoke runs.
2. Explicitly authorize and implement a narrowly scoped engineering-loss
   exception, recorded as a protocol change, without asserting those gates have
   been met or opening a policy campaign.

This plan does not implement either route. A narrow exception, if authorized,
must bind exactly the above task/outline/seed/three tracks, require reviewed CPU
F controls plus matching decoder/GPU preflight, reject other targets/policies,
and retain all current source, resource, licensing and registry checks.
Test missing controls, changed source/model hashes, enlarged episode grids,
and attempts to use the exception for policy campaigns before submission.
Source/task licensing review must not be declared complete by implication.

Prospective acceptance of mechanism execution is distinct from scientific
success: confirm the loss actually triggered, target identity ceased acting,
replacement came from the existing identities, unrelated versions remained
available, no episode_closed rejection occurred, and all costs were retained.
Report complete-task and per-obligation success regardless of outcome; if the
fresh clean control fails, conditional attack success is unavailable.
With one source group and one seed, report traces/counts only, no inferential
intervals or policy superiority. Stop for review after the fixed batch.

No GPU job, source download, score change or gate modification was performed
while preparing this document.
