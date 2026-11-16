# Prospective MATH block 3: planner-only launch preparation

The eight original block-3 IDs are source-reviewed within supplied-card coverage. The cumulative reviewed cohort is `0436a79e60ab4c9408692d5c1eca399a947014bb1309b1e2cf71e789d32be71f`. Membership, generic scientific procedure and block-1 records are unchanged. No workflow admission is implied.

The versioned block-3 binding uses the same Qwen loader, CheckedTransport, journal, registry, source verifier, response validator and fixed-block planner pipeline. A distinct `prospective-math-block3-planner-v1` key preserves block-1 and block-2 no-retry records. Block-1 files are not refactored because their hashes bind existing approved evidence. The small block-specific launcher is adapted from the accepted second-block launcher; no inference backend or approval framework is added.

## Scope

- Exactly the eight frozen block-3 sources; no replacements, retries or corrections.
- Qwen/Qwen3.5-27B, revision fc05daec18b0a78c049392ed2e771dde82bdf654; unchanged non-thinking deterministic BF16/SDPA settings and prompt.
- Eight calls, 3,072 output tokens per call, 13,312 input cap, 16,384 context, 131,072 total tokens.
- HPCAIq, one >=80GB GPU, four CPUs, 128GB RAM, one hour.
- Accounted overlap remains capped at four user GPUs; unknown accounting blocks dispatch.
- Workers, profiling, optimisation and recovery are disabled. Malformed/truncated but reliably accounted responses do not abandon subsequent questions; uncertainty/integrity/resource failures stop dispatch.

## Validation

35 focused tests passed in 1.662 seconds across block-3, existing block-2 and prospective pipeline tests. All 28 shell files passed checks. Tests use fakes and synthetic sources only; no real tokenizer or model was loaded locally. Evidence: outputs/prospective-math-block3-planner-binding/. The scoped instruction calls for focused checks, so no broad solver regression was repeated.

## Transfer

In the development checkout, review the staged file list before committing. These commands are provided for the user; no staging, commit or push has been performed by the assistant.

```bash
git add -- \
  configs/phase2/prospective_math_block3_source_review_v1.json \
  src/bc_phase2/prospective_block3_launch.py \
  scripts/launch_prospective_math_block3.py \
  experiments/run_prospective_math_block3.sbatch \
  tests/test_prospective_block3_launch.py \
  docs/PROSPECTIVE_MATH_BLOCK3_LAUNCH.md
git diff --cached --stat
git commit -m "Prepare frozen prospective MATH block three planner"
git push origin HEAD
```

## Preparation command

After transfer, on Jupyter:

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_BLOCK3="$(mktemp -d "$BC_STORAGE/diagnostics/prospective-math-block3-planner.XXXXXX")"
printf 'Preparation directory: %s\n' "$BC_BLOCK3"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_BLOCK3'])
old = Path(os.environ['BC_STORAGE']) / 'diagnostics/prospective-math-planner.ZCwnbP/cluster.json'
config = json.loads(old.read_text())
config.update(partition='HPCAIq', time='01:00:00', memory_gb=128,
              python=os.environ['BC_PYTHON'], output_root=str(root / 'outputs'))
with (root / 'cluster.json').open('x') as handle:
    json.dump(config, handle, indent=2)
PY
scontrol show partition HPCAIq -o > "$BC_BLOCK3/partition.txt"
"$BC_PYTHON" -I -B scripts/launch_prospective_math_block3.py prepare \
  --public "$BC_STORAGE/diagnostics/prospective-math.2VQEVU/math.public.json" \
  --inventory-report "$BC_STORAGE/diagnostics/d1-local-verify.1pghSs/local-verification.json" \
  --cluster "$BC_BLOCK3/cluster.json" \
  --partition-record "$BC_BLOCK3/partition.txt" \
  --output "$BC_BLOCK3/bound"
squeue --array -u "$USER" -o "%.22i %.12P %.20j %.2t %.10M %R"
printf '\nSaved preparation: %s\n' "$BC_BLOCK3"
)
```

This loads only the authorised local tokenizer and metadata, with a 300-second CPU preparation deadline. Share the printed scope summary. Exact source-transmission/GPU approval follows only after that binding; the block-1 approvals do not cover these new calls. No new scientific decision is needed before this preparation.

After exact approval, the existing CLI sequence is `approve --manifest ... --approval ... --output ...`, then `submit --release ... --dry-run --output ...`, then `submit --release ... --output ...`, using scripts/launch_prospective_math_block3.py. No approval has been recorded for block 3 and no submission has occurred. Do not edit generated manifests.
