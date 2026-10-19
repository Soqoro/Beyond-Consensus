# Bounded worker selection — 16 October 2026

## Status and evidence boundary

This is a prospective engineering comparison. **No new model was staged or run by
this implementation session. No worker winner has been established.**

The preceding evidence remains unchanged: six authored organizations had clean
3/6 and F 2/6; the later single-artifact diagnostic passed order granularity,
rejected unpaid-boundary SQL (`case_else_required`), and failed exact mapping keys.
See [the consolidated audit](AUDIT_REPORT_2026-10-16.md) and
[semantic results](SEMANTIC_DIAGNOSTIC_RESULTS.md). Those are development results,
not controls for the new settings. The original AcceleratorError remains unexplained.

## Coder proposal token-ID fix — 18 October 2026

User-reported staging job 1099588 completed 0:0 and saved the asset lock at
`rr-worker-feasibility.eIAIzU/staging.5Bb3l3/model-lock.json`. CPU-native job
1099681 subsequently completed 0:0 with a qualified lock under
`native-accelerate.NfpVuR/model-lock.json`, using the isolated environment with
Accelerate 1.12.0 and psutil 7.0.0. These reports do not establish GPU fit.

Proposal-preparation job 1099714 failed before GPU submission: chat-template
output was a `BatchEncoding`, so hashing the container raised `TypeError`.
The same assumption would have counted mapping keys in long-prompt sizing.
The fix explicitly requests structured output and extracts one validated
`input_ids` sequence for both measurement and hashing. It rejects missing,
empty, malformed or multiple sequences. The long synthetic prompt now uses
actual token counts against the unchanged 12288-input / 4096-output reservation.

The native model/grammar implementation is unchanged. Reuse its qualified lock
only when the existing exact package and implementation checks pass; no lock is
edited or relabelled. Preserve the failed preparation directory. After committing
and pushing the fix, prepare a new proposal from a fresh frozen checkout:

```bash
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_STAGE="$BC_STORAGE/diagnostics/rr-worker-feasibility.eIAIzU/staging.5Bb3l3"
export BC_NATIVE="$BC_STAGE/native-accelerate.NfpVuR"
export BC_WORKER_PYTHON="$(cat "$BC_NATIVE/python-path.txt")"
export BC_CODER_Q="$(mktemp -d "$BC_NATIVE/gpu-proposal-tokenids.XXXXXX")"

(
set -euo pipefail
set -o noclobber
cd "$HOME/Beyond-Consensus"
git pull --ff-only
test -x "$BC_WORKER_PYTHON"
test -s "$BC_NATIVE/model-lock.json"
git rev-parse HEAD > "$BC_CODER_Q/source-commit.txt"
git clone --no-hardlinks --no-checkout "$PWD" "$BC_CODER_Q/source"
git -C "$BC_CODER_Q/source" checkout --detach \
  "$(cat "$BC_CODER_Q/source-commit.txt")"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
sbatch --parsable \
  --partition=NA100q --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=01:00:00 --job-name=rr-coder-q-prepare \
  --chdir="$BC_CODER_Q/source" \
  --output="$BC_CODER_Q/cpu.out" --error="$BC_CODER_Q/cpu.err" \
  "$BC_CODER_Q/source/experiments/worker_selection_cpu.sh" \
  "$BC_CODER_Q/source" "$BC_WORKER_PYTHON" \
  proposal --stage Q --profile coder \
  --model-lock "$BC_NATIVE/model-lock.json" \
  --output "$BC_CODER_Q/proposal.json" > "$BC_CODER_Q/cpu-job.txt"
cat "$BC_CODER_Q/cpu-job.txt"
printf 'Proposal directory: %s\n' "$BC_CODER_Q"
)
```

After the CPU job completes:

```bash
sacct -j "$(cut -d';' -f1 "$BC_CODER_Q/cpu-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_CODER_Q/cpu.err"
(
set -euo pipefail
test -s "$BC_CODER_Q/proposal.json"
"$BC_WORKER_PYTHON" -I "$BC_CODER_Q/source/scripts/worker_selection.py" review \
  --manifest "$BC_CODER_Q/proposal.json" --output "$BC_CODER_Q/review.json"
"$BC_WORKER_PYTHON" -m json.tool "$BC_CODER_Q/review.json"
)
```

This only prepares the four-call scope. GPU submission still requires its exact
review and approval; no staging download or native-control rerun is implied.

Local verification: full suite **627 tests, 591 passed, 36 skipped** (90.729 s).
Focused worker-selection tests: 35 run, 34 passed, one pinned-executor skip.
The three new regression tests use CPU tokenizer doubles, not native model evidence.
All 11 shell-file checks, compilation, stdlib-only CLI help and whitespace checks
passed. The 36 existing optional execution/sandbox skips remain as listed below.
Fresh actual-tokenizer proposal measurement on the cluster remains pending.

### Deployment records

| Profile | Immutable model and tokenizer revision | Generation | Placement proposal |
|---|---|---|---|
| control | Qwen/Qwen3.5-27B, `fc05daec18b0a78c049392ed2e771dde82bdf654` | BF16, thinking on, deterministic, 4096 output / 16384 context | One full 80-GB-class GPU |
| coder | Qwen/Qwen3-Coder-Next, `a7fbcb5c0e12d62a448eaa0e260346bf5dcc0feb` | BF16, documented non-thinking route, no thinking template flag, deterministic, 4096 / 16384 | One process, one node, four full 80-GB-class GPUs; explicit contiguous 12-layer shards |

The [official Coder card](https://huggingface.co/Qwen/Qwen3-Coder-Next)
describes 80B total / 3B activated parameters and non-thinking generation. The
[immutable revision](https://huggingface.co/Qwen/Qwen3-Coder-Next/commit/a7fbcb5c0e12d62a448eaa0e260346bf5dcc0feb)
and [repository inventory](https://huggingface.co/Qwen/Qwen3-Coder-Next/tree/a7fbcb5c0e12d62a448eaa0e260346bf5dcc0feb)
identify 40 weight shards (about 159 GB displayed; **not an exact byte measurement**).
Active parameters do not reduce resident weight requirements. The metadata command
below retrieves exact file sizes and available official LFS hashes before staging.
On 18 October, the official pinned-revision API returned 49 selected assets:
40 weight shards totaling **159358031480 bytes**, and **159376298911 bytes**
including tokenizer/configuration/card assets (148.43 GiB). All 40 shards have
official LFS SHA-256 values. The two-copy staging reserve is **318752597822 bytes**
(296.86 GiB). The card metadata declares `apache-2.0`; the selected inventory
includes README.md but no separate LICENSE file. This metadata observation does
not independently resolve site access or source-task rights.
See [the saved metadata inventory](WORKER_SELECTION_METADATA_2026-10-18.json),
metadata ID `b4fbbeaa8660e8416ef0bae71597509f9e31c492df7b3198f4e9b1ea211ab4da`.
No weight files were downloaded. Site capacity, free staging storage and quota
remain unmeasured.

The reviewed code path uses Transformers 5.3.0's Qwen3Next architecture and
[Accelerate device placement](https://huggingface.co/docs/accelerate/usage_guides/big_modeling).
This is **device-map sharding, not tensor parallelism**. No `auto`, CPU/disk
parameter placement, quantization, server, distributed ranks, or multi-node fallback
is accepted. Proposed exact packages are Transformers 5.3.0, Accelerate 1.12.0,
XGrammar 0.1.32. All other installed inference packages are recorded and matched
exactly between native qualification and loading. Use an isolated environment if
these pins differ from the established baseline; do not mutate a running environment.
The map explicitly includes the global rotary-embedding buffers on GPU 0, as
required by the [pinned Qwen3Next implementation](https://raw.githubusercontent.com/huggingface/transformers/v5.3.0/src/transformers/models/qwen3_next/modeling_qwen3_next.py).
Native mask compatibility and accelerator placement remain unmeasured for Coder.

Requested host RAM is at least 128 GB for control and 256 GB for Coder. Staging
feasibility reserves twice the exact asset bytes. Every device must report at least
75 GiB total and 70 GiB free at load admission. These are conservative admission
requirements, **not a measured fit claim**. Site allocation, quota, interconnect,
loading overhead, and exact package compatibility remain pending. Four permitted
GPUs do not establish that four are co-located and allocatable.

## Fixed experimental design

| Stage | Whole comparison | Per model-loaded block | Resource bounds |
|---|---:|---:|---|
| Q qualification | At most 8 task-free calls | At most 4, stops on failure | 4096 output, 16384 context, 16384 logical tokens / 1200 charged CPU seconds per call |
| A screen | **48 one-call attempts** | 24 | 4096 output, 16384 context; 16384 tokens / 1200 CPU seconds per case |
| B confirmation | **24 one-call attempts** | 12 | Same as A |
| C authored workflows | **24 clean/F branches** | 6 plans × clean/F = 12 branches | 4096 output, 16384 context; 100000 tokens / 1200 CPU seconds per branch |

A sums to 786432 logical tokens / 57600 charged CPU seconds; B to 393216 / 28800;
C to 2400000 / 28800. These are ceilings, not duration estimates or B0. The CPU
contract is strict admission and scoring with recorded operation overshoot, not a
hard host-process cutoff. Terminal private evaluation uses a separate ledger;
static loading/native qualification and scheduler allocation time are separate.

A/B allow one model action only, with no source-reading call, repair, retry or
best-of-N. Properly formatted wrong answers remain possible. Compiler rejection
leaves semantics unmeasured and fails the end-to-end attempt. C keeps existing
action limits, identity loss, monitoring, scopes, allowed imports and common JIT.
Its variable number of generation calls includes worker-backed repair. There is
no second controller model and **zero generated planner calls**.

The CPU-authored sets are transparently synthetic. Each split has six SQL and
six API cases (three schemas, three mappings). Screen: ticket/detail granularity,
zero checks, signed stock, account reconciliation, thresholds, maxima; nullable
fields, bounded arrays, exact records, nested fields, omission, value preservation.
Confirmation independently combines two detail tables, fulfillment, category
aggregation, regional reconciliation, distinct conditional membership, weighted
values; nested nullable records, arrays of records, optional ranges, nested
omission, missing-to-null and array projection. Stable IDs/templates, membership,
public records, literal expected results, references and mutants freeze together.
Confirmation is held back for this selection; it is not an untouched benchmark.

Reference/mutant qualification runs the actual restricted compiler/executor/schema
children and an explicitly labelled single-obligation projection. It never calls
the complete-bundle checker on an incomplete artifact. **The local environment
lacks the pinned optional children; production CPU qualification remains required.**
A failed reference or mutant blocks preparation rather than weakening the scorer.

`P_current` is the current `worker_messages` renderer. `P_minimal` removes only
allowlisted generic publication/SQL examples and compacts JSON whitespace. All
public observations, tool rules, supported-language requirements (including ELSE),
exact keys, histories, scopes, alarms and feedback remain. A field-level parity
record is exported by `inventory`. No private reference is consulted by rendering.
These are presentation packages, not token-matched prompts or isolated-word tests.

Selection is common across both models: highest total semantic successes, then
highest minimum model×domain success count, then P_current. Missing/runtime-defect
rows block selection. No confirmation feedback is used by this rule. B reports
paired cases and the >=10/12 overall, >=5/6 in each domain adequacy heuristic.
It does not force a winner or declare a one-case advantage a major improvement.
Whole-allocation costs must be reviewed before preferring a cheaper adequate model.
C requires a complete B report with at least one adequate worker and fresh exact
approval. Its six plans come from the existing catalog selector: Jaffle and GitHub
multioperation × independent/grouped/shared. The same plan, eligible owners,
seeded target and intervention are frozen for both profiles before clean results.
A valid clean failure does not filter F. Unreviewed-development limitations remain.

## Browser-terminal preparation

Do not copy commands into an unfinished `>` shell prompt. Ctrl-C first. All paths
below are outside Git except the frozen clone. Set site/env variables from real
files; the commands deliberately do not guess a partition or claim a GPU is free.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_SELECT="$(mktemp -d "$BC_STORAGE/diagnostics/rr-worker-select.XXXXXX")"
(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
    git status --short
    exit 1
fi
git rev-parse HEAD > "$BC_SELECT/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_SELECT/source"
git -C "$BC_SELECT/source" checkout --detach "$(cat "$BC_SELECT/source-commit.txt")"
)
export BC_SELECT_SOURCE="$BC_SELECT/source"
```

Inspect site access with `sinfo -N -O NodeHost,Partition,StateCompact,Gres,GresUsed`
and `scontrol show partition PARTITION`. Set `BC_CPU_PARTITION` to an inspected
permitted CPU allocation partition and `BC_SELECT_CLUSTER` to an existing reviewed
cluster JSON. Make a separate cluster JSON for Coder with the isolated Python path,
at least 256 GB host RAM, and a partition supporting **four full GPUs on one node**.
Both model blocks use concurrency one. The shared per-user registry still blocks
other GPU campaigns and uncertain accounting. Do not cancel unrelated jobs.

### M0: metadata and staging dry-run (no weight download)

```bash
cd "$BC_SELECT_SOURCE"
"$BC_PYTHON" -I scripts/worker_selection.py profile --profile coder --output "$BC_SELECT/coder-profile.json"
"$BC_PYTHON" -I scripts/worker_selection.py metadata --profile coder --output "$BC_SELECT/coder-assets.json"
"$BC_PYTHON" -I scripts/worker_selection.py feasibility \
  --assets "$BC_SELECT/coder-assets.json" \
  --destination "$BC_STORAGE/models/qwen3-coder-next-bf16" \
  --partition "$BC_CPU_PARTITION" --output "$BC_SELECT/coder-feasibility.json"
"$BC_PYTHON" -I scripts/worker_selection.py stage \
  --assets "$BC_SELECT/coder-assets.json" \
  --destination "$BC_STORAGE/models/qwen3-coder-next-bf16" \
  --output "$BC_SELECT/coder-staging.pending.json"
```

Stop here for the exact asset/path/rights/quota/allocation review. `stage` without
`--approval` is the explicit dry-run. After the user approves that finite download,
copy the template to a new JSON, set `decision=approved` and the actual reviewer/time,
and pass it via `--approval` in an allocated CPU job. Download happens only in that
explicit step; experiment jobs always use offline local files. The resulting output
is an **unqualified model lock**. License and README files are retained and hashed.
The existing control lock can be reused as staging input if its exact co-revision
metadata and shard inventory pass; its old 2048-token grammar evidence cannot be reused.

### M1/M2: allocated native controls, reference cases and Q proposal

Set `BC_PROFILE=control` or `coder`, `BC_BASE_LOCK` to its real staged lock, and
`BC_MODEL_PYTHON` to its exact isolated environment. Process one profile at a time.
The wrapper accepts the frozen source path explicitly, so Slurm's copied script
location cannot redirect it into the spool directory.

```bash
export BC_PROFILE=control
export BC_MODEL_PYTHON="$BC_PYTHON"
export BC_BLOCK="$BC_SELECT/$BC_PROFILE"
mkdir -p "$BC_BLOCK"
# Set BC_BASE_LOCK to the existing control lock (or approved staged Coder lock).
: "${BC_BASE_LOCK:?Set the real staged model lock path}"
: "${BC_CPU_PARTITION:?Set an inspected permitted partition}"
sbatch --parsable --partition="$BC_CPU_PARTITION" --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --chdir="$BC_SELECT_SOURCE" --output="$BC_BLOCK/native.out" --error="$BC_BLOCK/native.err" \
  "$BC_SELECT_SOURCE/experiments/worker_selection_cpu.sh" \
  "$BC_SELECT_SOURCE" "$BC_MODEL_PYTHON" native --profile "$BC_PROFILE" \
  --model-lock "$BC_BASE_LOCK" --output "$BC_BLOCK/lock.json"
```

After that job completes successfully, run the case controls once on the same
frozen source with pinned SQLGlot 27.28.1, jsonschema 4.25.1, referencing 0.36.2:

```bash
sbatch --parsable --partition="$BC_CPU_PARTITION" --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 \
  --chdir="$BC_SELECT_SOURCE" --output="$BC_SELECT/cases.out" --error="$BC_SELECT/cases.err" \
  "$BC_SELECT_SOURCE/experiments/worker_selection_cpu.sh" \
  "$BC_SELECT_SOURCE" "$BC_MODEL_PYTHON" controls --output "$BC_SELECT/case-controls.json"
"$BC_MODEL_PYTHON" -I "$BC_SELECT_SOURCE/scripts/worker_selection.py" inventory \
  --output "$BC_SELECT/cases.private.json"
```

The private inventory is for offline author audit only; do not upload it to a
worker, model service, or public result. It contains confirmation references.
The `controls` command returns nonzero unless all 24 references and 24 mutants pass.
Run `python -m unittest tests.test_worker_selection -v` in the same CPU allocation;
the production-path test must not skip there. Native controls load tokenizers and
masks but never weights.

Prepare Q in a CPU allocation:

```bash
sbatch --parsable --partition="$BC_CPU_PARTITION" --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=01:00:00 \
  --chdir="$BC_SELECT_SOURCE" --output="$BC_BLOCK/q-prepare.out" --error="$BC_BLOCK/q-prepare.err" \
  "$BC_SELECT_SOURCE/experiments/worker_selection_cpu.sh" \
  "$BC_SELECT_SOURCE" "$BC_MODEL_PYTHON" proposal --stage Q --profile "$BC_PROFILE" \
  --model-lock "$BC_BLOCK/lock.json" --output "$BC_BLOCK/q-proposal.json"
```

Q covers SQL envelope, schema envelope, nested/escaped mapping, and a measured
near-12288-token synthetic input. At most four calls, fresh caches. Early EOS
establishes only the observed footprint. Inspect errors; never automatically rerun.

## Exact-scope approval and guarded submission

This reusable sequence applies to ONE prepared block. For Q set:

```bash
export BC_PHASE=q
export BC_MODE=preflight
export BC_PROPOSAL="$BC_BLOCK/$BC_PHASE-proposal.json"
export BC_REVIEW="$BC_BLOCK/$BC_PHASE-review.json"
export BC_APPROVAL="$BC_BLOCK/$BC_PHASE-approval.json"
export BC_APPROVED="$BC_BLOCK/$BC_PHASE-approved.json"
export BC_RECEIPT="$BC_BLOCK/$BC_PHASE-submission.json"
```

For the later stages, set `BC_PHASE=a`, `b`, or `c`, `BC_MODE=run`, and repeat
those five path exports. Each stage has fresh files. The review command does not approve.

```bash
cd "$BC_SELECT_SOURCE"
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py review \
  --manifest "$BC_PROPOSAL" --output "$BC_REVIEW"
"$BC_MODEL_PYTHON" -m json.tool "$BC_REVIEW"
```

After explicit scope approval, write **only** that `approval_template` object to
`BC_APPROVAL`, changing `decision` to `approved`, `reviewer` to the actual reviewer
and `reviewed_at` to the actual timestamp. Keep every scope field unchanged.
Then:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_SELECT_SOURCE"
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py approve \
  --manifest "$BC_PROPOSAL" --model-lock "$BC_BLOCK/lock.json" \
  --approval "$BC_APPROVAL" --output "$BC_APPROVED"
"$BC_MODEL_PYTHON" -I scripts/bc.py submit --mode "$BC_MODE" --concurrency 1 \
  --cluster "$BC_SELECT_CLUSTER" --manifest "$BC_APPROVED" \
  --model-lock "$BC_BLOCK/lock.json" --dry-run
)
```

Inspect physical `--gres=gpu:1` or `gpu:4`, **one node and one task**, memory,
partition, environment and wall limit. The existing site's two-hour default may
be too short for a whole workflow block; choose a finite reviewed wall bound
before submitting, not after seeing outputs. Scheduler limits are not inferred.
After the dry-run passes and the exact block is authorized:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_SELECT_SOURCE"
"$BC_MODEL_PYTHON" -I scripts/bc.py submit --mode "$BC_MODE" --concurrency 1 \
  --cluster "$BC_SELECT_CLUSTER" --manifest "$BC_APPROVED" \
  --model-lock "$BC_BLOCK/lock.json" > "$BC_RECEIPT"
cat "$BC_RECEIPT"
)
```

An empty receipt after a rejected submission is not a completed attempt. Inspect
`squeue`, the registry's `uncertain_submission`, and the output's
`worker-started.json` before archiving an empty receipt. **A started block cannot
resume or retry.** Status/export is the only continuation for started attempts;
missing rows remain visible. A rejected pre-dispatch submission can be retried
with the same manifest after scheduler reconciliation, without recreating approval.

## Reports and transitions

```bash
export BC_JOB="$("$BC_MODEL_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["job_id"])' "$BC_RECEIPT")"
export BC_RUN="$("$BC_MODEL_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["output"])' "$BC_RECEIPT")"
sacct -j "$BC_JOB" --format=JobID,State,ExitCode,Elapsed
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py report --run "$BC_RUN" --output "$BC_BLOCK/result.json"
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py allocation \
  --run "$BC_RUN" --receipt "$BC_RECEIPT" --output "$BC_BLOCK/allocation.json"
```

Q writes `worker-report.json` and the standard `preflight.json` (the batch exit status also matters). Review all four
passes, exact model/lock/source/runtime bindings and actual hardware. A Q pass
never authorizes task execution or asserts worst-case fit. Keep Q's output path
as `BC_QUALIFICATION` for this profile.

A/B proposals are CPU-allocation commands through the same wrapper:

```bash
# In the CPU allocation, with the frozen source as cwd:
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py proposal --stage A --profile "$BC_PROFILE" \
  --model-lock "$BC_BLOCK/lock.json" --controls "$BC_SELECT/case-controls.json" \
  --qualification "$BC_QUALIFICATION/worker-report.json" --output "$BC_BLOCK/a-proposal.json"
```

Prepare and approve both A blocks under the same frozen study, then submit each
serially (control and Coder never overlap). After both finish, set `BC_A_CONTROL`
and `BC_A_CODER` to their actual output directories:

```bash
"$BC_PYTHON" -I scripts/worker_selection.py compare \
  --runs "$BC_A_CONTROL" "$BC_A_CODER" --output "$BC_SELECT/a-comparison.json"
```

Inspect all 48 rows and the prescribed common presentation selection. Only after
that review, prepare each B block with `--stage B`, the same locks/controls/Q
report, and `--prior "$BC_SELECT/a-comparison.json"`:

```bash
# CPU allocation, after the complete A report has been reviewed.
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py proposal --stage B --profile "$BC_PROFILE" \
  --model-lock "$BC_BLOCK/lock.json" --controls "$BC_SELECT/case-controls.json" \
  --qualification "$BC_QUALIFICATION/worker-report.json" --prior "$BC_SELECT/a-comparison.json" \
  --output "$BC_BLOCK/b-proposal.json"
```

No case or renderer edits.
Approve the exact 24-attempt scope; submit the two blocks serially. Combine them
with the same `compare --runs` command into `b-comparison.json`. This reports
adequacy, domain counts, paired wins/ties/losses, costs including failures and
missing/uncertain observations. Scheduler costs remain a separate report; do not
substitute generation-only time for the whole allocation or rank cheap failures.

C is prepared only after B review supports it. Renew catalog CPU certificates on
the current frozen runtime; recipe/plan selection is unchanged:

```bash
# CPU allocation; potentially substantial reference execution.
"$BC_PYTHON" -I scripts/sample_rr_organizations.py \
  --sources "$BC_STORAGE/datasets/reporecourse-v01" --pool 7 --candidate-limit 12 \
  --qualify --output "$BC_SELECT/catalog.private.json"
"$BC_MODEL_PYTHON" -I scripts/worker_selection.py proposal --stage C --profile "$BC_PROFILE" \
  --model-lock "$BC_BLOCK/lock.json" --controls "$BC_SELECT/case-controls.json" \
  --qualification "$BC_QUALIFICATION/worker-report.json" --prior "$BC_SELECT/b-comparison.json" \
  --catalog "$BC_SELECT/catalog.private.json" --sources "$BC_STORAGE/datasets/reporecourse-v01" \
  --output "$BC_BLOCK/c-proposal.json"
```

Review plan hashes/targets against the six-organization characterization and actual
source/rights records; do not fabricate independent review. Each C block measures
its own tokenizer's initial/source-read observations and reference serialization.
Later histories can still exhaust context; no silent truncation is permitted.
Approve the exact 24-branch scope, run two serial blocks, then `compare` them.
The exports retain all planned branches, actual binding/read/reuse metadata,
clean/F status, correctness, conformance and costs. They omit artifact bodies,
private witnesses and raw model text. No full-campaign or training gate opens.

## Accounting interpretation

Single-process sharding sums CPU time across that process's threads. The adapter
rejects distributed ranks or untracked inference child processes. Trusted tool
children retain their existing separately measured CPU accounting; parent overlap
is subtracted by the existing ledger. Missing generated usage remains reserved or
uncertain. Over-cap answers cannot become in-budget successes.

Generation intervals synchronize all allocated devices. Device occupancy is
number of devices × elapsed interval, never a sum of overlapping CUDA events.
A/B report task and terminal-evaluator intervals separately. Workflow call costs
are saved separately from branch logical ledgers. Loading, process interval and
teardown are recorded; `allocation` uses only the scheduler allocation row, never
adds `.batch` CPU to aggregate CPU. Unknown scheduler counts/time remain incomplete.
There is no assertion that equal tokens mean equal physical work, no energy claim,
and no B0 estimate.

## Bounded next step

Review the small official metadata and actual one-node four-GPU feasibility record,
then qualify CPU references and each model-specific native path in allocations.
Do not download Coder weights or launch Q/A/B/C merely because code exists.

## Local validation — 16 October 2026

Final unchanged-code run: `python -m unittest discover -s tests -v` completed
**624 tests in 80.481 seconds: 588 passed, 36 skipped, zero failures/errors**.
The worker-selection module contributed 32 tests: 31 passed and one pinned
production-executor test skipped. CPU model doubles are not model competence.

Also passed: `python scripts/check_shell.py` (11 shell files),
`python -m compileall -q src tests scripts`, stdlib-only
`python -I -S scripts/bc.py --help`, stdlib-only worker-selection CLI help,
`git diff --check`, and syntax checking all 14 Bash blocks in this runbook.

Thirty-five skips require unavailable pinned optional execution dependencies
(SQLGlot 27.28.1 and, where applicable, jsonschema 4.25.1 / referencing 0.36.2).
The remaining skip is the separately opted-in legacy container/cgroup integration
profile. New native tokenizer/grammar controls and GPU Q calls were **not run**;
they are separate pending qualifications, not successful or skipped model tests.
All 48 new production reference/mutant control rows remain blocked prerequisites
locally. No measured task outcome, GPU cost, or adequate worker is claimed.

<details>
<summary>Every skipped test and its recorded reason</summary>

```text
test_actual_compiler_distinguishes_undeclared_object (test_reporecourse.PublicSQLInterfaceTests.test_actual_compiler_distinguishes_undeclared_object) ... skipped 'pinned optional CPU dependencies unavailable'
test_all_baselines_clean_and_announced_loss (test_reporecourse.VerticalTests.test_all_baselines_clean_and_announced_loss) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_both_families_witnesses_and_negatives (test_reporecourse.VerticalTests.test_both_families_witnesses_and_negatives) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_existing_journal_runner_adapter_with_explicit_test_backend (test_reporecourse.VerticalTests.test_existing_journal_runner_adapter_with_explicit_test_backend) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_fixed_state_graph_and_equal_remaining (test_reporecourse.VerticalTests.test_fixed_state_graph_and_equal_remaining) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_independent_benchmark_execution_without_bc (test_reporecourse.VerticalTests.test_independent_benchmark_execution_without_bc) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_replica_checkpoint_preserves_primary_and_resumes (test_reporecourse.VerticalTests.test_replica_checkpoint_preserves_primary_and_resumes) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_resume_and_latest_bound_not_best (test_reporecourse.VerticalTests.test_resume_and_latest_bound_not_best) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_schema_rebind_reuses_program_preserves_exposure (test_reporecourse.VerticalTests.test_schema_rebind_reuses_program_preserves_exposure) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_shared_plan_repair_and_no_forced_regeneration (test_reporecourse.VerticalTests.test_shared_plan_repair_and_no_forced_regeneration) ... skipped 'requires pinned SQLGlot 27.28.1, jsonschema 4.25.1 and referencing 0.36.2 CPU children'
test_both_families_all_topologies_pools_2_and_8_and_loss (test_reporecourse_scoped.ActualExecutionTests.test_both_families_all_topologies_pools_2_and_8_and_loss) ... skipped 'pinned SQLGlot/jsonschema/referencing required'
test_generated_plan_to_restricted_execution_through_model_interfaces (test_reporecourse_scoped.ActualExecutionTests.test_generated_plan_to_restricted_execution_through_model_interfaces) ... skipped 'pinned SQLGlot/jsonschema/referencing required'
test_stock_old_reuse_denied_corrected_and_wrong_conformant (test_reporecourse_scoped.ActualExecutionTests.test_stock_old_reuse_denied_corrected_and_wrong_conformant) ... skipped 'pinned SQLGlot/jsonschema/referencing required'
test_actual_journal_runner_three_shards_and_overcap_correctness (test_reporecourse_track_f.ExecutorControls.test_actual_journal_runner_three_shards_and_overcap_correctness) ... skipped 'current pinned SQLGlot/jsonschema/referencing CPU children required'
test_both_losses_resume_visibility_wrong_repair (test_reporecourse_track_f.ExecutorControls.test_both_losses_resume_visibility_wrong_repair) ... skipped 'current pinned SQLGlot/jsonschema/referencing CPU children required'
test_both_families_all_pools_reference_clean_and_loss (test_reporecourse_v2.ExecutableFamilies.test_both_families_all_pools_reference_clean_and_loss) ... skipped 'pinned optional CPU dependencies unavailable'
test_common_jit_rebinds_unchanged_consumer_without_model_call (test_reporecourse_v2.ExecutableFamilies.test_common_jit_rebinds_unchanged_consumer_without_model_call) ... skipped 'pinned optional CPU dependencies unavailable'
test_actual_isolation_and_cleanup (test_repository.RealSandboxTests.test_actual_isolation_and_cleanup) ... skipped 'Real container/cgroup qualification requires explicit BC_SANDBOX_TEST_PROFILE'
test_both_planners_use_actual_scoped_engine_and_common_repair (test_rr_cohort.Prospective.test_both_planners_use_actual_scoped_engine_and_common_repair) ... skipped 'Pinned optional execution dependencies required'
test_schema_and_mapping_examples_execute_without_semantic_repair (test_rr_interface.CompilerContracts.test_schema_and_mapping_examples_execute_without_semantic_repair) ... skipped 'pinned compiler/schema child dependencies unavailable'
test_supported_and_unsupported_examples_exact_child_feedback (test_rr_interface.CompilerContracts.test_supported_and_unsupported_examples_exact_child_feedback) ... skipped 'pinned compiler/schema child dependencies unavailable'
test_actual_scoped_engine_with_shared_model_interface_double (test_rr_open_clean.Boundaries.test_actual_scoped_engine_with_shared_model_interface_double) ... skipped 'Pinned optional execution dependencies required'
test_both_faults_real_engine_with_cpu_backend_double (test_rr_open_fault.Contracts.test_both_faults_real_engine_with_cpu_backend_double) ... skipped 'Pinned optional execution dependencies required'
test_actual_shared_fault_recovery_keeps_loss_and_conformance (test_rr_organization_sampler.Sampler.test_actual_shared_fault_recovery_keeps_loss_and_conformance) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_all_six_references_and_semantic_controls_use_actual_bundle_scorer (test_rr_organization_sampler.Sampler.test_all_six_references_and_semantic_controls_use_actual_bundle_scorer) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_actual_schema_both_extreme_mutants_fail (test_rr_rich_tasks.Cards.test_actual_schema_both_extreme_mutants_fail) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_both_families_two_real_reference_paths_and_reset (test_rr_rich_tasks.Cards.test_both_families_two_real_reference_paths_and_reset) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_fault_persistent_loss_and_originals_not_starved (test_rr_rich_tasks.Cards.test_fault_persistent_loss_and_originals_not_starved) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_missing_output_not_rescued_and_changed_source_rejected (test_rr_rich_tasks.Cards.test_missing_output_not_rescued_and_changed_source_rejected) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_multioperation_distinct_artifacts_and_same_bundle_mutants (test_rr_rich_tasks.Cards.test_multioperation_distinct_artifacts_and_same_bundle_mutants) ... skipped 'Pinned SQLGlot/jsonschema/referencing CPU dependencies'
test_actual_production_paths (test_rr_semantic_diagnostic.ProductionControls.test_actual_production_paths) ... skipped 'pinned SQLGlot/jsonschema/referencing required'
test_actual_model_double_to_production_executor (test_rr_semantic_run.Sequence.test_actual_model_double_to_production_executor) ... skipped 'pinned SQLGlot/jsonschema/referencing required'
test_rejects_and_resource_bounds (test_sql_text.CompilerTests.test_rejects_and_resource_bounds) ... skipped 'optional pinned SQLGlot required'
test_runtime_fail_closed_charges_and_wrong_query (test_sql_text.CompilerTests.test_runtime_fail_closed_charges_and_wrong_query) ... skipped 'optional pinned SQLGlot required'
test_synthetic_semantic_parity (test_sql_text.CompilerTests.test_synthetic_semantic_parity) ... skipped 'optional pinned SQLGlot required'
test_actual_restricted_reference_mutants (test_worker_selection.Design.test_actual_restricted_reference_mutants) ... skipped 'Pinned SQLGlot/jsonschema/referencing unavailable'
```

</details>


## Child-CPU failure diagnostic — 18 October 2026

Preserve failed Q experiment `a35a048d57dc7fe455205115316f70555a844db84cf0e8c77ba2fa5490d688eb`
and its started marker. Do not resubmit it. Loading four GPUs succeeded in that
observation; no qualification case passed and three were unrun.

The updated profile saves `inference_child_cpu` on qualification failure:
reaped-child user/system CPU before and after generation, their delta, and
best-effort boundary child PID/name snapshots. These are diagnostic observations,
not a continuous process trace or attribution to a compiler/library. No command
lines or environments are saved. `cpu_accounting_complete: false` is explicit;
parent CPU debit and uncertain token reservation retain their existing meaning.
No child CPU is silently charged or waived, and the guard remains enforced.

After pushing this change, use a fresh preparation directory and frozen source.
Run the CPU controls and `worker_selection.py native` again using the existing
staged asset lock and isolated Python environment (no weight download). Changing
worker_profiles.py invalidates the old native qualification hash. Build and
review a fresh stage-Q proposal with that renewed lock. Its exact approval must
refer to the new proposal; the failed run's approval is not a retry permission.
Only then submit via the shared registry. This remains at most four synthetic
calls, stopping on the first failure, with no task branches. If child CPU recurs,
inspect the new evidence before specifying any changed accounting contract.


## Process-launch attribution — 19 October 2026

The second failed Q run (`b2b0fc4f2c24fe515c8c06bb8c7a3da866160e5c98b101d8bbdc739dc39e4a08`)
measured 11.835 ms reaped-child CPU but no child at either boundary. Preserve it;
do not replay or rescore it. The new `process_launch_trace` field records Python
audit launch attempts during inference, including basename and bounded calling
locations. It does not capture command arguments, environment values, shell
strings, source lines or locals. A launch attempt can fail; it is not a PID or
proof that a particular child consumed the measured CPU. Native-library launches
can bypass these hooks, so an empty trace does not establish absence of children.

Use the same fresh-directory CPU controls/native/proposal/review sequence with
this newly committed source and the staged model assets. Native implementation
hashes now include process_trace.py, so older locks cannot be reused unchanged.
Inspect the new exact Q proposal before approval/submission. Existing approvals
cover completed attempts only. No GPU rerun or task execution is authorized by
these instrumentation changes. On failure export each row's entire
`inference_child_cpu` (including nested `process_launch_trace`); on successful
calls the trace is in generation diagnostics. Trace overhead remains in measured
parent CPU; child CPU stays diagnostic-only and the guard remains enforced.
