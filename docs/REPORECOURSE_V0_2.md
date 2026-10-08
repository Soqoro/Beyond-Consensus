# RepoRecourse v0.2 migration and review

The additive [2026-10-08 richer-cohort implementation](RICH_COHORT_PILOT.md)
adds generic prospective scheduling and three implemented source-grounded
requests plus a blocked fourth candidate. It preserves the existing v2 Engine,
scopes, common JIT and accounting. New runtime hashes and explicit cohort gates
apply; historical v1/v2 records and narrow approvals remain unchanged.

Implementation date: 2026-09-29. This is a local software update, not a model
result or permission to run experiments. The supplied
`reporecourse_v0_2_codex_update_prompt.md` is preserved unchanged.
`reporecourse_environment_design_v0_2.md` was not present; the supplied prompt
is the implementation specification.

## Milestones and implementation map

| Milestone | Implementation | Limit / evidence |
|---|---|---|
| M0: compatibility | New `rr-planning-request-v2`, `rr-work-plan-v2`, `rr-frozen-planning-v2`, `rr-branches-v2`, `rr-engine-v2`, `rr-fixed-state-v2` records | No legacy records rewritten; new runtime hashes invalidate new execution approvals |
| M1: variable pools | `reporecourse.v2`, opt-in `Engine`/`Environment`, pool-bound action and planner schemas | Every integer 2–8, including 7; legacy defaults remain four |
| M2: planning | `PromptedPlanner`, requirement allocation, shared catalog selectors; optional `beyond_consensus.models.reporecourse_planner` bridge | Existing frozen backend reused, no training; no GPU generation performed |
| M2: execution | Existing Engine, artifact store, restricted compiler/interpreters, evaluator and Resources | Both fixture families, independent/shared/grouped/branch-rejoin reference drivers; optional child tests not run here |
| M2: common recovery | Existing JIT plus `v2_recovery.reuse_consumer`; original sources remain available | Bounded latest-public-version rebinding, public checking, normal reassignment/bypass; fallible, no hidden-score search |
| M3: analysis | Task-balanced `aggregate_v2`, paired invariant hashes, B0 estimator, grouped splits and two exports | Development-only; unresolved rows remain provisional; no simulated measurements |
| M4: handoff | `scripts/rr_v2.py`, opt-in existing qualification wrapper, guarded submission dry-run | V2 GPU task submission intentionally remains blocked; no new engineering exception |

Reused components include the immutable artifact/version store, F/S hooks,
fixed-state R snapshots, persistent worker histories, existing compiler child,
public checker, terminal private evaluator, logical-token/CPU ledger, frozen
Transformers backend, and legacy Slurm registry/snapshot/submission workflow.
There is no second scheduler, ledger, model stager, or artifact store.

### Scientific formulation

The main comparison varies a **pre-execution planner**, with a frozen worker
backbone and common public monitor/JIT. Open planning sees public requests,
source IDs/content, output contracts, workers, caps and declared threat; it
cannot publish final artifacts. Author outlines enter only authored selection
or labelled reference demonstrations. Planner output prose is bounded and
recorded; syntax validation does not prove that prose contains no solution.
No post-failure learned controller, SFT/RL trainer or simulator was added.

### Old and new semantics

- Legacy `rr-manifest-v1`, results, solo utility and four-worker execution stay
  on the existing path. V2 checkpoints cannot enter that path, or vice versa.
- V2 pools contain `w0..w(N-1)`, N=2..8. Adaptive allocation can leave identities
  idle; matched mode enforces planned K. Observed primary/total K count attempted
  action dispatch, including rejected/withheld contributions. Idle slots incur
  no fabricated token fee and never dilute target eligibility.
- The initial graph is an acyclic, terminal-covering graph of at most 24 units.
  Dependencies require matching declared artifact interfaces. Ready units run
  in lexicographic-ID order. Corrections publish new versions without rewriting
  the frozen plan. Actual bindings can add undeclared edges; see the 2026-10-06
  declared-versus-realized dependency audit below.
  A helper need not have the same name as its producing unit.
- Open, shared-catalog, and fixed-plan lanes are distinct. Only fixed-plan
  references can vary restart/replication versus the common JIT. A third-party
  backend needs `count_input` and `generate`; the benchmark imports no BC method.
- Targets are resolved **after freezing** from all meaningful planned owners,
  including intermediate producers. F uses seeded uniform or all-target
  enumeration. Never-triggered rows retain a reason and their denominator.
  S reuses persistent safe-artifact control; it is not a qualified model attack.
  R requires a common incident snapshot, is fixed-plan-only, and uses equal
  **remaining** resources with historical charges separate.
- Each end-to-end branch clones the actual planning ledger, never a free clean
  solution. Physical generation reuse is recorded separately. Same seeds do
  not guarantee identical generations after histories diverge.
- One existing backend serves isolated logical histories sequentially with
  re-prefill; no cross-worker KV-cache reuse is assumed. Pools do not allocate
  extra GPUs. The four-physical-GPU campaign cap is unchanged. Variable-pool
  context-switch/memory qualification is still pending.
- Complete@B averages prespecified conditions within each base task, then tasks.
  Clean/F/S/R remain separate. ASR uses paired clean-correct S observations and
  task-balanced eligible means. Missing, interrupted and prerequisite-blocked
  results have no final score. Invalid model plans remain observed failures.
- Budget profile remains `rr-logical-tokens-cpu-v1` with admission reconciliation
  v2: actual input + all output (reasoning once), independently measured CPU,
  uncertain interruptions retained. No token fee for identities/messages.
  B0 uses the explicitly selected `max_all_attempts` development statistic,
  includes wrong completed attempts, and returns uncalibrated on censoring or
  insufficient observations. It does not replace historical calibration.

### Bounded choices and remaining gaps

Structural signatures ignore owner/name renaming but are not complete DAG
isomorphism or semantic-equivalence proofs. Meaningful-work validation excludes
unused units, but cannot prove that arbitrary helper instructions add value.
No artificial eight-worker task expansion was introduced.

Common JIT can retain unaffected bindings, rebuild missing units with any
available in-pool identity, bypass absent helper inputs, and rebind an existing
terminal consumer to newer public helper versions. It checks that new bundle
publicly and preserves old programs and lineage. It does not diagnose every
semantically bad helper or automatically quarantine a covertly controlled
identity. Existing public failures can trigger ordinary regeneration. No
private evaluator result chooses a repair. Successful and unsuccessful repair
must be measured before claiming a strong model recovery baseline.

V2 model **task execution** fails closed pending task review, competence, B0,
pool-specific grammar and memory approval. The existing narrow Jaffle trio
exception does not authorize this new protocol. `slurm-dry-run` reports these
blockers instead of fabricating runnable `sbatch` arguments. The optional
prompted-planner bridge can generate only when explicitly invoked in an actual
Slurm allocation with the existing 27B BF16 checks and matching planner grammar;
that is not a task-execution approval or a variable-pool memory qualification.

The main qualification matrix exercises F reference behavior. R compatibility,
S visibility/atomicity, ledgers and general recovery are additionally covered by
unit tests and retained legacy controls. No new model S result or universal
worst-case claim is established. Full model-worker pool qualification remains
external work; a short early-EOS probe cannot establish worst-case fit.

## Results and unchanged readiness

Historical evidence remains separate:

- Corrected earlier Jaffle clean engineering run: 1/1, 29,745 tokens,
  404.791 CPU seconds; this is not a v0.2 result.
- Latest reported Track F revision: H100 preflight passed; fresh clean failed
  with 49,219 tokens and 787.108870858/1,200 CPU seconds, zero output bindings.
  Both loss branches remained unlaunched. The subsequent public SQL interface
  revision has CPU qualification evidence but no supplied new GPU task result.
- Inventory remains **three source-grounded drafts and two synthetic controls**,
  **zero independently reviewed source packs**. Jaffle semantics stay recorded
  payments. Energy provider-license review remains pending. No 12-task or
  100-task release, calibrated B0, trained planner, or model recovery claim.

The v0.2 reference matrix is **56 conditions / 188 branches**: two synthetic
families × seven pools × four genuinely different organizations, each with clean
and all meaningful-owner F targets. This count is a plan, not 188 passed tests.
Independent/shared/grouped alternatives already existed; branch/rejoin adds two
components feeding both terminal outputs. Private reference actions remain
labelled reference-only, never worker competence measurements. Grouped controls
reuse the independent reference programs explicitly (`reference_program_source`),
while executing their one-owner grouped plan. The original private fixtures are
unchanged. Cluster retry 1083811 exposed and stopped at the formerly missing
grouped-witness lookup; 19 test methods passed but the matrix was not qualified.
The shared selector now serves both the matrix and standalone demo.

## Subsequent cluster CPU evidence

User-reported job **1083826** completed successfully in **8m08s** at
`rr-v2.X1E9At`. All **21 test methods passed without skips**, including actual
restricted children and common consumer rebinding. The separate full fixture
report returned **passed**, `model_executed: false`. This supersedes the earlier
cluster driver-selection failure for that frozen revision only. The subsequent supplied compact summary confirms **56 conditions and 188/188
successful reference branches**, source commit
`72d8ee01e9e7976e97d8aa8225705443710c9cfc`, all pools 2–8 and all four
organizations in both fixture families. Evidence remains scripted_reference_only;
GPU_qualified is false. The full remote report has not been
independently retrieved here. Local optional dependencies remain absent.

This CPU pass does not supply tokenizer/grammar approval: that job had no
`--model-lock`. Pool-bound planner and worker grammars, model competence,
representative context-switch/memory testing, B0 and source-task review remain
pending. No new GPU job is authorized by these results.

### Subsequent pool-7 grammar evidence

User-reported CPU job **1083832** passed in **2m34s**. Both execution and planner
grammars passed at **16384** context tokens, with separate qualified locks under
`rr-v2.X1E9At/grammar-pool7.C22eIe`. `model_executed` is false. Exact qualification
keys are recorded in STATUS.md. Only pool 7 is covered; no GPU or other-pool
approval follows. The next implementation gap is a dedicated, guarded synthetic
context-switch preflight for the v0.2 pool. Current `slurm-dry-run` remains blocked;
legacy preflight is not a substitute. Task execution and research gates remain.

## Local validation of this update

- Full unittest discovery: **313 tests, 295 passed, 18 skipped** (76.996 s).
- Focused v0.2 suite: **20 tests, 18 passed, 2 skipped**. The skipped methods
  cover the two-family real-child matrix and common consumer reexecution.
- Of the 18 full-suite skips, 17 require the unavailable pinned SQLGlot/
  jsonschema/referencing stack; one is the optional legacy real sandbox test
  requiring `BC_SANDBOX_TEST_PROFILE`. None is counted as passed.
- Actual local interpreter: Python 3.12.7. sqlglot, jsonschema and referencing
  are absent. The explicit `qualify` command returned `blocked_prerequisite`.
  Nothing was installed to conceal these missing prerequisites.
- `check_shell.py`: all 10 shell files passed. Compileall, diff whitespace
  checks, and both CLI help commands under `python -I -S` passed.
- The standalone request/catalog/freeze/resolve/submission-gate workflow passed
  under `-I -S`: pool 7 with a shared three-owner plan resolves four branches.
  Submission remains blocked. No model generation or SQL execution was involved.
- No GPU run, scheduler submission, new source-task approval, commit, push,
  model/data download or training was performed.

## Local commands (no cluster submissions)

Run from the repository using Python 3.12+. Store generated files outside Git.

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
python -I -S scripts/bc.py --help
python -I -S scripts/rr_v2.py --help
git diff --check
export RR_V2_DIR="$(mktemp -d /tmp/rr-v2.XXXXXX)"
python -I -S scripts/rr_v2.py qualify --dry-run --output "$RR_V2_DIR/matrix.json"
python -I -S scripts/rr_v2.py readiness --sources /path/to/existing/reporecourse-v01 --output "$RR_V2_DIR/readiness.json"
```

### Executable example per family — private reference CPU evidence only

These use the actual restricted children, artifacts and evaluator, not a
method-name success shortcut. They require **existing** sqlglot 27.28.1,
jsonschema 4.25.1 and referencing 0.36.2. Missing pins block qualification;
do not install a different environment to hide a skip.

```bash
# Shared data-product helper; with two identities the survivor repairs units.
python -I scripts/rr_v2.py demo --task synthetic-stock --pool 2 \
  --lane fixed_plan --outline shared --target-rule all \
  --output "$RR_V2_DIR/data-shared.json"
# API/schema/mapping: two type components rejoin in both output contracts.
python -I scripts/rr_v2.py demo --task synthetic-nullable --pool 7 \
  --lane fixed_plan --outline branch_rejoin --target-rule all \
  --output "$RR_V2_DIR/api-rejoin.json"
# Full CPU reference matrix, only when pinned dependencies are available.
python -I scripts/rr_v2.py qualify --output "$RR_V2_DIR/qualified-matrix.json"
```

### Request → supplied plan → frozen plan → targets

This example deliberately labels supplied authored planning, not an open model
result. For an open request use `--lane open` and a third-party/generated plan.
`reporecourse.v2.requirement_plan(public, config)` is the requirement allocator.

```bash
python -I -S scripts/rr_v2.py request --task synthetic-stock --pool 7 \
  --lane shared_catalog --target-rule all --output "$RR_V2_DIR/request.json"
python -I -S scripts/rr_v2.py plans --task synthetic-stock --pool 7 \
  --lane shared_catalog --outline shared --output "$RR_V2_DIR/catalog.json"
python -I -S scripts/rr_v2.py select --task synthetic-stock \
  --input "$RR_V2_DIR/request.json" --plan "$RR_V2_DIR/catalog.json" \
  --selector first --output "$RR_V2_DIR/frozen.json"
python -I -S scripts/rr_v2.py resolve --input "$RR_V2_DIR/frozen.json" \
  --output "$RR_V2_DIR/branches.json"
python -I -S scripts/rr_v2.py validate --input "$RR_V2_DIR/branches.json" \
  --output "$RR_V2_DIR/integrity.json"
python -I -S scripts/rr_v2.py slurm-dry-run --input "$RR_V2_DIR/branches.json" \
  --output "$RR_V2_DIR/submission-gates.json"
```

Nominal/recovery catalog selectors require measured, exactly compatible
calibration keyed by the candidate set, configuration and model binding.
Model-generated catalog API calls require generation events plus their ledger.
No private witness costs are automatically supplied. `freeze --input REQUEST
--plan PLAN --task TASK --output NEW_FILE` accepts a raw supplied plan and marks
its generation unmeasured; it does not invent model charges.

Open-generation request setup can add `--backend-config EXISTING_CONFIG
--model-lock QUALIFIED_PLANNER_LOCK`. That verifies/resolves the actual staged
lock, never substitutes the remembered revision. The config's action constraint
must be `reporecourse-plan-v2-pool-N`; the lock must have fresh matching grammar
approval. Only a separately authorized allocation may invoke `prompted-plan`
with that request, task, pool, config and lock. **Do not invoke generation as
part of these local checks.** The bridge reuses the existing backend; other
backends can implement the same Python interface without BC imports.

### Analysis, resume and export

`aggregate --input` and `compare --input` accept a JSON list of branch manifests;
`--results` is a JSON list of recorded branch results. `export` and `evidence`
accept one branch manifest. Use fresh output paths. The split file assigns every catalog task to train/dev/test;
related groups must agree. Planner adapter IDs and catalog source/selector are
separate score groups; method names are not exposed to workers or evaluators.

```bash
python -I -S scripts/rr_v2.py aggregate --input /path/manifests.json \
  --results /path/results.json --output "$RR_V2_DIR/summary.json"
python -I -S scripts/rr_v2.py compare --input /path/manifests.json \
  --output "$RR_V2_DIR/compatibility.json"
python -I -S scripts/rr_v2.py export --input /path/branches.json \
  --results /path/results.json --splits /path/task-to-split.json --split dev \
  --export-kind plan_outcomes --output "$RR_V2_DIR/plan-outcomes.json"
python -I -S scripts/rr_v2.py export --input /path/branches.json \
  --results /path/results.json --splits /path/task-to-split.json --split dev \
  --export-kind event_trajectories --output "$RR_V2_DIR/trajectories.json"
python -I -S scripts/rr_v2.py evidence --input /path/branches.json \
  --results /path/results.json --output "$RR_V2_DIR/evidence.json"
```

Resume API: `run_branch(manifest, branch_id, public, private, worker,
checkpoint=previous_result['checkpoint'])`. The checkpoint binds branch,
manifest, plan, public data, configuration and frozen runtime. It restores
costs, identity state and recorded observations; unknown outstanding work is
charged, and completed assignments are not replayed. R additionally uses
`recovery.freeze`/`resume`; `resolve --incident SNAPSHOT` binds one R row to that
actual incident target and hash, rather than drawing another target; only the declared recovery policy and incident-threat→R transition may
vary in a compatible fixed-state diagnostic. Historical and remaining work stay
separate. Do not resume a terminal failure under changed code.

Exports keep proactive `inputs` separate from outcome `targets`. Recorded event
observations, actions, tool results and costs are used directly, never rebuilt
from final answers. Private witness trajectories cannot be exported as public
training data. No private tests or optimal-plan labels are added. Group overlap
is rejected across source, supergroup, base change, schema slice, template and
semantic group when metadata is present; missing metadata is not independence.
Pool interpolation/extrapolation is labelled separately from observed primary
count coverage. The sanitized evidence command omits raw actions/programs.

## Cluster handoff — preparation only

After local review, **manual push**, then browser-terminal pull. Use the existing
Python and source directories; no downloads are part of qualification.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export RR_V2_CLUSTER="$(mktemp -d "$BC_STORAGE/diagnostics/rr-v2.XXXXXX")"
bash experiments/qualify_reporecourse.sh --v2-controls --pool-count 7 \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --output "$RR_V2_CLUSTER/cpu" --dry-run
```

When submitting the wrapper directly, set `sbatch --chdir` to the frozen
source root, or pass `--repo-root` explicitly. Slurm spools the batch script;
its copied script path is not a repository location. Earlier frozen wrappers
can instead be invoked by an `sbatch --wrap` launcher using their absolute real
path. Preserve failed output directories and use a fresh retry output.

The same existing wrapper, without `--dry-run`, belongs in a **user-authorized
CPU allocation** with a frozen source checkout and `BC_PYTHON` exported. Do not
run the full matrix on the login node. Optional `--model-lock` checks both pool-7
planner and execution grammars and writes distinct locks. Those locks cannot
authorize another pool. The wrapper never self-submits. No `sbatch` command is
being executed or newly authorized here.

Next minimal proposal: complete that CPU qualification and review its actual
reports first. Then, if separately authorized and the remaining approvals are
implemented/satisfied, qualify the pool-specific one-model context-switch path
on one 80-GB-class GPU, concurrency one, and use one frozen plan with clean plus
one seeded F target. S stays blocked until its qualification exists. Preserve
the legacy exact-trio gate; do not relabel it as v0.2 approval or launch a grid.

## Synthetic pool context-switch preflight (2026-09-30)

The additive `bc rr-v2-preflight-manifest` command now freezes a **preflight-only**
manifest. It contains no tasks or episodes, embeds the separately qualified
planner lock and binds the worker lock and source revision. Both locks must
refer to identical staged weights and tokenizer. The existing `bc submit`
registry/scheduler/snapshot path enforces `--mode preflight --concurrency 1`.
Task execution, model branch dispatch and the v0.2 campaign gate remain blocked.

One backend/model instance serves N worker histories and one separate planner
history in two sequential rounds (16 calls for pool 7). Each retained history
has identity-specific inert numbered records, fitted with the actual tokenizer
to 14080–14336 input tokens, and requests its own exact synthetic `read_source`
action. No tool is executed. Each revisit re-prefills the same isolated history;
no other identity's response is included and no cross-call KV cache is supplied.
The worker and planner decoder objects switch on that same loaded backend.
This tests retained-history switching, not growing multi-turn task conversations.

The report includes actual input/output tokens (reasoning is a subset), unknown
usage reservations on exceptions, per-call process CPU/wall/device timing,
memory allocation/reservation/peaks, prompt hashes, runtime provenance, and exact
response/grammar/EOS checks. Unknown generation failure stops the sequence.
Qualification overhead is separate from historical episode work. No task-specific
inputs, references, model-generated programs, SQL execution or repair are used.
A `passed_observed_sequence` report is deliberately narrower than memory approval:
`worst_case_fit_established` and `task_execution_allowed` remain false. Early EOS
does not exercise the entire 2048-token output allowance; full-cap memory testing,
actual worker/planner competence, B0 and task review remain separate gates.

### Browser-terminal preparation after pushing and pulling

Use a clean committed checkout and the existing environment. These commands
create a fresh manifest and inspect submission only; they submit no GPU job.
The existing pool-7 locks remain usable only if their qualification fingerprints
still verify; do not edit locks to bypass a stale qualification.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RR_GRAMMAR="$BC_STORAGE/diagnostics/rr-v2.X1E9At/grammar-pool7.C22eIe"
export BC_RR_CONTEXT="$(mktemp -d "$BC_STORAGE/diagnostics/rr-v2-context.XXXXXX")"
export BC_RR_CONTEXT_LOCK="$BC_RR_GRAMMAR/model-lock-json.json"
# Use an existing reviewed cluster config for one full A100/H100 80-GB-class GPU.
: "${BC_RR_CLUSTER:?Set the existing reviewed cluster configuration path}"
(
set -euo pipefail
"$BC_PYTHON" scripts/bc.py rr-v2-preflight-manifest \
  --pool 7 --model-lock "$BC_RR_CONTEXT_LOCK" \
  --planner-lock "$BC_RR_GRAMMAR/model-lock-plan.json" \
  --output "$BC_RR_CONTEXT/manifest.json"
"$BC_PYTHON" scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_CONTEXT/manifest.json" \
  --model-lock "$BC_RR_CONTEXT_LOCK" --dry-run
)
```

After reviewing the dry run and separately authorizing the one-GPU qualification,
use the same submit command without `--dry-run`, saving its output to a new
submission record. Do not use `--mode run`. Preserve any failed report and use a
new reviewed attempt rather than overwriting it. No GPU result for this probe
has yet been measured.


## Exact full-budget tensor geometry stress

The observed pool-7 sequence subsequently passed on H100 PCIe (16/16 calls,
237,144 tokens, 760.892 seconds; supplied summary recorded in STATUS.md).
Every call stopped before 2048 output tokens. Preserve that historical report.

Use `rr-v2-preflight-manifest --full-budget-stress` in a **new** directory for
the separate `rr-forced-token-full-budget-v1` protocol. Scheduler/registry,
concurrency-one, lock, source and task-run guards are the same. Pool 7 makes
16 calls, with exactly 14336 input and 2048 output tokens per successful call:
262144 total tokens. The synthetic prompt is padded with attended inert token
IDs to reach the exact input length. A diagnostic-only logits processor forces
one non-EOS token, minimum/maximum output are both 2048, and EOS/forced-EOS
termination is disabled for these calls only. No generated text is executed.

Both grammar objects and one frozen model remain resident while identities and
roles switch; normal grammar masking is not applied to the forced sequence.
No task generation settings or backend implementation are modified. Fresh caches
are created per call, retained histories are independently revisited, and
outputs are not inserted into another history. Exact output IDs/count, processor
call count and returned cache length must verify; absent cache telemetry cannot
pass. Timing and all input/output tokens are separately reported as diagnostic
work. Early stop, OOM, missing evidence or token mismatch cannot establish fit.

`full_budget_geometry_passed: true` establishes the measured tensor dimensions
under this synthetic intervention only. `worst_case_fit_established: false`
and `task_execution_allowed: false` remain intentional. Different attention
content, normal decoder behavior, growing conversations and hardware variants
are not universally qualified. No real result exists for this new stress probe.

After pushing/pulling, reuse the verified existing worker/planner locks only if
their fingerprints still pass. Create a fresh directory and manifest:

```bash
export BC_RR_STRESS="$(mktemp -d "$BC_STORAGE/diagnostics/rr-v2-stress.XXXXXX")"
(
set -euo pipefail
"$BC_PYTHON" scripts/bc.py rr-v2-preflight-manifest \
  --pool 7 --full-budget-stress \
  --model-lock "$BC_RR_GRAMMAR/model-lock-json.json" \
  --planner-lock "$BC_RR_GRAMMAR/model-lock-plan.json" \
  --output "$BC_RR_STRESS/manifest.json"
"$BC_PYTHON" scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_STRESS/manifest.json" \
  --model-lock "$BC_RR_GRAMMAR/model-lock-json.json" --dry-run
)
```

This block submits nothing. A user-authorized GPU submission uses the same
command without `--dry-run`, once, with a new submission record. Full-length
calls take longer than the earlier sequence; retain the reviewed two-hour
allocation. Do not reuse earlier success as this probe's result or launch task
runs after a geometry pass.


## Readiness audit after both pool-7 GPU probes (2026-09-30)

### Evidence and conclusion

| Gate | Evidence available in this review | Decision |
|---|---|---|
| CPU runtime/reference controls | Supplied 56-condition, 188/188-branch matrix; 21 cluster tests | Reference harness evidence only |
| Pool-7 worker/planner grammars | Supplied passing reports/keys for 16K context, separate locks | Pool-7 syntax evidence; current/historical binding still needs full records |
| Normal-decoder retained-history switching | `78419528eb91d65c58517565ad196ff82c7f84f76a1e240c80ce7d4996c6cc79`, 16/16 calls, 237144 tokens, H100 PCIe | Observed sequence passed |
| Forced full-budget geometry | `b67a0fa3e511f82a1f3120dedd70a3f6a06e34daca2dd9a4bbf8507d855c6939`, 16/16 calls, 262144 tokens, H100 PCIe | Exact synthetic geometry passed |
| Full provenance across probes | Compact summaries only; full manifests, report runtimes and frozen locks not supplied locally | Pending verification; do not assert the two runs share identical model/runtime bindings |
| Worker task competence | No v0.2 model task run supplied | Unmeasured |
| Planner competence | Preflight requested read_source, never submit_plan | Unmeasured |
| B0/calibration | No compatible measured development set | Uncalibrated |
| Source-task review/legal variation | Draft tasks and scripted synthetic controls | Native policy campaign blocked |

The supplied stress attachment was read directly. All seven workers and planner,
in both rounds, report exactly 14336 input tokens, 2048 output tokens, cache
length 16383, 2048 mask calls, verified inert token and no error. The summary
reports 262144 actual tokens, zero uncertain tokens, 2159.1261775558814 seconds
(about 36 minutes), and 61960355840 peak reserved bytes (about 57.7 GiB).
This is reported allocator reservation, not total device use or a guaranteed
free-memory margin. The lower reservation than the earlier probe is not an
optimization result. Both normal and forced probes used one reported model
instance; no task competence inference follows from their pass counts.

The practical conclusion is that the tested pool-7 sequential architecture and
full configured token geometry have positive H100 evidence. Another identical
stress rerun is not the default next step. Universal worst-case proof is not a
reasonable substitute for measuring actual bounded task behavior; retain OOM,
context and budget failures explicitly in any future diagnostic.

### Provenance verification still required

The local reviewer has not read the remote full JSON/snapshots. Preserve both
preflight directories. Collect, for each exact experiment ID above:

1. Full `preflight.json` and its matching `manifest.json` (with original fields).
2. The snapshot's `snapshot.json`, `resolved/manifest.json`, and
   `resolved/model-lock.json`; the planner lock is embedded in the manifest.
3. File SHA256 values, scheduler job/state/exit code, and snapshot verification
   result. Use actual runtime `snapshot_id`, not a remembered source revision.

Check manifest self-hash, report experiment/manifest/source binding, snapshot
inventory and resolved-manifest equality, worker-lock digest, planner/worker
weight and tokenizer identity, qualification keys, actual runtime model settings,
packages, device, and complete call sequence. Compare normal and stress conditions
field-by-field, allowing the documented probe intervention and source revision
changes explicitly. Historical qualification must be checked against its frozen
source, not relabelled stale merely because current source advanced. Hashes prove
internal integrity, not independent authenticity. Missing records stay unknown.
None of this requires model loading, SQL execution or a new GPU job.

### Current implementation constraints

`reporecourse.v2.resolve_branches` always sets `gpu_submission_allowed=False`.
`run_branch` rejects `worker.mode == 'model'` before execution. Those are literal
implementation blocks, not dynamic approval checks that become true after a
preflight report appears. Preflight manifests contain no task episodes and the
normal runner explicitly rejects them. The new GPU reports are not currently
consumed by a v0.2 task authorization path.

`PromptedPlanner` and its optional BC bridge can create a frozen public-input
plan with charged source reads/generation, but the standalone `prompted-plan`
command has no dedicated shared-registry qualification submission integration.
Do not invoke it via a hand-written sbatch job to bypass that requirement.
A successful plan also cannot pass the model-worker task gate. Scripted CPU
outlines and references must not be presented as generated plans.
Two implementation details must be addressed by a future exception: after the
current guard, `run_branch` assigns non-reference execution the label
`scripted_mock`; merely deleting the guard would therefore mislabel real model
results. Also, unexpected backend exceptions in the prompted-planner bridge need
an outer persisted failure/usage record; they must not disappear because no
frozen-plan file was written. Audit these paths and failure accounting before
adding any real-model diagnostic runner.


### Smallest next competence diagnostic — historical proposal

The 2026-10-02 single-stock adapter below implements only the first worker
stage. The second-family and planner stages remain proposals, not approvals.

First separate worker competence from planner competence:

1. **Worker stage:** one clean seed-0 episode on `synthetic-stock`, pool 7,
   fixed authored independent outline, same frozen model/common public JIT.
   Run once and review. This checks public source reading, valid publication,
   explicit bindings, execution and both terminal obligations. The supplied
   outline is labelled authored; no private reference program is supplied.
2. **Second-family stage, only after review:** one clean seed-0 episode on
   `synthetic-nullable` under the same bounded profile. Do not automatically
   queue it behind the first stage. One family passing cannot qualify the other.
3. **Planner stage, only after worker review:** one public-only generated plan
   for the already exercised fixture; stop at frozen-plan validation. At most
   the existing eight planner calls/two revisions; no hidden evaluator feedback,
   no branch expansion or target selection before freezing. A valid plan is
   structural evidence only, not successful task execution or planner superiority.

Proposed task caps reuse the declared 100000-token/1200-CPU-second engineering
profile, 24 actions per existing worker operation, 16K context and 2048 output
cap. These are **uncalibrated engineering caps**, not B0. Every generation,
re-prefill, rejection, compiler/executor operation, public check and repair
remains charged. Hidden evaluation stays terminal with its separate recorded
ledger. All attempts remain in planned coverage; interruptions and infrastructure
failures stay explicitly unresolved rather than being converted into semantic
failures or omitted. Terminal scientific failures are not rerun; eligible retries
preserve prior/uncertain charges and attempt provenance. Keep original immutable
reports and frozen snapshots.

This requires an explicit new synthetic-qualification manifest/runner exception
with exact task/condition hashes, evidence verification, registry concurrency
one and tests rejecting native tasks, faults, grids and policy comparisons.
Do not remove the general model block or substitute scripted_worker labels.
Task review/B0 are campaign gates; requiring already-measured competence/B0 to
run the sole diagnostic that measures them would be circular. A narrow labelled
exception must address that distinction explicitly, without calling its caps
calibration or expanding the legacy Jaffle authorization. It is not implemented
or authorized by this audit alone. No new GPU execution or policy campaign was
launched, and no historical score was changed.


### Executable offline provenance audit

After pushing/pulling the verifier, run the following in the browser terminal.
This uses existing small reports and source snapshots only; no GPU allocation,
model-weight read/download, SQL or scheduler submission is performed. It does
not import or execute code from historical snapshots. The historical grammar
keys are linked to the frozen records, not recomputed using today's Python/code.
The two supplied experiment IDs are explicit inputs; no latest-directory guess
is used. If either output root differs, locate its recorded submission output
and change that path rather than copying evidence between experiments.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RR_AUDIT="$(mktemp -d "$BC_STORAGE/diagnostics/rr-v2-audit.XXXXXX")"
"$BC_PYTHON" -I scripts/audit_rr_v2_preflights.py \
  --normal-run "$BC_STORAGE/outputs/qwen27b-na100/78419528eb91d65c58517565ad196ff82c7f84f76a1e240c80ce7d4996c6cc79-preflight" \
  --stress-run "$BC_STORAGE/outputs/qwen27b-na100/b67a0fa3e511f82a1f3120dedd70a3f6a06e34daca2dd9a4bbf8507d855c6939-preflight" \
  --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_RR_AUDIT/provenance.json"
"$BC_PYTHON" -m json.tool "$BC_RR_AUDIT/provenance.json"
```

A missing file, mismatched report or failed call yields `failed` and exit 2;
incompatible pair settings yield `binding_mismatch` and exit 2. A consistent
pair yields `verified_internal_bindings_review_pending`, not a task approval.
Changed source files are listed for separate inspection and scheduler completion
is not silently inferred from a JSON success field. Report hashes establish
internal integrity, not independent authenticity. Preserve failures and export
the new audit JSON for review; do not rerun GPU probes merely to make provenance
match. No model competence test is automatically scheduled by this command.


## Single synthetic-stock diagnostic workflow (2026-10-02)

This implements only the worker-stage exception proposed above. Use the new
`rr-v2-competence-manifest` command, followed by shared `submit --mode run`.
Do not submit a new preflight or use the standalone v2 branch runner. The frozen
normal/stress pair is reverified offline and the new allocation checks its actual
runtime against that evidence. A passing run would establish one synthetic
observation only. Stop for review after this episode.

### 1. After committing/pushing the implementation, prepare the cluster directory

Run in the Beyond-Consensus browser terminal. All paths below are from the
reported cluster setup. Missing paths stop the block; locate the actual file
rather than substituting a different model or qualification.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_STOCK="$(mktemp -d "$BC_STORAGE/diagnostics/rr-v2-stock.XXXXXX")"
export BC_STOCK_LOCK="$BC_STORAGE/diagnostics/rr-v2.X1E9At/grammar-pool7.C22eIe/model-lock-json.json"
export BC_STOCK_CLUSTER="$BC_STORAGE/diagnostics/reporecourse-track-f.m433Oa/cluster.ph100.json"
(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'Stop: preserve changes/reports outside the frozen checkout first.\n'
    exit 1
fi
test -s "$BC_STOCK_LOCK"
test -s "$BC_STOCK_CLUSTER"
mkdir "$BC_STOCK/source"
git archive HEAD | tar -xf - -C "$BC_STOCK/source"
git rev-parse HEAD > "$BC_STOCK/source-commit.txt"
chmod -R a-w "$BC_STOCK/source"
"$BC_PYTHON" -I scripts/audit_rr_v2_preflights.py \
  --normal-run "$BC_STORAGE/outputs/qwen27b-na100/78419528eb91d65c58517565ad196ff82c7f84f76a1e240c80ce7d4996c6cc79-preflight" \
  --stress-run "$BC_STORAGE/outputs/qwen27b-na100/b67a0fa3e511f82a1f3120dedd70a3f6a06e34daca2dd9a4bbf8507d855c6939-preflight" \
  --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_STOCK/provenance.json"
)
```

### 2. Run current CPU task controls once

This CPU-only allocation executes the fixed trusted reference machinery. It
loads no model. Explicit positional paths avoid Slurm's spooled-script directory.

```bash
(
set -euo pipefail
set -o noclobber
cat > "$BC_STOCK/cpu.sh" <<'SH'
#!/bin/bash
set -euo pipefail
cd "$1"
exec "$2" -I scripts/bc.py rr-qualify \
  --task synthetic-stock --sources "$3" --output "$4"
SH
bash -n "$BC_STOCK/cpu.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=00:30:00 --job-name=rr-stock-cpu \
  --chdir="$BC_STOCK/source" \
  --output="$BC_STOCK/cpu.out" --error="$BC_STOCK/cpu.err" \
  "$BC_STOCK/cpu.sh" "$BC_STOCK/source" "$BC_PYTHON" \
  "$BC_STORAGE/datasets/reporecourse-v01" "$BC_STOCK/qualification.json" \
  > "$BC_STOCK/cpu-job.txt"
cat "$BC_STOCK/cpu-job.txt"
)
```

Wait for this job to finish. Inspect `sacct` and the CPU output/error logs. The
manifest command checks the full report, including negative controls; a status
string alone is insufficient. If the worker lock is stale, stop and review the
changed grammar fingerprint rather than weakening the check.

### 3. Freeze the one-episode manifest and inspect the dry run

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
test "$(git rev-parse HEAD)" = "$(cat "$BC_STOCK/source-commit.txt")"
"$BC_PYTHON" -I scripts/bc.py rr-v2-competence-manifest \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --model-lock "$BC_STOCK_LOCK" \
  --qualification "$BC_STOCK/qualification.json" \
  --preflight-audit "$BC_STOCK/provenance.json" \
  --output "$BC_STOCK/manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_STOCK_CLUSTER" --manifest "$BC_STOCK/manifest.json" \
  --model-lock "$BC_STOCK_LOCK" --dry-run
)
```

Expected: one episode, array `0-0%1`, one GPU in PH100q, the configured 128G host
memory and two-hour wall limit. Availability is determined by the scheduler;
these settings are not a claim that resources are currently free.

### 4. Submit once, then collect after scheduler completion

```bash
(
set -euo pipefail
set -o noclobber
cd "$HOME/Beyond-Consensus"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_STOCK_CLUSTER" --manifest "$BC_STOCK/manifest.json" \
  --model-lock "$BC_STOCK_LOCK" > "$BC_STOCK/submission.json"
cat "$BC_STOCK/submission.json"
)
```

After that job completes, collect to a fresh file. This does not execute a model
or SQL, and can report missing coverage without replacing historical results.

```bash
export BC_STOCK_OUTPUT="$("$BC_PYTHON" -c \
'import json,sys; print(json.load(open(sys.argv[1]))["output"])' \
"$BC_STOCK/submission.json")"
export BC_STOCK_REPORT="$(mktemp "$BC_STOCK/review.XXXXXX.json")"
"$BC_PYTHON" -I scripts/bc.py aggregate --output "$BC_STOCK_OUTPUT" \
  > "$BC_STOCK_REPORT"
"$BC_PYTHON" -m json.tool "$BC_STOCK_REPORT"
printf 'Review file: %s\n' "$BC_STOCK_REPORT"
```

Do not launch `synthetic-nullable`, a planner or a fault branch automatically.
Terminal failures remain terminal. Infrastructure failure/interruption also
requires explicit recovery review for this first adapter; `resubmit` does not
silently restart it with a fresh budget. Full journals/trajectories remain under
the episode output; the compact aggregate includes the terminal evaluation and
resource ledger, not private witnesses or model histories.


## Declared versus realized dependencies: stock trace audit (2026-10-06)

### Evidence and observed outcome

User-supplied aggregate and selected episode trace identify experiment
`853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06`, episode
`88b40ff1cd8da4481793f27dfe7c86238c6f9a1f3e279021a85f37097a88e4b1`.
The export reports raw manifest SHA256
`a400d136366d1c71583784b9cfc84f80ce8e77706e30746a95ca85bcf3176fc8`
and result SHA256
`7bf6f1655d24e723d2ef2cb0359c2aecc4c84af563c0f85f3bb61209562c0cc2`.
These are supplied identifiers: the full remote files/snapshot were not retrieved
or independently rehashed in this audit. The selected trace is internally
consistent with the supplied aggregate. No model or SQL was executed for review.

The one clean synthetic episode completed successfully. Both `stock_report`
and `zero_report` passed both terminal fixtures (four checks). The pool had
seven identities, but only w0/w1 were assigned and active; w2–w6 published nothing.
There were no recorded failures, public alarms, repair actions or explicit
rebindings. Two artifacts were published, bound, executed and retained.
Three EOS-completed calls consumed 2951 input plus 600 output tokens = 3551;
429 reasoning tokens are a subset of the output, not an extra charge. Episode
CPU was 39.115224506/1200 seconds, tokens 3551/100000; uncertain usage and pending
reservations were zero. Terminal evaluator CPU was separately recorded as
0.030292715 seconds. These are one observation under uncalibrated caps, not B0.

| Unit / owner | Declared inputs | Observed action sequence | Tokens |
|---|---|---|---:|
| stock_report / w0 | No artifact dependencies | Read tables; publish SELECT sku, qty FROM stock ORDER BY sku | 2212 |
| zero_report / w1 | No artifact dependencies | Publish SELECT sku FROM stock_report WHERE qty = 0 ORDER BY sku, explicitly binding w0's version | 1339 |

The declared plan has zero artifact edges. The actual graph has one edge:
`stock_report -> zero_report`. The consumer binds version
`de4fa2f4ff1b5d1abca7232b7a808dd20c3207f5417b394a3016589fdf939893`;
the same version is the bound stock output. Its own bound version is
`f57a666c0fcaa71724ff8b6b29f06b78436e15f4c09de142a427b709d349471e`.
The consumer's exposure also includes the stock version. Both bound IDs exist
in the supplied artifact map. No explicit artifact-read call occurred: a binding
is an execution dependency even when the worker never reads the artifact body.

### Code audit and scientific conflict

`v2.validate_work_plan` checks acyclicity, terminal coverage, owners, interfaces
and agreement between declared `depends` and `consumes`. `Engine` schedules the
normalized plan and checks declared artifact availability. Those checks do not
turn the plan into a runtime access-control list.

`Environment.observation` exposes all existing artifact names, versions and
formats, plus bound outputs. `publish` checks existence of each bound version,
compiler safety and artifact closure; it does not compare bindings against the
assignment's `consumes`. It unions bindings with the worker's recorded exposure.
`read_artifact`, `execute_artifact`, messages and `bind_output` are also available
outside the declared consumer list. Source reads check the public source map,
not the assignment's `sources` subset. These are current permissions, not newly
introduced behavior. Changing only the publish check would not enforce complete
information-flow independence. Empty `consumes` is not proof of isolation.
Automatic metadata visibility is not itself an explicit artifact-read event;
full observation histories are needed to audit that exposure. An empty recorded
exposure set cannot establish absence of all cross-worker information.

The earlier wording “Corrections publish new versions, not a changed DAG” is
accurate for the frozen plan record but incomplete for executed artifact lineage.
`independent` is an authored plan ID; it cannot certify independent execution.
Plan-only structural descriptors describe the assigned graph, not the observed
version graph. Under current semantics, a planner comparison could estimate the
end-to-end effect of different plans with common adaptive workers; it cannot
attribute outcomes to enforced graph topology. There is no such measured planner
comparison in this episode.

### Decision and boundaries for the next phase

Preserve the existing permissive runtime and historical score. Treat the frozen
plan as the scheduling/assignment specification; distinguish it from both the
realized version-binding graph and the broader context-exposure graph. This is
a clarification of current behavior, not a new execution condition or retroactive
failure criterion. The stock result establishes clean artifact production,
explicit cross-worker version reuse and finite-test correctness. It does not
establish source-independent reconstruction, seven-active-worker competence,
recovery effectiveness or model-generated planning.

Before comparative planner experiments, add an offline, versioned conformance
report with declared and actual edges, missing/extra edges, primary versus repair
stages, producer unit/version identities, planned/observed active counts and
unknown/ambiguous mappings. Use publication events and assignment context to map
versions to units; names or authors alone can be ambiguous. Track context exposure
separately from executable bindings. Missing traces remain unknown, not “no drift”.
This reporting is proposed work, not implemented by the present audit.

If a future study needs an enforced-topology treatment, define it separately:
primary bindings and cross-worker information access need a reviewed interface
rule; rejected attempts retain their costs; common repair needs an explicit
exception that permits version replacement and bypass. Freeze that choice before
execution, renew relevant controls/manifests, and do not pool it with historical
permissive runs. Do not silently add strict enforcement to this successful run.

The second-family synthetic-nullable exception and planner stage remain blocked
pending their own implementation/review. No rerun, new job, source-data change,
scoring change or campaign expansion was performed by this audit.


## Open planning contract update (2026-10-06)

The later user decision selects open-generated bounded topology with an opt-in
plan-scoped execution contract. This supersedes the earlier proposal-only status
of automated conformance and scoped mediation, without changing historical
adaptive behavior or qualifying any new model experiment. The implementation,
source map, limits and CPU/preflight commands are in
[OPEN_PLANNING_RUNBOOK.md](OPEN_PLANNING_RUNBOOK.md).

New protocol `rr-open-planning-v1` separates `planning_lane` from
`execution_contract`. The original validator, prompted planner, Engine, resource
ledger, common JIT, restricted executors and scheduler remain in use. Generated
units need not resemble authored organizations. Structural validation permits
inefficient unused helpers in the new condition, but such units do not become
meaningful fault targets. Original sources are available everywhere; declared
artifact edges are optional input permissions.

Scope admission fixes import versions, records fresh assignment contexts and
mediates all worker-facing artifact and message paths. Recovery changes only
recorded affected scopes after existing public triggers. New grammar/control
approvals and model/footprint evidence remain required. Local CPU doubles are
labelled, and the production open-task entry remains blocked for separate review.


## Open clean and conditional recovery milestone (2026-10-08)

The audited synthetic-stock open clean experiment `1517216133b6…` succeeded;
subsequent separately approved conditional F experiment `f6066eca22da…` recovered
successfully after either meaningful owner loss. Full uploaded traces support
conformance, exact version lineage, public-triggered scope changes and inherited
planning charges. These are model observations on one selected successful plan,
not scripted reference results or general campaign qualification. All raw
historical records remain unchanged. See the detailed audit and proposed
prospective clean/F design in [the open-planning runbook](OPEN_PLANNING_RUNBOOK.md#completed-conditional-recovery-audit-2026-10-08).

The proposed fresh comparison resolves its all-owner schedule after freezing a
new plan and before inspecting clean correctness. It needs a distinct adapter,
current compatible qualification and explicit approval; neither existing narrow
adapter authorizes it. Comparing recovery policies or scientific planners remains
a separate question with task, calibration and design gates outstanding.
