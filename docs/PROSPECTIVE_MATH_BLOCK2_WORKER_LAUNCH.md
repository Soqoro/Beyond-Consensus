# Second prospective MATH composite: staged launch packet

Status: contracts and neutral frozen; local-tokenizer CPU qualification and exact live approval pending. No worker/model execution or submission performed during preparation.

Exactly NEUTRAL versus JOINT, n=4, K=2, mean-first, one clean execution and four independent owner repairs per distinct organisation. Fixed A/C; effective search is B ownership only. Three original MATH block slots remain in the denominator; this recipe addresses only slot 2.

## Frozen workload and resources

Five whole sources: `test/counting_and_probability/23957.json`, `test/precalculus/625.json`, `test/algebra/1098.json`, `test/prealgebra/996.json`, `test/geometry/686.json`.
Six tasks; one internal dependency edge; five authoritative final outputs. AI-assisted merges are recorded separately from raw plans. All eight block-2 contracts are admitted; the other three are qualified but unselected and cannot be recycled. Original review proposals remain unchanged.

Neutral ownership is frozen before prices. Its exact mapping is in the contract packet; the nonagon boundary producer and perimeter consumer have different owners (o2 and o3). The other four whole-question tasks occupy o0 and o1, two each. No owner exceeds K=2.

Wave: `353a933d6ed425d38bb64ceeb5a9e5fdad4da3ef89145673e77e7d0e614aba21`.
Contract packet: `1bec809466a5df3e7072ea710f108954fdebd5ddef464a1209feea2047f901a4`.

- 6 fresh profile calls; zero reused historical prices.
- At most 28 evaluation calls under verified component isolation; **34 total calls**.
- 16,384 context; 13,312 input cap; 3,072 generated tokens per call; **557,056 total tokens**.
- One >=80 GB GPU on HPCAIq, 4 CPUs, 128 GB host memory, **4 hours**.
- Existing solver allowance: 30 seconds, one thread, seed 0; no retry loop.
- At most ten evaluation sessions; exact identical organisations may share the existing physical sweep under the unchanged identity rule.
- Earlier planning overhead: eight calls / 11,847 tokens, retained separately and charged physically once, not counted again as new calls.
- Complete wrong answers remain outcomes. Incomplete profile coverage blocks this pair; no substitute bundle. Unknown dispatch/accounting halts the recipe. No automatic retries.

## Transfer only these new files

Run in the development checkout; these are instructions, not actions already performed:

```bash
git add -- \
  configs/phase2/prospective_math_block2_worker_v1.json \
  src/bc_phase2/prospective_block2_worker_launch.py \
  scripts/launch_prospective_block2_worker.py \
  experiments/run_prospective_block2_worker.sbatch \
  tests/test_prospective_block2_worker_launch.py \
  docs/PROSPECTIVE_MATH_BLOCK2_WORKER_LAUNCH.md
git diff --cached --stat
git commit -m "Prepare reviewed prospective MATH block two recovery pair"
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
export BC_PAIR="$(mktemp -d "$BC_STORAGE/diagnostics/prospective-math-block2-worker.XXXXXX")"
export BC_PLANNER_RUN="$BC_STORAGE/diagnostics/prospective-math-block2-planner.H06356/outputs/composite-d7ec0d1c9ae41949b7050ded3b553dc424220a9bc9b357fcc690967b81022e9d"
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
"$BC_PYTHON" -I -B scripts/launch_prospective_block2_worker.py prepare \
  --planner-run "$BC_PLANNER_RUN" \
  --cluster "$BC_PAIR/cluster.json" \
  --partition-record "$BC_PAIR/partition.txt" \
  --output "$BC_PAIR/bound"
squeue --array -u "$USER" -o "%.22i %.12P %.20j %.2t %.10M %R"
printf 'Saved preparation: %s\n' "$BC_PAIR"
)
```

This has a 300-second CPU-preparation deadline. It verifies the original planner result hash, all source/plan contracts, parent model binding, two distinct grammar schemas with both EOS tokens and adversarial controls, and full rendered root requests. Descendant requests use explicitly synthetic parents for this check; actual generated-parent fit is checked at every dispatch. It does not claim worst-case memory/context qualification or mathematical correctness.

## Exact live approval boundary

Share `bound/summary.json` after CPU preparation. Approval must cover its new scope digest, these five source statements, the recorded reviewer merges and the entire 34-call profile-to-recovery recipe. The previous eight-call planner approval does not cover workers. No extra policy decisions or new framework are needed.

After that approval, copy `bound/approval.pending.json` to a separate `approval.json`, setting `decision=approved`, reviewer/time and all three flags (`source_worker_transmission`, `contract_accepted`, `gpu_recipe_authorized`) to true. Keep the pending original. The exact commands, using the prepared BC_PAIR path, are:

```bash
"$BC_PYTHON" -I -B scripts/launch_prospective_block2_worker.py approve \
  --manifest "$BC_PAIR/bound/MANIFEST.disabled.json" \
  --approval "$BC_PAIR/approval.json" --output "$BC_PAIR/approved-release.json"
"$BC_PYTHON" -I -B scripts/launch_prospective_block2_worker.py submit \
  --release "$BC_PAIR/approved-release.json" --dry-run \
  --output "$BC_PAIR/submission-dry-run.json"
"$BC_PYTHON" -I -B scripts/launch_prospective_block2_worker.py submit \
  --release "$BC_PAIR/approved-release.json" --output "$BC_PAIR/submission.json"
```

The existing per-user registry, accounted overlap ceiling of four total GPUs, one-GPU allocation checks, frozen snapshot and no-retry records apply. No manual sbatch bypass.

## Local implementation evidence

39 focused offline tests passed in 3.221 seconds, including the unchanged block-1 launcher tests, block-2 planner tests, source/cohort tests and new worker binding tests. All 27 shell files passed the shell checker. These are CPU/mock observations, not real GPU qualification. The scoped handoff calls for focused tests; the broad solver regression was not repeated.

The original planner result hash is enforced during Jupyter preparation. The uploaded export alone does not independently establish the original file bytes. Full rendered requests and both-EOS grammar controls remain pending on the pinned local tokenizer. No dependency download, model loading, job submission, commit or push was performed here.

The generic procedure and existing block-1 implementation are unchanged. No contract was selected using new profile costs or worker correctness. Broad prior research exposure is acknowledged; this is AI-assisted review, not independent blinded human certification.
