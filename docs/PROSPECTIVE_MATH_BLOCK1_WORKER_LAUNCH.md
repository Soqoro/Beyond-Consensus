# First prospective MATH composite: staged launch packet

Status: contracts and neutral frozen; local-tokenizer CPU qualification and exact live approval pending. No worker/model execution or submission performed during preparation.

Exactly NEUTRAL versus JOINT, n=4, K=2, mean-first, one clean execution and four independent owner repairs per distinct organisation. Fixed A/C; effective search is B ownership only. Three original MATH block slots remain in the denominator; this recipe addresses only slot 1.

## Frozen workload and resources

Four whole sources: `test/algebra/2277.json`, `test/counting_and_probability/870.json`, `test/counting_and_probability/761.json`, `test/precalculus/24313.json`.
Six tasks; two internal dependency edges; four authoritative final outputs. AI-assisted merges are recorded separately from raw model plans. All eight first-block records have explicit dispositions; the other four are admitted but unselected and cannot be recycled.

Neutral owners, fixed before prices:

| Owner | Tasks |
|---|---|
| o0 | boxes: complete answer |
| o1 | trigonometric simplification; piecewise inverse of zero |
| o2 | piecewise inverse of six and required sum, consuming o1's inverse artifact |
| o3 | circle sample-space model; crossing-event probability, consuming its sample-space artifact |

Wave: `93bf006bec62b8eb166930c2214e602b95a0f5c8f532bbd0c7f7f374843a1601`.
Contract packet: `d043a7ba0a859edc30aeac4641b0f06095a6a4eb2a549a3ada422a0ed9685d92`.

- 6 fresh profile calls; zero reused historical prices.
- At most 32 evaluation calls under verified component isolation; **38 total calls**.
- 16,384 context; 13,312 input cap; 3,072 generated tokens per call; **622,592 total tokens**.
- One >=80 GB GPU on HPCAIq, 4 CPUs, 128 GB host memory, **4 hours**.
- Existing solver allowance: 30 seconds, one thread, seed 0; no retry loop.
- At most ten evaluation sessions; exact identical organisations may share the existing physical sweep under the unchanged identity rule.
- Earlier planning overhead: eight calls / 11,491 tokens, retained separately and charged physically once, not counted again as new calls.
- Complete wrong answers remain outcomes. Incomplete profile coverage blocks this pair; no substitute bundle. Unknown dispatch/accounting halts the recipe. No automatic retries.

## Transfer only these new files

Run in the development checkout; these are instructions, not actions already performed:

```bash
git add -- \
  configs/phase2/prospective_math_block1_worker_v1.json \
  src/bc_phase2/prospective_worker_launch.py \
  scripts/launch_prospective_worker.py \
  experiments/run_prospective_worker.sbatch \
  tests/test_prospective_worker_launch.py \
  docs/PROSPECTIVE_MATH_BLOCK1_WORKER_LAUNCH.md
git diff --cached --stat
git commit -m "Prepare reviewed prospective MATH block one recovery pair"
git push origin HEAD
```

## Jupyter CPU preparation (no GPU submission)

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_PAIR="$(mktemp -d "$BC_STORAGE/diagnostics/prospective-math-worker.XXXXXX")"
export BC_PLANNER_RUN="$BC_STORAGE/diagnostics/prospective-math-planner.ZCwnbP/outputs/composite-97d489086be8b8e807b6b7924f3cb3f6c155e33d499e40402d480de972ae54e7"
printf 'Preparation directory: %s\n' "$BC_PAIR"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_PAIR'])
parent = json.loads((Path(os.environ['BC_PLANNER_RUN']) / 'manifest.json').read_text())
config = dict(parent['release']['manifest']['scope']['cluster'])
config.update(partition='HPCAIq', time='04:00:00', memory_gb=128,
              python=os.environ['BC_PYTHON'], output_root=str(root / 'outputs'))
with (root / 'cluster.json').open('x') as handle:
    json.dump(config, handle, indent=2)
PY
scontrol show partition HPCAIq -o > "$BC_PAIR/partition.txt"
"$BC_PYTHON" -I -B scripts/launch_prospective_worker.py prepare \
  --planner-run "$BC_PLANNER_RUN" \
  --cluster "$BC_PAIR/cluster.json" \
  --partition-record "$BC_PAIR/partition.txt" \
  --output "$BC_PAIR/bound"
squeue --array -u "$USER" -o "%.22i %.12P %.20j %.2t %.10M %R"
printf 'Saved preparation: %s\n' "$BC_PAIR"
)
```

This has a 300-second CPU-preparation deadline. It verifies the original planner result hash, all source/plan contracts, parent model binding, three distinct grammar schemas with both EOS tokens and adversarial controls, and full rendered root requests. Descendant requests use explicitly synthetic parents for this check; actual generated-parent fit is checked at every dispatch. It does not claim worst-case memory/context qualification or mathematical correctness.

## Exact live approval boundary

Share `bound/summary.json` after CPU preparation. Approval must cover its new scope digest, these four source statements, the recorded reviewer merges and the entire 38-call profile-to-recovery recipe. The previous eight-call planner approval does not cover workers. No extra policy decisions or new framework are needed.

After that approval, copy `bound/approval.pending.json` to a separate `approval.json`, setting `decision=approved`, reviewer/time and all three flags (`source_worker_transmission`, `contract_accepted`, `gpu_recipe_authorized`) to true. Keep the pending original. The exact commands, using the prepared BC_PAIR path, are:

```bash
"$BC_PYTHON" -I -B scripts/launch_prospective_worker.py approve \
  --manifest "$BC_PAIR/bound/MANIFEST.disabled.json" \
  --approval "$BC_PAIR/approval.json" --output "$BC_PAIR/approved-release.json"
"$BC_PYTHON" -I -B scripts/launch_prospective_worker.py submit \
  --release "$BC_PAIR/approved-release.json" --dry-run \
  --output "$BC_PAIR/submission-dry-run.json"
"$BC_PYTHON" -I -B scripts/launch_prospective_worker.py submit \
  --release "$BC_PAIR/approved-release.json" --output "$BC_PAIR/submission.json"
```

The existing per-user registry, accounted overlap ceiling of four total GPUs, one-GPU allocation checks, frozen snapshot and no-retry records apply. No manual sbatch bypass.
