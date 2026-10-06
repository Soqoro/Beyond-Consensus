# Open planning and scoped execution runbook

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
