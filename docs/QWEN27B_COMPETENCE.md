# Opt-in Qwen3.5-27B clean competence gate

Prepared 2026-09-20. **No 27B weights, qualification, GPU preflight or model results
exist in this workspace.** The user selected 27B and skipped 9B. Existing 4B
profiles/defaults and all task/scorer/history rules remain intact. Do not promote
the candidate, start attacks/policy/SILO runs, or submit later stages automatically.

## Evidence and frozen condition

The prior [progress report](PROGRESS_REPORT_2026-09-20.md) remains the historical
record. Constrained 4B scored 1/4 (view), with three public integration passes,
28649 work. Aggregate used wrong operations; CASE omitted `sign_label`; join
repeated aliases then capped reasoning. CASE still fails. These are four probes
from **one synthetic source group**, not independent native instances.

The new condition preserves those task definitions, public instructions/tools,
JSON grammar/order/whitespace, retries/history, final columns/order, monitor,
BF16, thinking, deterministic decoding (temperature .7/top-p .8/top-k 20 stored),
2048 shared reasoning/action tokens, 12 actions and 100000 surrogate work each.
Context 8192 means **input + allowed output**, so at most 6144 input tokens at
the full output allowance. No history truncation or forced reasoning close.
Seed 0 is explicitly configured. The **actual historical resolved manifest is
absent locally**; its reported seed/settings are not reconstructed as evidence.
Until comparison succeeds and source differences are reviewed, label this an
**unmatched competence screen**, not model-only improvement.

New shared instrumentation records reservation/released work and wall time.
Charges and dispatch rules are unchanged: reserve 30 decoder CPU seconds × tool
charge per call, reconcile ceil(measured CPU seconds) × tool charge; unknown
failed/interrupted work retains its full reservation. Generated tokens include
reasoning, delimiters, EOS and failed/capped responses. Missing reasoning
partitions remain null. Prefill timing is unknown, not zero. Static grammar setup
is reported once per backend, separately from episode work. No 4B allocator
calibration is reused. Equal surrogate allowance does not mean equal FLOPs,
latency, electricity or GPU cost.

`competence-compare` checks resolved configs, tasks, regimes and grammar, and
reports interface hashes. An old immutable snapshot can supply missing interface
hashes. Different source revisions always require backend review even when
recorded invariant fields match. Do not claim causal size effects: tokenizer,
template, model configuration and hardware can differ. A necessary shared
behavioral fix requires a newly matched 4B rerun before a controlled claim.

## Official pin and dependency review

Small official metadata retrieved on 2026-09-20 from the
[model API](https://huggingface.co/api/models/Qwen/Qwen3.5-27B) resolved
`fc05daec18b0a78c049392ed2e771dde82bdf654`. This is the
[post-trained model](https://huggingface.co/Qwen/Qwen3.5-27B), not Base/MoE/quantized.
The pinned [config](https://huggingface.co/Qwen/Qwen3.5-27B/blob/fc05daec18b0a78c049392ed2e771dde82bdf654/config.json)
identifies `Qwen3_5ForConditionalGeneration`, vocabulary 248320, BF16 and FP32
recurrent state. The pinned [tokenizer config](https://huggingface.co/Qwen/Qwen3.5-27B/blob/fc05daec18b0a78c049392ed2e771dde82bdf654/tokenizer_config.json)
and [generation config](https://huggingface.co/Qwen/Qwen3.5-27B/blob/fc05daec18b0a78c049392ed2e771dde82bdf654/generation_config.json)
are staged at that same revision; effective stops/pad are derived and qualified,
not copied from 4B.

The loader exists in [Transformers 5.3.0 source](https://github.com/huggingface/transformers/blob/v5.3.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py),
including native FP32 recurrent arithmetic. Keep the reported working stack
(Python 3.12.10, torch 2.10.0+cu126, Transformers 5.3.0, XGrammar 0.1.32) if intact.
[Current documentation](https://huggingface.co/docs/transformers/model_doc/qwen3_5)
is background, not permission to install a newer framework. Actual checkpoint
loading remains untested. Runtime records parameter/buffer dtypes and observed
cache-state dtypes; internal accumulation is not instrumented. No whole-model
FP32 cast, component removal, quantization, auto-sharding or offload is performed.

Qualification uses the actual tokenizer/template, verifies the generation-prompt
thinking opener, generated close transition, absence of injected native/XML tool
blocks, exact effective stops and completion masks. Its full implementation,
metadata, package and schema key is embedded in a **new** qualified lock. No
persistent compiled grammar is reused. Source/package changes require another
qualification. Approximately 282 prior CPU seconds was setup CPU time, not wall
time; qualification belongs in a CPU allocation.

## 1. Local review and checks

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python scripts/check_docs_shell.py
python -m compileall -q src tests scripts
python -I -S scripts/bc.py --help
git diff --check
git status --short
git diff
```

Review both the pre-existing progress-report edits and this implementation. Then
**you** commit the intended files and push to the existing remote. No commit/push
has been performed by the assistant. Do not commit private data or output files.

## 2. Browser terminal: configure a separate approved GPU profile

A full A100/H100 80-GB-class allocation is required. NH100q/PH100q are historical
site examples, not assumed permissions. Ask the site or use your approved profile.
Runtime rejects MIG, 40/48 GB, multiple visible devices, less than 75 GiB total or
70 GiB free, and missing BF16 support **before weight loading**. Thresholds are
80530636800 and 75161927680 bytes. Passing them does not guarantee fit: roughly
54 decimal GB of BF16 parameters excludes caches, states and buffers. Resource
absence means queue/block; never fall back to a 40 GB allocation.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC27_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/qwen27b.XXXXXX")"
export BC27_CLUSTER="$PWD/configs/cluster.qwen27b.local.json"
export BC27_CONFIG="$PWD/configs/qwen27b-sql-competence.json"
export BC27_STAGE_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json"
export BC27_LOCK="$BC27_DIR/qualified-model-lock.json"
printf 'Save this directory for later shells: %s\n' "$BC27_DIR"
sinfo -N -O NodeHost,Partition,StateCompact,Gres,GresUsed
cp -n configs/cluster.qwen27b.template.json "$BC27_CLUSTER"
```

Edit the new local JSON: permitted partition, explicit site-approved time/host
RAM (template proposes 128 GB, not VRAM), Python and absolute storage/cache/
snapshot/output roots. Retain existing activation/modules if required. No invented
account/QoS/GRES is needed. Do not overwrite the 4B cluster file. Inspect:

```bash
"$BC_PYTHON" -m json.tool "$BC27_CLUSTER"
export BC27_PARTITION="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["partition"])' "$BC27_CLUSTER")"
```

## 3. Separate explicit staging (downloads weights only when you invoke it)

Check filesystem capacity **and your user quota** with the site's quota tools.
Set `BC27_QUOTA_BYTES` to confirmed available quota, not total filesystem free
space. The stager fetches pinned file sizes and requires their sum plus 10 GiB
within both quota and disk free space before download. This does not install or
upgrade packages. Use existing approved setup/download resources for this step.

```bash
df -h "$BC_STORAGE"
"$BC_PYTHON" scripts/bc.py stage-model --config "$BC27_CONFIG" \
  --root "$BC_STORAGE/models" --dry-run
read -r -p 'Confirmed available user quota in bytes: ' BC27_QUOTA_BYTES
export BC27_QUOTA_BYTES
```

After storage review, separately invoke the download once (not inside each GPU
array element). Concurrent staging is locked. Files stay outside Git.

```bash
"$BC_PYTHON" scripts/bc.py stage-model --config "$BC27_CONFIG" \
  --root "$BC_STORAGE/models" --available-quota-bytes "$BC27_QUOTA_BYTES"
```

## 4. CPU allocation: qualify tokenizer/decoder, no model loading

Freeze a clean committed checkout for CPU work. Package mismatches are blockers;
do not mutate a running environment. Request an approved CPU allocation through
sbatch (no srun needed). These CPU requests use the configured partition without
requesting a GPU; if that is not permitted, use a site-approved CPU partition.

```bash
(
set -euo pipefail
test -z "$(git status --porcelain)"
mkdir "$BC27_DIR/source"
git archive --format=tar HEAD | tar -xf - -C "$BC27_DIR/source"
git rev-parse HEAD > "$BC27_DIR/source-commit.txt"
chmod -R a-w "$BC27_DIR/source"
cat > "$BC27_DIR/qualify.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?CPU allocation required}"
cd "$BC27_DIR/source"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$BC_PYTHON" -I scripts/check_action_constraints.py \
  --model-lock "$BC27_STAGE_LOCK" --output "$BC27_DIR/cpu-qualification.json" \
  --qualified-lock "$BC27_LOCK"
SH
bash -n "$BC27_DIR/qualify.sh"
)
```

User submission only:

```bash
sbatch --partition="$BC27_PARTITION" --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=01:00:00 --output="$BC27_DIR/cpu.out" \
  --error="$BC27_DIR/cpu.err" "$BC27_DIR/qualify.sh"
```

After completion, inspect; do not continue on failure:

```bash
cat "$BC27_DIR/cpu.err"
"$BC_PYTHON" -m json.tool "$BC27_DIR/cpu-qualification.json"
test -f "$BC27_LOCK"
"$BC_PYTHON" scripts/bc.py manifest --config "$BC27_CONFIG" \
  --model-lock "$BC27_LOCK" --output "$BC27_DIR/manifest.json"
"$BC_PYTHON" scripts/bc.py competence-compare --manifest "$BC27_DIR/manifest.json" \
  --output "$BC27_DIR/comparison-unmatched.json"
```

To audit the **actual** historical 4B manifest if still present, use its real path,
not a regenerated config. The known directory is an example; check existence.
The optional `--control-source` takes its verified immutable snapshot directory.

```bash
export BC4_MANIFEST="$BC_STORAGE/diagnostics/sqlite-constrained.fkQai1/manifest.json"
if test -f "$BC4_MANIFEST"; then
  "$BC_PYTHON" scripts/bc.py competence-compare --manifest "$BC27_DIR/manifest.json" \
    --control-manifest "$BC4_MANIFEST" --output "$BC27_DIR/comparison-recorded.json"
fi
```

Missing raw evidence stays missing. Compare output lists invariant hashes and
permitted checkpoint/revision/tokenizer changes. Do not interpret missing source
hashes as matching. Full source identity and hardware differ even if fields match.

## 5. Dry-run and manually submit ONE GPU preflight

```bash
bash experiments/submit_gpu_preflight.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_DIR/manifest.json" --model-lock "$BC27_LOCK" --dry-run
```

Review partition, one GPU, Python, memory, paths, time. Then separately:

```bash
bash experiments/submit_gpu_preflight.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_DIR/manifest.json" --model-lock "$BC27_LOCK"
```

After completion:

```bash
export BC27_ID="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' "$BC27_DIR/manifest.json")"
export BC27_OUTPUT="$BC_STORAGE/outputs/$BC27_ID"
"$BC_PYTHON" -m json.tool "$BC27_OUTPUT-preflight/preflight.json"
tail -n 60 "$BC27_OUTPUT-preflight"/logs/*.err
```

Review `command_failed`, both structured completions, hardware-before-load,
placement/dtypes, qualification key, load and generation time/memory, actual
input/output/cache lengths and CPU executor result. The synthetic history reaches
within 32 tokens of 6144 input tokens. Early EOS does **not** establish worst-case
8192-token cache fit. OOM fails without fallback. Missing cache/prefill/accumulation
measurements are explicitly unknown. No hidden task data enters these prompts.

## 6. Only after preflight review: four probes, concurrency ONE

```bash
bash experiments/submit_pilot.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_DIR/manifest.json" --model-lock "$BC27_LOCK" \
  --concurrency 1 --dry-run
```

Review exactly four episodes, one shard. Separately submit:

```bash
bash experiments/submit_pilot.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_DIR/manifest.json" --model-lock "$BC27_LOCK" --concurrency 1
```

The shared registry/scheduler checks, immutable snapshots and resume identities
are reused. One active campaign/max four GPUs remains enforced by this workflow;
`%4` alone would not enforce a cross-job limit. Unrelated manual jobs are outside
a wrapper's authority. No batch job submits another. This initial profile has
one shard; later concurrency changes require explicit review, not a silent edit.

## 7. After completion: audit all four, including failures

```bash
"$BC_PYTHON" scripts/bc.py aggregate --output "$BC27_OUTPUT"
"$BC_PYTHON" scripts/bc.py competence-audit --run "$BC27_OUTPUT" \
  --output "$BC27_DIR/competence-audit.json"
"$BC_PYTHON" scripts/bc.py diagnostic-costs --run "$BC27_OUTPUT" \
  --output "$BC27_DIR/observed-costs.json"
"$BC_PYTHON" -m json.tool "$BC27_DIR/competence-audit.json"
```

If the original 4B output exists, repeat audit to a **new path** with
`--control-run "$BC_STORAGE/outputs/d701d4b32a8d44d6d4b51a7b0df94a7ab1b7b53a98d996a69248f2f2c1b3ba80"`.
Read that per-task comparison together with the compatibility report. Historical
summaries are labelled reported, never substituted for absent raw rows.

Audit exports contain bounded counters/ledger measurements, not raw text, native
references, whole environments or tensors. View rows absent from stored artifacts
remain unknown in offline diagnostics; terminal score is untouched. Projection
alias diagnostics describe declared output contracts. Public integration is
separate from terminal correctness. Generic rejection categories stay generic.
Capped text is still re-fed exactly as before; no history fix is hidden here.

Decision guide (not a statistical test): 4/4 permits considering native feasibility
after renewal; 3/4 requires inspecting the failure; 0–2/4 or repeated protocol/cap
failures stops expansion. Never retry semantic failures as infrastructure errors,
select seeds, increase the cap automatically or jump to another model.

## 8. Separate CPU solar reference renewal

These existing materials were obtained and reviewed; do not restart email or
substitute crypto pairs. Local absence is a path/access blocker, not evidence
that the cluster files are missing. Configure real existing paths:

```bash
export BC_SQLITE_ROOT="$BC_STORAGE/datasets/livesqlbench-0664a2f"
export BC_SQLITE_MATERIALS="$BC_STORAGE/private/livesqlbench/materials.private.jsonl"
export BC_SOLAR_REVIEW="$BC_STORAGE/private/livesqlbench/solar-check.NatDlH/solar-review.private.json"
export BC27_SOLAR="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-27b-renewal.XXXXXX")"
(
set -euo pipefail
test -f "$BC_SQLITE_MATERIALS"
test -f "$BC_SOLAR_REVIEW"
cat > "$BC27_SOLAR/renew.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?CPU allocation required}"
cd "$BC27_DIR/source"
"$BC_PYTHON" -I scripts/bc.py sqlite-stage --root "$BC_SQLITE_ROOT" \
  --materials "$BC_SQLITE_MATERIALS" --review "$BC_SOLAR_REVIEW" \
  --output "$BC27_SOLAR/reviewed-stage.json" > "$BC27_SOLAR/inspection.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-readiness --staged "$BC27_SOLAR/reviewed-stage.json" \
  --output "$BC27_SOLAR/readiness.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-validate --staged "$BC27_SOLAR/reviewed-stage.json" \
  --task-ids solar_2 solar_M_3 --count 2 --output "$BC27_SOLAR/native-validated.private.json"
printf '[{"source_ids":["solar_2","solar_M_3"]}]\n' > "$BC27_SOLAR/pair-candidate.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-pairs --staged "$BC27_SOLAR/reviewed-stage.json" \
  --candidates "$BC27_SOLAR/pair-candidate.json" --count 1 \
  --output "$BC27_SOLAR/pair-validated.private.json"
SH
bash -n "$BC27_SOLAR/renew.sh"
)
```

Separately submit CPU renewal, then inspect its reports:

```bash
sbatch --partition="$BC27_PARTITION" --nodes=1 --ntasks=1 --cpus-per-task=2 \
  --mem=8G --time=00:30:00 --output="$BC27_SOLAR/renew.out" \
  --error="$BC27_SOLAR/renew.err" "$BC27_SOLAR/renew.sh"
```

Require both individual positives, identical resets, source integrity, missing
and semantic-corruption controls, current executor binding, and inspect the joint
pair report. A failed pair is retained; it does not become a cooperative campaign.
The scorer is reviewed `bc_livesql_native_v1`, **not full upstream scorer parity**.
No arbitrary upstream Python, hidden material in prompts or relaxed semantics.

## 9. Only after user review: prepare two individual native episodes

This is a feasibility gate, not a model-size comparison to historical 4B solar
runs with different interfaces. A matched new 4B native control is optional and
requires separate authorization. Normal document discovery is preserved.

```bash
"$BC_PYTHON" scripts/bc.py validation-config --profile qwen35-27b-sql-competence \
  --data-manifest "$BC27_SOLAR/native-validated.private.json" --output "$BC27_SOLAR/config.json"
"$BC_PYTHON" scripts/bc.py manifest --config "$BC27_SOLAR/config.json" \
  --model-lock "$BC27_LOCK" --output "$BC27_SOLAR/manifest.json"
bash experiments/submit_pilot.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_SOLAR/manifest.json" --model-lock "$BC27_LOCK" --concurrency 1 --dry-run
```

After reviewing exactly two **individual single/clean** solar episodes and fresh
validation, the separate user submission is:

```bash
bash experiments/submit_pilot.sh --cluster "$BC27_CLUSTER" \
  --manifest "$BC27_SOLAR/manifest.json" --model-lock "$BC27_LOCK" --concurrency 1
```

Aggregate/audit the native output by its returned experiment ID just as above.
No 5–10-task expansion is submitted: additional supported database groups are a
future proposal requiring validation and user review, not selection by comparative
success. SILO stays paused. One pair/two repeated solar tasks provide no cross-domain
claim.

## Readiness boundaries

- Probe competence: unexecuted 27B; reported 4B 1/4.
- Native references: historical passes; renewal under current executor pending.
- Native model competence: no 27B result; historical 4B solar failures were unmatched.
- Research gate A: competent clean worker/interface, still pending.
- Research gate B: meaningful recovery-aware decomposition and fair methods, still
  pending even if A passes. The legacy catalogue is not a general optimizer.
  Preserve JIT and the additive-cost standby-deferral limitation; the historical
  256-work planner-search gap is already reconciled.

## Local validation outcome

The stable-source suite ran 194 tests: 193 passed, one existing opt-in legacy
skip (68.327 seconds). Nine shell files, 46 documentation shell blocks/four
embedded scripts, compileall, dependency-free CLI help and diff whitespace checks
passed. See [VALIDATION.md](VALIDATION.md) for the intermediate source-change
failure and successful rerun. These are CPU/mock software results only.
