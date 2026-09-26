# Beyond Consensus / RepoRecourse — audit and results report

**Date:** 2026-09-25  
**Decision state:** review before any further implementation or experiment.
The proposed contributor-loss exception has **not** been authorized, implemented
or submitted. This report makes no protocol or runtime change.

## 1. Executive assessment

We have built a reproducible restricted-data experimentation system and a new
RepoRecourse prototype. The latest real-model Jaffle smoke completed both required
outputs successfully within the declared engineering budgets.

**We have not demonstrated that recovery-aware delegation improves success after
contributor compromise.** The successful run needed no repair. Earlier policy
fixture successes, local scripted controls, and one clean source-grounded task
cannot establish that research claim.

The first RepoRecourse GPU episode failed with both query mistakes and a runtime
termination defect. We corrected the termination contract and reran as a new
experiment. The new result is 1/1, but it is not a causal estimate of the fix:
the public tool instructions changed and the successful trace never entered
repair. Historical failures remain failures.

## 2. Evidence provenance and scope

- Cluster observations come from user-supplied preflight reports, aggregates,
  resource ledgers and saved-artifact/trace exports. They were not fetched
  independently from Slurm during this review.
- Code findings come from inspecting the repository. Test evidence is separate
  from real-model evidence.
- Earlier results below are carried forward from the
  [September 24 report](PROGRESS_REPORT_2026-09-24.md), not rerun for this report.
- Source-grounded tasks, synthetic fixtures, SILO and native LiveSQL adaptations
  remain separate. They do not form one pooled benchmark score.
- The old token/tool surrogate and new logical-token/CPU resource profile are
  different measurements. Do not compare their raw totals as a common cost unit.
- A diagnostic export saying model_executed=false means the export did not call
  a model; it does not mean its historical GPU episode was scripted.

## 3. Project trajectory and earlier results

### Infrastructure and task path

The project established pinned model/tokenizer locks, frozen source snapshots,
manifests, episode journals, resumable accounting and browser-terminal Slurm
submission. Four persistent worker identities share one frozen model backend.

CooperBench execution did not qualify on the inspected Slurm environment.
Basic container probes passed, but required resource isolation/delegation did
not. That gate was not bypassed. The active work moved to restricted SQLite
artifacts and a labelled SILO adaptation. No PBS/cloud/personal-PC migration
was completed. These data tools are not an OS sandbox.

SQLite work added bounded SQL-text lowering to the existing approved query
representation, constrained JSON actions, explicit version bindings and separate
public checking/private evaluation. No arbitrary downloaded repository code,
raw worker SQL, or upstream Python test functions are executed.

### Historical evidence carried forward

| Condition | Reported outcome | Interpretation |
| --- | --- | --- |
| Numeric fixture campaigns | 32/32 clean/withholding; 32/32 clean/sabotage | Harness engineering |
| Corrected SQLite arithmetic pilot | 32/32 | Fixture success; no recovery success advantage |
| SILO original interface | 0/8; 101/480 values correct | Complete-task competence inadequate here |
| SILO submitted-carry interface | 0/8; 101/480 values correct | No complete-success improvement |
| 4B synthetic SQL, no thinking | 0/4; 23,786 surrogate work | Construction/submission failures |
| 4B thinking | 1/4; 30,715 work | Most failures remained |
| 4B constrained thinking | 1/4; 28,649 work | Syntax constraints insufficient |
| 27B constrained synthetic SQL | 4/4; 21,327 work | Basic synthetic competence |
| 27B categorized-feedback synthetic SQL | 4/4; 21,327 work | Feedback unexercised; no feedback-benefit claim |
| Native 27B, 8K | Both unscored after context guard | Configuration/runtime failure |
| Native 27B, 16K / 12 actions | 0/2; 113,123 work | Final artifacts not submitted |
| Earlier native 16K / 24 actions | 0/2; 171,715 work | Construction/semantic failures |
| Fresh matched JSON-tree arm | 0/2; 171,725 work | Separate current control |
| Fresh matched SQL-text arm | 1/2; 134,471 work | Local interface result |
| SQL-text naming follow-up | 1/2; 151,191 work | Same success count, greater work |
| Synthetic aggregation | 1/2; 11,085 work | Independent detail joins multiplied aggregates |

The synthetic aggregation audit directly identified row multiplication in the
stored executable artifact. It did not establish the same cause for every native
failure. Native solar tasks were repeatedly inspected; these are development
observations, not held-out evidence.

## 4. RepoRecourse implementation

RepoRecourse separates benchmark-owned requirements, tools, faults, accounting
and evaluation from policy choice. Existing backend/journal/Slurm components are
reused through adapters.

Implemented:
- Data-product SQL artifacts and bounded API/schema/mapping artifacts.
- Immutable artifact versions, explicit publication/binding and consumer rebinds.
- Four identities; announced contributor loss F, bounded sabotage S, and
  fixed-state equal-remaining R mechanisms with distinct accounting.
- CPU baseline drivers: solo, delegation/JIT, restart and independent replication.
- Finite supplied outlines; an optional calibrated selector that rejects missing
  compatible measured costs. No empirical planner advantage is claimed.
- Restricted SELECT lowering/execution, bounded schema validation, finite field
  mappings, public source tools and private terminal scoring.
- Logical input plus output tokens, including reasoning once, with separate CPU
  accounting and uncertain interrupted usage. Device/wall time is not added as CPU.

### Task inventory

| Task | Grounding/family | Evidence and limitations |
| --- | --- | --- |
| jaffle-recorded-payments | Fictional demo / data product | CPU qualified; one corrected clean GPU success |
| energy-generation-coverage | Source-grounded authored / data product | CPU qualified; provider-license review blocks model execution |
| github-topics-consumer | Source-grounded authored / API/schema | CPU qualified; no model task result |
| synthetic-stock | Synthetic data product | CPU engineering controls |
| synthetic-nullable | Synthetic API/schema | CPU engineering controls |

Three source packs are pinned: Jaffle, OWID energy and GitHub REST.
The source plan caps downloads at 22,296,539 bytes; no model weights are included
in that figure. There are three source-grounded draft tasks and two synthetic
diagnostics, not twelve reviewed benchmark tasks. Independent review is pending.

Initial local optional-dependency qualification recorded **10/10 reference
executions and 39/39 negative controls**, plus reset/source-integrity checks.
These are scripted CPU results, not model competence. The cluster subsequently
reported all five tasks cpu_qualified_review_pending and compiler/grammar passed.

## 5. Cluster bring-up and defects

| Issue | Diagnosis/action | Evidence limit |
| --- | --- | --- |
| CPU job looked in Slurm spool for scripts/bc.py | Slurm relocates submitted scripts; wrapper invokes the original frozen script explicitly | Use wrapper, not direct submission from the original runbook |
| Temporary database cleanup failed | SQLite transaction context did not explicitly close its connection; explicit closure and regression test added | Consistent with shared-filesystem cleanup failure; no node-level filesystem forensic claim |
| Accidental duplicate preflight | First job 1081822 completed 0:0; duplicate 1082394 was running, then user sent scancel | Final cancellation accounting was not supplied |
| GPU episode repair failed with episode_closed | Worker finish closed the entire shared episode; repair still requested another action | Fixed assignment-local termination and call guards |
| Primary SQL semantic errors | Saved trees used nonexistent column names | Static artifact/schema diagnosis; historical artifacts not repaired |

The termination correction also clarified the public tool instructions.
It persists assignment completion for resume and stops calls after terminal
closure/resource exhaustion. Regression tests cover primary/repair continuation,
resume and closure, but these tests do not replace GPU intervention evidence.

## 6. GPU qualification

Reported corrected preflight: job **1082568**, NVIDIA A100-SXM4-80GB,
Qwen/Qwen3.5-27B in bfloat16, revision
fc05daec18b0a78c049392ed2e771dde82bdf654.

The environment reports Python 3.12.10, Torch 2.10.0+cu126, Transformers 5.3.0,
XGrammar 0.1.32; CPU compiler SQLGlot 27.28.1 and validators jsonschema 4.25.1 /
referencing 0.36.2 are pinned separately.

RepoRecourse grammar generation, restricted SQL and schema probes passed.
Long-context generation used **14,335 input tokens and 735 output tokens**,
ending at EOS; peak reserved memory was 62,369,300,480 bytes (about 58.1 GiB).
The report explicitly says **worst_case_fit_established=false**: it does not
prove the full 16,384-context / 2,048-output boundary.

Fallback-library and ignored-sampling-flag messages accompanied working runs.
They are not evidence of task failure; do_sample=false was configured.
Preflight checks infrastructure and interfaces, not task competence.

## 7. The two RepoRecourse model results

Both used the Jaffle task, independent authored outline, delegation_jit policy,
clean track and one source group. Per-episode caps were **100,000 logical tokens
and 1,200 CPU seconds**, explicitly uncalibrated engineering allowances.

| Measure | Original implementation | Corrected implementation |
| --- | ---: | ---: |
| Complete-task success | 0/1 | 1/1 |
| Actual logical tokens | 18,302 | 29,745 |
| CPU cap debit | 372.720437001 | 404.791043613 |
| Uncertain tokens | 0 | 0 |
| Bound obligations at end | 1 | 2 |
| Both obligation checks passed | No | Yes |
| Public alarm | Both obligations | None |
| Repair attempted | Yes, impaired by defect | No |
| Infrastructure failures in aggregate | 0 | 0 |

Original experiment:
855edc500f48ec01eb9674e48bb6c2b9d7f59caa11fd218f5a41ab35da72bdcb  
Episode:
5bc62080154e613accd4b5804aca45fe220711b15df9d2d4f9de7948d8006df2

Corrected experiment:
b9492f9028928218e190cf0441956d681cecb524b824505d551047f55757a9f9  
Episode:
a9cfd17e2a30080a28a15d5c2e985502a129f8742a2753730cb440282921beaa

### Original failure

Both workers published structurally accepted queries, then execution failed.
They referenced customers.customer_id, orders.customer_id, orders.order_id and
payments.payment_id, whereas actual source names are customers.id,
orders.user_id, orders.id and payments.id. The required output alias customer_id
is distinct from the input column. The schema was available via the tables source.

Repair rebound the unchanged invalid customer artifact. A worker finish closed
the episode, and another worker action was rejected. The aggregate's zero
infrastructure failures does not mean the harness was defect-free: it classified
this as a completed unsuccessful episode.

### Corrected success

w0 produced customer_summary using 12,970 tokens and 148.600099732 CPU seconds.
w1 produced method_summary using 16,775 tokens and 256.103407222 CPU seconds.
Small remaining CPU charges are outside those unit subtotals.

w1 had one compiler rejection, read another source and successfully published
within primary work. Both public executions and both final finite obligation
checks passed. There were no public alarms, repair-stage operations or explicit
rebindings. w2 and w3 published nothing. Both primary artifact versions survived.

This is primary self-correction plus successful clean delegation. It is not
contributor replacement or evidence of recovery under attack. Because execution
and the public contract changed, neither cost differences nor score differences
are controlled estimates of the finish fix.

## 8. Verification and audit concerns

Latest completed repository checks before this report: **267 tests, 254 passed,
13 skipped**, plus all **10 shell checks**. Skips include optional child dependency
tests and the optional legacy real-sandbox integration test. Initial pinned-child
full-suite counts were 263 tests, 262 passed/one skipped; these are an earlier
revision, not proof that the latest full suite ran with all optional packages.
Cluster compiler qualification additionally reported four passing compiler tests.

Key unresolved questions:
1. Independent task/pack review and energy provider-license clearance.
2. Breadth of clean competence beyond one repeatedly inspected Jaffle task.
3. Actual model behavior under F/S/R; corrected repair is GPU-unexercised.
4. Matched measured calibration, B0 and finite-plan cost predictions.
5. Model-generated planning competence and any policy comparison.
6. Full-context memory bounds and robustness across nodes/runtime versions.
7. CPU admission accounting: supplied logs include model-host actual CPU above
   its 31-second reservation. Total actual usage was charged and stayed below
   the episode cap, but reservation adequacy/hard-bound semantics deserve audit.
8. Public checks and finite hidden fixtures do not prove universal correctness.
9. Shared compiler/executor/validator defects can affect references and candidates.
10. Dated runbook statements should be read with later evidence: the direct CPU
    sbatch form caused the spool-path failure; the tested wrapper is required.

No theoretical recovery advantage, statistical significance, broad benchmark
coverage, independent task review or robust attack success rate is established.

## 9. Proposal awaiting review — no execution authorization

The separate [three-episode plan](REPORECOURSE_CLEAN_BASELINE_AND_LOSS_PLAN.md)
proposes exactly one fresh clean control and two F conditions targeting w0 and
w1 respectively, on the same Jaffle task, outline, seed and allowances.

It is a review document, not an executable manifest. Current require_run permits
only one clean engineering smoke and rejects non-smoke runs. A narrow exception
would require an explicit protocol decision, validation of its exact scope and
CPU intervention controls; passing the clean smoke did not grant that exception.
The user requested this audit before deciding. No gate has been relaxed.

Possible decisions after review:
- Address harness/accounting/task-review issues before more model work.
- Authorize a strictly bounded engineering-loss exception with explicit limits.
- Complete broader review/competence/calibration gates first.
- Revise or pause the benchmark direction.

No experiment needs to be submitted merely to review this report.

## 10. Evidence locations

- [Original implementation, CPU evidence and source pins](REPORECOURSE_IMPLEMENTATION.md)
- [Current status](STATUS.md)
- [Research protocol](RESEARCH_PROTOCOL.md)
- [Prior project consolidation](PROGRESS_REPORT_2026-09-24.md)
- [Synthetic aggregation findings](SQLITE_AGGREGATION_FINDINGS_2026-09-24.md)
- [Source attribution](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md)

Known cluster paths (external to this checkout):
- Initial CPU session: /dataset/suaq0001/beyond-consensus/diagnostics/reporecourse.eT3M20
- Corrected CPU session: /dataset/suaq0001/beyond-consensus/diagnostics/reporecourse-finish.IzYQqX
- Results root: /dataset/suaq0001/beyond-consensus/outputs/qwen27b-na100/
  followed by the full experiment ID above.
- Successful preflight snapshot:
  23867ec5815e1e45d25eb17ab7e70f6f918bfa636784b61186c8a118a793f02d

Raw private evaluator material, model weights and cluster outputs are not copied
into this report or Git. No historical scores changed during its preparation.
