# Prospective block scopes — no live approval recorded

Exactly NEUTRAL versus JOINT, n=4, K=2, mean-first, fresh clean plus four independent original-snapshot R0 repairs per distinct organisation. No retries, replacements or cross-block refill. Later blocks stay frozen and do not depend on positive savings.

| Independently selectable cohort | Frozen candidate ceiling / blocks | First planning job cap | Subsequent one-pair cap |
|---|---|---|---|
| MATH-500 | 24 / 3 × 8 | ≤8 calls; 131,072 tokens; 1 hour | ≤16 fresh profile +80 evaluation calls; 1,572,864 tokens; 4 hours |
| MedQA four-option | 24 / 3 × 8 | ≤8 calls; 131,072 tokens; 1 hour | Same ceiling; derive tighter calls from reviewed isolated components |
| AIME 2025 | 12 / 2 × 6 | ≤6 calls; 98,304 tokens; 1 hour | Same per-pair ceiling |
| AIME 2026 | 12 / 2 × 6 | ≤6 calls; 98,304 tokens; 1 hour | Same per-pair ceiling |
| GPQA-Diamond qualification only | ≤6 / 1 block | ≤6 calls; 98,304 tokens; 1 hour | At most one pair, same ceiling; six IDs excluded from future primary work |

Each allocation: one ≥80,000,000,000-byte GPU, four CPUs, 128 GB host RAM, concurrency one. The existing shared-registry accounting allows at most four accounted user GPUs; unknown usage still blocks. Proposed HPCAIq placement must be checked on Jupyter before binding. Per call: 13,312 input +3,072 generated tokens, context16,384. Solver:30 seconds,1 thread,seed0. Prices are input-plus-generated tokens. Monetary charges unknown. These are proposed upper bounds, **not spend permission or an inference of current scheduler capacity**.

The two-stage path releases the GPU after planning while contracts are reviewed. At most ten main pairs; GPQA qualification is separate. A one-call/eight-task domain has ≤80 evaluation calls. Up to two existing reviewed implementation modes per component require ≤16 full-component profile calls, including prerequisites. New formats with more operations must update the bound explicitly. Profile failures retain attempted spend and block only their condition; they do not redraw the bundle.

## Source decision recorded — 2026-11-15

1. User authorised local preparation of the existing pinned MATH-500 pool on Jupyter, including exposure/duplicate reconciliation and freezing 24 candidates.
2. User selected the authors' four-option MedQA test pool. No development-pool amendment was granted. Prepare its source binding; download/access approval remains separate.
3. AIME and GPQA acquisition/access are independently pending; neither delays MATH preparation.

No specific GPU approval is requested yet: candidate identities, full rendered request measurements and a block-specific launcher binding are not complete. Approving a historical scope or manually changing its IDs is not the next command.

## Code transfer, if you choose to transfer these changes

Run on the development checkout. These commands stage only this implementation and its public metadata/docs; they are supplied for the user and were not executed. Do not stage outputs, datasets or unrelated modifications.

```bash
git add src/bc_phase2/prospective_sources.py \
  src/bc_phase2/prospective_adapters.py \
  src/bc_phase2/prospective_pipeline.py \
  src/bc_phase2/composite_scaling_runtime.py \
  scripts/prepare_prospective_cohort.py tests/test_prospective_cohort.py \
  configs/phase2/prospective_exposure_v1.json configs/phase2/prospective_policy_v1.json \
  docs/PROSPECTIVE_COHORT_HANDOFF.md docs/PROSPECTIVE_RUN_APPROVAL.md \
  docs/GPQA_QUALIFICATION.md
git diff --cached --stat
git commit -m "Prepare fixed source-disjoint blocks and thin benchmark adapters"
git push origin HEAD
```

## Exact first CPU command — local MATH read authorised

This extracts the pinned public questions; it neither selects by answers nor runs a model. It reads the JSONL through the trusted adapter and emits only id/problem. It does not certify family clearance.

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
BC_PYTHON=/dataset/suaq0001/beyond-consensus/envs/bc-gpu-py312/bin/python
BC_NEW="$(mktemp -d /dataset/suaq0001/beyond-consensus/diagnostics/prospective-math.XXXXXX)"
"$BC_PYTHON" -I -B scripts/prepare_prospective_cohort.py extract-math \
  --source /dataset/suaq0001/beyond-consensus/datasets/math500/6e4ed1a2a79a.xuhury8t/test.jsonl \
  --local-source-read-authorized \
  --output "$BC_NEW/math.public.json"
printf 'Public preparation: %s\n' "$BC_NEW"
)
```

Then `inventory` requires that exact public-file hash and source-specific access receipt; `freeze` requires an inventory-bound exposure/family review. `block-plan` emits the chosen block's disabled planner packet. These commands are executable preparation interfaces, not Slurm launchers:

```text
prepare_prospective_cohort.py inventory --public PUBLIC.json --access-receipt ACCESS.json --output INVENTORY.json
prepare_prospective_cohort.py freeze --inventory INVENTORY.json --exposure configs/phase2/prospective_exposure_v1.json --family-review FAMILY_REVIEW.json --output COHORT.json
prepare_prospective_cohort.py block-plan --cohort COHORT.json --public PUBLIC.json --slot 1 --output BLOCK1_PLANNING.disabled.json
prepare_prospective_cohort.py block --cohort COHORT.json --dispositions BLOCK1_REVIEW.json --slot 1 --output BLOCK1_WAVE.disabled.json
```

No executable live launch is claimed while source, tokenizer/scheduler and launcher bindings remain missing. The next exact live command must name a newly bound block release under the existing registry/approval machinery. Do not submit the old MATH/MedQA campaign to stand in for it.

Authorisation quote: “Authorise local MATH preparation; use MedQA test pool”. This does not authorise a download, model call or GPU submission.
