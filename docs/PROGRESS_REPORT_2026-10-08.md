# Beyond Consensus / RepoRecourse progress report

**Review date: 8 October 2026**

## 1. Executive summary

We have demonstrated the following engineering sequence on **synthetic-stock**:

1. A model generated a valid execution plan after one rejected proposal.
2. Workers completed that plan successfully under enforced assignment scopes.
3. In two separately approved follow-up branches, the system recovered successfully after losing either meaningful worker.
4. Trace audits confirmed public-triggered recovery, persistent identity loss, consistent artifact bindings, and reconciled resource accounting.

**This is a completed engineering milestone, not yet evidence that one planner or recovery policy outperforms another.** The fault branches followed a plan selected after observing clean success, and all three observations concern one small synthetic task.

## 2. What we have built

| Component | Current capability |
| --- | --- |
| Restricted execution | Worker SQL lowers into approved representations and runs through the trusted restricted executor. |
| Artifact tracking | Immutable versions, exact bindings, publication provenance, and complete output obligations. |
| Logical worker pools | Opt-in pools of 2–8 identities sharing one frozen model; current model experiments use seven available identities. |
| Open planning | Model-generated bounded plans, validated and frozen before execution. |
| Scoped execution | Assignment-specific artifact access, messages, observations, and fresh contexts. |
| Common recovery | Public alarms trigger recorded JIT reassignment and scope changes; lost identities remain unavailable. |
| Resource accounting | Repeated input and generated tokens, separate CPU accounting, inherited planning charges, and retained uncertain usage. |
| Qualification | CPU reference controls, role-specific grammar checks, GPU footprint probes, and source/evidence binding. |
| Cluster workflow | Frozen snapshots, shared scheduler registry, bounded concurrency, separate approvals, and duplicate-attempt protection. |
| Audit reporting | Execution status, correctness, conformance, budgets, missingness, and intervention status remain distinct. |

Hidden evaluator material remains separate from planner and worker inputs. Historical results have not been rescored. JIT refers to the common just-in-time recovery mechanism; it is held fixed in the intended planner comparison.

## 3. Earlier development results

These stages explain why the implementation changed. They are **different experimental conditions and should not be pooled**.

| Stage | Reported result | Main finding |
| --- | --- | --- |
| SILO submitted-value control | **0/8** correct | Episodes completed, but semantic correctness remained unsuccessful. |
| Qwen3.5-4B synthetic tool probes | **0/4**, then **1/4** with reasoning; constrained condition also **1/4** | Better formatting alone did not establish reliable task competence. |
| Qwen3.5-27B synthetic tool probes | **4/4** in reviewed runs | Established competence on those small probes, not native tasks. |
| Native solar JSON-tree control | **0/2** in the matched interface comparison | Native task execution remained difficult. |
| Native solar SQL-text condition | **1/2** | SQL-text improved the observed result, but one native task still failed. |
| Synthetic aggregation diagnostic | **1/2** | The failed query joined independent detail tables before aggregating, multiplying rows and inflating totals. |
| Initial RepoRecourse Jaffle smoke | **0/1** | Exposed execution/interface issues. |
| Corrected Jaffle clean smoke | **1/1**, 29,745 tokens | Demonstrated a successful clean repository-grounded engineering run. |
| Later fresh Jaffle control | **0/1** | The earlier success did not establish stable competence across changed conditions. |
| Pool-seven authored stock diagnostic | **1/1**, 3,551 tokens | Workers succeeded, but realized artifact reuse differed from the authored “independent” plan. |

The last finding motivated an important distinction: **a declared graph is not automatically the executed dependency graph**. This led to explicit conformance reporting and assignment-scoped execution.

Historical legacy charged-work units and current RepoRecourse logical tokens/CPU are different resource profiles. They must not be treated as a single cost series.

## 4. Qualification results

### CPU reference and runtime controls

The v0.2 scripted reference matrix reported:

- **56 conditions**
- **188/188 successful reference branches**
- Two synthetic task families
- Pools **2–8**
- Four authored organizations

These establish harness behavior under scripted references, **not model-generated planning performance**.

For the latest fault adapter, cluster qualification reported:

| Control suite | Result |
| --- | ---: |
| Clean adapter | **12/12 passed, zero skips** |
| Fault adapter | **10/10 passed, zero skips** |
| Worker grammar | Passed, 2,048 output-token cap |
| Planner grammar | Passed, 6,144 output-token cap |
| Context limit | 16,384 |

The fault suite included the restricted-SQL integration control that was unavailable in the local base environment. CPU qualification job **1088580** completed with exit code **0:0**.

### Planner output capacity

The qualification sequence exposed two distinct problems:

1. A 24-unit action required **2,125 tokens including a stop token**, exceeding the original 2,048 cap even without reasoning.
2. At 4,096 tokens, the model used enough reasoning to truncate the response.

After correcting role admission and raising only the planner cap to **6,144**, all five footprint cases passed. The 24-unit response used **4,377 output tokens**, including **2,252 reasoning tokens**.

This establishes **fit for the observed cases**, not universal worst-case memory or output capacity.

## 5. Latest model results

### Frozen experimental setting

- **Model:** Qwen3.5-27B
- **Pinned revision:** `fc05daec18b0a78c049392ed2e771dde82bdf654`
- **Generation:** BF16, thinking enabled, `do_sample=false`
- **Context:** 16,384 tokens
- **Worker output cap:** 2,048
- **Planner output cap:** 6,144
- **Available identities:** seven
- **Task:** synthetic-stock
- **Planning:** open-generated
- **Execution:** `plan_scoped_v1`
- **Recovery:** common scoped JIT
- **Per-branch caps:** 100,000 tokens and 1,200 charged CPU seconds
- **Interpretation:** uncalibrated engineering limits

### A. Clean generated-plan run

Experiment: `1517216133b6dfbf131f56f3cf2d63821ef0992ed4f528f037256830b830e291`

The first four-unit proposal was rejected. The second proposal formed this two-unit dependency:

```text
u0 / w0: stock_report
          ↓ exact artifact version
u1 / w1: zero_report
```

Both outputs passed terminal evaluation.

| Measurement | Result |
| --- | ---: |
| Clean success | **Yes** |
| Contract conformance | **Yes** |
| Active workers | **2 of 7 available** |
| Planner calls | 2 |
| Worker calls | 3 |
| Planning tokens | 3,005 |
| Total tokens | **7,476** |
| Total charged CPU | **208.01 seconds** |
| Uncertain usage / pending reservations | **Zero** |

The precise planning CPU charge was **110.594050202 seconds**. Total charged CPU was **208.011154226 seconds**. Both planner proposals, including the rejected one, remain charged.

### B. Conditional worker-loss runs

Experiment: `f6066eca22dacf05927d4eda364d6702be202fd08408c7619cae4633c97a75ab`

Both branches reused the frozen plan physically and included its planning charges logically.

| Measurement | Loss of w0 | Loss of w1 |
| --- | --- | --- |
| Intended loss triggered | Yes | Yes |
| Final success | **Yes** | **Yes** |
| Contract conformance | Yes | Yes |
| Both obligations passed | Yes | Yes |
| Total tokens | **9,949** | **10,802** |
| Total charged CPU | **232.30 s** | **245.37 s** |
| Uncertain usage / pending reservations | Zero | Zero |

Precise CPU charges were **232.298667658** and **245.374443477** seconds, respectively. The supplied scheduler export reports jobs **1088628_0** and **1088628_1** completed **0:0**, in **6:33** and **6:46**. Scheduler elapsed time is separate from charged CPU.

#### Loss of w0

- Loss occurred before the stock publication committed.
- No earlier artifact existed to retain.
- **w1 rebuilt stock_report.**
- **w2 produced zero_report using the rebuilt stock artifact’s exact version.**

#### Loss of w1

- The stock artifact had already been committed and survived unchanged.
- Loss occurred before the zero-report publication committed.
- **w0 repaired zero_report in a fresh assignment context.**
- It read the retained stock artifact, but its final query used the original stock table directly.

That second case demonstrates **retention plus source-based repair**. It should not be described as executable reuse of the retained artifact.

## 6. What the audits verified

The uploaded records supported these checks:

- Frozen-plan hashes matched their contents.
- Saved journals agreed with final results.
- Each targeted loss occurred once, before publication commit.
- Lost identities remained unavailable.
- Recovery scopes referenced recorded public alarms.
- Artifact bindings and recorded exposure were consistent.
- Recomputed conformance found no protocol violations.
- Each fault branch inherited the **3,005-token planning ledger once**.
- Token and CPU totals reconciled.
- Evaluator work remained separate, with no terminal feedback to workers.

Each fault branch made **five new model calls** after inheriting the historical planning ledger. Both obligations passed both recorded terminal fixtures, giving four checks per branch; these are finite tests, not universal correctness proofs.

**Audit boundary:** the exports included manifest projections rather than every original qualification record. The review establishes internal consistency of supplied evidence, not independent authentication of the remote filesystem. No model or SQL was rerun during these audits. Raw journals and private exports remain outside Git.

## 7. What we can and cannot conclude

### Supported

- The scoped open-planning path can complete this synthetic task.
- A generated dependency can be realized through exact artifact bindings.
- Common JIT recovered from either meaningful owner’s loss in the tested plan.
- Recovery can reconstruct missing work and preserve unaffected work.
- The tested accounting and provenance records are consistent.

### Not established

- General clean competence across tasks.
- General recovery probability.
- Better performance than restart, replication, or no recovery.
- Superiority of one pre-execution planner.
- Seven-active-worker competence.
- Calibrated budget efficiency or B0.
- Native-task or repository-wide generalization.
- Statistical independence of these observations.

**The most important design limitation is selection after clean success.** The two fault branches are conditional follow-ups, not a prospectively scheduled matched experiment.

## 8. Proposed next experiment

The documented next step is a **small prospective clean/F engineering check**.

| Design element | Proposal |
| --- | --- |
| Task | synthetic-stock |
| Planning sequences | One fresh sequence |
| Seed | Prespecified seed index 1 |
| Plan selection | Retain its outcome; do not regenerate until successful |
| Target rule | All meaningful owners, specified before generation |
| Execution branches | One clean plus one loss per eligible owner |
| Maximum branches | **Eight** with pool seven |
| Workers and recovery | Same frozen workers and common scoped JIT |
| Budget | Same total caps, planning charged in every branch |
| Scheduling | Concurrency one |
| Reporting | Include clean failures, invalid planning, non-triggered faults, interruptions, and missing rows |

The branch schedule must be fixed **before observing clean correctness**. A completed clean failure must not remove the fault branches.

**Status:** design documented; the separate prospective adapter is not yet implemented or approved. Existing clean and conditional-fault adapters do not authorize this experiment.

This check would validate prospective branching. It would still **not compare planners or estimate recovery benefit against another policy**.

For eight branches, the maximum aggregate logical allowance would be 800,000 tokens and 9,600 charged CPU seconds. These are caps, not forecasts of actual physical computation or scheduler time. Physical planning is counted once in physical-work reporting and its ledger is inherited in every logical branch.

## 9. Decisions needed for the research experiments

Before scaling, settle these questions:

1. **Primary comparison:** which two concrete pre-execution planners are being compared?
2. **Task coverage:** which independently reviewed task groups provide meaningful variation beyond stock?
3. **Budgets:** what compatible calibration establishes useful total allowances?
4. **Target weighting:** how will losses be averaged within plans when planners use different numbers of owners?
5. **Outcome handling:** how will invalid planning, clean failures, missing results, and non-triggered faults remain in the analysis?
6. **Replication:** how many task groups and prespecified planning sequences are needed for the intended claim?

The intended main comparison should vary the **planner**, while holding workers, public monitoring, and JIT recovery common. Comparing recovery policies belongs in a separately labelled fixed-plan experiment.

## 10. Current handoff

- **Completed:** scoped clean planning, conditional recovery, CPU qualification, trace audits, and prospective design.
- **Latest local validation:** **393 passed, 23 optional-dependency skips** out of 416 tests; all ten shell checks passed.
- **Pending:** prospective adapter, its controls, task breadth/review, calibration, and a concrete scientific comparison.
- **No new experiment has been launched.**

The validation counts above refer to the latest implementation/design checks, not a new test run performed when saving this report. This file records evidence and proposals; it grants no execution approval.

## Repository records

- [Implementation status](STATUS.md)
- [Open-planning runbook, audits, and prospective design](OPEN_PLANNING_RUNBOOK.md)
- [RepoRecourse v0.2 migration and review](REPORECOURSE_V0_2.md)
- [Research protocol](RESEARCH_PROTOCOL.md)
