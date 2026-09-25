# RepoRecourse v0.1: implementation, evidence and runbook

2026-09-24. **CPU-qualified prototype; independent review and model qualification
pending.** No GPU episode, scheduler submission, model download, commit or push
was performed. Existing SQLite/SILO/solar/aggregation results remain unchanged.

## Milestones and implementation map

The implementation followed [design v0.1](reporecourse_benchmark_design.md):
M0 shared core and boundaries → M1 two executable CPU families → M2 three actual
source packs → M3 prospective qualification gates → M4 baseline/plan integration.
M0–M2 have local CPU evidence. M3–M4 have executable adapters and prepared gates;
the empirical model/calibration portions remain unexecuted.

| Component | Implementation / reuse |
|---|---|
| Neutral benchmark | `src/reporecourse/`: public tasks, tools, artifacts, faults, resources, terminal evaluator, plans, manifests, CPU qualification |
| Existing SQL safety path | Factored into `src/restricted_artifacts/`; legacy imports remain adapters. No change to accepted SQL semantics. Executor additionally reports child CPU time. |
| Schema/mapping | New bounded trusted child; pinned optional jsonschema/referencing dependencies |
| Model / persistence / scheduler | Existing Transformers backend, EpisodeJournal, immutable snapshots, scheduler inspection and shared per-user Slurm registry via `experiments/reporecourse.py` |
| Policies | Neutral solo, delegation/JIT, restart and independent replication drivers. Existing finite-selector objective/tie break reused through an optional BC plugin. Legacy route solver/surrogate calibration is **not** converted into new costs. |
| Content | `benchmarks/reporecourse/{public,private}`, source registry, task schema, attribution and sanitized CPU qualification record |
| CLI / batch | Additive `rr-*` commands; existing `submit`, `run`, `status`, `aggregate`, `resubmit`; new CPU-only `qualify_reporecourse.sh` |

The runtime and evaluator can execute without importing `beyond_consensus`; a
subprocess import-denial test checks actual execution/scoring of both families.
Policy names are not sent to the worker or evaluator. Private witnesses are used
only by explicitly labelled reference tests, never by the model worker/planner.

### Scientific changes and limits

This is an additive protocol. Historical `token_tool_surrogate_v1` accounting,
results, task definitions and native-policy gates remain intact. The new neutral
baseline drivers do not claim equivalence to every legacy BC repair route.
Factoring SQL code changes implementation fingerprints; new qualifications bind
the actual shared implementation files. Old qualification records are not silently
rewritten or accepted for changed code.

The illustrative unpaid-order request was not supported by Jaffle's seed fields.
The draft therefore requests recorded payments by customer and payment method;
it invents no balances or refund semantics. Independent review is still needed.
Deployment/configuration execution is deferred. The title is a working name,
without naming-clearance or novelty claims.

## Actual task inventory

All five tasks are **development-only**. Three are source-grounded drafts; two
are synthetic tests, excluded from the repository-task target.

| Task / grounding | Required outcomes | Two private reference organizations | Current state |
|---|---|---|---|
| `jaffle-recorded-payments` / demo_grounded | All-customer recorded-dollar totals/counts; payment-method totals/counts | Direct independent reports; shared payment/customer helper | CPU qualified; Apache-2.0 inspected; independent review pending |
| `energy-generation-coverage` / repo_grounded_authored | Country-year electricity report; observed/missing coverage report | Independent filtered reports; shared selection preserving nulls | CPU qualified; **underlying provider license review blocks model execution** |
| `github-topics-consumer` / repo_grounded_authored | Request validator; response validator; names-to-topics consumer contract | Independent schemas; shared names-array definition | CPU qualified; MIT inspected; independent review pending |
| `synthetic-stock` / synthetic_diagnostic | Stock report; zero-stock report | Independent queries; shared stock helper | CPU engineering only |
| `synthetic-nullable` / synthetic_diagnostic | Required/nullable response validator; compatible renamed mapping | Independent definitions; shared definition | CPU engineering only |

Pins (separate from parser/validator/model versions):

- Jaffle: `36bde6cba69d962b83be1d52fc65a0dce1cb4ebb`.
- OWID: `7e387a16f70a510e433f8aac7efeac6faa1e5059`.
- GitHub REST: `4377b4f4845badf28d13464dfb3042c6cf0e3a1f`.

[Source attribution and adaptations](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md)
and [exact file hashes](../benchmarks/reporecourse/source_registry.json) record the
inspected sources. Explicit staging downloads at most **22,296,539 bytes**:
Jaffle 37,563; energy 9,289,688; GitHub 12,969,288. Deterministic retained slices
are 39,350, 15,702 and 6,463 bytes respectively. Only allowlisted files are fetched;
no repository is cloned, imported or executed. `--packs` stages packs independently.
Downloaded source/data and raw runs stay outside Git.

There are two data-product and one API tasks, three source groups, zero independently
reviewed packs, and two non-demo authored tasks. The target remains six per family
across at least four reviewed packs. **Nine tasks and at least one source pack are
unfilled**, plus all independent reviews. Endpoint variants do not create new
repository groups. No historical-change or held-out claim is made.

## Local CPU results

The frozen [CPU evidence](../benchmarks/reporecourse/qualification/cpu-2026-09-24.json)
contains task/implementation hashes and sanitized checks, not raw episodes:

- **10/10 reference executions pass**: independent and shared-helper witnesses for
  each of the five tasks under the same task evaluator.
- **39/39 negative controls detected**: missing outputs, wrong values/aliases/types,
  accept-all/reject-all validators, and dropped or wrong mapping fields.
- Source-integrity and repeat/reset checks pass for every task. Alternate private
  fixtures exercise reusable programs, declared duplicates/nulls/coverage, and
  API positive/negative cases. These are finite tests, not all-input equivalence.
- SQL compiler qualification passes in the pinned CPU environment.
- Both-family tests execute solo clean and delegation/JIT, restart and replication
  under clean and announced loss. Other tests cover persistent sabotage, retained
  artifacts, cheaper explicit consumer rebinding/reexecution, fixed-state recovery,
  interrupted reservations, and the absence of private best-candidate rescue.
- Scripted workers consume measured CPU, **zero model tokens**, and establish
  harness feasibility only. They do not establish LLM competence or a policy ranking.

Qualification used Python 3.12.7, SQLGlot 27.28.1, jsonschema 4.25.1 and referencing
0.36.2. The standard-library-only environment also runs CLI/core tests. See the
verification section below for final suite counts and each optional skip.

The data-product expected values use independent Python calculations. Candidate
and reference programs share the trusted SQL execution boundary. Schema cases
have authored expected acceptance/output labels and use the same pinned validator
for execution. Shared-component defects remain a limitation.

## Public language and safety boundary

SQL remains `sqlite-sql-text-v1` → SQLGlot 27.28.1 bounded child → approved
`bc-select-tree-v1` → restricted SQLite. Supported features include explicit
projections, aliases, SELECT subqueries, inner/left/cross joins, searched CASE,
group/having/order/limit, and the existing allowlisted scalar/aggregate functions.
No raw SQL fallback, wildcard, CTE/window, DDL/DML, hooks, macros or external object
access. Existing parser/authorizer bounds remain in force.

Schemas use a declared Draft 2020-12 subset: type, properties, required,
additionalProperties, items, min/maxItems, enum, const, minimum/maximum and
min/maxLength. Boolean schemas are permitted but must pass positive and negative
behavioral evaluation. `$ref` accepts only explicit version-bound `rr:<alias>`
references; acyclic expansion is bounded to depth 16 / 400 nodes. Remote/file
retrieval, regex, formats, plugins and unknown keywords are rejected. GitHub's
selected OpenAPI 3.0.3 slice has an explicitly documented projection; this is not
a general dialect converter.

Mappings select/rename finite field paths with `missing=error|omit|null`, preserve
present nulls, and support bounded `each` over at most 128 array items. Output
schemas are checked. No expressions, callbacks, custom validators or live APIs.
The schema child has a 3-second CPU, 256-MiB memory and 6-second wall bound;
request/output/tree sizes are bounded. Only the trusted child imports optional
validator packages. CPU functionality and CLI help remain stdlib-only.

Workers access allowlisted source IDs and artifact versions, not host paths.
Publish-and-bind is atomic; replacing a helper never mutates an old consumer's
bindings. `rebind_artifact` copies unchanged programs with explicit new versions.
Only the latest explicitly bound terminal bundle is graded. Private references,
fixtures, faults and expected values stay outside worker views. This is a
restricted content/tool interface, **not an OS sandbox** or same-UID isolation.

## Policies, identities and accounting

Four persistent identities share one model instance in a shard. F targets an
active contributor before its first assigned artifact handoff, announces loss,
and retains earlier publications. No fifth fallback or disappearing source.
S implements bounded safe artifact replacement, separately labelled one-shot or
persistent; no malicious-identity label reaches workers. Natural-language attack
search/message replacement is deferred. R freezes a common graph/trace/alarm and
uses an explicitly **equal-remaining** allowance, preserving historical work and
charging restoration separately. Persistent S control remains active after R restoration. It is not pooled with equal-total F/S.

Outcomes, submitted organization and observed provenance are distinct. JIT repairs
missing/public-failing obligations and retains unrelated versions. Restart clears
bindings and contexts while retaining the recorded store. Replication uses fresh
source-only contexts before common repair, orders admission by observed primary token work, and uses
common public checks plus agreement; disagreement does not reveal truth. Agreement
is conservative and is not semantic equivalence. The same identities' compromise
and observed exposure survive resets.

Three public outlines change actual grouping, dependencies and execution order;
owner renaming alone is not another organization. Active-count differences are
reported. The BC finite-selector plugin shares the catalog, eligibility, reserve
and JIT backend between nominal/recovery objectives. It blocks absent compatible
measured calibration. **No empirical plan costs, B0 or prediction errors exist.**
Constructed selector numbers appear only in unit tests. Open-planning supports a
charged public-only model call returning at most three executable plans; it has
only a test backend exercise, no real-model qualification or enabled campaign.

New profile `rr-logical-tokens-cpu-v1`: actual input tokens on every call plus all
output tokens (reasoning is a subset). Reservations are released against actual
usage; unknown interrupted work stays separately labelled uncertain and debits
admission conservatively. Compiler/validator/decoder/model-host/planner/tool/public
check CPU is measured separately. Nested parent CPU is subtracted before counting
exclusive outer tool CPU; device/wall timings are observations, not added CPU.
Trusted runtime/evaluator parent overhead is also measured without adding nested child CPU twice. Artifact storage size and executions/rebindings are recorded. Parent bookkeeping
is accounted at operation boundaries, not a hard OS process-isolation guarantee.
Terminal private evaluation freezes the bundle, has its own 240-second CPU cap,
and provides no worker feedback. Static model/grammar setup is separate.

The prospective engineering ceiling is 100,000 **logical tokens** and 1,200 CPU
seconds, not a conversion from historical surrogate work and not calibrated B0.
The B0 plan prespecifies ordinary development delegation, failures/censoring,
nearest-rank 75th percentile, and multipliers 1.25/1.5/2/3 (initial 1.5). A censored
percentile remains unresolved. No calibration was executed.

## Gates and planned counts

The current three-pack clean team+solo plan has **12 episodes** (3 × 2 × 2 seeds).
A separate supplied-outline clean/F sensitivity plan has **58 episodes**, enumerating
actual active contributors across three outlines and two seeds. Neither is enabled
for submission. The eventual balanced 12-task clean grid is **48 episodes**; its
18/24 team and 8/12-per-family thresholds do not apply to today's incomplete set.
The six-task subset, broader mechanism grid and paper-scale studies remain deferred.

Only **one clean engineering smoke** is submit-eligible after current task CPU
qualification, hash-bound decoder qualification, staged model lock and actual-GPU
preflight. Energy remains blocked by the provider-license gate. Passing a smoke
will not open a policy campaign automatically.

The existing registry/Slurm guard enforces one active campaign and at most four
GPUs. Qualification defaults to one shard, one allocated full 80-GB-class GPU,
all worker contexts on that backend. No CPU offload, quantization or 40-GB fallback
is introduced. Registry/scheduler checks cannot prevent unrelated manual submissions
or scheduler races outside this workflow. Batch scripts never submit other jobs.

**Not run:** new tokenizer/XGrammar qualification against the user's model lock,
80-GB GPU preflight, long-context real generation, any RepoRecourse model episode,
model competence, empirical planning/calibration, independent review. Local source
pins were checked; the actual cluster model lock must be checked there. Expected
27B model/tokenizer revision is `fc05daec18b0a78c049392ed2e771dde82bdf654`.

## LOCAL: reproducible CPU checks

Python 3.12+. Use a fresh environment and fresh output directory; no GPU imports.

```bash
python -m venv .venv-rr
.venv-rr/bin/python -m pip install -r requirements-reporecourse.txt
export BC_PYTHON="$PWD/.venv-rr/bin/python"
export RR_SOURCES="$PWD/data/reporecourse-sources"
export RR_CHECK="$(mktemp -d /tmp/reporecourse-review.XXXXXX)"

"$BC_PYTHON" scripts/bc.py rr-source-plan --dry-run --output "$RR_CHECK/source-plan.json"
# Explicit bounded setup after inspecting the sizes/licenses above:
"$BC_PYTHON" scripts/bc.py rr-stage --sources "$RR_SOURCES"
bash experiments/qualify_reporecourse.sh --local \
  --sources "$RR_SOURCES" --output "$RR_CHECK/cpu"
"$BC_PYTHON" scripts/bc.py rr-visibility --sources "$RR_SOURCES" --task github-topics-consumer
"$BC_PYTHON" scripts/bc.py rr-plans --sources "$RR_SOURCES" --task jaffle-recorded-payments
"$BC_PYTHON" scripts/bc.py rr-demo --task synthetic-stock --track F --target w0 \
  --output "$RR_CHECK/data-loss.json"
"$BC_PYTHON" scripts/bc.py rr-demo --task synthetic-nullable --track F --target w0 \
  --output "$RR_CHECK/api-loss.json"
"$BC_PYTHON" -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
python -I -S scripts/bc.py --help
git diff --check
```

For one pack use `rr-stage --packs jaffle` (or `github`, `energy`) and
`rr-qualify --sources "$RR_SOURCES" --task TASK --output NEW.json` independently.
`rr-readiness` checks catalog/source hashes and split overlap without a model.
`rr-calibration-plan` prints the unexecuted prospective design.

## CLUSTER BROWSER TERMINAL: user-triggered gates

These are commands for **after reviewing, committing and pushing** the changes.
No step below has been run on the cluster by this implementation. Do not change
an environment used by active jobs. The existing cluster JSON must point at the
same Python environment and a previously confirmed 80-GB partition; a partition
name alone is not hardware proof.

### 1. Pull, verify paths, stage the explicit allowlist

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RR_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_RR_BASE_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json"
# Set this to your actual existing NA100q/80-GB cluster configuration:
export BC_RR_CLUSTER=configs/cluster.na100.local.json

test -f "$BC_RR_CLUSTER"
test -f "$BC_RR_BASE_LOCK"
"$BC_PYTHON" -m pip install -r requirements-reporecourse.txt
"$BC_PYTHON" -m pip check
"$BC_PYTHON" scripts/bc.py rr-source-plan --dry-run
"$BC_PYTHON" scripts/bc.py rr-stage --sources "$BC_RR_SOURCES"
mkdir -p "$BC_STORAGE/diagnostics"
export BC_RR_SESSION="$(mktemp -d "$BC_STORAGE/diagnostics/reporecourse.XXXXXX")"
```

The cluster-config filename is user-local and is deliberately not invented as an
existing file. Locate it with `rg --files --hidden --no-ignore configs` if needed,
then set `BC_RR_CLUSTER` to that actual file. Do not modify model revisions.

### 2. Freeze code and submit CPU qualification

```bash
(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
  git status --short
  printf 'Stop: use a clean reviewed checkout.\n'
  exit 1
fi
mkdir "$BC_RR_SESSION/source"
git archive --format=tar HEAD | tar -xf - -C "$BC_RR_SESSION/source"
git rev-parse HEAD > "$BC_RR_SESSION/source-commit.txt"
chmod -R a-w "$BC_RR_SESSION/source"
)
export BC_RR_PARTITION="$("$BC_PYTHON" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["partition"])' "$BC_RR_CLUSTER")"
sbatch --partition="$BC_RR_PARTITION" --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=01:00:00 \
  --output="$BC_RR_SESSION/cpu.out" --error="$BC_RR_SESSION/cpu.err" \
  "$BC_RR_SESSION/source/experiments/qualify_reporecourse.sh" \
  --sources "$BC_RR_SOURCES" --output "$BC_RR_SESSION/cpu" \
  --model-lock "$BC_RR_BASE_LOCK"
```

Wait for that job to finish. Inspect `cpu.out`, `cpu.err`, all five task reports,
`compiler.json`, and `grammar.json`. All must pass; `cpu/model-lock.json` must exist.
The optional grammar uses the new **`reporecourse-json-v1`** envelope to support
schema/mapping publications and atomic binding. It does not change SQL semantics.
Do not substitute an old SQL-only decoder qualification.

### 3. Prepare exactly one smoke, then preflight

```bash
export BC_RR_LOCK="$BC_RR_SESSION/cpu/model-lock.json"
"$BC_PYTHON" scripts/bc.py rr-manifest --sources "$BC_RR_SOURCES" \
  --tasks jaffle-recorded-payments --engineering-smoke \
  --qualification "$BC_RR_SESSION/cpu/jaffle-recorded-payments.json" \
  --model-lock "$BC_RR_LOCK" --output "$BC_RR_SESSION/smoke-manifest.json"

"$BC_PYTHON" scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_SESSION/smoke-manifest.json" \
  --model-lock "$BC_RR_LOCK" --dry-run
# Explicit user submission after inspecting the dry-run:
"$BC_PYTHON" scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_SESSION/smoke-manifest.json" \
  --model-lock "$BC_RR_LOCK"

export BC_RR_ID="$("$BC_PYTHON" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' \
  "$BC_RR_SESSION/smoke-manifest.json")"
export BC_RR_OUTPUT="$("$BC_PYTHON" -c \
  'import json,sys; from pathlib import Path; print(Path(json.load(open(sys.argv[1]))["output_root"])/sys.argv[2])' \
  "$BC_RR_CLUSTER" "$BC_RR_ID")"
# Run after preflight finishes:
"$BC_PYTHON" -m json.tool "$BC_RR_OUTPUT-preflight/preflight.json"
```

Require `command_failed: false`, correct hardware/model revision, successful SQL
and schema probes. Long-input generation is measured, but early EOS does not prove
worst-case 16K-context/2048-output memory fit. Preserve any failure and stop at it.

### 4. Submit the one smoke only after reviewing preflight

```bash
"$BC_PYTHON" scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_SESSION/smoke-manifest.json" \
  --model-lock "$BC_RR_LOCK" --dry-run
"$BC_PYTHON" scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_SESSION/smoke-manifest.json" \
  --model-lock "$BC_RR_LOCK"
# After completion:
"$BC_PYTHON" scripts/bc.py status --output "$BC_RR_OUTPUT"
"$BC_PYTHON" scripts/bc.py aggregate --output "$BC_RR_OUTPUT"
export BC_RR_EXPORT="$(mktemp -d "$BC_RR_SESSION/export.XXXXXX")"
"$BC_PYTHON" scripts/bc.py rr-export --run "$BC_RR_OUTPUT" \
  --output "$BC_RR_EXPORT/results.json"
```

For interrupted/infrastructure work only, use the **actual** snapshot path returned
by submission: `python scripts/bc.py resubmit --snapshot ACTUAL_PATH --concurrency 1
--dry-run`, then explicitly resubmit if appropriate. It reuses recorded actual and
uncertain charges. Completed failures are not retried. Do not delete results or
reuse old report paths. `rr-export` omits private programs, fixtures and histories.
Review the one-task trace and resource use before proposing any larger experiment.

## Verification record

Final suite outcomes are recorded in the additive RepoRecourse entry in
[STATUS.md](STATUS.md). The dependency-equipped suite exercises both CPU children.
The stdlib environment skips nine RepoRecourse child-dependent tests and three
legacy SQLGlot tests. Both environments skip the legacy real OS-sandbox integration
because `BC_SANDBOX_TEST_PROFILE` is not configured; that sandbox is not required
or claimed by this restricted data path. GPU qualification is separate and unrun.

### Assignment termination correction (2026-09-25)

Worker finish ends only its current assignment. It neither certifies correctness
nor freezes the shared bundle; the orchestrator does that after scheduled work.
The first cluster smoke exposed the former global-finish defect during repair.
Its 0/1 result is preserved. Fresh qualification and a manifest are required for
a corrected run; the two primary SQL semantic errors remain to be diagnosed.
