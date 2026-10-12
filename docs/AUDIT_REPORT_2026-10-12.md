# Beyond Consensus / RepoRecourse — Audit Report

**As of 12 October 2026**

## 1. Executive summary

We have progressed from SQL/tool-interface debugging to a working RepoRecourse implementation with generated planning, scoped execution, and recovery from worker loss.

**Completed results:**

- A Jaffle engineering smoke run succeeded after earlier implementation failures.
- A generated stock plan completed successfully.
- Two subsequent conditional worker-loss branches recovered successfully.
- A separate prospective stock run completed clean and both owner-loss branches successfully.
- Four richer tasks now pass cluster CPU qualification and footprint checks.
- The worker/planner GPU footprint probes passed their observed cases.

**Not yet completed:**

- The four-task planner comparison has **not run: 0 of 16 conditions observed**.
- Independent task reviews and attributed rights reviews remain pending.
- No review-waiver implementation has been made.
- No calibrated budget baseline, planner-superiority result, or population-level robustness estimate has been established.

The user's latest instruction pauses the proposed waiver change for this audit. This report records evidence and limitations; it does not authorize new execution.

## 2. Evidence basis

This report consolidates user-supplied cluster summaries and earlier recorded results with the repository's [status record](STATUS.md) and [richer-cohort runbook](RICH_COHORT_PILOT.md). It does not claim fresh access to the cluster or independent authentication of every remote artifact. No model or task SQL was executed to prepare this report.

Latest cluster evidence supersedes older documentation statements that cluster CPU renewal was pending. Historical runs remain separate from the proposed four-task comparison.

## 3. What we built

### Execution and planning

The current implementation supports:

- Seven logical worker identities sharing one frozen model on an allocated GPU.
- Planning before execution and fault-target selection.
- Explicit assignment scopes controlling artifact access and communication.
- Exact artifact-version bindings.
- Common public monitoring and just-in-time repair across planner conditions.
- Separate correctness, conformance, execution-status, and budget reporting.
- Logical planning charges inherited once per execution branch, with physical planning reuse reported separately.

Workers use restricted data tools and validated artifacts. This is not arbitrary repository-code execution or an operating-system sandbox.

### Accounting and evidence

We added or strengthened:

- Token and CPU accounting, including failed and denied operations.
- Retention of invalid plans, interrupted runs, and unrun conditions.
- Immutable reports and provenance checks.
- Distinctions between declared imports, observed reads, and executable artifact bindings.
- Destructive evaluator controls using incorrect artifacts with valid publication records.
- Source integrity, reset reproducibility, and task-footprint checks.

Historical scores have not been replaced by later offline diagnostic results.

## 4. Earlier SQL experiments and findings

| Stage | Observed result | Interpretation |
| --- | --- | --- |
| Qwen3.5-4B native Solar runs | 0/2, including the larger action-budget run | More actions alone did not resolve the failures. |
| 4B synthetic tool compatibility, 768-token output | 0/4 | Tool-use compatibility was inadequate in this setup. |
| 4B reasoning, 2,048-token output | 1/4 | Improvement, but three tasks still failed. |
| 4B constrained actions, 2,048-token output | 1/4; public integration passed 3/4 | Better action structure did not ensure semantic correctness. |
| Matched 27B Solar JSON-tree arm | 0/2 | Both tasks failed under the tested interface. |
| Matched 27B Solar SQL-text arm | 1/2 | A local interface improvement on two repeatedly inspected tasks. |
| Synthetic aggregation diagnostic | 1/2 | The failed query multiplied independent detail rows through joins. |

Offline inspection established specific causes in individual runs:

- Unresolved column references.
- Incorrect results despite successful SQL execution.
- Missing or unsubmitted obligations.
- Context-limit failures.
- Join-induced overcounting.

These findings do not justify attributing every failure to the model. Interface, runtime, context, submission behavior, and query semantics all contributed. These stages used different configurations and should not be pooled into a single comparative success rate.

## 5. RepoRecourse execution results

### Earlier Jaffle smoke

The first inspected Jaffle smoke failed: both published artifacts encountered execution errors, and repair did not complete successfully.

A later corrected run succeeded:

| Run | Success | Tokens | CPU debit |
| --- | --- | ---: | ---: |
| Jaffle smoke `b9492f…` | 1/1 | 29,745 | 404.79 s |

Both obligations passed. One primary SQL rejection occurred before successful completion. No public alarm remained.

### Open-generated stock and conditional recovery

| Condition | Success | Conformant | Tokens | CPU debit |
| --- | --- | --- | ---: | ---: |
| Clean `151721…` | Yes | Yes | 7,476 | 208.01 s |
| Conditional loss of w0, `f6066e…` | Yes | Yes | 9,949 | 232.30 s |
| Conditional loss of w1, `f6066e…` | Yes | Yes | 10,802 | 245.37 s |

Both intended losses triggered. Both recovery branches satisfied `stock_report` and `zero_report`.

Trace review distinguished the mechanisms:

- After w0 loss, another worker reconstructed the stock artifact and a consumer used its exact version.
- After w1 loss, repair used original source data; reading a retained artifact did not establish executable artifact reuse.

**Limitation:** these fault branches were selected after observing clean success. They are conditional engineering evidence.

### Separate prospective stock milestone

Experiment: `e10d7ffbe1335f578745c36cbbeb2828d73046d0ed9c51fa672d35a80a31aa72`

| Condition | Correct and conformant | Tokens | CPU debit |
| --- | --- | ---: | ---: |
| Clean | Yes | 9,120 | 169.30 s |
| Loss of w0 | Yes | 11,849 | 196.63 s |
| Loss of w1 | Yes | 12,723 | 211.66 s |

This used one two-unit plan, two active owners, and seven available identities. Planning used two calls, including one rejected response. Its 3,005 planning tokens were already included in each branch total.

**Conclusion:** the prospective protocol worked on this synthetic task. This is not evidence that one planner outperforms another. The completed stock experiment should remain historical evidence rather than be silently rerun or replaced.

## 6. Planner capacity qualification

The planner's output allowance required several corrections:

| Stage | Result |
| --- | --- |
| 2,048-token planner cap | The representative 24-unit action required 2,125 tokens including stop; it could not fit. |
| 4,096-token cap, initial GPU probe | Planner calls failed runtime admission; worker cases passed. |
| 4,096-token cap after role correction | Four cases passed; the 24-unit plan exhausted output after substantial reasoning. |
| 6,144-token cap | All five observed cases passed. |

The successful 24-unit response used **4,377 output tokens**, including **2,252 reasoning tokens**.

Current role limits:

- Context: **16,384 tokens**.
- Worker output: **2,048 tokens**.
- Planner output: **6,144 tokens**.

These probes establish observed-case feasibility, not worst-case memory or output fit.

The reused richer-cohort GPU preflight `e923cb…` reported all five cases passed on an NVIDIA A100-SXM4-80GB, with 15,373 logical tokens, zero uncertain tokens, one model instance, and 680.60 seconds total wall time. It was task-free qualification, not a richer-task competence result.

## 7. Current four-task cohort

| Task | Outputs | Source group |
| --- | ---: | --- |
| `jaffle-payment-release` | 4 | Jaffle |
| `energy-single-indicator-release` | 5 | Energy |
| `github-topics-client-package` | 4 | GitHub REST API description |
| `github-multioperation-integration` | 5 | GitHub REST API description |

There are four tasks across three source groups. The two GitHub tasks are not independent repositories. Energy's constant field-contract output is documentation, not a fifth numerical problem.

Each task has executable independent and shared reference organizations. These are authored qualification witnesses, not model-generated experimental results.

The new multioperation task combines pinned topics and languages API payloads into validators and bounded mappings. It does not issue live API requests or execute downloaded repository scripts.

### Latest cluster qualification

Directory:

```text
/dataset/suaq0001/beyond-consensus/diagnostics/rr-four-task.y6a46O
```

Frozen source commit:

```text
5b44deae2af495629fdc47131e66583db7882f46
```

| Check | Result |
| --- | --- |
| Cohort controls | **109 passed; zero skips, failures, or errors** |
| Role-lock reuse | Compatible |
| Four task qualifications | `cpu_qualified_review_pending` |
| Four task footprints | Passed |
| Worker and planner locks | Present |
| Existing GPU evidence audit | `verified_internal_bindings_review_pending` |

This cluster evidence supersedes the earlier documentation's cluster-renewal-pending status. The compact summaries establish reported status; a deeper audit should inspect the full qualification files and their bindings.

### Earlier local implementation verification

The implementation record reports:

- 455 standard-library tests: 426 passed, 29 skipped.
- 109 pinned cohort controls passed without skips.
- 56 additional pinned runtime/Track F/SQL tests passed.
- Nine focused richer-task tests passed.
- Shell checks, compilation checks, diff checks, and CLI help without site packages passed.

These checks overlap in coverage and are not independent scientific observations. No tests were rerun merely to write this report.

## 8. Proposed comparison — still unrun

The prepared design compares requirement-level planning with prompted open-generated planning. For each task/planner configuration, it schedules clean execution and a prospectively selected owner-loss condition.

| Quantity | Prepared scope |
| --- | ---: |
| Tasks | 4 |
| Planner conditions | 2 |
| Configurations | 8 |
| Maximum execution branches | 16 |
| GPU concurrency | 1 |
| Per-branch token cap | 100,000 |
| Per-branch CPU cap | 1,200 seconds |

The frozen design uses the same Qwen3.5-27B workers, evaluator, public monitoring, and common JIT across planners. Owner selection occurs after planning and before clean outcomes; idle identities are excluded. Clean correctness is not a filter for scheduling the corresponding fault condition. Engineering caps are not calibrated B0 values.

Current proposal:

```text
2d28c55d86b2d1eed1ff8b8a90ab976017b0327fdc2f47f50c2670e435a6b294
```

Scope hash:

```text
38edb92c30bdc5a6ecb1d6d5c3d71e41fae3b6de42369f03756023f834d66acb
```

| Task | Requirement clean | Requirement F | Prompted clean | Prompted F |
| --- | --- | --- | --- | --- |
| Jaffle payment release | Unrun | Unrun | Unrun | Unrun |
| Energy single indicator | Unrun | Unrun | Unrun | Unrun |
| GitHub topics | Unrun | Unrun | Unrun | Unrun |
| GitHub multioperation | Unrun | Unrun | Unrun | Unrun |

All 16 conditions remain unrun. Coverage is 0/16; this is not a 0% success rate. There are no richer-cohort planner costs, recovery outcomes, or comparative success rates yet.

## 9. Review gate and recent discussion

The current `rich_pilot` implementation requires:

- Independent task-review receipts.
- Attributed source-rights review receipts.
- An underlying-provider basis for Energy.
- Exact cohort approval after those prerequisites resolve.

These are project admission rules, not Slurm or GPU requirements. Their purpose is to distinguish technical executability from task/evaluator validity and a documented source-use basis. Missing receipts do not themselves establish that the sources are prohibited; they establish that the required review evidence is absent.

The user requested skipping review. We discussed an explicitly labelled unreviewed-development path, but:

- **No waiver code was implemented.**
- No reviews were marked approved.
- No execution gate was bypassed.
- No richer-cohort job was submitted in the supplied evidence.

The user then requested this audit before deciding what to do. The current template remains pending at:

```text
/dataset/suaq0001/beyond-consensus/diagnostics/rr-four-task.y6a46O/reviews.json
```

The current code therefore continues to block submission. The discussion of a possible policy change is not evidence that a supported waiver path exists.

## 10. Audit conclusions

**Supported by the evidence:**

- The restricted execution and recovery implementation works in the demonstrated engineering cases.
- Generated planning and recovery succeeded on synthetic stock.
- Four richer tasks now pass the reported CPU qualification.
- The tested worker/planner footprint fits the observed GPU probes.

**Not established:**

- Which planner is better.
- General recovery reliability across repositories.
- Independent validity of the four richer task/evaluator pairs.
- Completed rights review.
- Worst-case context or memory feasibility.
- Calibrated B0 budgets or confirmatory scientific results.

**Current stopping point:** technical preparation is complete for the reported checks; the four-task experiment remains unrun. This audit does not implement any additional policy change or submit any experiment.

## 11. Evidence locations for the next audit

Within `/dataset/suaq0001/beyond-consensus/diagnostics/rr-four-task.y6a46O`:

- `source-commit.txt`: frozen source identity.
- `cpu/cohort-controls.json`: control results.
- `cpu/role-lock-reuse.json`: compatibility result.
- `cpu/<task>.json`: task qualification records.
- `cpu/<task>-footprint.json`: task footprint measurements.
- `cpu/worker-lock.json` and `cpu/planner-lock.json`: role locks.
- `footprint-audit.json`: reused GPU evidence audit.
- `evidence.pending.json`: assembled evidence with pending reviews.
- `proposal.pending.json`: proposed cohort.
- `review.pending.json`: exact blockers, scope, and review templates.
- `reviews.json`: pending editable review receipts.

Repository context:

- [Richer cohort design and runbook](RICH_COHORT_PILOT.md).
- [Implementation and historical status](STATUS.md).
- [Open planning runbook](OPEN_PLANNING_RUNBOOK.md).
- [Source attribution and licenses](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md).

No raw private task references, hidden tests, model outputs, or credentials are included in this report.
