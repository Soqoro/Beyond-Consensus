# Prospective MATH block 2: planner-only launch preparation

The eight original block-2 IDs are source-reviewed within supplied-card coverage. The cumulative reviewed cohort is `439a352f650efcf04e09fcf20fcaf4e467beeefefa2e6b5020fe4238ac43e378`. Membership, generic scientific procedure and block-1 records are unchanged. No workflow admission is implied.

The versioned block-2 binding uses the same Qwen loader, CheckedTransport, journal, registry, source verifier, response validator and fixed-block planner pipeline. A distinct `prospective-math-block2-planner-v1` key preserves block-1 no-retry records. Block-1 files are not refactored because their hashes bind existing approved evidence. The small block-specific launcher is adapted from the accepted first-block launcher; no inference backend or approval framework is added.

## Scope

- Exactly the eight frozen block-2 sources; no replacements, retries or corrections.
- Qwen/Qwen3.5-27B, revision fc05daec18b0a78c049392ed2e771dde82bdf654; unchanged non-thinking deterministic BF16/SDPA settings and prompt.
- Eight calls, 3,072 output tokens per call, 13,312 input cap, 16,384 context, 131,072 total tokens.
- HPCAIq, one >=80GB GPU, four CPUs, 128GB RAM, one hour.
- Accounted overlap remains capped at four user GPUs; unknown accounting blocks dispatch.
- Workers, profiling, optimisation and recovery are disabled. Malformed/truncated but reliably accounted responses do not abandon subsequent questions; uncertainty/integrity/resource failures stop dispatch.

## Validation

32 focused tests passed in 1.522 seconds across block-2, existing block-1 and prospective pipeline tests. The additional slot-2 routing test passed with all ten block-2 tests in 0.071 seconds. All 26 shell files passed checks; isolated CLI help runs without GPU imports. Tests use fakes and synthetic sources only; no real tokenizer or model was loaded locally. Evidence: outputs/prospective-math-block2-planner-binding/.

## Preparation command

After transfer, on Jupyter:

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_BLOCK2="$(mktemp -d "$BC_STORAGE/diagnostics/prospective-math-block2-planner.XXXXXX")"
printf 'Preparation directory: %s\n' "$BC_BLOCK2"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_BLOCK2'])
old = Path(os.environ['BC_STORAGE']) / 'diagnostics/prospective-math-planner.ZCwnbP/cluster.json'
config = json.loads(old.read_text())
config.update(partition='HPCAIq', time='01:00:00', memory_gb=128,
              python=os.environ['BC_PYTHON'], output_root=str(root / 'outputs'))
with (root / 'cluster.json').open('x') as handle:
    json.dump(config, handle, indent=2)
PY
scontrol show partition HPCAIq -o > "$BC_BLOCK2/partition.txt"
"$BC_PYTHON" -I -B scripts/launch_prospective_math_block2.py prepare \
  --public "$BC_STORAGE/diagnostics/prospective-math.2VQEVU/math.public.json" \
  --inventory-report "$BC_STORAGE/diagnostics/d1-local-verify.1pghSs/local-verification.json" \
  --cluster "$BC_BLOCK2/cluster.json" \
  --partition-record "$BC_BLOCK2/partition.txt" \
  --output "$BC_BLOCK2/bound"
squeue --array -u "$USER" -o "%.22i %.12P %.20j %.2t %.10M %R"
printf '\nSaved preparation: %s\n' "$BC_BLOCK2"
)
```

This loads only the authorised local tokenizer and metadata, with a 300-second CPU preparation deadline. Share the printed scope summary. Exact source-transmission/GPU approval follows only after that binding; the block-1 approvals do not cover these new calls. No new scientific decision is needed before this preparation.

After exact approval, the existing CLI sequence is `approve --manifest ... --approval ... --output ...`, then `submit --release ... --dry-run --output ...`, then `submit --release ... --output ...`, using scripts/launch_prospective_math_block2.py. No approval has been recorded for block 2 and no submission has occurred. Do not edit generated manifests.
