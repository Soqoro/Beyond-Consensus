# Sampled organization study: staged execution adapter

## Scope and evidence

Six selected authored organizations (independent, grouped, shared for each of
Jaffle payment release and GitHub multioperation integration) give twelve
prospective conditions: clean plus one seed-1 meaningful-owner F branch per
plan. The selected plans are fixed before execution; the clean result cannot
choose or remove a fault target. This is development organization
characterization, not an open-generated planner comparison or held-out study.

The supplied normal audit `rr-normal-audit.BwJ9rS/audit.json` reports verified
internal bindings and current compatibility with no changed files/errors for
experiment `5dd357626b3ad6a3677f6bca7ca1b7e548557c1b86fe6a7c03fdc91a701c96a0`.
Its three calls used 17521 tokens and no uncertain usage. The audit does not
independently certify authenticity, scheduler completion, task competence or
worst-case fit. The earlier AcceleratorError remains unexplained.

The adapter reuses the shared Slurm registry, cohort runner, scoped engine,
monitor, common JIT and evaluator. It changes no core model, decoder, action
schema, source recipe, task contract, evaluator or resource implementation.
Only worker calls use the model; there is no model planner invocation or
planner-lock requirement. Seven logical identities share one model/GPU; each
branch retains 100000 tokens / 1200 CPU seconds, context 16384 and output 2048.
The unused planner allowance remains labelled 6144 in the frozen configuration.

Runtime plan receipt, validation and target-resolution CPU is measured once
and logically charged in each branch; offline catalog construction/reference
expense stays separately reported. Runtime receipt timing creates fresh branch
IDs. The adapter checks the committed plan, request and selected owner against
the proposal and binds results to the actual saved schedule. No plan selection
is repeated using execution outcomes. Failed, interrupted and unrun conditions
remain in the analysis, with unknown rates where coverage is incomplete.

Pending independent/source/provider review remains explicitly deferred in the
existing `rich_development_unreviewed` lane. It is not converted to a clearance.
The new manifest needs exact twelve-condition approval after its review. Old
blocked proposals and all historical evidence remain unchanged.

## 1. Freeze the pushed implementation and submit CPU preparation

This uses the existing catalog, guarded lock and successful normal audit. It
renews adapter controls and measures initial/one-source worker prompt sizes for
the actual six plans, plus private-side reference serialization sizes. It does
not requalify the model grammar or generate GPU responses. Dependencies/models
must already be cached; no downloads are requested.

Run in the Jupyter terminal after pushing the changes:

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_SAMPLE_BASE="$BC_STORAGE/diagnostics/rr-two-workstreams.9vczlH"
export BC_SAMPLE_AUDIT="$BC_STORAGE/diagnostics/rr-normal-audit.BwJ9rS/audit.json"
export BC_SAMPLE_RUN="$(mktemp -d "$BC_STORAGE/diagnostics/rr-sampled-ready.XXXXXX")"

(
set -euo pipefail
set -o noclobber
cd "$HOME/Beyond-Consensus"
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: keep local exports outside Git before freezing source.\n'
    exit 1
fi
for path in "$BC_SAMPLE_BASE/catalog-cpu/catalog.json" \
    "$BC_SAMPLE_BASE/decoder-cpu/guarded-lock.json" "$BC_SAMPLE_AUDIT"
do
    test -s "$path" || { printf 'Missing: %s\n' "$path"; exit 1; }
done
git rev-parse HEAD > "$BC_SAMPLE_RUN/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_SAMPLE_RUN/source"
git -C "$BC_SAMPLE_RUN/source" checkout --detach "$(cat "$BC_SAMPLE_RUN/source-commit.txt")"

cat > "$BC_SAMPLE_RUN/qualify.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
: "${BC_SAMPLE_RUN:?}" "${BC_SAMPLE_BASE:?}" "${BC_SAMPLE_AUDIT:?}" "${BC_PYTHON:?}" "${BC_STORAGE:?}"
cd "$BC_SAMPLE_RUN/source"
test "$(git rev-parse HEAD)" = "$(cat "$BC_SAMPLE_RUN/source-commit.txt")"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
"$BC_PYTHON" -I scripts/check_rr_sampled_run.py \
  --output "$BC_SAMPLE_RUN/controls.json"
"$BC_PYTHON" -I scripts/prepare_rr_sampled_run.py footprint \
  --catalog "$BC_SAMPLE_BASE/catalog-cpu/catalog.json" \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --worker-lock "$BC_SAMPLE_BASE/decoder-cpu/guarded-lock.json" \
  --output "$BC_SAMPLE_RUN/footprint.json"
"$BC_PYTHON" -I scripts/prepare_rr_sampled_run.py proposal \
  --catalog "$BC_SAMPLE_BASE/catalog-cpu/catalog.json" \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --worker-lock "$BC_SAMPLE_BASE/decoder-cpu/guarded-lock.json" \
  --normal-audit "$BC_SAMPLE_AUDIT" \
  --controls "$BC_SAMPLE_RUN/controls.json" \
  --footprint "$BC_SAMPLE_RUN/footprint.json" \
  --output "$BC_SAMPLE_RUN/proposal.json"
"$BC_PYTHON" -I scripts/prepare_rr_sampled_run.py review \
  --manifest "$BC_SAMPLE_RUN/proposal.json" \
  --worker-lock "$BC_SAMPLE_BASE/decoder-cpu/guarded-lock.json" \
  --output "$BC_SAMPLE_RUN/review.json"
SH
bash -n "$BC_SAMPLE_RUN/qualify.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --job-name=rr-sampled-cpu --export=ALL \
  --chdir="$BC_SAMPLE_RUN/source" \
  --output="$BC_SAMPLE_RUN/cpu.out" --error="$BC_SAMPLE_RUN/cpu.err" \
  "$BC_SAMPLE_RUN/qualify.sh" > "$BC_SAMPLE_RUN/cpu-job.txt"
printf 'Preparation directory: %s\n' "$BC_SAMPLE_RUN"
cat "$BC_SAMPLE_RUN/cpu-job.txt"
)
```

The direct batch file uses explicit paths and does not resolve its source from
Slurm's spool directory. It neither requests a GPU nor self-submits another job.
`PA100q` is the previously used CPU preparation partition; its current availability
must be checked on the cluster if submission fails.

## 2. Inspect after the CPU job finishes

```bash
sacct -j "$(cut -d';' -f1 "$BC_SAMPLE_RUN/cpu-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
tail -n 60 "$BC_SAMPLE_RUN/cpu.err"
if test -s "$BC_SAMPLE_RUN/review.json"; then
    "$BC_PYTHON" -m json.tool "$BC_SAMPLE_RUN/review.json"
else
    tail -n 60 "$BC_SAMPLE_RUN/cpu.out"
fi
printf 'Preparation directory: %s\n' "$BC_SAMPLE_RUN"
```

Return the review and scheduler outcome. Do not repeat a failed job in the same
output directory. A changed implementation/evidence check is a reason to inspect
compatibility, not to edit a passed report or automatically rerun GPU qualification.

## Approval, execution and export interfaces

The fresh review exposes an exact `rr-sampled-run-approval-v1` template. Only
after approval of that concrete scope, record the reviewer/date and use
`prepare_rr_sampled_run.py approve --manifest ... --worker-lock ... --approval ...
--output ...`. It checks current evidence again and writes a new approved manifest.
No pending template is automatically accepted.

The approved manifest uses the existing `scripts/bc.py submit --mode run
--concurrency 1` path, configured cluster, shared registry and worker lock.
There are six ordered shards, each with two branches. An unresolved started
attempt or infrastructure/conformance pause blocks further execution. There
is no automatic retry, condition override, parallel cohort or clean rerun.
Hardware/runtime must match the saved normal qualification before worker actions.

Read-only results use the standard `bc.py aggregate --output RUN` and
`prepare_rr_sampled_run.py export --run RUN --output FRESH_FILE`. The export
includes private journals/evidence and must remain outside Git. It reports all
six configurations/twelve conditions, source groups, clean/F correctness,
conformance, costs and missing coverage. These are correlated development
conditions; do not interpret them as twelve independent task samples.
