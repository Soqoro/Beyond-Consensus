# Bounded decoder diagnosis and organization characterization

**15 October 2026 — development preparation, no new GPU result**

## Scientific stopping point

The immutable unique-key preflight `a3aadd6913fb1f2968de6c735183c65f48dfd2cf36c0c9c7c2ed724c6d959a32`
(job 1096744_0) passed nested mapping, failed its dispatched escaped-key call
with AcceleratorError, and never attempted long-context mapping. Known usage
was 692 tokens; 2143 tokens remained an uncertain reservation, not measured
usage. The supplied stderr was empty. Existing evidence does not distinguish
OOM, a common kernel failure, or guard/generation integration. Instrumentation
is not a demonstrated fix. See the [audit addendum](AUDIT_REPORT_2026-10-14.md).

The latest assignment-interface cohort remains 2/16 scheduled successes;
semantic mistakes are separate from the decoder problem. Historical attempts,
uncertain charges, task versions, and scores are preserved.

## A. Matched synthetic diagnostic

Two fresh-process arms use the same original nested and escaped-key prompts,
in that order. The native arm retains the strict final parser; the guarded
arm adds unique-key enforcement. Both use the pinned model/runtime and explicit
`CUDA_LAUNCH_BLOCKING=1` set before CUDA initialization. This debugging treatment
is not a production fix or a performance comparison. Maximum four calls total,
one GPU at a time, no task inputs/actions/evaluator, no retries or long-context
call. Fatal errors stop that arm; later calls remain not attempted.

Native completion, strict parsing, length-limit completion, and accelerator
failure are separate observations. Instrumentation keeps bounded host-side
stage/error evidence and mask summaries, without logits, tensor values, frame
locals, environment dumps, or arbitrary generated text. Masked negative infinity
is legitimate. Invalid indices, NaNs, positive infinity, and empty usable support
must be distinguished and fail closed without token fallback.

The control may fail parsing; it must not be dropped. If only the guarded arm
fails, suspicion narrows to its integration or changed generation trajectory,
not necessarily Unicode. If both fail, inspect the common path. If both pass,
the original failure was not reproduced under the debug treatment; its cause
remains unknown. Inputs reconstructed from retained prompt definitions are
labelled and compared with historical token/hash metadata when available.

A separate normal-mode three-call guarded qualification requires diagnostic
review, affected native/CPU qualification, and a separate exact approval.
Launch blocking must be disabled; success only under synchronous debugging
does not qualify normal task execution. The normal sequence includes the
previously unattempted long-context case. It is at most three additional calls,
never an automatic repeat-until-pass loop.

## B. Organization catalog

Only `jaffle-payment-release` and `github-multioperation-integration` are sampled.
The goal is three materially different complete plans per task, from a bounded,
deterministic candidate set of at most twelve per task. Independent, grouped,
and shared forms are authored public-contract recipes with explicit generic
transformations and preconditions, not a model-discovered plan distribution.

Public plans contain no private reference bodies, hidden fixtures, expected
values, or preferred costs. Private witnesses are used only to certify
feasibility through existing scoped execution and the terminal bundle evaluator.
Missing assets/dependencies remain blockers. Reference success is not model
competence or an optimality/cost claim. Missing and semantic-mutant controls
must remain effective. Selection uses fixed structural coverage, not outcomes.

Grouping several outputs into one assignment differs from assigning separate
fresh-context units to the same identity. Relabelled copies do not satisfy the
variation quota; owner-concentration differences remain visible. Helpers have
public interfaces and no terminal obligations. Original sources remain available
and helper consumption is not forced. Observed reads and executable bindings
are reported separately. Common scoped JIT and persistent loss remain unchanged.

## Prepared study boundary

The proposed scope is two tasks × three qualified organizations × (clean + one F)
= twelve scheduled logical conditions. Each branch retains pool seven, 100000
logical tokens, 1200 charged CPU seconds, and the same reserve/JIT rule. Aggregate
ceilings are 1200000 tokens and 14400 CPU seconds; these are caps, not calibration,
GPU-hour forecasts, or total development costs.

One meaningful owner is seeded before clean outcomes; idle workers are excluded.
Both branches are scheduled prospectively. Ordinary clean semantic failure does
not cancel F. Different organizations have different target ownership/fault
fractions; identical exposure is not claimed. Missing configurations and
nontriggered faults remain visible. Infrastructure, integrity, or accounting
failures may pause the remaining study with coverage retained.

The proposal remains blocked if fewer than six plans qualify or the worker
normal-mode qualification gate is closed. Existing development review deferrals
remain explicit; they are not rights clearance or a blanket changed-scope
approval. This is organization characterization, not a generated-planner contest,
a trained adapter result, or held-out generalization. Beyond Consensus remains
a pre-execution full-plan adapter; these recipes are not its eventual menu.

Offline construction/qualification costs and future worker execution costs are
separate. No hidden free-search comparison, training, simulator fitting, task
harvesting, automatic scaling, or old four-task cohort rerun is introduced.

## Local validation and remaining evidence

Validation on 15 October: full unittest suite **546 tests, 513 passed, 33
optional-dependency skips**. The skips include the two source-family executor /
recovery tests added for the catalog; pinned SQLGlot 27.28.1, jsonschema 4.25.1
and referencing 0.36.2 are unavailable locally. Existing optional execution skips
remain. New decoder mask/adapter tests use CPU doubles, not native GPU kernels.
Pinned native tokenizer/XGrammar qualification and model calls were not run.
Shell validation (10 files), compileall, diff whitespace checks and isolated
stdlib CLI help passed. The missing-source catalog/proposal/analysis CLI smoke
retained six blocked slots, twelve planned conditions and unknown rates.

No new GPU diagnostic, normal qualification or task result exists. The catalog
requires the existing cluster source packs and pinned CPU executor before six
reference successes can be claimed. The exact sampled GPU task adapter remains
unimplemented; this handoff prepares the design and blocked proposal only.

## Commands: local inspection

Run from the repository root. Core imports and help need only Python 3.12+
stdlib. Missing pinned optional executors must remain reported skips/blockers.

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
python -I -S scripts/sample_rr_organizations.py --help
python -I -S scripts/prepare_rr_decoder_diagnostic.py --help
python -I -S scripts/prepare_rr_sampled_cohort.py --help
```

`sample_rr_organizations.py --sources EXISTING_SOURCE_ROOT --output NEW_JSON`
inspects public candidates without executing references. Add `--qualify` only
where the existing pinned CPU dependencies and source packs are present. It
records blocked prerequisites rather than manufacturing a qualified catalog.

## Commands: freeze source and run CPU controls on Jupyter

These are user-triggered commands after reviewing/pushing this implementation.
They do not install or download anything. Use the recorded cluster environment
and existing source packs. The base lock supplies staged model metadata; its old
decoder qualification is not reused. Both affected locks are renewed.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_WORK="$(mktemp -d "$BC_STORAGE/diagnostics/rr-two-workstreams.XXXXXX")"
export BC_BASE_LOCK="$BC_STORAGE/diagnostics/rr-unique-nfc.lOjYvr/worker-lock.json"
export BC_PARENT="$BC_STORAGE/outputs/qwen27b-na100/a3aadd6913fb1f2968de6c735183c65f48dfd2cf36c0c9c7c2ed724c6d959a32-preflight"
export BC_CLUSTER="$HOME/Beyond-Consensus/configs/cluster.qwen27b-na100.local.json"

(
set -euo pipefail
set -o noclobber
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: preserve exports outside Git and use a clean checkout.\n'
    exit 1
fi
test -s "$BC_BASE_LOCK"
test -s "$BC_PARENT/manifest.json"
test -s "$BC_PARENT/preflight.json"
git rev-parse HEAD > "$BC_WORK/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_WORK/source"
git -C "$BC_WORK/source" checkout --detach "$(cat "$BC_WORK/source-commit.txt")"

sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --job-name=rr-decoder-cpu --chdir="$BC_WORK/source" \
  --output="$BC_WORK/decoder.out" --error="$BC_WORK/decoder.err" \
  "$BC_WORK/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_WORK/source" --decoder-diagnostic-controls \
  --model-lock "$BC_BASE_LOCK" --output "$BC_WORK/decoder-cpu" \
  > "$BC_WORK/decoder-job.txt"

sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --job-name=rr-catalog-cpu --chdir="$BC_WORK/source" \
  --output="$BC_WORK/catalog.out" --error="$BC_WORK/catalog.err" \
  "$BC_WORK/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_WORK/source" --organization-catalog \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --output "$BC_WORK/catalog-cpu" > "$BC_WORK/catalog-job.txt"
printf 'Retain this directory: %s\n' "$BC_WORK"
)
```

PA100q above is the previously used CPU partition, not a claim of current
availability. No GPU is requested by these CPU jobs. Do not proceed merely
because Slurm exits zero: inspect reference status and missing slots too.

```bash
sacct -j "$(cut -d';' -f1 "$BC_WORK/decoder-job.txt"),$(cut -d';' -f1 "$BC_WORK/catalog-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_WORK/decoder.err"
tail -n 40 "$BC_WORK/catalog.err"
"$BC_PYTHON" -m json.tool "$BC_WORK/catalog-cpu/catalog.json"
```

## Commands: diagnostic proposal, exact approval and dry run

After both required grammar reports and decoder CPU controls pass:

```bash
(
set -euo pipefail
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/prepare_rr_decoder_diagnostic.py proposal \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" \
  --native-lock "$BC_WORK/decoder-cpu/native-lock.json" \
  --controls "$BC_WORK/decoder-cpu/controls.json" \
  --parent-manifest "$BC_PARENT/manifest.json" \
  --parent-report "$BC_PARENT/preflight.json" \
  --output "$BC_WORK/diagnostic-proposal.json" \
  --approval-template "$BC_WORK/diagnostic-approval.pending.json"
)
```

Preparation validates parent identity, current source/control hashes, native
schema equivalence and both exact model qualifications. Review the pending
record and save a separate `diagnostic-approval.json` with only `decision`,
`reviewer`, and `reviewed_at` completed for the approved scope. No approval is
inferred from a passed CPU job. After that specific approval:

```bash
(
set -euo pipefail
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/prepare_rr_decoder_diagnostic.py approve \
  --proposal "$BC_WORK/diagnostic-proposal.json" \
  --approval "$BC_WORK/diagnostic-approval.json" \
  --output "$BC_WORK/diagnostic-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_CLUSTER" --manifest "$BC_WORK/diagnostic-manifest.json" \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" --dry-run
)
```

After reviewing the dry run and allocating the authorized session, the exact
submission command is:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_CLUSTER" --manifest "$BC_WORK/diagnostic-manifest.json" \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" \
  > "$BC_WORK/diagnostic-submission.json"
cat "$BC_WORK/diagnostic-submission.json"
)
```

The parent wrapper starts the two fresh children sequentially and sets launch
blocking before their Python/CUDA startup. Do not run its internal child script
by hand. The shared scheduler/registry guards remain in force. If a submission
fails, inspect its receipt and registry before any new submission; shell
redirection can create an empty receipt. Never delete a started marker or
resubmit a started diagnostic. There is **no resume/retry** for these model calls.

```bash
export BC_DIAG_OUTPUT="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["output"])' "$BC_WORK/diagnostic-submission.json")"
export BC_DIAG_JOB="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["job_id"])' "$BC_WORK/diagnostic-submission.json")"
sacct -j "$BC_DIAG_JOB" --format=JobID,State,ExitCode,Elapsed
```

After completion, read-only aggregation and review preparation:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/bc.py aggregate --output "$BC_DIAG_OUTPUT" \
  > "$BC_WORK/diagnostic-summary.json"
"$BC_PYTHON" -I scripts/prepare_rr_decoder_diagnostic.py review \
  --manifest "$BC_WORK/diagnostic-manifest.json" \
  --report "$BC_DIAG_OUTPUT/preflight.json" \
  --output "$BC_WORK/diagnostic-review.pending.json"
)
```

## Commands: separately reviewed normal qualification

If the matched diagnostic is unresolved, stop here. Otherwise review the full
report, including any native strict-parser rejection and trajectory differences.
Save the reviewed record as `diagnostic-review.json`; only an explicit approved
review may set `normal_qualification_allowed=true`. It cannot make an incomplete
or mismatched diagnostic eligible. Prepare a separate normal approval:

```bash
(
set -euo pipefail
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/prepare_rr_decoder_diagnostic.py normal-proposal \
  --manifest "$BC_WORK/diagnostic-manifest.json" \
  --report "$BC_DIAG_OUTPUT/preflight.json" \
  --review "$BC_WORK/diagnostic-review.json" \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" \
  --controls "$BC_WORK/decoder-cpu/controls.json" \
  --evidence-output "$BC_WORK/normal-evidence.json" \
  --approval-template "$BC_WORK/normal-approval.pending.json"
)
```

After exact approval, save `normal-approval.json` with decision/reviewer/time.
From the same qualified source, prepare and dry-run the three-call normal attempt:

```bash
(
set -euo pipefail
unset CUDA_LAUNCH_BLOCKING
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/prepare_rr_unique_preflight.py \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" \
  --controls "$BC_WORK/decoder-cpu/controls.json" \
  --diagnostic-evidence "$BC_WORK/normal-evidence.json" \
  --approval "$BC_WORK/normal-approval.json" \
  --output "$BC_WORK/normal-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_CLUSTER" --manifest "$BC_WORK/normal-manifest.json" \
  --model-lock "$BC_WORK/decoder-cpu/guarded-lock.json" --dry-run
)
```

Normal submission uses the same `bc.py submit` command without `--dry-run`,
inside `set -euo pipefail; set -o noclobber`, with launch blocking unset and a new
`normal-submission.json` receipt. Do not reuse the diagnostic receipt or output.
If code changes after diagnosis, renew affected CPU/native evidence and review
its compatibility before preparing this record. No ordinary task cohort follows
automatically from a pass.

## Commands: blocked cohort proposal and read-only coverage analysis

These can run while GPU diagnosis is pending. They preserve all twelve slots
and explain blockers. No model loader, task submission or approval bypass exists
in these scripts. The current reference/mock schedule uses the existing branch
engine; a reviewed GPU task adapter remains a separate missing gate.

```bash
(
set -euo pipefail
cd "$BC_WORK/source"
"$BC_PYTHON" -I scripts/prepare_rr_sampled_cohort.py \
  --catalog "$BC_WORK/catalog-cpu/catalog.json" \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --worker-lock "$BC_WORK/decoder-cpu/guarded-lock.json" \
  --output "$BC_WORK/sampled-proposal.json" \
  --approval-template "$BC_WORK/sampled-approval.pending.json"
"$BC_PYTHON" -I scripts/analyze_rr_sampled_cohort.py \
  --proposal "$BC_WORK/sampled-proposal.json" \
  --output "$BC_WORK/sampled-analysis.json"
)
```

After a normal qualification exists, a **new** proposal may include
`--normal-qualification PATH_TO_REPORT`. This retains evidence for exact
compatibility review; a passed status alone never clears task execution. Analysis
can accept `--records JSON_FILE`, an object mapping configuration IDs to saved
results. It rejects unknown configurations and preserves missing branches.

## Debugging reference

PyTorch 2.10 documents asynchronous CUDA execution and launch blocking for
locating errors: [CUDA semantics](https://docs.pytorch.org/docs/2.10/notes/cuda.html)
and [CUDA environment variables](https://docs.pytorch.org/docs/2.10/cuda_environment_variables.html).
This diagnostic applies that setting equally to both fresh processes. It changes
execution timing; it does not establish a production fix or kernel cause.


## Recovery: qualified catalog exceeds the generic JSON limit

If proposal preparation raises `reporecourse.common.Rejected: file_size` at
`load(args.catalog)`, retain the completed CPU outputs and diagnostic proposal.
The sampled CLI now uses the existing bounded 128 MiB operator-record loader;
worker/action limits remain unchanged. Analysis uses that loader too because a
sampled proposal embeds the catalog. This is a read-boundary correction, not a
new qualification or altered reference outcome.

After reviewing/pushing/pulling the correction, run the **updated**
`scripts/prepare_rr_sampled_cohort.py` and `scripts/analyze_rr_sampled_cohort.py`
from the updated repository with the existing catalog, source packs and worker
lock, and fresh output paths. Do not edit the old frozen source or regenerate
the already written diagnostic proposal. Its eventual submission must still
use its original frozen source and controls. No GPU submission is part of this
recovery. The proposal's runtime/task hashes must still match the saved catalog;
the fix does not waive any incompatibility check.
