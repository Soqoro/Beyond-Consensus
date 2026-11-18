# First two-regime MATH comparison

The first cell uses four logical owners, capacity two, at least two new whole questions and preferably six tasks. The eight reserved source IDs in rank order are in `configs/phase2/two_regime_slots_v1.json`. The first planner request transmits only `test/precalculus/43.json`. MedQA has its own first cell, beginning at `test/row/846`. Each candidate receives at most one call. A family conflict or missing diagram occupies its original rank.

## Transfer and prepare

On the development checkout, the following commands transfer only the implementation and launch packet. Run them yourself when ready to publish. The Slurm snapshot builder requires a clean, committed Jupyter checkout.

```bash
files=(configs/phase2/two_regime_slots_v1.json experiments/run_two_regime.sbatch
       scripts/two_regime.py src/bc_phase2/two_regime.py src/bc_phase2/two_regime_launch.py
       src/bc_phase2/two_regime_results.py tests/test_two_regime.py docs/TWO_REGIME_FIRST_PAIR.md)
git add -- "${files[@]}"
git commit --only -m "Run bounded two-regime comparisons from reviewed source prefixes" -- "${files[@]}"
git push origin HEAD:main
```

On Jupyter, run this CPU preparation. It writes the disabled manifest, measured request size, pending approval template and reviewer card. The previous successful MATH planner receipt supplies the pinned public file, model, tokenizer and scheduler settings.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORE/envs/bc-gpu-py312/bin/python"
export BC_CELL=math500-n4-extra
export BC_PARENT="$BC_STORE/diagnostics/prospective-math-block3-planner.ZeXgsA/outputs/composite-f85c5e2b667e77b5ed5e3520d0794cebe51876540f206effcf81139d2ae1a0e4"
export BC_CAMPAIGN="$(mktemp -d "$BC_STORE/diagnostics/two-regime-math.XXXXXX")"
export BC_STEP="$BC_CAMPAIGN/plan-1"
"$BC_PYTHON" -I -B scripts/two_regime.py prepare \
  --cell "$BC_CELL" --parent "$BC_PARENT" --output "$BC_STEP" &&
cat "$BC_STEP/preparation.json" "$BC_STEP/source-review.json"
```

The first live decision covers statement transmission to the pinned local Qwen3.5-27B, revision `fc05daec18b0a78c049392ed2e771dde82bdf654`, and one planner call on HPCAIq. One GPU with at least 80,000,000,000 bytes of VRAM, four CPUs, 128 GB host RAM and one hour. Maximum 13,312 input and 3,072 generated tokens, 16,384 total. The renderer measures the actual input. Local monetary charges are unverified. Supply the preparation and source review for the decision. The family-review record binds to the card hash and the approval binds to the manifest digest.

## Dispatch an approved step

After affirmative review, save the completed template as `$BC_STEP/approval.json`, with reviewer, time, scope consent and source-review decision. These commands work for each planner or worker step with its corresponding approved manifest.

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
"$BC_PYTHON" -I -B scripts/two_regime.py approve \
  --manifest "$BC_STEP/manifest.disabled.json" --approval "$BC_STEP/approval.json" \
  --output "$BC_STEP/release.json"
"$BC_PYTHON" -I -B scripts/two_regime.py submit --release "$BC_STEP/release.json" \
  --dry-run --output "$BC_STEP/dry-run.json"
"$BC_PYTHON" -I -B scripts/two_regime.py submit --release "$BC_STEP/release.json" \
  --output "$BC_STEP/submission.json"
cat "$BC_STEP/submission.json"
)
```

To resume inspection of an existing submission, read the receipt from the same stage directory.

```bash
BC_JOB="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job_id"])' "$BC_STEP/submission.json")"
BC_RUN="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["output"])' "$BC_STEP/submission.json")"
sacct -j "$BC_JOB" --format=JobID,State,ExitCode,Elapsed
```

## Review and execute the first eligible bundle

After each terminal planner receipt, export the statement, raw plan, observed usage and contract-review template.

```bash
"$BC_PYTHON" -I -B scripts/two_regime.py review-plan --run "$BC_RUN" \
  --output "$BC_STEP/contract-review.json"
```

Save the ordered list consisting of `previous_prefix` plus the reviewed `entry_for_review` as `$BC_CAMPAIGN/history.json`. An admitted entry must identify the reviewer, type of review and timestamp, retain both supplied digests, and contain genuine responsibilities, parent task IDs, fields and one terminal obligation. An unresolved, invalid or unsupported entry records that decision and its reason. A source blocked before planning uses just its source ID and bound family review. The next command recomputes the stopping decision from the original planner journals.

```bash
BC_PROGRESS="$(mktemp -d "$BC_CAMPAIGN/progress.XXXXXX")"
"$BC_PYTHON" -I -B scripts/two_regime.py review --cell "$BC_CELL" --parent "$BC_PARENT" \
  --history "$BC_CAMPAIGN/history.json" --output "$BC_PROGRESS/review.json"
cat "$BC_PROGRESS/review.json"
```

For `next_candidate`, set `BC_STEP="$BC_PROGRESS/planner"` and run the preparation command with `--history "$BC_CAMPAIGN/history.json"`. For `bundle_frozen`, complete the single selected-component pass in frozen order. Save `alternatives.json` as a list of records containing source ID, reviewer, rationale and decision. Use `outside_domain` when the review finds no supported alternative. For the first admitted procedure use `admit_procedure`, provenance, affirmative `preserves_responsibilities` and `solution_free`, and a `procedures` object with the complete task-ID-to-instruction mapping. End the pass at that component. The supported variant changes worker instructions with the original direct-parent inputs and output contracts.

```bash
export BC_STEP="$BC_CAMPAIGN/pair"
"$BC_PYTHON" -I -B scripts/two_regime.py prepare --cell "$BC_CELL" --parent "$BC_PARENT" \
  --history "$BC_CAMPAIGN/history.json" --alternatives "$BC_CAMPAIGN/alternatives.json" \
  --output "$BC_STEP" &&
cat "$BC_STEP/preparation.json"
```

This worker manifest covers fresh profiles, mean-first selection, fresh clean runs and every owner repair in one approval. It binds the exact source set, option set and computed call cap. A six-operation target has at most 11 profile calls and 60 evaluation calls before applying the component isolation bound. The allocation ceiling is four hours on one GPU. The accepted solver uses one thread, seed zero and 30 seconds. The existing registry retains uncertain submissions and prevents repeated cell or candidate attempts.

Each terminal comparison writes `execution/cell.json` and `execution/RESULTS.md`. After setting `BC_RUN` from the worker receipt, regenerate the primary grid with the following command. Supply another `--run` for each previously observed pair. Each report has a fresh destination.

```bash
BC_REPORT="$(mktemp -d "$BC_CAMPAIGN/report.XXXXXX")"
"$BC_PYTHON" -I -B scripts/two_regime.py report --run "$BC_RUN" --output "$BC_REPORT/grid"
```

The MATH review accepts a separate JSON object with `kind`, `reviewer` and `artifacts`, keyed by the canonical digest of the source ID and stored terminal JSON string. Values are true, false or null. Pass it with `--math-judgments`. The MedQA reporter accepts the pinned local private evaluator using `--medqa-private` during offline grading.

## Independent MedQA preparation

Use the same Jupyter preparation command with the following variables. Its first one-call decision covers the question and all four original options for row 846.

```bash
export BC_CELL=medqa-n4-extra
export BC_PARENT="$BC_STORE/diagnostics/prospective-medqa-block2-planner.cOxi69/outputs/composite-8ce77d60a8592e0a91171a5f4e2a13da3b16556946d66af383fcff7ff61385c3"
export BC_CAMPAIGN="$(mktemp -d "$BC_STORE/diagnostics/two-regime-medqa.XXXXXX")"
export BC_STEP="$BC_CAMPAIGN/plan-1"
"$BC_PYTHON" -I -B scripts/two_regime.py prepare --cell "$BC_CELL" --parent "$BC_PARENT" --output "$BC_STEP"
```
