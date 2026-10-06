# Beyond Consensus and RepoRecourse audit report

**Date:** 2026-10-06  
**Purpose:** Review completed work, results and unresolved scientific questions before choosing the next phase.  
**Decision state:** No new experiment or campaign is authorized by this report.

## 1. Executive assessment

We have built and tested the restricted-data runtime, model and scheduler integration, versioned artifact handling, accounting, and much of the RepoRecourse v0.2 experimental machinery. The latest real-model synthetic-stock episode succeeded: both outputs passed their finite checks, using 3,551 tokens and 39.115 CPU seconds.

The latest audit also found an important interpretation issue. Although the authored plan specified independent work, the second worker explicitly reused the first worker's output. This is allowed by the current runtime. The success remains valid, but it demonstrates successful artifact reuse rather than independent reconstruction.

**The central research claim remains unestablished:** we have not demonstrated a recovery or planner advantage under matched budgets. Clean successes, scripted recovery controls and GPU memory probes answer different questions. They must remain separate.

The immediate review question is what a plan is intended to control: assignments followed by adaptive workers, or an enforced dependency structure. That choice affects future comparisons and should precede campaign expansion.

## 2. Evidence and audit scope

Cluster results below come from user-supplied reports, ledgers and selected traces. Repository code and local tests provide separate implementation evidence. Full remote result files and snapshots for the latest stock episode were not independently retrieved and rehashed; the supplied aggregate and selected trace are internally consistent.

Earlier results are carried forward from the [September 25 report](PROGRESS_REPORT_2026-09-25.md) and its linked reports. Recent evidence and implementation decisions are recorded in [STATUS](STATUS.md) and the [v0.2 migration and audit record](REPORECOURSE_V0_2.md).

Four distinctions govern this review:

- **Software tests:** check implementation behavior; they are not model results.
- **Scripted reference controls:** show that trusted reference drivers can satisfy specified conditions; they are not learned planning or recovery results.
- **GPU qualification:** checks observed generation, grammar and memory behavior; it is not task competence.
- **Model task episodes:** measure success on the stated tasks and conditions, with their limited evaluation coverage.

An offline export marked `model_executed: false` describes the export operation, not whether its historical episode used a model.

## 3. Project trajectory and historical results

### Infrastructure and restricted execution

We established pinned model/tokenizer locks, manifests, source snapshots, private evaluation material, immutable artifact versions, episode journals, resource ledgers and browser-terminal Slurm submission. The shared scheduler guard inspects other GPU work and limits campaign concurrency.

CooperBench did not pass the required execution-isolation gate in the inspected environment. That gate remained in place. Active development moved to restricted SQLite artifacts, the labelled SILO adaptation, and then RepoRecourse. These tools are not an OS sandbox: workers do not execute arbitrary repository code or raw SQL. Optional SQL text is compiled into the existing approved representation before the fixed executor runs it.

### Earlier experiments

| Stage or condition | Recorded result | What it supports |
| --- | --- | --- |
| Numeric fixture campaigns | 32/32 clean/withholding; 32/32 clean/sabotage | Harness functionality on numeric diagnostics |
| Corrected SQLite arithmetic pilot | 32/32 | Fixture competence; no recovery success advantage |
| SILO original interface | 0/8 complete tasks; 101/480 values correct | Inadequate complete-task performance in this condition |
| SILO submitted-carry interface | 0/8; 101/480 values correct | No observed complete-success improvement |
| 4B synthetic SQL, no thinking | 0/4 | Tool construction/submission problems |
| 4B synthetic SQL, thinking | 1/4 | Most failures persisted |
| 4B synthetic SQL, constrained thinking | 1/4 | Better format control did not resolve task correctness |
| 27B constrained synthetic SQL | 4/4 | Basic competence on four synthetic probes |
| 27B categorized-feedback synthetic SQL | 4/4 | Feedback was unexercised; no feedback-benefit finding |
| Native 27B, 8K context | Two episodes unscored after context guard | Configuration failure, not scored task failure |
| Native 27B, 16K and 12 actions | 0/2 | Final artifacts not submitted |
| Earlier native 16K and 24 actions | 0/2 | Construction and semantic failures |
| Fresh matched JSON-tree arm | 0/2 | Current structured-interface control |
| Fresh matched SQL-text arm | 1/2 | Local interface improvement on the two solar tasks |
| SQL-text naming follow-up | 1/2 | Same success count |
| Synthetic aggregation diagnostic | 1/2 | Incorrect aggregation across independent detail joins |

The native solar query and view, and their joint pair, passed scripted reference validation, negative controls, reset and source-integrity checks. That established evaluation feasibility, not model competence. The SQL-text arm passed `solar_M_3`; `solar_2` remained unsuccessful. These were two repeatedly inspected development tasks in one database, not held-out benchmark evidence.

Offline inspection identified several distinct failure mechanisms: malformed actions, output/context limitations, unresolved columns, missing submissions, and incorrect result semantics. In the aggregation diagnostic, joining two detail tables multiplied rows before summation and counting. For one team, the stored answer was amount 50 and six notices instead of 25 and two. This supports a specific semantic diagnosis, not a universal explanation for every prior failure.

Historical costs also caution against treating larger budgets as a solution. The matched tree/text arms used 171,725 and 134,471 units of the old surrogate work measure respectively; the naming follow-up used 151,191 with the same 1/2 success count. These units cannot be directly compared with RepoRecourse's separate token and CPU accounting.

## 4. RepoRecourse implementation and v1 results

RepoRecourse separates task requirements, restricted tools, contributor faults, resource accounting and terminal evaluation from policy choice. Implemented components include:

- Data-product SQL artifacts and bounded API/schema/mapping artifacts.
- Publication, immutable versions, explicit bindings and consumer rebindings.
- Contributor-loss F, safe-artifact S and fixed-state R mechanisms, with distinct accounting.
- Scripted baseline drivers and authored outlines; selectors reject absent or incompatible measured costs.
- Public monitoring separate from hidden terminal correctness checks.
- Logical input/output token charging, reasoning counted once, separate CPU limits and uncertain-usage records.

Five initial tasks received CPU qualification with independent review still pending: Jaffle recorded payments, energy generation coverage, GitHub topics consumer, synthetic stock and synthetic nullable. Energy additionally has provider-license review constraints. These are a small draft inventory, not a broad reviewed benchmark.

| Real-model observation | Result | Resources and interpretation |
| --- | --- | --- |
| Initial Jaffle smoke, `855edc50…` | 0/1 | 18,302 tokens; semantic execution failures and an episode-closure defect during repair |
| Corrected Jaffle smoke, `b9492f90…` | 1/1; both obligations correct | 29,745 tokens; 404.791 CPU seconds; no public alarm or repair |
| Later Track F preparation, fresh clean condition | Failed; zero bindings | 49,219 tokens; 787.109 CPU seconds; loss branches remained unlaunched |

The corrected Jaffle run recovered from one primary SQL rejection before publication. It did not exercise post-loss repair. The runtime fix and public instructions changed together, so the before/after success is not a causal estimate of the termination fix alone.

## 5. RepoRecourse v0.2 implementation

The opt-in migration supports 2–8 logical identities on one frozen model and allocated GPU, while preserving legacy four-identity runs. It introduces pre-execution planning contracts, frozen-plan branching, task-balanced reporting and separate planning/recovery lanes. Planning is frozen before target selection, and its actual cost is charged logically in each end-to-end branch; physical reuse is reported separately.

Validation covers plan ownership, acyclicity, interfaces, output coverage, source/runtime hashes, branch resume and accounting. Track R remains equal-remaining and must not be pooled with equal-total comparisons. There is no controller training.

These implemented mechanisms do not imply that general model-generated planning campaigns are qualified. The real-model adapter added so far is a narrow clean synthetic-stock exception with fixed conditions, source-bound qualification, memory provenance and repeat-attempt guards.

### CPU reference matrix

| Dimension | Recorded coverage |
| --- | --- |
| Tasks | Synthetic stock and synthetic nullable |
| Pools | 2, 3, 4, 5, 6, 7, 8 |
| Organizations | Independent, shared, grouped, branch/rejoin |
| Conditions | 56 |
| Branches | 188 |
| Successful branches | 188/188 |
| Evidence type | Scripted reference only; no model executed |

The cluster also reported 21 focused v0.2 tests passing. This is evidence that the reference machinery works across the tested matrix, not 188 successful model episodes.

## 6. Pool 7 grammar and GPU qualification

Worker and planner grammar CPU qualifications passed at a 16,384-token context limit. GPU probes used one frozen Qwen3.5-27B bfloat16 model on an H100 PCIe, switching among seven worker identities and a planner identity.

| Probe | Result | Measured use | Limit |
| --- | --- | --- | --- |
| Normal decoding, two rounds across eight identities | 16/16 calls passed | 237,144 tokens; 760.892 seconds wall time; peak reserved 62,136,516,608 bytes | Outputs ended early; not full-output memory coverage |
| Forced full-budget geometry | 16/16 calls passed at 14,336 input plus 2,048 output tokens | 262,144 tokens; 2,159.126 seconds wall time; peak reserved 61,960,355,840 bytes | Forced inert outputs; not ordinary model reasoning or task competence |

Both reported zero uncertain tokens. These are positive observations for the tested sequence and geometry, not a universal worst-case memory guarantee or evidence of eight model instances.

An offline provenance audit found consistent supplied internal bindings, inventories, manifest/lock relationships and report accounting. The user confirmed scheduler completion. Hash consistency is an integrity check, not independent authentication of every remote event.

The frozen model revision is `fc05daec18b0a78c049392ed2e771dde82bdf654`. Reported dependencies include Torch 2.10.0+cu126, Transformers 5.3.0 and XGrammar 0.1.32. Optional compiler/validator versions remain separately pinned.

## 7. Latest stock competence result

Experiment: `853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06`.

| Measure | Result |
| --- | --- |
| Condition | Clean synthetic stock; authored independent plan |
| Episodes | 1 planned, 1 completed, 1 successful |
| Evaluation | Both obligations passed two terminal fixtures each |
| Available identities | 7 |
| Active identities | 2: w0 and w1 |
| Model calls | 3; all ended at EOS |
| Input / output tokens | 2,951 / 600 |
| Total tokens | 3,551 / 100,000 cap |
| Reasoning tokens | 429, already included in output tokens |
| Episode CPU | 39.115224506 / 1,200 seconds cap |
| Terminal evaluator CPU | 0.030292715 seconds, separately recorded |
| Uncertain usage / pending reservations | Zero |
| Failures / alarms / repair actions | Zero |
| Publications / bound outputs | 2 / 2 |
| Planning model executed | No |

The caps are uncalibrated engineering limits. This result does not supply a measured B0 calibration.

### Actual execution differed from the declared graph

The authored plan declared no dependency between the two units. In execution:

1. w0 read the tables and published `SELECT sku, qty FROM stock ORDER BY sku`.
2. w1 published `SELECT sku FROM stock_report WHERE qty = 0 ORDER BY sku`, explicitly binding w0's immutable version.

There were **zero declared edges and one realized binding edge**, from `stock_report` to `zero_report`. No explicit artifact-read action was needed: artifact metadata was visible in the worker observation, and the binding supplied the execution dependency.

Code review confirms that the current plan validates and schedules assignments but is not an access-control list. Runtime publication checks valid versions and safe executable artifacts without restricting bindings to declared `consumes`. Broader reads and metadata exposure also prevent an independence claim based solely on empty declared dependencies.

**Audit disposition:** preserve the successful score and current semantics. Label the outcome clean artifact production and cross-worker version reuse. It does not establish independent reconstruction, seven-active-worker competence, generated planning or recovery effectiveness. See the [detailed dependency audit](REPORECOURSE_V0_2.md#declared-versus-realized-dependencies-stock-trace-audit-2026-10-06).

## 8. Engineering issues resolved along the way

- Slurm relocated submitted scripts, breaking relative script paths; frozen-source wrapper invocation corrected the workflow.
- SQLite connections needed explicit closure to avoid temporary-directory cleanup failures.
- Assignment completion previously closed an entire episode; assignment-local termination and guards were added.
- Synthetic long-context prompt ambiguity caused a reasoning loop; the revised numbered-record probe passed, without changing historical results.
- SQL-text grammar controls exposed escaping/masking problems; qualification and frontend checks were kept separate.
- Pending Slurm arrays were returned as compressed IDs that `scontrol` rejected; array-expanded inspection now checks concrete task IDs while retaining campaign blocking.
- Immutable reports require new output paths rather than overwriting incomplete observations.

The latest recorded local regression run completed **341 tests: 323 passed and 18 skipped**, with no failures. Shell checks passed for ten files. Skips are not passes or GPU evidence.

## 9. Outstanding gates and scientific limitations

| Item | Current position |
| --- | --- |
| Scripted v0.2 reference execution | Passed the recorded two-family matrix |
| Pool 7 normal and forced-geometry probes | Passed the observed sequences |
| Clean synthetic-stock model competence | One successful episode, with two active workers and artifact reuse |
| Synthetic-nullable model competence | Pending its own reviewed exception and implementation |
| Declared versus realized graph reporting | Audit requirements recorded; automated conformance report not yet implemented |
| Model-generated planning comparisons | Not measured; general campaigns remain blocked |
| Recovery advantage under contributor loss | Not established |
| Compatible B0 and resource calibration | Pending; engineering caps are not calibration |
| Reviewed native task coverage and legal variation | Incomplete; draft qualifications do not remove review gates |
| Generalization across tasks, sources and seeds | Not established by these development observations |

Do not pool SILO, native SQLite, synthetic fixtures and RepoRecourse scores. Do not pool equal-total and equal-remaining lanes. Finite adapted evaluation is not full upstream benchmark equivalence. Repeatedly inspected tasks cannot support held-out claims.

## 10. Decisions for this review

The current evidence supports continuing careful engineering investigation, but it does not yet support the project-level effectiveness claim.

Before choosing another model run, resolve these questions:

1. **What is the planning treatment?** Common adaptive workers may revise dependencies after receiving a plan. That permits an end-to-end planner comparison, but not a claim that assigned topology alone caused an outcome.
2. **Do we need strict topology enforcement?** If yes, define a separate versioned condition covering bindings and information access, including explicit repair exceptions. Do not retrofit it onto historical scores.
3. **What is the next missing evidence?** An offline declared/realized graph report would expose deviations without another GPU run. Second-family competence, calibration and fault trials each need their own justified scope and gates.

No additional task, rerun, fault branch or planning campaign is authorized by this report. Historical scores and runtime behavior remain unchanged.

## 11. Evidence index

| Evidence | Identifier or repository record |
| --- | --- |
| Earlier consolidated results | [September 25 report](PROGRESS_REPORT_2026-09-25.md) |
| Protocol and lane definitions | [Research protocol](RESEARCH_PROTOCOL.md) |
| Current handoff and limitations | [Status](STATUS.md) |
| Migration, qualification and dependency audit | [RepoRecourse v0.2](REPORECOURSE_V0_2.md) |
| Corrected Jaffle clean | `b9492f9028928218e190cf0441956d681cecb524b824505d551047f55757a9f9` |
| Normal pool 7 probe | `78419528eb91d65c58517565ad196ff82c7f84f76a1e240c80ce7d4996c6cc79` |
| Forced geometry probe | `b67a0fa3e511f82a1f3120dedd70a3f6a06e34daca2dd9a4bbf8507d855c6939` |
| Latest stock competence | `853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06` |

This report adds documentation only and preserves the existing audit edits in the protocol, status and migration documents.
