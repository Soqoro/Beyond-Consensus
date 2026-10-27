# Beyond Consensus — Phase II Codex handoff, version 3.0

You are implementing the next phase of the Beyond Consensus research project in its existing repository. This is an implementation-and-CPU-validation task, NOT authorisation to run models or launch experiments.

## 0. Read, preserve, and report

First inspect the working tree, repository instructions (including any AGENTS.md/REVIEW.md), existing Phase I evaluators, tests, schemas, and model-run guards. Reuse correct existing components rather than creating a parallel framework. Preserve unrelated user changes and all released Phase I code/configuration/results. Do not modify the paper in this task.

Read these supplied sources when available:
- PHASE2_PLAN_V3.md and PILOT_MANIFEST_V3.yaml: controlling protocol; they supersede the v1/v2 planning files;
- beyond_consensus_audited.tex and beyond_consensus_audit_notes.md: model, exact theorem, and limitations;
- consolidated_results(1).md: reported n=2–4 evidence, not a substitute for missing raw graphs;
- original Phase I graphs, cost maps, queries and replay records discoverable in the repository.

Document source paths and hashes actually inspected. Do not invent a repository path, infer workload edges from names, reuse another project's budget/model, or claim unavailable source bindings passed. A missing input should block only the dependent evidence claim: proceed with independent local fixtures and list the missing binding.

Before editing, state a concise implementation plan. Build a focused vertical slice: exact allocation -> mock DAG execution -> all-owner physical replay -> honest cost/quality report. Extend the existing project rather than creating a production orchestration framework. Future calibration, attacks and statistical analysis are interface/protocol requirements here, not permission to implement and run a full campaign. At the end report actual changes, actual commands, actual results, skipped/unrun checks, and blockers. Missing model IDs or budget amounts do not block the mock implementation; they DO block real execution. Do not ask for deployment credentials to complete offline work.

## 1. Strict execution boundary

Allowed now: local code changes, local CPU tests, bounded synthetic solver timing at n=4–10, deterministic/seeded-stochastic mock execution, documentation, and a review bundle.

Forbidden now: remote API calls, local LLM inference, dataset/model downloads, GPU use, cluster submissions, training, paid smoke/pilot runs, commits, pushes, deleting/resetting user changes, and rewriting Phase I evidence. A configured API key is not permission. Do not call a live local model server either. Tests must use injected mocks and block outbound connections. Do not print secrets or include restricted dataset contents in reports.

Use the existing local-development -> user-reviewed Git transfer -> browser-accessed Linux Slurm workflow. Do not introduce PBS/qsub, SSH/SCP, multi-node execution, or one GPU per logical agent. Four concurrent GPUs is a future ceiling, not present execution permission. No cluster configuration is to be invented.

The delivered executable entry point must register mock backends only. A manifest edit, environment variable or forged approval flag must not activate a real backend in this handoff. Future adapters require separate implementation review and explicit stage authorisation. Define narrow interfaces or reuse dormant ones; do not build a provider gateway, live attacker, model server, cluster launcher, or general authorisation platform. Unit-test future guards with mocks, without claiming that Python flags provide an OS-level security boundary. Dependency installation may not fetch from the network; unavailable local dependencies are reported, not bypassed.

## 2. Fixed scientific contract

There are m predefined tasks in a fixed DAG H, with fixed positive rational estimated replay costs c_v and exactly n nonempty interchangeable owners. The primary regime is n <= m <= 2n and 1 <= |S_i| <= 2. The campaign range is n=4,...,10; small n is allowed in tests. Every operation must be required directly or as an ancestor of a required output. Reject unused padding; do not dynamically prune work after allocation.

For each task v, D+(v) includes v and its descendants. For ownership group S:

    F(S) = sum(c_x for x in union(D+(v) for v in S))

Count shared descendants once PER INCIDENT. R_i=F(S_i). Mean-first minimises (sum_i R_i, max_i R_i); worst-first minimises (max_i R_i, sum_i R_i). Report both in common (mean,max) order as well. Do not conflate those orderings or compare only selected graph IDs.

Ownership is a logical output-integrity fault domain. Workers use one fixed model/capability configuration and task-scoped roles. Do not compromise the shared model or global service and call it one-owner compromise. Task prompts/inputs/tools/cost rules cannot change with owner labels. No hidden owner memory; a task can resume after a different owner runs. For a->b->c with ownership {a,c}/{b}, scheduling is valid at task level even though contracting owners creates a cycle.

Planner, scheduler, injector, ledger and offline evaluator are protected infrastructure; count their costs separately. Any required model-generated synthesis/critique is a real task, not an uncounted extra agent. Do not promote solution-bearing planner outputs into unpriced trusted workflow inputs. This evaluates allocation of logical fault domains over task-isolated workers, not an unrestricted stateful MAS or a general topology optimiser.

Freeze one allocation per workflow/n/estimator/method/allocation-seed condition BEFORE any evaluation trace. Reuse it across execution repetitions: never redraw the random baseline, recall the LLM allocator, rerun a stochastic tie-break, or refit costs for each repeat. Identify a partition by sorted task groups and identify an owner by its sorted member-task IDs within that partition. A changed partition creates a new condition. If allocation variability is studied later, keep a separate allocation-draw index; compute each draw's owner mean/max before aggregating draws. Never average unrelated agent_0 groups and call the result a worst-owner mean. Estimator/graph/config hashes accompany each condition; owner names are display labels.

## 3. Exact ownership solver

Integrate or implement the real weighted-matching reduction, not an enumeration disguised as the scalable solver:

1. Validate the task DAG, task coverage, positive finite rational weights, n/m bounds, objective and optional incident budget B.
2. Compute recovery closures and all singleton/pair costs.
3. Add d=2n-m virtual vertices. Real-real edge (u,v) has weight F({u,v}); real-virtual edge has F({u}); virtual-virtual edges are forbidden.
4. With optional B, retain only edges whose weight is <=B. B=0 with positive costs must return infeasible, not a partial answer.
5. A candidate is feasible only if every vertex is covered by exactly n matching edges. A maximum-cardinality result may be nonperfect: explicitly reject it.
6. Mean-first: obtain the minimum feasible total S*. Search distinct retained edge weights for the smallest threshold under which a perfect matching with minimum total S* still exists, then return such a matching.
7. Worst-first: find the smallest edge-weight threshold admitting a perfect matching, then minimise total weight inside that threshold.
8. Decode exactly m-n pairs and 2n-m singletons. Canonicalise unlabelled groups for reproducible recording; tie behaviour may follow stable graph construction and a pinned solver, but never alter the objective with arbitrary floating-point epsilons.

Use exact arithmetic: parse decimal inputs without binary-float conversion, scale rational weights and thresholds to common integer units when required, and record the conversion. Do not claim exact real costs from rounded estimates. Pin/record the installed matching API version. Do not add undocumented compatibility restrictions or replace general matching with a bipartite assignment solver.

Return the allocation, per-owner closure and cost, exact sum/max, objective, feasibility/budget status, cost-model identifier, and preprocessing/solve timings. With point estimates, infeasible means infeasible for the supplied estimates, not proof of real recovery-budget impossibility. The optional mathematical B is distinct from mandatory execution spending caps. Keep solver B tests, but require predicted_incident_budget=null in the current comparative run compiler. A fair budget-constrained comparison of all baselines is not yet specified. Reporting restoration against a common expenditure threshold does not change that rule. Do not filter matching alone by B, or interpret unit-weight ablation scores as a currency budget.

Build an independent brute-force reference for bounded small cases. It must enumerate ownership partitions and evaluate closure unions independently, not invoke the production matcher or merely compare the production function against itself. Compare optimal metric pairs, not owner labels. Test original K=2 cases only where actual source graphs/costs are present. Report source-bound, synthetic, and unbound cases separately.

## 4. Baselines and fair inputs

Implement local random_valid, direct_workload_balance, greedy_mean, greedy_worst, matching_mean, matching_worst, matching_mean_unit and matching_worst_unit.

Uniform random: shuffle real tasks uniformly, pair the first 2(m-n), leave the rest single, and canonicalise. The draw is frozen across worker repetitions. Direct balance minimises maximum sum of OWNED estimated replay costs; its total sum is invariant. Solve that bottleneck exactly with singleton/pair sums and a stable tie rule that does not consult descendant overlap. Label it own-work-replay balancing, not measured forward-work or latency balancing. Greedy starts from the same frozen random allocation, scores complete recovery unions, selects the best strict lexicographic improving valid transfer/exchange, and stops after 20 accepted moves or no improvement. No hidden matching fallback. Record all method outputs before running workers.

Define LLM allocation prompt/response validation and test it using recorded/synthetic replies only. Give it the fixed tasks, graph, costs, complete singleton/pair recovery-score table, target objective and cap. Allow at most one structural correction in the future protocol; invalid output remains an invalid-plan outcome. Never silently replace it with our solution. Preserve allocation cost and attempts separately from task execution.

Unit-weight variants differ only in optimiser weights; measured execution still uses the same heterogeneous worker. The real main grid has eight outputs. The two unit-weight outputs form an explicit preselected ablation subset, not an unbudgeted addition or an omitted promised experiment.

## 5. Minimal task/artifact runtime

Use typed, validated records consistent with the repository for workflow, task, ownership, artifact version, call usage, allocation request, incident and outcome. Schemas must capture declared parents, allowed immutable inputs, required outputs, task-level limits, task/model/tool configuration, provenance, cost unit and relevant version IDs.

Implement a stable topological scheduler and protected artifact access. Workers can read only declared parents and allowlisted immutable sources. Reject undeclared reads; do not repair the task DAG using test-run traces and continue claiming a frozen comparison. Per-task context contains neither gold labels, method names, arbitrary owner names, nor other co-owned task history.

Use deterministic and seeded-stochastic mock workers whose usage is explicitly synthetic. A mock worker must actually compute from its input artifacts, so taint propagation is testable. Do not count a fixture's invented tokens as measured LLM usage. Keep the executor interface narrow; no full benchmark framework or model-server stack is required now.

The primary controlled design supports one clean trace per workflow/executor/replicate shared across allocations only after verifying payload, schedule and input-contract invariance. This is a common-baseline experimental design, not proof that independent stochastic runs produce identical outputs. All allocations and estimates must be committed before that clean run. Preserve original task-level provenance and attach separate immutable ownership bindings; do not mutate the shared trace when rebinding. Owner IDs stay in protected metadata, not prompts. An invariance failure blocks shared-trace mode, not a silent fallback.

Distinguish random streams from reset state. Clean mock streams use workflow/executor/task/phase/repetition/attempt. Replay mock streams additionally use canonical partition and compromised task-group identity. Different incident/repetition keys cannot silently share one worker stream; arbitrary owner names, method order and mutable loop RNG are not identities. Fixed configurations must be resumable with stable logical trial IDs and append-only physical attempts. Provider seeds later are recorded, not treated as guarantees of determinism/independence. A sham/attack common-random-number policy is allowed only when explicitly specified; keep it separate from ordinary replay keys.

Count physical clean execution once in research accounting, but charge one full clean execution to each counterfactual deployment. Any identical-partition execution reuse must be explicit and is not an independent replicate.

## 6. Independent invalidation and actual replay

For every selected allocation and EVERY owner independently:
- Fork the original complete clean snapshot, never the prior incident's repaired state.
- Compute D_i from every task of the selected owner plus descendants.
- Delete/invalidate all D_i outputs and stale context; retain trusted artifacts outside D_i.
- Re-execute affected operations in task order using fresh trusted workers.
- Deny access to the clean outputs of affected tasks, including application caches, paths, and hidden message history.
- Evaluate required outputs with an isolated evaluator and record all operations/costs.

Mock replay must invoke workers again; it cannot copy saved clean answers and claim reconstruction. Count an affected task once even when two compromised tasks reach it. An incomplete clean graph has no complete-work snapshot: retain its planned incidents as no_clean_snapshot, not zero-cost successful repairs. A complete-but-incorrect clean trace remains flagged; do not call its later correction restoration from a previously correct result.

All-owner sweeps are alternative single-owner incidents, not sequential cumulative compromises. A stopped partial sweep cannot yield a claimed full worst-owner value.

Compile the entire logical slot registry before execution. Freeze a seeded balanced/interleaved method order and randomised owner order, independent of predicted gain or observed cost. Stable topological task ordering is separate. If a resource cap halts the campaign, retain remaining slots as not_run_due_campaign_stop; do not execute whichever trials are cheapest or replace failed cases. Resume the same frozen condition only. A configured infrastructure retry is another billed attempt of the same trial; semantic/schema failure is not permission to regenerate until success. Interrupted or duplicate invocations must not overwrite earlier events.

## 7. Mock corruption and reset tests only

Implement a bounded owner-output mutation hook and mock tests, not a live adversarial LLM campaign. A future real attack fork occurs before the target owner's first task. Mutate only that owner's artifacts, execute downstream tasks on them, and detect at completion or a predefined terminal failure/resource boundary. No label-informed attacks, scheduler/evaluator modification, or retries until damage occurs.

Add an unchanged-output sham branch from the same checkpoint. Clean-trace sham reuse requires matching provenance/execution conditions; otherwise it is a separate continuation. Record direct-output exposure separately: corruption of a terminal required output is valid without downstream consumers. Do not exclude terminal owners under a blanket downstream-consumption requirement.

Future attack budgets are equal total per owner incident with per-task limits, not automatically doubled for two-task owners. Record attempted application, observed reads/direct-output exposure, pre-repair validity, post-repair validity, and costs. For an abort, let E contain tasks with schema-valid committed artifacts at detection. Preserve E minus D_i and execute U = D_i union (V minus E) with trusted workers. D_i intersect E is reconstruction; V minus E is missing completion work, including unaffected missing tasks. A failed attempted task with no committed artifact is missing. Charge every previous and new attempt; do not equate U's bill with the completed-work theorem when E!=V. Test this exact distinction rather than merely attaching a completion label to closure-only replay.

## 8. Usage, failure, and analysis semantics

Separate actual attempted spend from the cost of a COMPLETE reconstruction. Keep execution completion, semantic validity, and usage completeness as separate fields. Record separate execution/coverage, schema, semantic-validity and accounting axes. Execution reasons include completed, task_error, resource_stopped, infrastructure_failure, no_clean_snapshot, invalid_allocation, not_run_due_campaign_stop and protocol_violation; semantic validity is valid/invalid/unknown; usage is complete/pending/missing. Do not collapse unknown grade, invalid schema, an unstarted trial, and a completed wrong answer into one result.

A complete but semantically wrong repair has a known full cost and failed validity. An interrupted repair has partial observed spend but unknown full cost. Missing usage is unknown, not zero. Never replace missing full costs with zero, partial spend, an arbitrary cap or infinity. Keep every planned incident and failure reason. Unknown actual usage must remain visibly unknown even if a conservative budget reservation exists.

For each fixed partition with a complete balanced owner-by-execution-repeat matrix, compute mean of owner means, maximum of owner means, and largest observed bill separately. Reject a summary that mixes partitions, estimator versions, cost units, executor conditions, incomplete costs or duplicate logical slots. Reorder display labels by canonical owner membership first. A partial matrix has an incomplete full-cost summary; observed subsets are diagnostics only.

Objective-matched cost comparisons use the SAME common-complete source conditions for both methods, with prespecified source weights, exclusions and coverage. Separate complete subsets are not comparable. Even the common-complete result is conditional evidence when failure-dependent missingness occurs; do not infer unconditional population savings. Retain all planned outcomes and complete-invalid costs; do not filter merely on semantic success.

Reporting budget status is within/exceeded/unknown/not_applicable. Known full measured cost <=threshold is within; known spend >threshold establishes exceeded; unresolved cost is unknown, not zero or within. For restoration-under-budget, a completed valid result with known within-budget spend passes; a known failed attempted restoration or known overrun fails; absent execution/grade/usage remains unknown unless failure is already established. Invalid allocations are known nondeployments in an intention-to-plan endpoint, not zero-cost repairs. Not-run-due-campaign-stop is unobserved, not a semantic mistake. Report pass/fail/unknown and coverage by cause. Any [passes/N,(passes+unknown)/N] bounds are missingness identification bounds, not statistical confidence intervals. Compute such endpoints within each workflow/allocation first, then aggregate using the frozen source/domain weights; do not turn more owner incidents into more independent problems.

Keep independent source problems as statistical clusters; plans/counts/owners/repeats are nested, not independent samples. Implement deterministic numeric summaries and completeness checks now. Do not invent confidence intervals, p-values, main sample sizes, non-inferiority margins or observed-max guarantees before the analysis specification is frozen. A bounded-budget quality-cost endpoint is separate from the uncensored reconstruction-cost estimand.

Maintain one event ledger with separate research, one-deployment and reconstruction views. Include failed attempts and retries, expose cached/uncached fields without double counting, and do not mix local tokens/GPU-seconds with API currency. Record synthetic usage as synthetic. Never estimate invisible provider tokens from output text length and label them billed usage.

Future cost guards must reserve allowed call costs atomically before calls and retain uncertain reservations until resolved. Test overspend/concurrency/unknown-usage behaviour using mocks only. Undefined prices, limits, or approvals must fail closed. No real execution is provided in this handoff, regardless of any approval flags. Test future preflight checks using mock authorisation records. Do not turn this requirement into an elaborate security subsystem or claim it replaces external execution control.

## 9. Data adapters, calibration and staged gates

At this stage, implement local-only input/evaluator boundaries using synthetic fixtures shaped like MATH-500, GPQA and GAIA records. Do not download benchmarks. Use allowlists: no math solutions/answers, no GPQA Correct Answer field name/explanation or private answer-position mapping, no GAIA answers/annotated steps in model payloads. GPQA choice order is deterministically permuted once per source problem and shared across methods. Keep gated data out of public artifacts. ARC-100 stays disabled, identity unresolved.

Split and deduplicate by original source problem. Calibration uses development only, a frozen uniform random collection allocation by default, and does not require an already-fitted estimator. A direct-cost collection policy needs its own declared ex-ante weights; do not create a circular dependency. Now implement the supplied-cost/estimator interface and leakage tests, not production fitting on absent data. Pilot uses a frozen development estimator per declared condition. Main execution requires the final estimator, dataset/split/sample manifests, repetitions, quality criterion and statistical plan. Corruption requires its own attack/sham policy and owner budget; do not require those to start clean calibration. No main data can be used to tune estimates or screen for optimiser advantage.

Implement a stage-specific preflight validator and use PILOT_MANIFEST_V3.yaml as a disabled template. Preserve 4–10 agents only when eligible. Keep the three-workflow n=4 smoke test. The revised 12-workflow pilot provisionally uses four meaningful eligible workflows each at n=4,7,10, six outputs, and two worker repetitions, with frozen allocations. This guards against extrapolating an all-four-agent calibration to ten-agent graphs. Cover larger task/closure/context sizes or report unsupported scope; never pad to fulfil a quota. The change increases pilot repairs and is NOT spending authorisation.

Illustrative shared-clean counts are smoke 3+24=27; revised pilot 24+1008=1032; main 180+10080=10260 (60 problems, eight outputs, three repeats, mean n=7). A 12-problem two-output unit-cost subset at mean n=7 and three repeats adds 504 repairs if clean traces are reused. These counts exclude calibration, attacks, retries and other extras. The actual compiler expands explicit m/n/partition/repetition records; an average-n estimate or provisional count cannot launch a grid. Each planned slot has a stable ID and initial pending status, even if the corresponding allocator later fails.

## 10. Mandatory acceptance tests

Provide tests for:
1. Both lexicographic objectives against independent partition enumeration, including tied optima and arbitrary task labels.
2. n<=m<=2n boundaries, exact singles/pairs, rational weights, virtual-virtual prohibition, perfect cardinality, budget below/equal/above threshold, invalid inputs.
3. Source-bound Phase I agreement when raw evidence exists; missing raw graphs remain visibly unbound.
4. Shared descendants counted once; independent-task mean invariance; m=n no-choice control; nested-closure lower-bound cases.
5. Uniform random partition multiplicities on a tiny case; direct-balance invariant-sum issue; no exact fallback in greedy/LLM validation.
6. Owner-permutation payload invariance; interleaved ownership of a task chain; denial of hidden memory and undeclared artifact reads.
7. Fresh physical replay, unchanged baseline snapshot hashes, no cross-incident leakage, exactly n incident slots, and common-clean traces not exposed to allocators.
8. Internal taint consumed by a downstream mock, terminal-output corruption, sham branch, early abort and separately priced completion work, injector unable to mutate protected state.
9. Completed-invalid versus interrupted-unknown costs, incomplete owner matrices, invalid allocations, missing provider usage, no false cheap-failure win.
10. Gold-field isolation and GPQA option permutation on synthetic data; estimator cannot read held-out runtime artifacts.
11. Correct physical/deployment ledger reuse, bounded retries, atomic mock budget reservations, and remote/model/download/GPU/submission guards.
12. Stage-gate dependency order: calibration can be configured before a fitted estimator, while main cannot; no inference/spending actually occurs.
13. Frozen partition across repeats, display-owner relabelling invariance, rejection of mixed partitions/duplicate slots/config drift, and separate allocation-draw versus worker-repeat indexes.
14. Distinct replay stream IDs for different incidents/repeats; declared sham coupling; immutable provenance with ownership views; restart/resume does not overwrite or double count physical attempts.
15. Paired common-complete cohort versus biased method-specific filtering; known fail versus unknown budget/grade; not-run versus executed failure; missingness bounds are not confidence intervals.
16. Aborted corruption with missing tasks OUTSIDE D_i: execute their completion as well as reconstructing committed affected outputs; preserve the correct unaffected committed artifacts.
17. Revised pilot-size arithmetic/eligibility, scale-coverage gate, null comparative B, and identical price/model/task-limit settings in each paired comparison.
18. Outcome-blind trial scheduling, remaining slots preserved on halt, unchanged allocations on resume, and no semantic/schema retry-until-success.

Set bounded CPU test/timing limits. Heavy verification is not a reason to start cluster jobs. Existing unavailable dependencies or raw inputs must be listed honestly; do not mark skipped work as passed.

## 11. Deliverables and stop point

Produce:
- A concise implementation plan and inventory of reused components.
- The focused implementation, tests, mock fixtures, and disabled versioned manifest/schema.
- Independent exactness and source-binding reports, with counts actually run and test limitations.
- A mock end-to-end demonstration showing all-owner costs, validity/completeness statuses, and the three accounting views; label all data synthetic.
- An audit log of observed commands, exit statuses, files changed, dependency versions and source/code hashes; protect secrets.
- A README with exact local verification commands and the next calibration-readiness requirements.
- A final report separating implemented/tested, implemented/not tested, blocked/missing, and future work. Distinguish pass counts from independence or statistical power. Keep result verification within the repository-specific acceptance scope actually run.

Use local CPU/mock examples to demonstrate the scientific invariants, not to claim measured recovery benefits. Keep scripts small and portable. Extra source-binding or production features that cannot be completed are explicit gaps, not reasons to broaden scope or fabricate inputs.

Do not produce fabricated real benchmark outcomes, forecasts based on invented token rates, or a claim that all Phase I bindings passed when only synthetic tests ran. Do not launch paid smoke runs. Stop after the local CPU/mock review bundle is ready; the user will review before Git transfer and any separately authorised model execution.
