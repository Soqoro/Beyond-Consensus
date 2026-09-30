# RepoRecourse v0.2 migration and review

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
  in lexicographic-ID order. Corrections publish new versions, not a changed DAG.
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
