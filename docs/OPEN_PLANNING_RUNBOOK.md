# Open planning and scoped execution runbook

## Prospective cohort handoff (2026-10-08)

[RICH_COHORT_PILOT.md](RICH_COHORT_PILOT.md) is the current local implementation
and command handoff: prospective stock check first, then a separately reviewed
two-planner rich-task pilot. Three cards have executable references; the fourth
API candidate is blocked. Fresh evidence and manifest-scoped authorization are
required. The dated steps below retain the history of the narrower clean and
conditional-fault exceptions; they do not authorize the new cohort.

## Current next step (2026-10-07)

The planner-6144 footprint passed all five observed GPU cases. The supplied
export was reviewed for internal consistency; this does not qualify autonomous
planning or authorize task execution. Preserve the failed 2048/4096 conditions
and the successful v3 report as separate evidence. The next reviewable scope is
[one clean engineering trial](#clean-only-engineering-proposal-2026-10-07).
The clean-only adapter below is implemented; it requires fresh CPU adapter controls
and a separately reviewed, manifest-bound approval receipt. No task-dispatch
permission has been issued.

Date: 2026-10-06. Local implementation only. No GPU inference, submission,
training, commits or pushes were performed. The requested
`reporecourse_environment_design_v0_2.md` was not found; the supplied October 6
update and current protocol/audit are the specification.

## Contract and implementation map

| Component | Authority and behavior |
| --- | --- |
| `reporecourse.v2.configuration` | New explicit `planning_lane` and `execution_contract`; omitted fields preserve old config identity/defaults. New protocol `rr-open-planning-v1`. |
| `PromptedPlanner` and BC planner bridge | Same count/generate backend interface, separate planner context/output cap; eight total calls including public reads, one proposal plus at most two failed structural revisions. Raw responses, public feedback, actual/uncertain costs retained. No fallback plan. |
| `validate_work_plan` and new plan grammar | Invent IDs, 1–24 units, 2–8 legal owners, intermediate artifacts, terminal mappings, interfaces and dependencies. Cross-check imports/edges; unknown payload fields rejected. Inefficient legal plans allowed; unused units are not meaningful fault targets. |
| `AssignmentScopes` | One admission/observation/tool authority for `plan_scoped_v1`. Original sources available to all; source-focus lists are hints. |
| Engine and existing ModelWorker | Deterministic scheduler; new assignment gets a fresh history, retries retain it. Same model weights, full charged re-prefill, no cross-call KV cache supplied by the Transformers backend. Identity loss persists. |
| Existing common JIT | New ID `rr-common-scoped-jit-v1`; only loss/public-alarm triggers admit repair overlays. Same owner-selection/rebuild/rebind algorithm across planners. |
| `conformance.report` | Read-only declared/direct/transitive/exposure/denial comparison, with unknown coverage explicit. Automatically included for scoped Engine and v2 branch results. |
| `open_planning` and `scripts/rr_v2.py` | Blocked engineering proposal from actual historical manifest/lock; CPU-double planner-to-worker vertical slice reuses the existing runtime. |
| Existing `rr-v2-preflight-manifest --plan-scoped` | Shared-registry synthetic qualification using new pool-specific grammars. No task episodes or task permission. |

Planning lanes are `open_generated`, `authored_diagnostic`, `shared_catalog`, and
`fixed_recovery`; the latter two remain paired with existing shared-catalog and
fixed-plan lanes. Execution contracts are independent of planner identity:
`adaptive_legacy` preserves opportunistic sharing; `plan_scoped_v1` controls
mediated primary imports and observations. Nothing relabels historical success.

## What the contract controls

Each scope resolves declared producer artifacts to their latest published
immutable versions at assignment admission. It exposes only those imports and
own revisions. Scoped publication additionally checks declared produced names,
formats and terminal mappings. SQL aliases/nested queries resolve against public
originals plus explicit direct bindings. Schema and mapping references resolve
through direct bound schemas; inherited schema references are expanded within
those schemas, without granting new direct imports. Publication receipts and
version closure are checked before execution, restore and final grading.

Artifact metadata, reads, execution, rebindings and output binding pass through
the same layer. Search/list tools expose only approved original sources. Worker
public checks show only its own output checks. Checkpoints restore only that
scope's output bindings. Context/history checks reject mismatched restoration.
Other same-owner assignments start with empty histories.

Arbitrary messages are permitted only from declared predecessor units, queued
with unit provenance and exposure, and delivered only under compatible imported
ancestry. Unrelated messaging is denied generically. Fixed public loss
announcements remain trusted coordination facts. No global chat is exposed.

A denied request is logged and charged by the existing tool/model ledger. It
neither creates a dependency nor automatically unlocks recovery. Unused allowed
imports are valid. Metadata exposure can occur without an explicit body read;
reports keep that separate from executable version bindings.

Recovery overlays record their trigger event/public evidence, revision ID,
unit/owner, original sources, current imported versions, own prior revisions,
and empty context imports. They permit helper replacement, unchanged-consumer
reexecution with checked bindings, or direct-source reconstruction. Other units
retain their scopes. Old artifacts and the initial plan remain intact. Reset
never makes an unavailable identity eligible. The existing JIT is bounded and
fallible, not an oracle or a learned recovery controller.

These are mediated information-flow controls, not proof of semantic answer-free
planning, independent errors or absence of every timing/native-engine side
channel. Planner prose/interfaces are bounded and logged but can contain solution
hints. Full remote evidence remains necessary: hashes show internal bindings,
not independent event authenticity. Missing logs yield unknown conformance.

## Historical audit

The new read-only reporter was run against the supplied selected stock export
for experiment `853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06`.
It found zero declared edges and one realized primary edge
`stock_report -> zero_report`; correctness and in-budget observations remain
true. Contract conformance is null/descriptive for adaptive legacy, with missing
visibility coverage explicit. No model/SQL ran and no historical score changed.
Full remote files were not independently retrieved. The historical artifact
payload is not embedded into planner inputs or committed as a training example.

## Current readiness and proposed scope

The new code is not GPU-qualified. Prior adaptive stock competence, old grammar
keys and old memory results do not approve changed scopes. Local tests using
backend doubles are labelled scripted mock, not real generation. Pinned child
execution tests require SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2.
The default local environment lacks these dependencies; their tests skip and
cluster CPU qualification must pass without skips before considering GPU work.

The proposal builder requires the actual historical stock manifest and its
matching model lock. It copies worker settings, token/CPU caps and seed, changes
only the explicit contract/grammar, and records the independently specified
planner output cap. It does not invent resolved settings or approvals.

Proposed first scope: pool 7, one planner generation sequence (up to two charged
structural revisions, at most eight total calls including reads), one clean
branch, and at most one already-selected F branch **after** separate review of a
clean conformant success and explicit approval. The same frozen plan and actual
planning ledger apply to both logical branches. No repeated plan sampling after
failure; nontriggered targets remain nontriggered. With the reported stock
settings the engineering caps are 100,000 logical tokens and 1,200 CPU seconds
per branch, 24 worker actions, 16K context and 2,048 worker output tokens. These
are not B0. A separate planner cap of 2,048 is only the starting proposal, not
proof that every legal 24-unit plan fits. No plan-output footprint is qualified.

Open task submission stays blocked; `prompted-plan` fails closed for the new
protocol before loading weights. `PromptedPlanner` and `ModelWorker` are the
executable backend adapters, exercised together with labelled CPU doubles.
A future approved shared-registry task runner must bind the reviewed proposal,
new controls/grammar/footprint evidence and explicit clean/F decisions. There is
no `force_run`, custom sbatch task escape, or automatic downstream submission.
Native tasks, nullable GPU work, larger sweeps, calibration and SFT/RL are deferred.

## Local review and manual push

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
python -I -S scripts/bc.py --help
python -I -S scripts/rr_v2.py --help
git diff --check
git status --short
git diff
```

Review and stage only intended source/tests/documentation, then commit and push
manually. Preserve pre-existing audit edits. Keep reports, models, data, locks
and snapshots outside Git.

Read-only historical analysis, with an existing result or selected export:

```bash
python -I scripts/rr_v2.py conformance \
  --input "$BC_EXISTING_EXPORT" --output "$BC_NEW_AUDIT_FILE"
```

The output must be a new path. Nothing is rescored or executed.

## Cluster CPU qualification after the user pushes

Run from the cluster browser terminal. These commands are for user-triggered
execution; nothing is submitted by local implementation. The CPU allocation
uses an original frozen script path through a wrapper, not Slurm's spool path.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_OPEN="$(mktemp -d "$BC_STORAGE/diagnostics/rr-open.XXXXXX")"
(
set -euo pipefail
test -z "$(git status --porcelain)"
mkdir "$BC_OPEN/source"
git archive HEAD | tar -xf - -C "$BC_OPEN/source"
git rev-parse HEAD > "$BC_OPEN/source-commit.txt"
chmod -R a-w "$BC_OPEN/source"
cat > "$BC_OPEN/cpu.sh" <<'SH'
#!/bin/bash
set -euo pipefail
export BC_PYTHON="$2"
cd "$1"
exec bash "$1/experiments/qualify_reporecourse.sh" \
  --repo-root "$1" --scoped-controls --pool-count 7 \
  --sources "$3" --output "$4" --model-lock "$5"
SH
bash -n "$BC_OPEN/cpu.sh"
)
```

Set `BC_OPEN_BASE_LOCK` to the actual existing frozen 27B lock. Do not substitute
another checkpoint. Select an available permitted CPU partition using current
scheduler information. Then submit **once**, when the user chooses to do so:

```bash
(
set -euo pipefail
: "${BC_OPEN_BASE_LOCK:?Set the existing 27B model lock path}"
: "${BC_OPEN_CPU_PARTITION:?Set a checked CPU partition}"
test -s "$BC_OPEN_BASE_LOCK"
set -o noclobber
sbatch --parsable --partition="$BC_OPEN_CPU_PARTITION" \
  --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --chdir="$BC_OPEN/source" --output="$BC_OPEN/cpu.out" --error="$BC_OPEN/cpu.err" \
  "$BC_OPEN/cpu.sh" "$BC_OPEN/source" "$BC_PYTHON" \
  "$BC_STORAGE/datasets/reporecourse-v01" "$BC_OPEN/cpu" "$BC_OPEN_BASE_LOCK" \
  > "$BC_OPEN/cpu-job.txt"
)
```

After completion, inspect `sacct`, `cpu.out`, `cpu.err`, the fixture report and
both grammar reports. Compiler/validator controls must pass with zero skips.
This still does not establish generated planning or model competence.

## Prepare changed grammar preflight and inspect its dry run

Use the actual cluster JSON already reviewed for one full 80-GB-class GPU.
Do not infer node capacity from its partition name. After successful CPU controls:

```bash
(
set -euo pipefail
: "${BC_OPEN_CLUSTER:?Set the reviewed cluster JSON path}"
cd "$HOME/Beyond-Consensus"
test "$(git rev-parse HEAD)" = "$(cat "$BC_OPEN/source-commit.txt")"
"$BC_PYTHON" -I scripts/bc.py rr-v2-preflight-manifest \
  --pool 7 --plan-scoped \
  --model-lock "$BC_OPEN/cpu/model-lock-json-pool-7.json" \
  --planner-lock "$BC_OPEN/cpu/model-lock-plan-pool-7.json" \
  --output "$BC_OPEN/preflight-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_OPEN_CLUSTER" --manifest "$BC_OPEN/preflight-manifest.json" \
  --model-lock "$BC_OPEN/cpu/model-lock-json-pool-7.json" --dry-run
)
```

Stop at the dry run. GPU qualification requires an explicit user decision.
This synthetic preflight has no task episodes and does not qualify 24-unit plan
serialization or task execution. Its reports are not accepted as task approval.

## Prepare the blocked engineering proposal

Set paths to the actual historical successful stock manifest and its exact
matching historical lock. This command reads existing records; it loads no model.

```bash
"$BC_PYTHON" -I scripts/rr_v2.py open-proposal \
  --input "$BC_STOCK_MANIFEST" --model-lock "$BC_STOCK_HISTORICAL_LOCK" \
  --planner-output-cap 2048 --output "$BC_OPEN/open-proposal.json"
"$BC_PYTHON" -m json.tool "$BC_OPEN/open-proposal.json"
```

The proposal contains resolved worker/planner settings, counts and blockers.
It is deliberately not a runnable task manifest. Fresh CPU/grammar evidence,
planner-output/observation qualification and explicit clean approval are still
required; F has an additional clean-conformance review and approval gate.

## Local verification and unresolved integration tests

Latest local run after the reference-name correction: **368 tests, 347 passed,
21 skipped**. The scoped module has 27 tests, 24 passed and three skipped.
All 10 shell files passed the repository
shell checker; compileall, `git diff --check`, and both CLI help commands under
`python -I -S` passed. These are implementation checks, not qualification of new
model planning, scoped task competence, or a larger memory footprint.

Twenty skipped tests need the optional pinned CPU dependencies listed above.
The `--scoped-controls` allocation runs the scoped, existing RepoRecourse,
Track F, v2 and SQL compiler suites and fails on any relevant skip:

- `test_reporecourse.PublicSQLInterfaceTests.test_actual_compiler_distinguishes_undeclared_object`
- `test_reporecourse.VerticalTests.test_all_baselines_clean_and_announced_loss`
- `test_reporecourse.VerticalTests.test_both_families_witnesses_and_negatives`
- `test_reporecourse.VerticalTests.test_existing_journal_runner_adapter_with_explicit_test_backend`
- `test_reporecourse.VerticalTests.test_fixed_state_graph_and_equal_remaining`
- `test_reporecourse.VerticalTests.test_independent_benchmark_execution_without_bc`
- `test_reporecourse.VerticalTests.test_replica_checkpoint_preserves_primary_and_resumes`
- `test_reporecourse.VerticalTests.test_resume_and_latest_bound_not_best`
- `test_reporecourse.VerticalTests.test_schema_rebind_reuses_program_preserves_exposure`
- `test_reporecourse.VerticalTests.test_shared_plan_repair_and_no_forced_regeneration`
- `test_reporecourse_scoped.ActualExecutionTests.test_both_families_all_topologies_pools_2_and_8_and_loss`
- `test_reporecourse_scoped.ActualExecutionTests.test_generated_plan_to_restricted_execution_through_model_interfaces`
- `test_reporecourse_scoped.ActualExecutionTests.test_stock_old_reuse_denied_corrected_and_wrong_conformant`
- `test_reporecourse_track_f.ExecutorControls.test_actual_journal_runner_three_shards_and_overcap_correctness`
- `test_reporecourse_track_f.ExecutorControls.test_both_losses_resume_visibility_wrong_repair`
- `test_reporecourse_v2.ExecutableFamilies.test_both_families_all_pools_reference_clean_and_loss`
- `test_reporecourse_v2.ExecutableFamilies.test_common_jit_rebinds_unchanged_consumer_without_model_call`
- `test_sql_text.CompilerTests.test_rejects_and_resource_bounds`
- `test_sql_text.CompilerTests.test_runtime_fail_closed_charges_and_wrong_query`
- `test_sql_text.CompilerTests.test_synthetic_semantic_parity`

The remaining skip is
`test_repository.RealSandboxTests.test_actual_isolation_and_cleanup`, requiring
the separately approved `BC_SANDBOX_TEST_PROFILE`. It belongs to the optional
legacy OS-sandbox path and is not required or enabled by this data-tool phase.

M0's selected-export audit and local mediation/planner unit controls are complete.
M1's optional actual-child execution matrix and M2's real-generation integration
qualification remain pending. The injected-backend vertical slice is implemented,
but its actual SQL execution test also awaits those pinned dependencies. M3 is
a blocked, hash-bound engineering proposal and synthetic preflight dry run;
there is no approved production open-planning task dispatcher in this update.

### CPU job 1087335: reference-driver correction

The supplied failed cluster run reached actual pinned execution tests. Twelve
synthetic-stock subcases rejected the reference driver's `stock`/`zero`
publication names because the scoped authored plans declared
`stock_report`/`zero_report`. The correction changes only the new scoped
reference driver's publication names and symbolic version references; programs,
legacy drivers and runtime permission checks are preserved. A stdlib regression
now catches this mismatch even where compiler integration tests must skip.

After reviewing/pushing the correction, repeat the CPU workflow above with a
**new** `BC_OPEN` directory and frozen source. Keep `rr-open.xpK6b4` and its failed
reports intact. Do not rerun its old snapshot or proceed to GPU qualification
until the new CPU controls and grammar reports pass. Local unit results do not
substitute for this fresh pinned execution qualification.


### Scoped pool-seven preflight: reported result and offline audit

The user supplied a successful CPU qualification from
`rr-open-fix.T7sJw0`, frozen commit
`f4c25a0c028cbb2e730f791eff9e753b8335b3fa`: fixtures and both scoped
grammars passed, with both qualified locks present. The subsequent preflight
`c634622159286dcc20ce6424c4f0f5da0cb160d3d40b2dfb29ce861dc11c6d9e`
reported `passed_observed_sequence` on NVIDIA A100-SXM4-80GB: all 16 calls
(seven workers plus planner, two rounds) passed using one model instance,
237560 tokens, zero uncertain tokens and 1178.78 seconds wall time.
These are user-supplied summaries, not independently verified local artifacts.
Worst-case fit and task execution remain false; this is not task competence.

The offline preflight auditor now derives grammar names from the frozen
execution contract and supports explicit `--normal-only`. That mode emits
`rr-v2-preflight-single-audit-v1`, separate from the paired normal/stress audit;
it cannot replace paired stress evidence or authorize task execution. Frozen
snapshot, manifest, lock, runtime, call and accounting checks remain required.
No historical reports, model settings or execution behavior are changed.

After pushing/pulling the auditor update, audit the existing run without
resubmitting it. Use a fresh output directory:

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_OPEN="$BC_STORAGE/diagnostics/rr-open-fix.T7sJw0"
export BC_OPEN_AUDIT="$(mktemp -d "$BC_OPEN/provenance.XXXXXX")"

"$BC_PYTHON" -I scripts/audit_rr_v2_preflights.py \
  --normal-only \
  --normal-run "$BC_STORAGE/outputs/qwen27b-na100/c634622159286dcc20ce6424c4f0f5da0cb160d3d40b2dfb29ce861dc11c6d9e-preflight" \
  --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_OPEN_AUDIT/audit.json"
```

Review the audit and the submission receipt's job ID with `sacct` before
preparing the next bounded proposal. Scheduler completion is not verified by
this offline auditor. A passing audit means internal bindings were verified;
production open-planning tasks remain blocked pending their separate gates.


## Clean-only engineering proposal (2026-10-07)

**Status: proposed, blocked, not an executable manifest or approval.** This
narrows the next proposed scope to one clean synthetic-stock branch. It does not
modify the earlier immutable proposal
`2b050af79f31234bd9607cdb6244b321145f00069f0ddd72f9300e944cd78388`,
whose conditional F branch and 2048-token planner setting remain historical.
The existing proposal builder still emits that older scope; its output must not
be used as the clean-only manifest described here.

### Evidence reviewed

The uploaded v3 export binds experiment
`2c87a3340e7d3e47542c64191528ecc0e9cacfc2cd393756d1c26e325eb79c21`,
CPU packet
`b0d2d7c31348ad24e9d1ee746ed77c7aeff8802dfc6a7b3d483dacce595bfc83`,
and source commit `bb27c7c96491a08fdd4a0d0128dc002bc46a39e9`.
Supplied scheduler evidence reports job 1088148_0 COMPLETED, exit 0:0.
The runtime reports one NVIDIA A100-SXM4-80GB and one loaded model instance.

| Case | Input tokens | Output tokens | Reported reasoning tokens | Result |
| --- | ---: | ---: | ---: | --- |
| plan_02 | 749 | 470 | 281 | passed |
| plan_07 | 1189 | 815 | 186 | passed |
| plan_24 | 2685 | 4377 | 2252 | passed |
| scope_empty | 969 | 84 | 72 | passed |
| scope_imports16 | 3859 | 201 | 131 | passed |

All five ended at EOS with complete constrained actions. Total usage was 15398
logical tokens, zero uncertain tokens, and 672.1919073 seconds wall time.
Plan_24 used 2125 output tokens beyond reported reasoning, matching the measured
action-plus-stop size, with 1767 tokens below the 6144 cap. These are observed
responses to authored reproduction cases, not autonomous task decomposition.

The local review checked 68 internal consistency conditions across the uploaded
manifest, packet, locks, qualification reports, snapshot metadata, generations
and accounting. All passed. The 134 local implementation files listed under
src/scripts/experiments also matched the uploaded snapshot hashes. The reviewer
did not access the remote filesystem or scheduler: embedded contents and claimed
remote file hashes do not independently prove remote file authenticity or a
complete remote snapshot inventory. No model or SQL was executed by this review.
`worst_case_fit_established` and `task_execution_allowed` remain false.

### Proposed frozen scope

| Setting | Proposed value |
| --- | --- |
| Purpose | One development engineering check of autonomous planning plus clean execution |
| Task | synthetic-stock only; public hash `3778abbd6ff3234eb22c9f42aa34108c2065a80496529d702d198ecb9bc1167c` |
| Historical settings source | Actual resolved stock experiment `853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06`, embedded in the reviewed proposal |
| Model/tokenizer revision | Qwen/Qwen3.5-27B, `fc05daec18b0a78c049392ed2e771dde82bdf654`, BF16, thinking enabled, deterministic decoding |
| Logical pool / physical allocation | w0–w6; one shared model on one allocated GPU; concurrency one |
| Planning / execution | open_generated / plan_scoped_v1; assignment-local histories; common public scoped JIT |
| Context / output reservation | 16384 context; worker 2048 output (maximum input 14336); planner 6144 output (maximum input 10240) |
| Planning bound | One planning sequence, at most eight calls including public reads; at most two structural revisions within that bound |
| Plan bound | 1–24 units under the existing validator; no authored fallback or hidden answer selection |
| Worker action bound | 24, inherited from the resolved proposal |
| Total branch budget | 100000 logical tokens and 1200 CPU cap units, including planning and execution; uncalibrated engineering caps, not B0 |
| Execution branches | At most one fresh clean branch; zero F, S, or R branches |
| Seeds | Preserve recorded streams: planner 75663671558091; execution 80114559081572. Preserve provenance of unused target/attack streams without selecting a fault target. |
| Success criterion | Valid frozen plan, conformant scoped execution, all obligations passed by the terminal evaluator within the shared caps |

Charge every planner read, generation, validation and structural retry through
the existing ledger. Deduct actual planning usage from the same clean branch
budget before execution, and report physical usage separately without double
charging it. Do not restart the budget at plan freeze. Invalid planning, exhausted
resources, context rejection and task failure must be retained as outcomes; no
best-of selection or automatic rerun. Per-call admission must reserve the full
role output allowance. The five observed prompts do not establish the maximum
input/output memory envelope.

Public monitoring alone drives repairs. Hidden evaluation is terminal and must
not select a plan, feed revisions, or authorize an automatic fault branch.
A successful trial would establish one observed synthetic clean outcome, not
benchmark competence, calibrated efficiency, recovery benefit or generalization.

### Remaining gates and implementation handoff

| Gate | Current evidence / required action |
| --- | --- |
| Scoped CPU execution | Earlier supplied controls passed; bind the actual task/public material and current execution implementation to applicable controls. Renew controls for changes; do not infer compatibility from a preflight summary. |
| Role grammar | Worker-2048 and planner-6144 qualifications passed in the reviewed packet. Validate exact keys, packages, templates, model locks and source compatibility for the proposed runner. |
| Observed footprint | Five v3 cases passed. Preserve the separate earlier long-input evidence and its geometry; no worst-case-memory claim or automatic transfer across hardware/contracts. |
| Task provenance/review | Synthetic task remains labelled cpu_qualified_review_pending. Record its qualification and unresolved independent review explicitly; any engineering exception must be narrowly approved, not relabelled as general task qualification. |
| Executable task gate | Implemented below with a manifest-bound approval receipt and fresh adapter controls. Unapproved dispatch, fault branches, incompatible evidence, and repeated attempts are rejected. |
| Task prompt admission | Bind actual public planner/worker inputs and check role context reservations; qualification reproduction prompts are not measurements of task prompts. Fail closed on overflow. |
| Explicit approval | Obtain approval of the concrete clean-only manifest, evidence and remaining engineering limitations after preparation. This document is not that approval. |
| Calibration and research | B0, autonomous competence and general campaign qualification remain unmeasured. The proposed trial cannot unlock policy comparisons, other tasks, training or fault campaigns. |

Prepare that implementation and its review packet before requesting final run
approval. Keep source changes, newly required qualifications and historical
observations separate. Neither the legacy clean/F exception nor the v3 task-free
preflight grants permission for this new trial.


### Clean adapter implementation and preparation interface

`rr_open_review` audits saved v3 manifest/report/lock files and the full local
snapshot inventory without executing historical code. It checks the five
responses, role keys/caps, rendered-input bindings, generation contracts,
accounting and memory observations. A passing audit still requires review of
scheduler completion and authenticity. It cannot grant approval.

`rr_open_clean` prepares a distinct `rr-open-clean-manifest-v1`, initially with
`approval: null` and `task_execution_allowed: false`. It binds the historical
proposal, audited footprint, current source, actual task/evaluator hashes, stock
controls, scoped reference matrix, new adapter tests and both role locks. The
existing worker/planner model and execution files must match the observed
footprint snapshot. Changes to those contracts require renewed qualification;
this adapter does not automatically bless a changed runtime. Added adapter and
routing code is separately source-bound and covered by fresh controls.

Preparation commands, after freezing the reviewed source and setting paths:

```text
python scripts/bc.py rr-open-footprint-audit --run RUN --snapshots SNAPSHOTS --output AUDIT
python scripts/check_rr_open_clean.py --output ADAPTER_CONTROLS
python scripts/bc.py rr-open-clean-manifest --sources SOURCES --model-lock WORKER_LOCK --planner-lock PLANNER_LOCK --qualification STOCK_CONTROLS --scoped-fixtures SCOPED_MATRIX --adapter-controls ADAPTER_CONTROLS --footprint-audit AUDIT --output PROPOSAL
```

These are interfaces, not copy/paste path substitutions or job submissions.
Run CPU execution controls in the normal CPU allocation using the pinned
optional dependencies. `check_rr_open_clean.py` rejects skipped tests, including
the real restricted-SQL child integration test. It records source, implementation
hashes and runtime versions. Existing stock controls and the complete scoped
reference matrix are also required; adapter tests do not replace them.

The proposal command prints a **pending** approval template. Review the proposal,
exact evidence, scheduler completion and accepted limitations before creating
an approval receipt. The receipt must name the reviewer and review time, exact
proposal/source/evidence hashes, one clean branch, zero faults, and all listed
engineering limitations. It is an attributed local decision record, not a
cryptographic attestation of who signed it. No command fills in approval on the
user's behalf. Only after explicit approval may `rr-open-clean-approve` bind that
receipt into a new manifest; the original proposal stays immutable. Normal
`bc.py submit --mode run --concurrency 1` then applies the shared scheduler and
registry gates. No private submission path is added.

The allocation runner loads one shared model and switches its qualified planner
and worker role configurations. It freezes one planning sequence, preserves its
journal and charges its ledger once into the clean execution budget. Invalid
plans and interrupted/uncertain generations remain recorded outcomes. There is
no call to the generic fault-branch resolver, no resampling and no resume/retry
of a started attempt. A start marker is written before loading weights.

Compatibility detail: the legacy Environment requires an active identity even
for a clean run. The adapter supplies the first frozen plan owner as an inert
value, preventing random target selection, and labels it separately in the
record. The track remains clean and the experimental target is null; no fault
is scheduled. This preserves the qualified core runtime instead of changing its
historical clean/F semantics.

The terminal evaluator remains private. Success additionally requires observed
scoped conformance and completion within both shared resource caps. Task
journals can contain generated artifacts and evaluation details: keep them
outside Git. Aggregation preserves missing/invalid/infrastructure outcomes and
does not present the run as a recovery or policy comparison.


### Recovery from `bc: file_size` during clean preparation

The full scoped matrix can exceed the general 2 MiB input limit. Clean preparation
and approval now read operator-owned matrix/proposal files through a separate
bounded 128 MiB loader (depth 64, four million nodes); duplicate keys and nonfinite
values remain invalid. General task/tool input limits are unchanged. Keep the
full matrix; do not truncate results to fit the old loader.

For supplied job 1088269, preserve the completed files in
`rr-open-clean-retry.uGqN7j`. After updating the checkout, run all 12 current
adapter controls without skips and write a fresh adapter report and proposal.
Existing stock/scoped controls and role locks may be reused only if the builder's
current implementation, package and qualification-key checks pass. This fix
changes no worker/decoder contract and does not itself require a new GPU probe.


## Audited clean result and proposed conditional F diagnostic (2026-10-07)

Initial proposal status: **no fault execution approved**. The separate adapter
implementation is described below. The existing clean-only approval cannot
authorize this diagnostic.

### Evidence reviewed

The uploaded clean-run evidence identifies experiment
`1517216133b6dfbf131f56f3cf2d63821ef0992ed4f528f037256830b830e291`,
episode `b54c592475e6065a320f0ada4af8f71927560eb0f5170a6945204358d4e5238b`.
The user reported Slurm job 1088508_0 completed 0:0 in 7:29. Local read-only
inspection found matching frozen-plan/plan hashes, agreement between saved
execution and final records, exact artifact bindings, and consistent ledgers.
The full remote manifest was not supplied: its projection and reported file
hashes do not establish independent filesystem authenticity.

The planner's first four-unit proposal was rejected with `output` feedback;
its second proposal was accepted. Both calls remain charged. The frozen plan
has u0/w0 publish stock_report, then u1/w1 consume that exact version to publish
zero_report. Two of seven available identities were active. Both obligations
passed the recorded finite terminal checks. There were no execution failures,
public alarms, recovery overlays or unknown conformance surfaces. Recomputing
conformance from the saved result agrees, apart from list ordering and the
expected task_correct transition from null before evaluation to true afterward.
No model or SQL was executed in this audit; historical records remain unchanged.

| Charged work | Planning | Remaining task execution/overhead | Total |
| --- | ---: | ---: | ---: |
| Model calls | 2 | 3 | 5 |
| Tokens | 3005 | 4471 | 7476 |
| CPU seconds | 110.594050202 | 97.417104024 | 208.011154226 |

The total caps were 100000 tokens and 1200 CPU seconds. Reservations and uncertain
usage were zero. Terminal evaluation has a separate ledger. This is one clean
synthetic engineering success, not general competence, B0 or recovery evidence.

### Concrete proposed scope

Prepare a new, explicitly labelled **conditional-on-observed-plan Track F
engineering diagnostic**, with exactly two branches:

| Branch | Permanent loss target | Trigger |
| --- | --- | --- |
| loss_w0 | w0, owner of u0 | Existing first assigned publication handoff, before commit |
| loss_w1 | w1, owner of u1 | Existing first assigned publication handoff, before commit |

Use frozen plan ID
`f1830e07a9fdc84416164b1cc0163998e0de5ca227f07a18a631b6f78bf0ff1f`
and plan hash
`7b39725077587c94ab5978505429d118b4fab701e6284e52d50ec4b13a98ded7`.
Enumerate both meaningful owners, with within-diagnostic weight 1/2 each. Idle
w2–w6 are not initial fault targets. They remain the existing identities available
to common scoped JIT. No planner rerun, hand-edited plan, supplied solution,
additional identity, fault S/R, alternate policy, task or parameter sweep.

Each branch starts with fresh execution state plus the exact frozen planning
ledger: 3005 tokens and 110.594050202 CPU seconds. Its total caps stay 100000 and
1200, leaving 96995 tokens and 1089.405949798 CPU seconds before execution.
All new primary, checking, repair and integration work is charged. Do not import
clean artifacts, worker histories, evaluator answers or a post-incident state.
Planning is logically charged in each branch and physical reuse is separate.
This is equal-total Track F, not equal-remaining Track R. Failed, interrupted,
non-triggered and nonconformant outcomes remain visible; no automatic retries.

Preserve model revision, role caps (worker 2048/planner 6144), pool seven, 16384
context, public task, evaluator, worker instructions, execution seed, 24-action
limit and common scoped JIT. Loss occurs through the existing public runtime
trigger without consulting terminal correctness. Previously committed versions
survive under the existing rules; the blocked publication is never rescued.

### Scientific conflict and required implementation

The historical frozen request specifies target_rule=uniform. Enumerating both
owners is a **new diagnostic selection rule**, not a historical resolution of
that request. Do not edit/reseal the old request or call generic resolve_branches
and relabel its output. A separate adapter must bind the unchanged historical
frozen record and an explicit new all-owner selection rule. The generic resolver
also adds a clean row; this proposal does not authorize that additional run.

The historical clean result selected this plan for follow-up. It is a descriptive
anchor, not a fresh matched control or an unbiased planner sample. Report the
new outcomes individually as conditional recovery observations. Do not turn the
two rows into a general ASR estimate, planner comparison or recovery-policy effect.
If source/hardware changes affect behavior, record them and block any equivalence
claim; a fresh matched experiment would require another reviewed proposal.

Before seeking execution approval:

1. Audit the actual full historical manifest, frozen record, saved execution and
   snapshot inventory on the cluster; bind their hashes and scheduler receipt.
2. Implement a separate bounded proposal/approval/runner path. Keep clean-only
   guards and generic campaign gates unchanged. Reject changed plans, targets,
   inputs, ledgers, role settings and repeat attempts.
3. Add no-skip CPU controls for both losses, pre-commit timing, persistent loss,
   surviving artifacts, scope overlays, ledger inheritance, interrupted usage,
   no evaluator feedback and preservation of all branch outcomes.
4. Compare current execution/model contracts with qualified evidence. Renew
   affected CPU/grammar/footprint qualification where compatibility is unproven;
   do not infer universal memory fit from the earlier observed probes.
5. Produce a concrete hash-bound two-branch manifest and approval template that
   accepts synthetic review pending, uncalibrated caps, observed-only memory
   qualification and selection conditional on this successful clean plan.
6. Obtain separate explicit approval, then use the shared registry/scheduler
   workflow at concurrency one. This document is not a submission instruction.

The present update records the audit and proposal only. No source behavior,
qualification status, historical score, manifest, approval or GPU job is changed.

### Conditional F adapter implementation and preparation interface

The separate `rr-open-fault-manifest-v1` adapter now implements this proposal.
Its CLI prepares two target-bound shards only; it does not invoke the generic
branch resolver, modify the old uniform request, regenerate planning, or add a
clean row. The current clean-only adapter and its approval schema are unchanged.
A fresh clean *qualification proposal* is reused as a container for current task,
scoped matrix, grammar, footprint and adapter controls; do not approve or run
that qualification proposal as a new clean attempt.

Preparation interfaces (paths are placeholders, not submission commands):

```text
python scripts/check_rr_open_clean.py --output CLEAN_ADAPTER_CONTROLS
python scripts/check_rr_open_fault.py --output FAULT_ADAPTER_CONTROLS
python scripts/bc.py rr-open-clean-manifest --sources SOURCES --model-lock WORKER_LOCK --planner-lock PLANNER_LOCK --qualification STOCK_CONTROLS --scoped-fixtures SCOPED_MATRIX --adapter-controls CLEAN_ADAPTER_CONTROLS --footprint-audit FOOTPRINT_AUDIT --output CURRENT_QUALIFICATION_PROPOSAL
python scripts/bc.py rr-open-fault-manifest --clean-proposal CURRENT_QUALIFICATION_PROPOSAL --model-lock WORKER_LOCK --history-run HISTORICAL_CLEAN_OUTPUT --snapshots SNAPSHOT_ROOT --receipt HISTORICAL_RUN_SUBMISSION --controls FAULT_ADAPTER_CONTROLS --output FAULT_PROPOSAL
```

Run both control scripts in the pinned CPU allocation from a verified source
checkout. The fault suite includes actual scoped Engine/ModelWorker/SQL execution
with a deterministic CPU backend double for both targets. It is not model
competence evidence. Qualification requires all ten fault controls, plus all
current clean controls, to pass without skips. Added routing files change adapter
fingerprints, so the old adapter report cannot be reused. Existing task/matrix,
role locks and footprint evidence can be reused only when all current binding,
package and execution-contract checks pass.

The history reader checks the original approved full clean manifest, frozen
planning journal, execution record, successful final result, planning prefix,
resource totals, conformance, snapshot inventory, resolved model/cluster and
submission receipt. It reads no historical code as an executable module.
Historical scheduler completion is still a human review item; a receipt and
internally consistent files are not an independent authenticity attestation.

A new `rr-open-fault-approval-v1` receipt binds exact proposal, source, evidence,
limitations and targets. `rr-open-fault-approve --manifest FAULT_PROPOSAL
--approval REVIEWED_RECEIPT --output APPROVED_FAULT_MANIFEST` only writes a new
approved record; it does not submit. The separate approval must be obtained
from the user after reviewing the actual proposal and current CPU evidence.

After that approval, the normal shared `submit --mode run --concurrency 1`
workflow schedules shards 0/1. The runner rechecks evidence in the allocation,
requires the same observed hardware/packages as the clean run, loads one model
per allocation, and switches only to the qualified worker role. Per-episode
start markers precede loading; duplicate/retry submissions and injected backends
are rejected. Each branch starts fresh from the inherited planning ledger, with
no clean artifacts or histories. Interrupted usage and construction failures
remain recorded. Terminal evaluation has no return edge to worker execution.

Aggregation preserves each target, its weight, missing/interrupted/failed result,
and recorded intervention status rather than pooling into a general attack
success metric. Neither this implementation nor a passing CPU report authorizes
GPU execution. No new model result has been obtained locally.

## Completed conditional recovery audit (2026-10-08)

Uploaded audit text SHA256 (as received, not the original cluster file):
`ebc46f692cdab29c3bb391ad9c6de0378ef8b3379e1e9f96378e2d8bc46f4460`.
Raw traces remain outside Git.

Approved fault experiment:
`f6066eca22dacf05927d4eda364d6702be202fd08408c7619cae4633c97a75ab`.
Proposal: `1489575d0ee3a03794dca242670f0b70f960870532ca835095f4695a19852774`.
The supplied scheduler export records 1088628_0 and 1088628_1 completed 0:0,
in 6:33 and 6:46 respectively. CPU job 1088580 completed 0:0; the supplied
qualification summaries report all 12 clean and 10 fault controls passed without
skips, including the restricted-SQL integration control. Worker/planner grammar
qualified at 2048/6144 output tokens and 16384 context. Those are reported
cluster observations, distinct from local optional-dependency skips.

Both F branches completed successfully and conformantly on synthetic-stock.
Each triggered exactly one permanent loss before the targeted publication
committed. Neither lost identity was assigned or published afterward. Recovery
scopes reference recorded public alarms. Frozen-plan hashes, exact version
bindings, saved execution records and token/CPU ledger sums were internally
consistent. Recomputed conformance agreed apart from list ordering and the
expected pre-evaluation task_correct=null versus post-evaluation true.

| Target | Observed recovery | Preserved work | Tokens | Charged CPU seconds |
| --- | --- | --- | ---: | ---: |
| w0 | w1 reconstructed stock_report; w2 produced zero_report bound to the reconstructed stock version | No artifact existed before loss | 9949 | 232.298667658 |
| w1 | w0 repaired zero_report in a fresh assignment context | Original stock_report retained unchanged | 10802 | 245.374443477 |

For loss of w1, the repair worker read the retained stock artifact but published
a zero_report query over the original stock table with no executable artifact
binding. Declared imports are permissions, so this is conformant. Distinguish
retained-artifact reading/context exposure from executable version reuse; do not
claim that both repairs executed through the retained producer artifact.

Each branch inherited the original 3005-token / 110.594050202-CPU-second planning
ledger exactly once, then made five new model calls. Physical planning reuse was
explicit; no planning rerun occurred. Total caps remained 100000 tokens and 1200
CPU seconds. Uncertain usage and outstanding reservations were zero. Both
obligations passed both recorded terminal fixtures (four checks per branch),
with evaluator work separate and no terminal feedback to workers.

The uploaded export includes full branch records but omits the large qualification
subtree of the manifest. Local review establishes internal consistency, not
independent remote-file authenticity or reconstruction of the complete manifest
hash. The scheduler output is user-supplied evidence, not a local scheduler query.
No SQL/model was executed during this audit, and no historical score was changed.

Milestone: one successful model-generated clean plan followed by two successful
conditional F recovery observations. This establishes a narrow engineering path.
Selection occurred after clean success; it does not establish an unbiased
recovery rate, planner superiority, calibrated efficiency or a policy effect.
The previous clean-only and fault approvals have been consumed by their exact
attempts and grant no new run permission.

## Proposed prospective matched clean/F check (2026-10-08)

Status: **design for review, not implemented or approved for execution**.
The next bounded comparison should remove selection on clean success before
introducing a competing planner. It compares fresh clean and F outcomes for one
freshly generated plan under the same frozen workers and common public JIT.
It is an engineering check of prospective branching, not a research campaign.

### Prespecified scope

- One planning sequence on synthetic-stock, seed index 1, using the existing
  deterministic seed-stream derivation recorded in the request. This seed is a
  proposed fixed design choice, not a selected successful seed or a measurement.
- Open-generated, adaptive-size planning; seven existing identities; unchanged
  plan_scoped_v1 mediation, original-source permissions and common scoped JIT.
- Qwen3.5-27B revision fc05daec18b0a78c049392ed2e771dde82bdf654, BF16,
  do_sample=false, thinking enabled, context 16384; planner output 6144 and
  worker output 2048. Keep current eight planning calls, two structural revisions,
  24-unit bound and 24 actions per operation, subject to compatible qualification.
- Choose target_rule=all in the NEW request before any generation. Freeze and
  validate the plan before deriving all meaningful owner targets. Do not modify
  an old uniform request, force the prior two-unit graph, or target idle workers.
- One clean branch plus one F branch per eligible owner. Pool seven gives a
  maximum of eight execution branches; actual count follows the frozen plan.
  This upper bound must be visible in the proposal and explicitly approved.
- First assigned publication loss before commit, persistent identity loss,
  existing public checking and recovery overlays. No S, R, policy switch,
  additional task, training, prompt tuning, or automatic retry.

### Matching and execution order

Freeze source, public/private task hashes, model, role locks, prompts, execution
settings and applicable qualification before the planning sequence. Bind the
resolved plan, planning journal/ledger and target list into durable branch
records. Both clean and loss runs start from original sources with empty artifact
stores and fresh histories; no clean checkpoint, answer or evaluator output is
an execution input for another branch. Planning is reused physically only.

Generate the entire branch schedule before evaluating clean success. Run clean
first, then eligible targets in sorted identity order, at concurrency one on the
same qualified hardware type and runtime. The clean score must not decide which
fault branches exist or run. Structural validity/admission failure is a recorded
planning outcome, not a reason to sample another plan until one succeeds.
Stop on infrastructure or provenance failures for explicit review and retain
unexecuted rows as missing; do not filter them from the report. An ordinary
completed clean failure is not an infrastructure stop or a target-selection gate.

A valid plan with K meaningful owners produces 1+K rows. If no valid plan is
obtained within the single planning sequence, retain its actual planning charges
and invalid/infrastructure status, with zero execution branches and no invented
fault targets. Report that planning outcome alongside the prespecified sequence
count; do not report an empty executed subset as successful.

### Budget and reporting

Use the same uncalibrated 100000-token/1200-CPU-second total cap for every branch.
Clone the fresh actual planning ledger into each branch; all subsequent primary,
public check, recovery and integration work reduces that remaining allowance.
Report physical planner work once, its logical replication count, and each
branch's ledger separately. Maximum aggregate logical allowance is 800000 tokens
and 9600 charged CPU seconds for eight branches; these are caps, not predictions
of measured physical or wall cost. Terminal evaluator charges remain separate.

Prespecify a table with planning status, K, clean success/conformance, target,
trigger status, F success/conformance, all obligations, replacement identities,
retained versions, direct bindings versus read exposure, total and post-alarm
resources, uncertainty, missingness and infrastructure outcomes. Never-triggered
F rows keep their reason and target denominator. Report fault outcomes whether
or not clean succeeds; any clean-success-conditioned summary must be separately
labelled and must not replace the all-outcome table. No episode-independent CI
or population-level recovery rate follows from this one-task/one-plan check.

Historical clean/F observations remain a separate development series. Their
cost differences are not matched treatment effects. This new check would compare
loss versus no loss under common recovery; it would not estimate recovery benefit
against no recovery, nor compare pre-execution planners.

### Required gates and later scientific comparison

The existing clean adapter permits one clean row and the conditional fault adapter
requires the historical successful plan. Neither implements this prospective
protocol. Do not relax their gates or splice manifests to approximate it.
A separately reviewed adapter must support durable planning-before-branching,
predeclared all-target resolution without clean-score filtering, inheritance of
fresh planning charges, complete outcome retention and interrupted planning.
Renew affected no-skip CPU, grammar, observation and memory qualifications;
observed footprint qualification is not a universal fit guarantee.

Before any submission, prepare an immutable proposal binding source/evidence,
seed, one planning sequence, branch upper bound, unchanged caps and limitations,
then obtain separate explicit approval. The actual plan/targets are necessarily
unknown before generation; the approved protocol must bind how their derived
records are created and checked rather than allow discretionary post-result
changes. No approval or scheduler job is created by this design document.

For a later scientific planner comparison, first specify two concrete
pre-execution planners, their public inputs/objectives and equal charged planning
allowances, while keeping workers, monitor and JIT common. Require qualified
independent task groups, prespecified splits and compatible calibration. Distinct
plans can have different meaningful owner counts: average targets within each
plan/task before task-level comparison; do not pool branch counts as independent
samples. A no-recovery/restart comparison would be a separate fixed-plan lane,
not an unannounced replacement of the intended planner comparison. None of these
broader gates is resolved by the present synthetic successes.
