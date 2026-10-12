# Beyond Consensus / RepoRecourse audit report

**Review date: 11 October 2026**  
**Status: prospective synthetic-stock milestone completed; richer pilot not yet run.**

## 1. Executive summary

The latest prospective stock experiment completed clean execution and both
preselected worker-loss branches successfully. All three were contract-conformant
and within their engineering resource caps. One planning sequence produced two
units and two meaningful owners from seven available identities. Unlike the
earlier conditional recovery diagnostic, the new targets and schedule were frozen
before execution, rather than selected after observing clean success.

We have also implemented a generic cohort runner and three richer task candidates,
qualified the supplied cluster controls and observed footprint cases, and reviewed
the richer public contracts locally. A fourth API task is still an unexecutable
draft. The richer four-task planner comparison remains blocked on that task and
attributed task/rights reviews.

**Supported conclusion:** the prospective planning, scoped execution, fault
injection and common recovery workflow works on this synthetic example.
**Not established:** planner superiority, general robustness, calibrated budget
efficiency, or competence across repository-grounded tasks.

## 2. Evidence provenance and audit limits

This report combines:

- User-supplied scheduler output and cluster qualification summaries.
- The uploaded full cohort export for the latest stock experiment.
- Local inspection of implementation, public task contracts and reporting code.
- Local automated validation of the reporting correction.
- Historical results already recorded in the October 8 progress report.

Latest stock export SHA256, computed from the received attachment:
`e5be83787cf2344316e0a73f407d9d29e04afe864f4edce0bb4a291d0d27d26b`.
This identifies the received bytes, not independently authenticated cluster files.
The export contains saved results and audit records; it is not a new model or SQL
execution. Its top-level `model_executed=false` and `sql_executed=false` describe
the export operation, not the historical experiment.

The current repository HEAD is
`e9139a401efd900a0a96e08ad1fc0c01dd3f11f3`. The local reporting fix and October 11
documents are uncommitted changes at report preparation. No commit, push, new GPU
submission or source download was performed during this review. Historical
manifests, snapshots, results, scores and approvals have not been rewritten.
Private exports and raw traces remain outside Git.

## 3. Implementation delivered

| Component | Implemented behavior |
| --- | --- |
| Restricted tools | SQL text lowers to approved IR; trusted restricted execution, bounded schemas and mappings; no worker-generated host code. |
| Artifact provenance | Immutable versions, exact bindings, complete output obligations, recorded reads and publications. |
| Worker identities | Opt-in pools of 2–8 identities, including seven, sharing one frozen model instance per allocation. |
| Open planning | Bounded model-generated plans, charged rejected responses, validation and freezing before execution. |
| Assignment scopes | Mediated observations, artifact reads, messages and restored state; fresh assignment contexts preserve identity loss. |
| Common JIT recovery | Public alarms and recorded overlays reassign affected work without hidden-evaluator feedback. |
| Prospective cohort | Durable target schedule before clean evaluation; completed clean failures retain fault branches; interrupted/unrun outcomes remain visible. |
| Matched planner design | Requirement-level allocation and prompted-open planning share workers, monitoring, JIT and total budgets. The comparison has not run. |
| Accounting | Logical planning charge in each branch, physical reuse separately, token and CPU ledgers, retained uncertain usage. |
| Qualification | CPU controls, role grammar locks, public prompt footprints, observed GPU probes, hash-bound proposals and approvals. |
| Cluster management | Frozen source snapshots, shared registry and scheduler inspection, bounded concurrency, duplicate-attempt and retry restrictions. |
| Reporting | Correctness, conformance, execution status, intervention, coverage and budgets remain separate. |

The richer runner was implemented as a new opt-in path. Historical experiments
have not been migrated into it or rescored.

## 4. Historical development results

These are different conditions and resource profiles. Do not pool them into one
success rate or interpret their cost differences as a controlled treatment effect.
Entries below are carried forward from the existing October 8 review, not freshly
re-audited from every original cluster file.

| Stage | Recorded result | Interpretation |
| --- | --- | --- |
| SILO submitted-value diagnostic | 0/8 | Completed execution did not imply semantic success. |
| 4B synthetic tool compatibility | 0/4; reasoning 1/4; constrained 1/4 | Formatting and output changes alone did not establish reliable competence. |
| 27B synthetic tool compatibility | 4/4 in reviewed runs | Small-probe competence only. |
| Matched native solar JSON tree | 0/2 | Neither task passed. |
| Matched native solar SQL text | 1/2 | One success; no general interface-effect estimate. |
| Synthetic aggregation | 1/2 | Independent-detail joins multiplied rows before aggregation in the failed task. |
| Initial Jaffle smoke | 0/1 | Exposed interface/execution issues. |
| Corrected Jaffle smoke | 1/1; 29745 tokens | One clean repository-grounded engineering success. |
| Later fresh Jaffle control | 0/1 | Earlier success was not stable competence across changed conditions. |
| Authored pool-seven stock diagnostic | 1/1; 3551 tokens | Authored structure and observed artifact use differed. |

Native reference validation passed for solar tasks individually and jointly,
including missing/corrupt-obligation controls. That validates the reviewed
adaptation controls; it is not autonomous model success or upstream scorer parity.
The later offline unsubmitted solar query ran but failed reference comparison;
no candidate was promoted and historical failure remained unchanged.

## 5. Qualification history and current evidence

### Runtime and grammar

The v0.2 scripted CPU matrix reported **188/188 reference branches** over 56
conditions, two synthetic families, pools 2–8 and four authored organizations.
These were scripted controls, not model-generated research outcomes.

Planner qualification exposed a concrete output-cap problem:

1. The 24-unit action alone required 2125 tokens including a stop token, exceeding
   the original 2048 cap.
2. At 4096, the model's reasoning plus answer hit the length limit.
3. After fixing role admission and using planner cap 6144, all five observed
   footprint cases passed. Worker cap stayed 2048.

Current rich-cohort cluster summaries report:

| Evidence | Result |
| --- | --- |
| CPU job 1089913 | Completed 0:0; 99 controls passed, no skips/failures/errors. |
| Stock and three richer task qualifications | `cpu_qualified_review_pending`. |
| Worker/planner grammar | Passed; context 16384, output caps 2048/6144. |
| All four public task footprints | Passed. |
| Footprint CPU job 1089959 | Completed 0:0; five CPU cases passed. |
| GPU footprint job 1089991_0 | Completed 0:0 in 11:23; five observed cases passed. |

GPU footprint experiment:
`e923cb200f4835deb8457fe14e7bf50ee488b5b8be5d5070819bbaf75954f8e1`.
Hardware: NVIDIA A100-SXM4-80GB; one model instance; 15373 tokens; zero uncertain
usage; 680.60 seconds reported probe wall time. Plan_24 used 4377 output tokens,
including 2252 reasoning tokens. All responses reached EOS with complete grammar.

**Qualification limit:** observed cases passed; worst-case memory fit and general
task competence were not established. CPU qualification does not clear task rights
or independent review.

## 6. Earlier generated-plan clean and conditional recovery

Clean experiment:
`1517216133b6dfbf131f56f3cf2d63821ef0992ed4f528f037256830b830e291`.
Conditional fault experiment:
`f6066eca22dacf05927d4eda364d6702be202fd08408c7619cae4633c97a75ab`.

| Branch | Correct and conformant | Tokens | Charged CPU seconds |
| --- | --- | ---: | ---: |
| Historical clean | Yes | 7476 | 208.011154226 |
| Conditional loss w0 | Yes | 9949 | 232.298667658 |
| Conditional loss w1 | Yes | 10802 | 245.374443477 |

Planning used two calls, including one rejected proposal: 3005 tokens and
110.594050202 CPU seconds. The fault branches physically reused that frozen
planning result and logically charged it in each branch. Both losses triggered
before publication and persisted. The w1-loss repair read retained stock but
queried the original source, so reading must not be called executable reuse.

These fault runs were selected after clean success. They remain conditional
engineering observations, separate from the prospective run below.

## 7. Latest prospective stock experiment

Experiment:
`e10d7ffbe1335f578745c36cbbeb2828d73046d0ed9c51fa672d35a80a31aa72`.
User-supplied scheduler output: **1092937_0 completed 0:0 in 12:45**.

### Settings and plan

- Qwen/Qwen3.5-27B, revision `fc05daec18b0a78c049392ed2e771dde82bdf654`.
- BF16, thinking enabled, deterministic decoding; context 16384.
- Worker output cap 2048; planner cap 6144.
- Seven available identities; open planning and `plan_scoped_v1` execution.
- One prompted-open planning sequence; seed index 1 is a deterministic design
  setting, not evidence of an independent random sample.
- Each branch: 100000 logical tokens and 1200 charged CPU seconds, uncalibrated.
- Two generated units, two meaningful owners, one declared dependency, depth two.
- Two physical planner calls, one rejected response, valid final plan.
- Planning charge: **3005 tokens / 103.476834250 CPU seconds**.
- Targets frozen before execution; maximum eight branches authorized, actual three.

### Outcomes

| Branch | Completed | Both obligations correct | Conformant | Tokens | CPU debit seconds |
| --- | --- | --- | --- | ---: | ---: |
| Clean | Yes | Yes | Yes | 9120 | 169.303781757 |
| F(w0) | Yes | Yes | Yes | 11849 | 196.625777765 |
| F(w1) | Yes | Yes | Yes | 12723 | 211.657250723 |

All were within caps. Uncertain token/CPU usage was zero. No configurations were
missing. Planning charges are already included in branch totals; do not add them
again. Summed logical branch tokens are not physical GPU cost because planning
is reused. Terminal evaluation has its own accounting.

### Recovery observations

| Loss | Trigger and retained work | Repair | Post-alarm tokens / CPU seconds |
| --- | --- | --- | ---: |
| w0 | Before u0 publication; no retained artifact | w1 rebuilt u0, w2 completed u1 | 6217 / 66.1231 |
| w1 | Before u1 publication; stock artifact retained | w0 completed u1 | 3591 / 42.0314 |

Post-alarm costs are a recorded subset of total cost, not an additional ledger.
The declared producer-to-consumer edge was observed as an artifact read. The
consumer's query used the original stock table: this does not prove a necessary
executable dependency. Shared original sources remain authorized.

This run removes clean-success selection from its branch schedule, but remains
one synthetic task and one plan. It compares loss versus no loss under common
recovery; it does not estimate recovery benefit against a no-recovery baseline.

## 8. Reporting bug and local validation

The generic `aggregate` command produced
`Result changed provenance; cannot resubmit`. The cohort reader had already
validated whole-manifest provenance; the appended legacy shard check expected
an episode-row hash. This was a reporting-route mismatch, not evidence by itself
that remote records changed.

The cohort-specific exporter read the saved run successfully. The local fix routes
cohort coverage through the cohort reader, preserving schedule, provenance and
interrupted/unrun validation. Changed hashes still fail. Terminal invalid plans
remain terminal; reporting missing coverage does not authorize retries.

Validation after the code correction:

- Full suite: **446 tests, 74.128 seconds, OK with 28 skipped** (418 passed).
- Focused cohort suite: 23 tests, OK with one optional-dependency skip.
- Shell checker: all 10 shell files passed.
- Standard-library-only CLI help and `git diff --check` passed.

Skipped local tests are not passed tests. Earlier cluster no-skip controls are
separate evidence, not a claim that every optional test ran locally. Documentation
added afterward did not change runtime behavior. Old snapshots remain immutable;
new local code does not retroactively alter cluster source provenance.

## 9. Richer-task review

| Candidate | Outputs / grounding | Current disposition |
| --- | --- | --- |
| Jaffle payment release | Four related payment reports; demo-grounded | Implemented and CPU-qualified as review-pending. Task and rights receipt needed. |
| Energy single indicator | Five outputs; one indicator, two countries, fixed window | CPU-qualified as review-pending. Task and underlying-provider rights review needed. |
| GitHub topics client | Two shape validators and two mappings; offline API adaptation | Implemented and CPU-qualified as review-pending. Task and rights receipt needed. |
| GitHub multioperation | Six proposed roles; same GitHub source group | No finalized task, second operation closure or executable references. Blocked. |

Local review found clear public semantics but limited structural variety. Jaffle
repeats related aggregation work; Energy includes a constant documentation output;
GitHub request/response validators share a shape and mappings rename fields.
Output count is not a proxy for distinct difficulty or optimal agent count.

There are three implemented richer cards, not four admitted tasks or four
independent source groups. The configured rich lane requires all four. Running a
three-task subset would require an explicit revised design and proposal, not an
unrecorded omission. No richer model outcomes exist in the supplied evidence.

## 10. Decisions and audit checklist

Before the next experiment:

1. Review this evidence and preserve the completed stock run; no stock rerun is
   indicated by the reporting bug.
2. Complete the fourth API candidate from an inspected pinned second operation,
   bounded source closure, explicit contract, two references and negative controls.
3. Obtain attributed task/rights reviews. Energy provider clearance remains a
   separate requirement; local assistant review is not independent approval.
4. Renew controls and footprints affected by task/source changes, then prepare
   an exact matched cohort proposal. Keep budgets and limitations explicit.
5. Approve that concrete scope separately before any new task execution.

For the audit, verify exact proposal/approval/run identifiers, source and task
hashes, role locks, scheduler receipts, pre-execution target freezing, retained
failed planning charges, all branch coverage, artifact reads versus executable
bindings, persistent identity loss, and separate terminal evaluation. Verify that
reported outcomes are not pooled across historical conditions or resource units.

The intended later comparison remains requirement-level versus prompted-open
planning with the same frozen workers and common public JIT. Task-level summaries
must average targets within each plan/task; branch counts are not independent
samples. B0 calibration, broader competence, population inference and a planner
advantage remain unestablished.

## 11. Related records

- [October 8 historical progress report](PROGRESS_REPORT_2026-10-08.md)
- [Current implementation status](STATUS.md)
- [Cohort implementation and cluster runbook](RICH_COHORT_PILOT.md)
- [Detailed richer-task review](RICH_TASK_REVIEW_2026-10-11.md)
- [Source and rights record](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md)
- [Research protocol](RESEARCH_PROTOCOL.md)
- [RepoRecourse v0.2](REPORECOURSE_V0_2.md)
- [Open planning runbook](OPEN_PLANNING_RUNBOOK.md)
