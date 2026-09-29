# Codex implementation prompt — RepoRecourse v0.2 update

Use this prompt in the existing Beyond Consensus / RepoRecourse repository. Supply `reporecourse_environment_design_v0_2.md` alongside it. This is an implementation request, not authorization to submit experiments or train a model.

```text
Implement RepoRecourse v0.2 in the EXISTING Beyond Consensus / RepoRecourse
repository. Read reporecourse_environment_design_v0_2.md when available.

The main scientific formulation is now fixed:

A pre-execution planner receives a public task, variable-sized worker pool,
resource limits, and declared threat. It proposes a division of labour.
Frozen workers execute it. The SAME monitor and strong JIT recovery backend
handle observed problems across all planners.

Beyond Consensus will be a learned planning adapter evaluated through this
interface. Do NOT turn this update into training a post-failure controller.
RepoRecourse remains usable without importing the Beyond Consensus method.

Implement variable-sized teams, honest planning/evaluation modes, shared
recovery, cost-fair branching, task-balanced scoring, and outcome-data export.
Reuse the current restricted SQL/schema runtime and Slurm infrastructure.

Inspect first, write a brief milestone plan, then implement and run available
local tests. Deliver executable vertical slices, not only schemas or a scaffold.
Do not fabricate qualified tasks, calibrated costs, model runs, or results.


1. INSPECT AND MAKE AN INCREMENTAL MIGRATION

Read AGENTS.md, the v0.2 design, current status/audits, the task registry,
RepoRecourse runner, plan schemas/selectors, worker and assignment state,
F/S/R hooks, JIT, provenance, budgets, scorers, exports, and Slurm scripts.
Inspect git status and preserve unrelated or uncommitted user changes.

Map the v0.2 requirements to existing code before editing. Identify actual
hardcoded-four assumptions and what already supports variable identities.
Do not create a second scheduler, model stager, artifact store, or ledger.

The last supplied audit recorded one clean Jaffle success, three
source-grounded draft tasks, two synthetic controls, and unresolved review,
calibration, and real-model recovery gates. Check for newer local records.
Do not assume the subsequent three-episode Track-F experiment has run or
passed. Preserve all old results and their evidence classifications.

Use new schema/protocol versions for changed behavior. Old four-identity
manifests/results must remain readable with their historical meanings.
Do not silently migrate an active experiment, reinterpret its budget, or
resume a completed failure under new code.

If the design file is absent, record that fact; this prompt restates the
required update. For genuinely underspecified semantics, document a bounded
implementation choice and its compatibility consequences. Do not silently
broaden the research claim or introduce a new task/attack assumption.

Keep a concise design-to-code migration/status document. Avoid duplicating
large runbooks instead of implementing missing behavior.


2. PRESERVE THE EXECUTION AND AUTHORIZATION BOUNDARIES

Workflow remains local development/tests -> user-reviewed GitHub push ->
cluster browser-terminal pull -> user-triggered Slurm jobs.

No SSH/SCP, tunnels, Colab, rented/cloud compute, PBS, Redis, external model
services, container workarounds, or arbitrary repository-code execution.

Use the existing frozen Qwen3.5-27B BF16 worker profile and actual locks.
The last reported revision is fc05daec18b0a78c049392ed2e771dde82bdf654;
verify rather than replacing an existing lock by assumption.

One allocated GPU serves the logical execution-worker contexts in a shard.
Require the existing qualified full 80-GB-class configuration for that model.
Respect CUDA_VISIBLE_DEVICES. No silent quantization, CPU offload, smaller
model, or unallocated multi-GPU fallback.

Preserve the shared campaign guard: at most FOUR physical GPUs concurrently,
with one concurrent shard by default during qualification. Eight logical
workers do not authorize eight GPUs or eight model copies.

Authorized here: local changes, CPU/mock/reference tests using available
materials, read-only inspection, and manifest/submission dry runs. Small
public documentation inspection is allowed when necessary for an actual
implementation detail; pin any changed dependency explicitly.

Not automatically authorized: scheduler submissions, GPU generation,
model/database downloads, commits/pushes, dataset-access messages, system
installations, RL/SFT training, simulator fitting, large task harvesting,
adaptive attack search, or a full benchmark campaign.

Do not promote pending source/license/independent-review states to approved.
Keep existing narrowly scoped engineering exceptions narrow. This update is
not an allow_unreviewed/force_run switch for new pools, tasks, or policies.
Missing external materials block the affected execution gate, not all local
software work.


3. SEPARATE TASKS, EXPERIMENT SETTINGS, PLANS, AND EPISODES

Retain or adapt the following distinct records; suggested names need not
replace established naming conventions:

Task:
  immutable sources, public request, terminal obligations, supported tools,
  public checks, private evaluator binding, grounding label, source group,
  semantic/review qualification, and version.

Experiment configuration:
  worker pool/model, planner, planning lane, active-count mode, budget,
  threat/target rule, monitor, recovery backend, scheduler, and seed streams.

Work plan:
  units, artifact interfaces, dependency edges, ownership, primary readiness/
  schedule, and optional resource allocation.

Episode/branch:
  a frozen task/config/initial-plan identity, selected intervention,
  execution state, resource ledger, trace, and terminal status.

Worker-pool size is NOT a task requirement. The request defines what must be
produced, not a universal list of internal steps or an obligatory topology.

Keep the two existing families: data-product artifacts and API/schema/mapping
artifacts. Preserve their public semantics, private tests, and safe tools.
Do not add meaningless outputs or relays to make a task use more agents.

Every plan must cover the same terminal job. A lost worker never removes
its obligation from the evaluator. Structural plan validity does not prove
semantic correctness; only final behavior is scored.

Keep author witness implementations private. Supplied outlines are disclosed
only in the explicitly authored-catalog lane and equally to all selectors.


4. MAKE WORKER POOLS CONFIGURABLE FROM 2 THROUGH 8

Remove hardcoded-four assumptions from:
- Schemas and generated action/plan grammars.
- Worker registry, ownership validation, contexts, and scheduling.
- Fault eligibility, persistent status, alarms, and replacement assignment.
- Checkpoint/resume, reporting, metrics, and trajectory serialization.
- Model-call dispatch and runtime resource planning.

Support every integer N_pool in [2, 8], including 7. Keep the legacy default
of four for existing configurations. Preserve a separately labelled clean
solo utility lane rather than forcing it into the multi-contributor track.

Changed plan/action grammars require fresh qualification with the actual
tokenizer and schema. If a grammar depends on the pool registry, include
that registry in its cache/approval key; a four-ID grammar approval cannot
authorize w7. Keep qualified legacy grammars for legacy runs.

Resolve identifiers against the configured registry; do not infer availability
or eligibility from fixed positions or a constant list of w0..w3.

Record separately:
- N_pool: identities available for the episode.
- K_primary_planned: identities assigned meaningful initial work.
- K_primary_observed: identities that actually performed primary work.
- K_total_observed: identities that performed any work, including recovery.
- Per-identity assignments, resource use, and workload concentration.

Define contribution events explicitly. Do not require successful publication
for a worker to count as attempted work: a contributor whose publication is
withheld must not disappear from the exposure record.

Support two modes:

adaptive_size:
  The planner can use fewer than N_pool. A one-primary-worker grouped plan is
  allowed only where the track permits it and is labelled as concentration.
  Idle identities provide no prepaid knowledge or free work.

matched_primary_count:
  Validate a declared planned primary count and meaningful assignments.
  Log actual deviations caused by failure/execution separately. Do not
  retroactively exclude a faulted branch because the fault prevented one
  planned contributor from acting.

Creating an unused identity does not incur an invented token fee. Its actual
reads, prompts, generation, and checks cost resources when performed.
A finished assignment does not permanently retire an otherwise eligible
worker: with only two identities, the survivor may need to do several units.

Keep assignment completion distinct from episode completion. Loss persists
across retry, reset, and resume. There is no extra always-honest identity
outside the configured pool.

Time-share one model explicitly. Preserve context isolation and account for
re-prefill/cache behavior. Do not assume that keeping eight full KV caches
resident is required or automatically fits. Record the actual memory policy
and qualify it before GPU use; never hide truncation or claim simulated
logical parallelism as a physical speedup.


5. IMPLEMENT THE THREE PLANNING/EVALUATION LANES

A. OPEN PLANNING — MAIN PLANNING-ADAPTER LANE

A planner receives only:
  public task/source access, allowed tools, available workers, budgets,
  declared threat class, and the common recovery contract.

It must not see the future selected fault identity, hidden evaluator,
reference programs, author witness plans, successful prior test solutions,
or eventual worker errors/outcomes.

Implement a bounded plan-generation/revision loop through the existing model
backend. Charge source reads, input/output tokens, and failed revisions.
Provide an actual frozen prompted-planner adapter, not an assumed-success
stub. Local tests use a labelled scripted planner; real generation remains
user-triggered.

The initial planner stops after the plan is validated and frozen. During
execution, all runtime reallocation goes through the common JIT backend.
No method-specific hidden recovery calls in the main planning scoreboard.
A combined custom-plan/custom-recovery mode, if present, must be separate.

Plans contain bounded subtask instructions/interfaces, not trusted final
artifacts emitted by an unattackable planner. Bound and record planner-to-
worker payloads, forbid direct final-artifact publication by the planner,
and expose content for audit. Do not claim a syntax check can prove that
arbitrary prose contains no solution information.

B. SHARED-CATALOG SELECTION

Support authored outlines and model-generated catalogs as separately labelled
catalog sources. Nominal and recovery-aware selectors receive the SAME
candidate set, public information, and JIT contract.

Private witness programs and private witness costs are not silently supplied
with outlines. Outcomes from hidden tests cannot select a deployment plan.

If catalog generation is physically reused, charge its logical generation
work to each evaluated episode. Report this reuse separately.

C. FIXED-PLAN RECOVERY

Allow a common initial plan and, for Track R, a common incident snapshot,
while varying recovery policy. Clearly distinguish this from the main
pre-execution-planner comparison and from equal-total-cost evaluation.

Do not require all three lanes to instantiate a Beyond Consensus-specific
recovery-route representation. A third-party planner/policy should run via
public interfaces without importing the proposed method.


6. VALIDATE AND EXECUTE MEANINGFUL WORK GRAPHS

Use an initially acyclic artifact dependency graph with a configurable,
versioned default cap of 24 declared units. Iterative corrections create
new artifact versions; they do not silently mutate the initial DAG.

Validate:
- Unique IDs, existing owners, legal source access, and bounded payloads.
- Declared producers/consumers and compatible public artifact interfaces.
- All original terminal obligations covered without illegal duplicate binds.
- DAG readiness and bounded scheduling.
- Pool/primary-count restrictions and resource-allocation format.
- No privileged final-answer creation or arbitrary executable code.

After the common charged revision allowance, an invalid model plan is an
observed planner failure. Do not silently repair its intended meaning.
Distinguish that from an unqualified task or broken deployment prerequisite.

Separate three structures:
1. Required final outcomes/compatibility rules.
2. Planned units, assignments, and dependencies.
3. Observed artifact-version and message provenance.

An undeclared read enlarges observed dependencies. A read edge signals possible
influence, not automatic semantic failure. The evaluator must not mark all
descendants wrong or force expensive LLM regeneration.

Keep program artifacts, materialized results, and input-binding versions
separate. Test that a repaired helper can be explicitly rebound and unchanged
consumer programs reexecuted, producing new results while history stays intact.

Selected plans must drive actual execution, not just a reported diagram over
the same fixed trace. Reuse the deterministic scheduler with a versioned
ready-unit tie-break rule. Keep the communication bus fixed across plans.

Provide effective-plan descriptors: unit/dependency counts, depth, sharing,
ownership concentration, and motif annotations where justified.
Do not count owner renaming, repeated no-work relays, or backup masks as new
semantic decompositions. Structural equivalence detection must state its
limits; it is not a general semantic-equivalence oracle.

For CPU fixtures, exercise independent, shared, grouped, and at least one
branch/rejoin organization with genuinely distinct work. Include cases where
shared reexecution is cheap and ordinary/JIT strategies win.

For the existing Jaffle request, preserve customer_summary and method_summary.
Qualify candidate independent/shared/grouped outlines against its actual
recorded-payment contract; do not invent refund or unpaid-order semantics.
Do not inflate it to eight primary workers just to match a pool size.


7. FIX THE JIT CONTRACT ACROSS ALL MAIN PLANNER COMPARISONS

Reuse and explicitly version the common monitor/JIT implementation:
code, prompts, worker checkpoint, decoder, source access, retry bounds,
public checks, scheduling, and resource rules.

It must support, where the task allows:
- Identifying missing obligations or public suspicion.
- Excluding announced-unavailable or policy-quarantined identities.
- Inspecting actual artifact/message lineage.
- Preserving unaffected published work.
- Rebinding/revalidating/reexecuting intact consumers.
- Reassigning/rebuilding missing units from original permitted sources.
- Bypassing a failed helper to reconstruct a required terminal output.
- Rechecking and explicitly binding actual chosen outputs.

If the existing JIT lacks a listed capability, document and test a bounded
shared extension. Do not give it only to Beyond Consensus or silently claim
unsupported behavior.

A deterministic scaffold plus frozen charged LLM decisions is acceptable.
It is fallible, not an optimal repair oracle.

In semantic sabotage, it sees public checks and suspicions, not true
compromise labels. Use availability, quarantine, and check-status fields
rather than labelling all nonattacked workers as known semantically honest.

All policies may perform the same reading, indexing, or outlining after an
alarm and retain unspent budget. No special cold-repair penalty, disappearing
source, or forced standby preparation is introduced.

Record optional reserve decisions separately from recovery capabilities.
For decomposition-isolation experiments hold the reserve rule fixed. If
reserve is also optimized, label that joint treatment instead of attributing
all gains to the graph.

Do not train or retune JIT in this update. Initial learned-planner training
will be a later phase after task/organization measurements are adequate.


8. MAKE FAULTS FAIR FOR VARIABLE COUNTS AND PLANS

Select the fault after the initial plan is frozen, using an independently
seeded declared policy. The planner knows the threat class, not the draw.

Define eligibility from meaningful planned execution contributors, including
intermediate producers. Do not sample unused pool slots. Retain planned and
realized eligibility/target coverage so withheld contributions remain visible.

Support seeded uniform eligible-target sampling and bounded all-eligible-
identity enumeration for Track F. Plan-aware attack hooks may use permitted
public plan/context information. Do not select targets using hidden outcomes.

A target that never reaches the event stays a nontriggered condition with a
reason. Do not replace it with a more successful attack or discard its row.

Preserve exact threat distinctions:

F: announced fail-stop at a predeclared outward publication/handoff event.
   Withhold only the new contribution under that retention rule. Existing
   published artifacts remain. Permanently stop that identity. Announce
   unavailability, never a replacement answer.

S: persistent semantic contributor control through permitted messages and
   artifact actions, including intermediate work. Keep source/evaluator/
   budget/logging integrity protected. Do not reveal coalition truth to the
   practical monitor. Preserve one-shot tampering as a separate mode.

R: same primary plan/state/fault/localization alarm for repair diagnostics.
   No corrected artifacts or hidden tests. Equal remaining allowance is
   separately labelled from equal total cost.

Reuse existing safe fault hooks. Add variable-count coverage, not a new attack
search system. Unsupported real-model S behavior remains a readiness blocker,
not a stub with fabricated outcomes. F alone is availability evidence, not
covert adversarial-robustness evidence.

Compromise targets an identity and all its permitted work, not one graph unit.
Splitting a unit does not reduce the identity's intervention scope. No fifth
(or ninth) free replacement appears, and reset never restores honesty.

Report fault count, eligible contributors, and fault fraction separately.
Do not silently mix fixed-one-fault and equal-fraction experiments.

Test publication atomicity so a withheld payload cannot be recovered through
a preview/alternate artifact API or selected by hidden grading. Preserve
legitimately published earlier work and all original obligations.


9. FREEZE PLANS AND BRANCH WITHOUT FUTURE-INFORMATION LEAKAGE

Create distinct identifiers for base task, planner input, planning attempt,
frozen plan, execution branch, and retry attempt. Preserve stage provenance.

Generate one plan for a given task/pool/budget/planner-seed/threat profile
before exposing any realized fault. That plan may be reused for matched clean,
F, and S branches with the same declared initial threat information.

Never run the clean branch first, learn its answer or failure pattern, then
regenerate a better plan for the attacked branch.

Each end-to-end branch pays its share as though its plan-generation calls
were performed for that deployment. Record immutable planning events and
logical charges, plus physical cache/reuse facts, without double counting.

Do not treat the whole clean run as free preparation for the attacked run.
Execution snapshots may only reuse compatible prefixes before divergence,
including costs, tool state, RNG state, artifact bindings, and identity state.
Reject incompatible source/model/prompt/budget/scheduler/protocol snapshots.

Give planner generation, execution randomness, target selection, and attack
search separate seed streams. A common seed does not imply identical worker
outputs after histories diverge.

Provide staged manifest resolution: planner request -> frozen plan/invalid-
plan result -> eligible target enumeration -> branch manifest. Do not require
unknown generated plan IDs or target lists to be fabricated in advance.

Invalid planning must retain the scheduled base-task condition in reports;
do not silently omit fault branches and inflate completion by evaluating
only planners that generated a valid graph.


10. PRESERVE REAL RESOURCE ACCOUNTING

Use the existing compatible logical-token/CPU profile where available.
Do not create a new ledger merely because the specification is v0.2.
Any changed semantics receive a new profile ID and fresh manifests.

logical_model_work = sum(actual input tokens presented per call)
                   + sum(all generated output tokens).

Include planner, workers, public LLM checking, JIT, invalid-plan revisions,
failed generations, retries, and re-prefill. Reasoning is included once in
output totals. Messages cost their generated and subsequently processed
tokens; do not add a fictional message/agent fee.

Keep raw per-model/tokenizer counts and measured device/service/wall time.
Track model-host, planner-search, compiler, decoder, executor, and public-
checker CPU without overlap. Separate initialization, attack generation,
offline trajectory search/training, storage, and private final grading.

Public checks/integration inside the loop consume team resources. Private
terminal grading is separately bounded/measured after the chosen bundle is
frozen and cannot provide repairs or another selection opportunity.

Audit reservations versus actual usage, including any previous 31-second
model-host reservation issue. Preserve actual charges, release unused
allowances, retain unknown interrupted work, and forbid calls after exhaustion.
An estimate is not a hard runtime bound. Log physical overshoot if it occurs;
correct outputs exceeding declared success caps do not earn Complete@B.

Provide a development-only B0 estimation interface with a prespecified
statistic and explicit treatment of failures/censoring. If measurements are
insufficient, return uncalibrated instead of estimating from winners alone.

Use the same per-family/worker-backbone B0 across planners and pool sizes.
Do not give larger teams an automatic larger token budget. Support later
multipliers 1.25, 1.5, 2, 3 without launching the grid.

Equal tokens across different planner sizes/tokenizers are not equal FLOPs.
Retain usage completeness flags, including unknown reasoning counts. No
proprietary-model connection or fictional API price is required here.

Do not label scalar success-minus-cost reward as automatically lexicographic
in success probability: per-trajectory ordering does not establish that in
expectation. Benchmark score and future training reward remain distinct.


11. TASK-BALANCED SCORING AND COMPLETE FAILURE REPORTING

For each branch, keep terminal correctness, resource compliance, and execution
status distinct. In-budget success requires every outcome/regression to pass
AND all declared execution budgets to be respected.

Grade only the latest explicitly bound output bundle. No hidden-best candidate
rescue. Program syntax, public-check passage, and graph validity are not final
correctness. Maintain existing assignment-local finish behavior.

Report clean, F, S, and R separately, with planning lane, pool, active count,
resource profile, model, and source grouping visible.

Aggregate by base task first:
  Complete@B = mean_tasks(mean_prespecified_conditions(Y)).

Declare within-task weights before outcomes. With sampled targets use the
specified target distribution; with exhaustive F targets report that scope.
A task with eight targets must not silently receive eight times the dataset
weight of one with a single target.

Show all planned, resolved, executed, missing, blocked, invalid-plan, capped,
nontriggered, infrastructure-interrupted, and finalized rows. Missing results
are not successes or silently removed denominators. Clearly label provisional
reports; do not invent final scores for unresolved infrastructure work.

Retain model-created invalid plans as observed failures after allowed
revisions. Qualification failures before a model attempt remain explicit
unrun prerequisites, not fabricated wrong model answers.

Include per-output correctness, clean-correct ASR with its actual paired
eligibility, false alarms, detected-but-unfinished, post-alarm/total cost,
reexecution versus regeneration, and target coverage.

Observed worst case means worst among tested targets, not a universal
robustness guarantee. Do not rank by backup counts, graph-cut certificates,
repair/corrupted-work ratios, or cost among successes alone.

Provide a small paired comparison report with invariant hashes for worker,
JIT, monitor, access, scheduler, scorer, and budgets. An intended planner-only
comparison with incompatible fields must be flagged, not pooled.


12. GROUPED SPLITS, STRUCTURAL COVERAGE, AND TRAINING EXPORTS

Keep current draft/review/license statuses and actual task inventory.
The design's 12-task prototype and approximately 100-task release are future
coverage targets, not content to fabricate during this update.

Add task eligibility/coverage metadata for meaningful organization variation
without hardcoding an intrinsic worker count into the public request.
A valid witness pair establishes possible alternatives, not that every
planner will discover them or that a recovery-aware plan is superior.

Split by repository/source family, shared base change, codebook/schema slice,
author template, and near-duplicate semantic dependencies. Related source
packs may need a common supergroup. Different rows, fault targets, graph
permutations, or seeds do not make independent base tasks.

Support prespecified task/count/budget/structure splits. For example, training
pools 2/3/4/6 and testing 5/8 must label unseen-count interpolation versus
larger-count extrapolation accurately. Pool holdout is not automatically an
active-worker-count holdout; report actual active counts.

Authored-catalog topology holdouts can use declared graph families. In open
planning, output graph motifs are not ordinary input splits: report structural
stress tasks and generated distributions, not an unsupported held-out-topology
claim. External-environment transfer requires actual external evaluation.

Implement TWO training-export formats, without training a model:

A. Plan outcomes:
  public planner input, task/source group, pool/budget/threat, frozen plan,
  branch outcomes, actual costs, and complete provenance bindings.

B. Event trajectories:
  the observation visible at that time, actor/action, actual cost,
  next visible observation, and terminal outcome labels.

Keep model inputs separate from training targets/private analysis fields.
Future selected identities, realized sabotage, hidden checks, author solutions,
and final outcomes cannot enter the proactive planner input.
Do not regenerate historical observations from a later evaluator-informed
summary. Use visibility-filtered recorded state.

Export all outcomes, including bad plans, unnecessary replication, failed
repair, caps, and nontriggered faults. Respect grouped train/dev/test filters.
Private-runtime test materials remain excluded from public bundles.

Label real-model, scripted/mock, reference-only, offline-replay, and simulated
records distinctly. Do not produce simulated outcomes or fit a simulator here.
Never call a limited stochastic best-in-catalog label globally optimal. Any
future best-plan selection/estimation uses separate samples and reports search
cost. Retain schema fields for that provenance without inventing measurements.

No SFT/RL trainer, adapter weights, or large trajectory-generation campaign
is part of this update.


13. BASELINES AND BOUNDED EXPERIMENT TEMPLATES

Keep separate planner choices and recovery choices in configuration.

Working initial planner paths should include requirement-level allocation,
a frozen prompted open-weight planner using the existing backend, and
supplied-catalog selection. Reuse existing nominal/recovery-aware selectors
only with truthful compatible-calibration status.

Expose future small-base/SFT/RL planner plugins through the same contract,
but do not register unimplemented adapters as successful methods.
Restart and selective replication remain separately labelled references;
changing both plan and repair is not a planner-only result.

Prepare a lightweight core evaluation TEMPLATE:
  one declared pool, one budget, one clean branch, one seeded eligible-
  contributor F branch, and one bounded S branch when qualified.

Do not launch it or construct fake rows for missing planners/tasks/attacks.
Generated-plan target resolution happens after the plan is frozen.

Use a fixed smaller subset for all-target loss, pool sizes, active-count
controls, and budget sweeps. Output exact logical episode counts and a cost
estimate with its measurement source before any submission.
Do not multiply every axis across every task by default.

Preserve the existing narrow Jaffle clean/F(w0)/F(w1) engineering gate.
New variable-count functionality must not silently expand that permission.
If its results are absent, its real-model recovery gate stays pending even
when variable-size CPU tests pass.


14. IMPLEMENTATION MILESTONES AND ACCEPTANCE TESTS

M0 — Audit and compatibility:
  Requirements-to-code map, semantic versions, actual readiness status,
  old manifest readability, no changed scientific history.

M1 — Variable-team vertical slices:
  Pools 2–8, adaptive/matched count modes, scheduling, assignments,
  persistent faults, provenance, budgets, and resume through BOTH current
  families using labelled CPU fixtures.

M2 — Planning/execution integration:
  Actual open-planner adapter, shared-catalog and fixed-plan lanes,
  graph validation and execution, frozen common JIT, publication/binding,
  and cost-fair clean/fault branching.

M3 — Analysis/data interfaces:
  Task-balanced scoring, compatibility reporting, grouped split checks,
  pool/structure coverage, leakage-safe exports, and bounded manifest
  templates. Task qualification remains explicit.

M4 — Handoff and gated cluster readiness:
  Real commands, dry runs, evidence inventory, and next minimal experiment.
  No GPU run or dataset/model-training campaign is executed here.

Prioritize these behavior tests rather than accumulating flag-only tests:

- Old four-identity runs retain original behavior and provenance.
- Every pool 2–8 works; exercise upper-index identities and two-identity
  repair where the survivor completes multiple assignments.
- Adaptive pools may leave identities idle; matched counts are validated
  without excluding expected effects of the injected loss.
- Unused slots never dilute target probability; enumerate exactly eligible
  contributors, preserve never-triggered events, and retain obligations.
- Assignment finish does not close the episode; faults/checkpoints do not
  resurrect unavailable identities or replay costs/events twice.
- Different legal organizations actually change execution, while owner
  relabeling is not reported as new semantic topology.
- Both families support the real artifact/interpreter/scorer path, not a
  scripted method-name success shortcut.
- A fixed helper can be rebound and consumers reexecuted without mandatory
  regeneration; messages and version reads retain provenance.
- Planner observations cannot access future fault truth or evaluator data;
  common JIT cannot become a hidden correctness oracle in S.
- Invalid plans consume their attempted planning work and remain failures.
- Clean/fault branches share a frozen plan and logical planning charges
  without clean-answer leakage or duplicated physical-cost claims.
- Near-cap estimates reconcile with real usage; over-cap correctness is not
  budget success and interrupted unknowns are not silently refunded.
- Task-balanced aggregation gives equal base-task weight despite different
  numbers of targets. Missing runs and clean-correct denominators stay visible.
- Train/dev/test export rejects source-group leakage and keeps future labels
  out of planner inputs. Mock/real/simulated modes cannot silently mix.
- Benchmark-only execution works without importing Beyond Consensus.
- Existing restricted SQL/schema boundaries and source/private separation
  remain enforced.
- Slurm dry runs preserve GPU limits, immutable snapshots, wrapper paths,
  quoting, and deliberate submission gates.

Run established available checks and relevant optional-dependency suites:
  python -m unittest discover -s tests -v
  python scripts/check_shell.py
  python -m compileall -q src tests scripts
  git diff --check
  python -I -S scripts/bc.py --help

Report actual results and each relevant skip. Earlier revision counts do not
qualify this code. Missing GPU execution is not a software-test success.
Do not install a different heavy environment automatically to hide skips.


15. RUNBOOK AND FINAL HANDOFF

Update AGENTS.md and one concise v0.2 migration/runbook document. Preserve
existing script names and the tested CPU-submission wrapper.

Provide actual implemented commands for:
- Legacy/v0.2 validation and pool configuration.
- CPU fixture qualification for both families and pools 2–8.
- Plan inspection, open-generation request setup, and catalog selection.
- Common-JIT compatibility and task/source readiness.
- Staged plan/target/branch manifest resolution and exact episode counts.
- Task-balanced aggregation, grouped splits, and trajectory export.
- Guarded Slurm preflight/dry-run, resume, and sanitized evidence export.

Separate LOCAL review/test/manual-push steps from CLUSTER browser-terminal
pull/qualification/manual-submission steps. Do not auto-push or auto-submit.

GPU preflight checks actual model placement, representative context switching,
and the memory footprint reached; it must not claim full 2–8-context fit from
a short early-EOS probe. Use no new GPUs for idle logical identities.
Large CPU qualification belongs in allocations, not on the login node.

No job depends on a live browser/laptop, no downloads occur per shard, and no
batch script launches uncounted downstream jobs. Keep secrets, private tests,
raw outputs, model/data caches, and source snapshots outside Git.

Final response must include:
1. Files changed, reused components, and an honest spec-to-implementation map.
2. Actual tests, optional coverage/skips, and cluster work NOT performed.
3. Old/new semantics for pools, counts, lanes, targeting, budgets, and scoring.
4. One clearly labelled executable example per family showing a changed plan
   and ordinary JIT recovery; identify scripted versus real evidence.
5. Qualified task/plan counts and pending review/license/calibration gates.
6. Leakage-safe export fields and version compatibility guarantees/limits.
7. Exact next local and cluster commands, plus a minimal proposed user-gated
   smoke. Do not authorize it yourself or revive a broad campaign.

The deliverable is a working v0.2 environment for comparing PRE-EXECUTION
MAS planners under identical workers and recovery—not a newly trained
recovery controller, a larger list of fake tasks, or an apparent improvement
created by weaker baselines and hidden cost advantages.
```
