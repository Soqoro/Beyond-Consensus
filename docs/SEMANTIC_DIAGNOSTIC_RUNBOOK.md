# Three-call synthetic semantic diagnostic

Prepared 2026-10-16. No GPU submission or model execution performed locally.

## Evidence and scope

User-reported CPU job 1098418 completed 0:0 in three seconds, frozen source
82cd822fa80ff427cbb8d4101af98819d30ecd19, at
`/dataset/suaq0001/beyond-consensus/diagnostics/rr-semantic-controls.sqPwI7`.
All seven production controls passed: three positive artifacts passed semantic
checks; four wrong artifacts passed the unchanged public monitor but failed
independent semantic checks. Pinned versions were Python 3.12.10, SQLGlot
27.28.1, jsonschema 4.25.1 and referencing 0.36.2. These are reported CPU control
results, not model competence. The full saved report must pass adapter checks.

The new `rr-semantic-run-manifest-v1` uses the existing shared per-user registry,
Slurm submission, snapshots, runner and aggregate dispatch. It is run-only,
concurrency one, one shard, three cases in fixed order:

1. `order_grain`: orders counted once after joining multiple payments.
2. `unpaid_boundary`: distinguish no orders, unpaid orders and zero-paid amounts.
3. `mapping_keys`: exact required output names with preserved input values.

Each case receives one fresh scoped assignment, one model call, no retries and
no repair. Pool seven shares one frozen model/GPU; only w0 acts. No model planner
is called. The public observation supplies all invented sources directly,
because a separate read call would exceed this one-call scope. This is a new
synthetic observation contract, not a matched reconstruction of cohort prompts.
Setup timing is omitted from the prompt; declared diagnostic caps are exposed
and actual setup CPU remains charged. Independent oracles and authored positive/
negative control programs never appear in model observations.

Worker context 16384/output 2048, per-case token cap 16384 and CPU cap 1200.
Terminal evaluation uses a separate 1200-CPU-second ledger per case; it invokes
no model and is never worker feedback. Maximum task reservations: 49152 tokens
and 3600 CPU seconds across three calls/cases, plus 3600 separate terminal CPU
allowance. These are uncalibrated synthetic limits, not B0 or historical work.
Source materialization, model calls, parsing, compiler, public checker and
orchestration are charged. Terminal checking is charged separately. Process CPU
observations overlap ledger parent subsets and must not be added a second time.

Record parsing/completion, public-monitor results and semantic correctness
separately. Bad JSON, wrong action, length limit or ordinary semantic failure
remain recorded observations; no call is repeated. Device/uncertain usage,
prerequisite and cleanup failures stop subsequent cases and preserve missing
coverage. Interruption persists the current ledger; a durable started marker
prevents resubmission even when the report is incomplete. Generated actions must
be exactly one publication of the assigned report. SQL always traverses the
existing compiler-to-IR and protected child executor. No generated host code or
raw worker SQL is executed on the host.

## Reuse and new checks

The passed production report is reused only when all seven outcomes, diagnostic
implementation hash, full core hashes and pinned runtime versions agree.
The new adapter requires fresh no-skip tests and tokenizer-only measurements of
the three actual public prompts. Those tests also exercise production children
with CPU doubles; their results never become model scores.

The saved normal qualification is independently re-audited for internal binding
and current model/core compatibility. Its exact worker lock and model settings
must match. Before calling workers, actual allocated hardware, capability,
VRAM, CUDA and dependencies must match the saved normal runtime. No launch
blocking, new model settings, planner calls, implicit retries, parallel cohort,
condition override or injected production backend are accepted.

The proposal contains a scope-bound approval template. Preparing it never
submits a job. Approval of the prior twelve-condition cohort does not authorize
these three new model calls. Existing task/recovery outcomes remain unchanged.

## Jupyter CPU preparation after pushing

```bash
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_SEMANTIC_CONTROLS="$BC_STORAGE/diagnostics/rr-semantic-controls.sqPwI7/controls.json"
export BC_SEMANTIC_LOCK="$BC_STORAGE/diagnostics/rr-two-workstreams.9vczlH/decoder-cpu/guarded-lock.json"
export BC_SEMANTIC_NORMAL="$BC_STORAGE/outputs/qwen27b-na100/5dd357626b3ad6a3677f6bca7ca1b7e548557c1b86fe6a7c03fdc91a701c96a0-preflight"
export BC_SEMANTIC_RUN="$(mktemp -d "$BC_STORAGE/diagnostics/rr-semantic-ready.XXXXXX")"
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: keep exports outside Git before freezing source.\n'
    exit 1
fi
for path in "$BC_SEMANTIC_CONTROLS" "$BC_SEMANTIC_LOCK" "$BC_SEMANTIC_NORMAL/preflight.json"; do
    test -s "$path" || { printf 'Missing: %s\n' "$path"; exit 1; }
done
git rev-parse HEAD > "$BC_SEMANTIC_RUN/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_SEMANTIC_RUN/source"
git -C "$BC_SEMANTIC_RUN/source" checkout --detach "$(cat "$BC_SEMANTIC_RUN/source-commit.txt")"
cat > "$BC_SEMANTIC_RUN/prepare.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$BC_SEMANTIC_RUN/source"
test "$(git rev-parse HEAD)" = "$(cat "$BC_SEMANTIC_RUN/source-commit.txt")"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
"$BC_PYTHON" -I scripts/check_rr_semantic_run.py \
  --output "$BC_SEMANTIC_RUN/adapter-controls.json"
"$BC_PYTHON" -I scripts/prepare_rr_semantic_run.py footprint \
  --worker-lock "$BC_SEMANTIC_LOCK" --output "$BC_SEMANTIC_RUN/footprint.json"
"$BC_PYTHON" -I scripts/prepare_rr_semantic_run.py proposal \
  --worker-lock "$BC_SEMANTIC_LOCK" \
  --production-controls "$BC_SEMANTIC_CONTROLS" \
  --adapter-controls "$BC_SEMANTIC_RUN/adapter-controls.json" \
  --footprint "$BC_SEMANTIC_RUN/footprint.json" \
  --normal-run "$BC_SEMANTIC_NORMAL" --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_SEMANTIC_RUN/proposal.json"
"$BC_PYTHON" -I scripts/prepare_rr_semantic_run.py review \
  --worker-lock "$BC_SEMANTIC_LOCK" --manifest "$BC_SEMANTIC_RUN/proposal.json" \
  --output "$BC_SEMANTIC_RUN/review.json"
SH
bash -n "$BC_SEMANTIC_RUN/prepare.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=00:30:00 --export=ALL \
  --job-name=rr-semantic-prep --chdir="$BC_SEMANTIC_RUN/source" \
  --output="$BC_SEMANTIC_RUN/cpu.out" --error="$BC_SEMANTIC_RUN/cpu.err" \
  "$BC_SEMANTIC_RUN/prepare.sh" > "$BC_SEMANTIC_RUN/cpu-job.txt"
printf 'Preparation directory: %s\n' "$BC_SEMANTIC_RUN"
cat "$BC_SEMANTIC_RUN/cpu-job.txt"
)
```

PA100q is a previously used CPU partition, not a claim of current availability.
No GPU is requested, and the script cannot submit another job.

After completion:

```bash
sacct -j "$(cut -d';' -f1 "$BC_SEMANTIC_RUN/cpu-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_SEMANTIC_RUN/cpu.err"
if test -s "$BC_SEMANTIC_RUN/review.json"; then
    "$BC_PYTHON" -m json.tool "$BC_SEMANTIC_RUN/review.json"
else
    tail -n 40 "$BC_SEMANTIC_RUN/cpu.out"
fi
printf 'Preparation directory: %s\n' "$BC_SEMANTIC_RUN"
```

Return the review before GPU submission. Keep blocked outputs intact.

## Later execution interfaces

After exact approval, write its reviewer/date/approved decision from the review
and call `prepare_rr_semantic_run.py approve --manifest PROPOSAL --worker-lock
LOCK --approval RECEIPT --output FRESH_APPROVED_MANIFEST`. Submit via the existing
`bc.py submit --mode run --concurrency 1` with matching cluster/model bindings.
No private expected answers are injected by this approval.

Read-only `bc.py aggregate --output RUN` returns `semantic-report.json`, including
raw responses, separate resource ledgers and missing cases. Keep raw reports
outside Git. Completed scheduler jobs are not evidence that semantic checks
passed; report all three cases and failures. These selected synthetic cases
cannot establish recovery effectiveness, decoder causality, or held-out competence.
