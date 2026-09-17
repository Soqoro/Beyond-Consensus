# Bounded validation cycle

## Implementation plan (2026-09-17)

1. Reuse native staging and reference controls to report sanitized per-task
   readiness, deterministic bounded selection, source/reset integrity and joint
   validation. Missing author materials remain an external scoring blocker.
2. Instrument the existing allocator without changing decisions; reconcile saved
   ledgers and separate current-code reproductions from historical evidence.
   Exercise real preparation paths with labelled constructed tests and prepare
   opt-in operation measurements with separate holdout groups.
3. Audit SILO model/context handling, add evaluator-only error attribution, and
   freeze fresh-source full/local/boundary batteries. Boundary inputs must be
   actual submitted artifacts. Add opt-in serialization/model profiles without
   changing defaults or exposing arithmetic answers.
4. Add explicit public/evaluator/execution metrics, sanitized provenance and
   generation diagnostics. Preserve legacy fields, terminal results, lazy GPU
   imports, source snapshots and the shared Slurm guard.
5. Run the required local checks and document actual evidence, blockers and
   ordered browser-terminal dry-run commands. No jobs, downloads or pushes.

The existing uncommitted documentation is preserved. Locally available cluster
evidence consists of summaries and user-supplied conversation excerpts; the
complete remote pilot ledgers, model locks, job inventories and native database/
author-material staging are not available in this checkout.

## Implemented paths and current evidence

### A. Native prerequisites and reference controls

`sqlite-readiness` writes a sanitized JSON report with a human summary. For each
record it reports release, database/group/split, pinned database/document hashes,
private material presence and exact-record approval, supported translations,
setup/cleanup and joint-state status, blockers and manual actions. It never
prints reference SQL, hidden tests, reviewer notes or private paths. With no
staging manifest, it reports `scoring_unavailable`, with unknown readiness/counts.
The historical 270-record inspection is preserved; it was not rerun locally.

`sqlite-validate --up-to --count 10` deterministically selects supported reviewed
development tasks by artifact kind, group and ID. It executes the reviewed
reference bundle, repeats the same bundle after reset, checks source integrity,
and tests omission and semantic corruption of every obligation. Reports include
evaluated counts and strict/native-subset comparison diagnostics for ordering,
duplicates, NULLs, two-decimal rounding and empty outputs. All controls have
separate charged work. `--count` without `--up-to` keeps its old exact-count gate.

The runtime still accepts only its complete restricted SELECT grammar and view
definitions. Raw SQL, writes, triggers, window expressions/CTEs outside that
grammar, arbitrary Python tests and nonempty setup/cleanup remain unsupported.
Native comparisons are a reviewed result-comparison adaptation, **not execution
of the full upstream Python scorer**. Reference controls do not establish model
competence. Large file hashing and database controls belong in CPU allocations.

`sqlite-pairs --count 2` requires two explicit candidate pairs and preserves
rejected candidates and missing selection slots. Each check sees the **same
whole artifact bundle**, using disposable copies of the same initial state;
supported checks are reads, so no evaluator mutation is admitted. Only
`crypto_M_2 + crypto_8` is currently named. It remains unvalidated; a second real
candidate needs material/compatibility review. No candidate or score was invented.

Local integration blocker: no registered native databases, approved author
solutions/tests, review file or staged model lock exists in this checkout. The
new controls passed on labelled synthetic records only. Native and paired model
configs can be made from actual validated data with `validation-config`; no
four-policy native run is authorized or prepared as a substitute.

### B. Zero preparation, the 256 units, and the scientific conflict

`allocation_diagnostics: true` instruments the existing allocator. It records
all candidates, preparation owners, route executors/dependencies, pruning,
compromise/detection scenarios, schedules, base/recourse costs, reserve, objective,
calibration provenance and solver limits. Checking/integration/search overhead
are explicitly **unmodelled in the allocator objective**, not predicted as zero.
The configured reserve is enforced by execution; the recovery objective itself
uses its existing total-cap check. No policy or cost decision changed.

Current code, four independent SQLite units, sufficient cap and equal disclosed
cold/prepare/prepared predictions reproduce **32 candidate plans × four excluded
identities × two visited states = 256 finite-search units**. JIT visits zero
primary search states. Both also pay one catalogue-setup unit. The implementation
path is `EpisodeEngine.plan_primary → choose_plan → solve_allocation →
shortest_schedule → BudgetLedger.reconcile_work`. This is a documented
`token_tool_surrogate_v1` planner charge, not generated tokens, wall time, a
minimum allowance or an invented 256 constant. The tested reproduction used
explicit predictions of 2000 each; those are **not measured GPU costs**.

This matches the reported recovery/JIT gap in both conditions, but **does not
prove the historical attribution**. Full pilot `result.json` ledgers, checkpoint
cost estimates and raw events are not local. `allocation-audit` reconciles every
available result's entries, stages, total, model token formula, recorded plan and
group mean; the exact remote attribution remains pending that command. The
checked-in pilot configuration has no calibration file. Actual historical
resolved calibration provenance remains unknown. No measured preparation benefit
or real-model calibration has been established.

**Conflict with the requested nonzero-selection test:** the present catalogue
lets JIT buy the same source indexing after the alarm at the same additive price,
without a latency/deadline advantage for advance preparation. For any advance
plan P and scenario s, JIT can buy its surviving preparations and use its repair
schedule. Thus `repair(empty,s) <= preparation(P) + repair(P,s)`. Adding the same
primary cost and taking the maximum over scenarios makes no preparation weakly
dominate that plan. An empty candidate is visited first, so ties retain it. Merely
making prepared reconstruction cheaper cannot reverse this result.

Therefore this cycle does **not** force an empirically selected nonzero plan or
weaken JIT to obtain one. Tests cover trace-equivalent decisions, several cheap
warm-cost cases retaining no preparation, replication selection, execution of an
explicit **constructed behavioral preparation plan**, charged artifact/context
restoration, compromised-contributor rejection and JIT's identical after-alarm
operations. The requested test of a strict nonzero optimum under this unchanged
catalogue is not satisfiable. A future changed scientific model of phase-specific
availability/latency or primary reuse would need explicit review and measurement.

Future ledger entries have additive stable charge IDs; reconciliation detects a
duplicated entry ID, inconsistent totals/stages, or a doubled model-token charge.
Legacy identical entries without IDs remain ambiguous and are never deleted.
The charge semantics and historical results are unchanged; this is observation
schema `bc-ledger-observations-v2`, with the same work unit.

`measurement-plan` freezes two training and two disjoint holdout development
sources. One single/clean execution per source measures six operations on each
of its four units: cold execution; requested source index; subsequent execution
using that index; requested outline; subsequent execution using that outline;
full independent replication. That is **four executions, 16 units, 96 bounded
operations**, all through the existing worker/ledger/Slurm runner. Failed/missing
preparations stay unavailable. Interrupted operation work remains charged.

`measurement-report` records sample origin, total preparation-plus-execution,
mean estimates and holdout prediction errors. These measurements use explicit
style requests and do not automatically replace the allocator's combined
index/outline calibration. Compatibility binds the measurement condition;
activation is deliberately unavailable without an explicit matched-operation
review. No favorable cost relationship or nonzero-preparation pass condition is
assumed. Mock operation measurements are labelled `mock-measured`.

### C. SILO interface audit and bounded competence conditions

The supplied third-smoke excerpt has correctly named current assignments and
15-element shards. Actual predecessor versions expose final values 386, 458 and
436. All four submissions have valid shape. Offline replay gives 15/60 globally
correct values, all in u0. Boundary checks fail in u1–u3; u1 and u2 each also have
one incorrect local increment. u3's later increments agree with its own shard.
The repeated u1 answer is not evidence of a cache defect.

Code audit: one persistent identity carries the single/clean history through all
four units; predecessor reads are version-bound and charged. The backend encodes
the full history on each call and does not reuse answers or cross-call KV state.
Its `use_cache=True` is confined to a generation call. Context/observation limits
fail explicitly rather than silently truncating. Completed wrong results remain
terminal; manifest/source identity prevents resuming them under a changed setup.
Strict JSON parsing and operation-specific tool validation remain unchanged.

Unavailable for that historical run: exact rendered template/input token IDs,
generation token partitions/stopping reasons, raw complete checkpoint, actual
job/snapshot and hardware. No such records were reconstructed. Future private
journals record message and rendered-token hashes, assignment/seed/version reads,
history size, context/generation limits, output/reasoning tokens, stopping cause
and memory peaks. Bundles include allowlisted job/snapshot, resolved model/config,
model-lock identity, template hash and actual device facts; no full environment or
private paths. Old absent facts stay null.

`silo-analyze` is offline only. It separates coverage/shape, global correctness,
incoming-state consistency with the observed predecessor, local increments,
inherited wrong state and additional worker errors. No analysis function is a
worker tool or monitor input. An all-zero, shape-valid four-segment regression
passes the public monitor/integration and fails final scoring without an oracle
alarm or correction.

The optional `submitted_final_value_v1` interface adds the actual predecessor ID
and actual last submitted integer only when that predecessor is already legally
read. It preserves wrong values; malformed/empty data yield explicit unavailable
status. Ancestors of a frozen boundary artifact are retained for provenance,
without granting extra original-shard or ancestor-artifact access. Original
serialization stays default. Prompts/prefill are charged and calibration identity
changes with the interface.

| Per model/interface condition | Sources | Executions | Scoring |
| --- | ---: | ---: | --- |
| Full baseline, run first | 8 | 8 | Unchanged global SILO scorer |
| Local accumulation | Same 8, four shards each | 32 | Changed local task, start at zero |
| Boundary continuation | Same 8, three transitions each | 0–24 | Actual frozen predecessor; global and local consistency separately |
| Separate confirmation | 2 fresh development sources | 2 | Full scorer; held out from configuration selection |

The diagnostic ceiling is **64 executions per condition**, not 64 model calls;
each execution can take multiple charged actions. Confirmation is two additional
executions only after choosing a condition. Seed 0 is prespecified for execution.
The generator starts at 1000, excludes original seeds 0–7 and any supplied known
data manifests, rejects validation/test groups and freezes ascending accepted
seeds before outcomes. Without extra exclusions, the eight development seeds
are 1001, 1002, 1003, 1007, 1008, 1011, 1013, 1014; confirmation uses 1015 and
1016. An undisclosed external dataset cannot be checked for overlap.

Boundary tasks must be frozen from actual terminal full-baseline checkpoints.
Missing/malformed predecessors retain the 24-slot denominator and are unavailable;
gold is never substituted. Baseline manifest/config/episode/checkpoint hashes and
charged work remain bound to the replay. Offline data-preparation CPU time is
reported separately; replay reads and inference are charged again. Include these
setup/baseline costs in end-to-end comparisons.

Profiles are `qwen35-4b-control` (exact recorded pin, BF16/no-thinking),
`qwen35-4b-reasoning` (same pin, template capability must verify before weights
load), and `qwen35-9b-later` (explicit resolved pin, staging and new hardware
preflight required). All retain context 8192 and a shared reasoning/output cap
of 768 initially. The 9B profile is intentionally unresolved, not runnable as-is.
Actual template support and GPU behavior have not been tested locally. Start
with the 4B control, then change **one factor** (serialization, reasoning, or later
model). Do not launch their Cartesian product or promote defaults from diagnostics.

### Additive metrics and safeguards

`metrics.observations` and grouped summaries separate public coverage, valid
shape, public integration, missing artifacts, evaluator availability, semantic
correctness and execution status. Legacy `integration_failures` still means
completed unsuccessful episodes. A hidden wrong answer never becomes an inferred
public failure. Missing historical evidence is null. Operation measurements have
no accuracy denominator. Aggregation checks profile/interface/mode as well as
the existing experiment, model, source, regime and A/B bindings; repeated seeds
do not become additional independent source groups.

No SQLite fixture prompt was rewritten. No source inputs, scorer gold, model
default, policy objective, scheduler guard or repository-execution gate was
relaxed. No jobs, downloads, pushes or external messages were sent.

## Ordered commands

Use a new output directory for each cycle. Code changes require new manifests;
old unsuccessful episodes remain terminal. The following commands are implemented
CLI paths. Files created under `/tmp` or `$BC_STORAGE` stay outside Git.

### 1. Local checks and review

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help

export BC_LOCAL_CYCLE="$(mktemp -d /tmp/bc-validation.XXXXXX)"
python scripts/bc.py sqlite-readiness --output "$BC_LOCAL_CYCLE/native-readiness.json"
python scripts/bc.py allocation-reproduce --config configs/pilot.json \
  --cold 2000 --prepare 2000 --prepared 2000 \
  --output "$BC_LOCAL_CYCLE/current-code-allocation.json"
python scripts/bc.py silo-battery --output-root "$BC_LOCAL_CYCLE/silo"
git status --short
git diff
```

The equal 2000 costs above are constructed predictions for an algorithm audit,
not measured model estimates. The user reviews, commits and pushes the repository
changes through their existing GitHub workflow; do not add staged data or outputs.

### 2. Browser terminal: preserve evidence and inspect existing ledgers

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
git status --short
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CYCLE="$(mktemp -d "$BC_STORAGE/validation-cycle.XXXXXX")"

python scripts/bc.py allocation-audit \
  --run "$BC_STORAGE/outputs/d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd" \
  --output "$BC_CYCLE/pilot-ledger-audit.json"
python scripts/bc.py silo-analyze \
  --run "$BC_STORAGE/outputs/9a7b999f0fdae4ed106080940417c0ee6002fd691658ca8b7044623bd15a583e" \
  --output "$BC_CYCLE/silo-v3-analysis.json"
```

Inspect the resulting JSON locally in the browser terminal. These reports do not
rewrite the old runs. They need the full original result/checkpoint files.

### 3. Native gate: only when the missing files are present

Existing public registration can be inspected with:

```bash
python scripts/bc.py sqlite-readiness \
  --staged "$BC_STORAGE/sqlite-stage-public.json" \
  --output "$BC_CYCLE/native-readiness.json"
```

If databases are large, run that hashing audit in the CPU job below as well.
No dataset download or author contact is part of this cycle. Set
`BC_SQLITE_MATERIALS` to the actual author-supplied full-records JSONL outside Git.
The existing upstream release root is shown below; verify that it exists.

```bash
export BC_SQLITE_ROOT="$BC_STORAGE/datasets/livesqlbench-0664a2f"
: "${BC_SQLITE_MATERIALS:?Set the actual private author-material JSONL path}"
python scripts/bc.py sqlite-stage --root "$BC_SQLITE_ROOT" \
  --materials "$BC_SQLITE_MATERIALS" --output "$BC_CYCLE/materials-stage.json"
python scripts/bc.py sqlite-review-template --staged "$BC_CYCLE/materials-stage.json" \
  --task-ids crypto_M_2 crypto_8 --output "$BC_CYCLE/review.private.json"
```

This creates **unapproved** entries for the known candidate, not approval or SQL.
Privately review the exact author records, port supported references/tests into
the typed AST, bind real tables/schema/conditions, and record truthful reviewer
notes. Add other actual development task IDs when creating a larger review.
Identify a second compatible pair from those materials in a private JSON list
using the same schema as `configs/sqlite-pair-candidates.json`. Empty setup and
cleanup and meaningful obligation tests are required; unsupported operations
remain blocked. Then create a new registration binding the completed review:

```bash
python scripts/bc.py sqlite-stage --root "$BC_SQLITE_ROOT" \
  --materials "$BC_SQLITE_MATERIALS" --review "$BC_CYCLE/review.private.json" \
  --output "$BC_CYCLE/reviewed-stage.json"
```

Prepare a CPU-only validation job through ordinary Slurm; this is not a second
GPU submission stack. Choose a site-approved partition for CPU work. This example
uses the partition in the user's existing profile, subject to the site's check:

```bash
export BC_REPO="$(pwd -P)"
export BC_PYTHON="$(command -v python)"
export BC_PARTITION="$(python -c 'import json; print(json.load(open("configs/cluster.pa100.local.json"))["partition"])')"
(
  set -euo pipefail
  test -z "$(git status --porcelain)"
  mkdir "$BC_CYCLE/native-source"
  git archive --format=tar HEAD | tar -xf - -C "$BC_CYCLE/native-source"
  git rev-parse HEAD > "$BC_CYCLE/native-source-commit.txt"
  chmod -R a-w "$BC_CYCLE/native-source"
)
export BC_REFERENCE_SOURCE="$BC_CYCLE/native-source"
cat > "$BC_CYCLE/native-reference-job.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Run reference execution inside a CPU allocation}"
cd "$BC_REFERENCE_SOURCE"
"$BC_PYTHON" -I scripts/bc.py sqlite-readiness --staged "$BC_CYCLE/reviewed-stage.json" --output "$BC_CYCLE/reviewed-readiness.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-validate --staged "$BC_CYCLE/reviewed-stage.json" --up-to --count 10 --output "$BC_CYCLE/native-validated.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-pairs --staged "$BC_CYCLE/reviewed-stage.json" --candidates "$BC_CYCLE/pairs.private.json" --count 2 --output "$BC_CYCLE/pairs-validated.json"
SH
sbatch --test-only --partition="$BC_PARTITION" --nodes=1 --ntasks=1 \
  --cpus-per-task=2 --mem=8G --time=00:30:00 \
  --output="$BC_CYCLE/native-%j.out" --error="$BC_CYCLE/native-%j.err" \
  "$BC_CYCLE/native-reference-job.sh"
```

Stop at the dry run. Actual submission requires the user's next instruction.
The CPU source archive is a read-only copy of the reviewed commit, with its commit
recorded beside it; reference reports also bind the executing source-tree hash
and reject source changes during controls. GPU jobs continue to use the existing
verified snapshot implementation.
After real controls validate tasks, prepare the single/clean model paths:

```bash
python scripts/bc.py validation-config --data-manifest "$BC_CYCLE/native-validated.json" \
  --output "$BC_CYCLE/native-control.json"
python scripts/bc.py manifest --config "$BC_CYCLE/native-control.json" \
  --model-lock "$BC_MODEL_LOCK" --output "$BC_CYCLE/native-control-manifest.json"
bash experiments/submit_gpu_preflight.sh --cluster configs/cluster.pa100.local.json \
  --manifest "$BC_CYCLE/native-control-manifest.json" --model-lock "$BC_MODEL_LOCK" --dry-run
bash experiments/submit_pilot.sh --cluster configs/cluster.pa100.local.json \
  --manifest "$BC_CYCLE/native-control-manifest.json" --model-lock "$BC_MODEL_LOCK" --concurrency 1 --dry-run
```

Require observed model competence before continuing to paired tasks. With two
actually validated pairs, repeat `validation-config`/`manifest`/guarded dry run
using `pairs-validated.json` and new `pairs-control*` output names. The config
uses the actual admitted count; missing tasks are never replaced by fixtures.

### 4. SILO: full control first, then freeze real predecessors

The following can proceed while native materials remain unavailable. Include
every additional known development/evaluation data manifest in `--exclude`.
The listed `silo-prefix.json` is the earlier eight-source registration.

```bash
python scripts/bc.py silo-battery --output-root "$BC_CYCLE/silo" \
  --exclude "$BC_STORAGE/silo-prefix.json"
python scripts/bc.py validation-config --data-manifest "$BC_CYCLE/silo/full.json" \
  --profile qwen35-4b-control --output "$BC_CYCLE/silo/control-full.json"
python scripts/bc.py manifest --config "$BC_CYCLE/silo/control-full.json" \
  --model-lock "$BC_MODEL_LOCK" --output "$BC_CYCLE/silo/control-full-manifest.json"
python scripts/bc.py diagnostic-costs --manifest "$BC_CYCLE/silo/control-full-manifest.json" \
  --output "$BC_CYCLE/silo/full-planned-costs.json"
bash experiments/submit_gpu_preflight.sh --cluster configs/cluster.pa100.local.json \
  --manifest "$BC_CYCLE/silo/control-full-manifest.json" --model-lock "$BC_MODEL_LOCK" --dry-run
bash experiments/submit_pilot.sh --cluster configs/cluster.pa100.local.json \
  --manifest "$BC_CYCLE/silo/control-full-manifest.json" --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1 --dry-run
```

No live capacity is assumed from `PA100q`. The guard inspects scheduler state,
and preflight reports the actual device. The user can choose concurrency 1–4
after reviewing availability; one model/GPU per shard, one active campaign.
Finish preflight and the full control through separately authorized submissions
before the following read-only steps:

```bash
export BC_FULL_ID="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' "$BC_CYCLE/silo/control-full-manifest.json")"
export BC_FULL_RUN="$BC_STORAGE/outputs/$BC_FULL_ID"
python scripts/bc.py aggregate --output "$BC_FULL_RUN"
python scripts/bc.py diagnostic-costs --run "$BC_FULL_RUN" --output "$BC_CYCLE/silo/full-measured-costs.json"
python scripts/bc.py silo-analyze --run "$BC_FULL_RUN" --output "$BC_CYCLE/silo/full-analysis.json"
python scripts/bc.py silo-boundaries --run "$BC_FULL_RUN" --output "$BC_CYCLE/silo/boundary.json"
```

Inspect `planned`, `denominator` and `unavailable` before making the boundary
config. For each nonempty diagnostic mode, independently:

```bash
for BC_MODE in local boundary; do
  python scripts/bc.py validation-config --data-manifest "$BC_CYCLE/silo/$BC_MODE.json" \
    --profile qwen35-4b-control --output "$BC_CYCLE/silo/control-$BC_MODE.json" || break
  python scripts/bc.py manifest --config "$BC_CYCLE/silo/control-$BC_MODE.json" \
    --model-lock "$BC_MODEL_LOCK" --output "$BC_CYCLE/silo/control-$BC_MODE-manifest.json" || break
  python scripts/bc.py diagnostic-costs --manifest "$BC_CYCLE/silo/control-$BC_MODE-manifest.json" \
    --output "$BC_CYCLE/silo/$BC_MODE-planned-costs.json" || break
  bash experiments/submit_pilot.sh --cluster configs/cluster.pa100.local.json \
    --manifest "$BC_CYCLE/silo/control-$BC_MODE-manifest.json" --model-lock "$BC_MODEL_LOCK" \
    --concurrency 1 --dry-run || break
done
```

These are dry runs only. Submit one campaign at a time later. No loop performs
actual submissions. Analyze/export each completed mode separately. For an
interface comparison, use `validation-config --interface submitted_final_value_v1`
and fresh names. For reasoning use `--profile qwen35-4b-reasoning`, original
interface and a fresh preflight. For the later model use
`--profile qwen35-9b-later --revision ACTUAL_40_HEX_REVISION` only after explicitly
selecting that revision; model staging/download is a separate future action.
Do not change two factors together. Use `confirmation.json` for a new full
manifest only after configuration selection, without inspecting its outcomes
during selection.

### 5. Optional measured operation costs and sanitized export

```bash
python scripts/bc.py measurement-plan --output-root "$BC_CYCLE/measurements" \
  --exclude "$BC_STORAGE/silo-prefix.json" "$BC_CYCLE/silo/full.json" "$BC_CYCLE/silo/confirmation.json"
for BC_SET in training holdout; do
  python scripts/bc.py validation-config --measurement \
    --data-manifest "$BC_CYCLE/measurements/$BC_SET.json" \
    --output "$BC_CYCLE/measurements/$BC_SET-config.json" || break
  python scripts/bc.py manifest --config "$BC_CYCLE/measurements/$BC_SET-config.json" \
    --model-lock "$BC_MODEL_LOCK" --output "$BC_CYCLE/measurements/$BC_SET-manifest.json" || break
  python scripts/bc.py diagnostic-costs --manifest "$BC_CYCLE/measurements/$BC_SET-manifest.json" \
    --output "$BC_CYCLE/measurements/$BC_SET-planned-costs.json" || break
  bash experiments/submit_pilot.sh --cluster configs/cluster.pa100.local.json \
    --manifest "$BC_CYCLE/measurements/$BC_SET-manifest.json" --model-lock "$BC_MODEL_LOCK" \
    --concurrency 1 --dry-run || break
done
```

These configs explicitly use a 500,000-work measurement cap per execution to
cover six operations per unit; that is not the policy comparison's 100,000 cap.
The shared output/reasoning/context limits remain unchanged. After separately
authorized completed measurements, obtain output directories from their manifest
IDs just as for `BC_FULL_RUN`, then:

```bash
: "${BC_TRAIN_RUN:?Set the actual completed training output directory}"
: "${BC_HOLDOUT_RUN:?Set the actual completed holdout output directory}"
python scripts/bc.py measurement-report --training "$BC_TRAIN_RUN" --holdout "$BC_HOLDOUT_RUN" \
  --output "$BC_CYCLE/measurements/cost-validation.json"
python scripts/bc.py export --output "$BC_FULL_RUN" --bundle "$BC_CYCLE/full-control.tar.gz" --dry-run
```

Review the export plan; the normal `export` command writes the allowlisted bundle
for browser download. No raw checkpoints/hidden materials are included.
