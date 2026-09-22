# Matched synthetic correction diagnostic — 2026-09-22

## Why this diagnostic

The user-reported feedback-enabled experiment
`ef260dc917102ddb9c1684f008622ce50918616a6f99a0bcb42f20cda193ca20`
passed all four synthetic tasks at **21327** work, with zero rejections and three
model calls per task. All 12 generations completed at EOS; all ledgers reconciled.
That reproduces the previous 27B synthetic total and does not exercise feedback.
The native result remains 0/2 at 171715 work; its offline replay cost is separate.

## Frozen comparison

Two independently authored invalid drafts use the existing synthetic database:

- `sqlite-correction-0`: aggregate draft with a two-argument SUM.
- `sqlite-correction-1`: join draft with an undefined column qualifier.

These are intentionally near-complete public draft inputs, not sampled model
mistakes, native solutions or reference-selected repairs. The tasks are labelled
`bc_sqlite_tool_correction_v1`, `tool_correction`, one shared synthetic source group.
The existing independent Python terminal expectations score the entire required
output. The model may rewrite the draft; no hidden answer or error category is
included in its initial task contract.

Run two conditions with identical source, tasks, model, seeds and limits:

| Config | Feedback |
| --- | --- |
| `configs/qwen27b-sql-correction-generic.json` | Existing generic rejection |
| `configs/qwen27b-sql-correction-categorized.json` | `sqlite-errors-v1` categories/hints |

Each condition has two episodes in one GPU shard. The existing pinned Qwen3.5-27B,
8192 context, thinking, constrained 2048-output cap and seed 0 are retained.
Single/clean Protocol A only; 100000 work, 12 actions and two retries per episode.
Exactly four executions total if both conditions are run once. Run campaigns
sequentially through the shared registry, not in parallel or by batch self-submission.

## Supplied draft and accounting

The first action slot executes the frozen draft through the normal tool handler
and restricted executor. It is recorded as a user-side diagnostic input and a
`diagnostic_seed_action` event, never as an assistant/model generation. No tokens
are fabricated for generating the supplied draft. Its ordinary tool charge and
bounded SQL charge (10 + 30 with these defaults) consume the same episode budget.
Its text and feedback enter every subsequent model input and are charged through
normal full prompt counting. Fixed construction is part of task setup, shared
between conditions, not an online solver.

The initial rejection consumes one of the three permitted rejected attempts
(two retries). At most eleven model action slots remain, and two further rejected
actions terminate the operation. Every model call still reserves its full output
allowance. No free correction call, extra work budget or altered history is added.
An unexpectedly successful seed blocks the diagnostic; it cannot become a success.
Completed resume does not execute the seed again. An interrupted operation follows
the existing conservative retry/accounting rules; duplicate seed attempts are
reported and do not count as a complete matched diagnostic.

Generic/categorized histories before the feedback observation are identical.
The added hint changes subsequent input length, so realized work may differ:
equal total caps are preserved, not equal realized tokens or hardware time.
The model must still read its contract and explicitly submit the artifact ID.
Task identity, source and manifest hashes bind both drafts.

## Audit and interpretation

`bc correction-audit --generic-run RUN --feedback-run RUN --output NEW.json`
performs no model/SQL execution. It checks identical normalized configs (except
labels and feedback), source, tasks, regime, decoder contract and interface hashes,
then validates aggregates/provenance and reconciles ledgers. It reports seed
execution/rejection counts, exact seed hashes, model-only rejections, feedback
exposure, paired terminal success and total work. Missing results stay visible.
Write reports outside both historical runs; paths cannot overwrite existing reports.

The usual competence audit remains available but marks this suite
`paired_correction_review_only`; it cannot grant native eligibility or compare
these two supplied drafts with historical four-task competence scores.
No statistical or recovery conclusion follows from two corrections in one source
group. Both conditions passing would show correction is possible, not a benefit
from categories. A difference is a bounded descriptive observation; no new seeds,
automatic reruns, budgets or native enablement follow.

## Browser-terminal sequence (after review and push)

Use the existing qualified 8192-context lock. The normal qualification/preflight
checks remain authoritative; stop if they reject it. Do not update source or
packages between the two conditions. Preserve the directory variables printed
below across shells.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_CORRECTION_CLUSTER="$PWD/configs/cluster.qwen27b-na100.local.json"
export BC_CORRECTION_LOCK="$BC_STORAGE/diagnostics/sqlite-feedback.JeJ2Ju/qualified-model-lock.json"
export BC_CORRECTION_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/sqlite-correction.XXXXXX")"
(
set -euo pipefail
test -z "$(git status --porcelain)"
test -f "$BC_CORRECTION_LOCK"
test -f "$BC_CORRECTION_CLUSTER"
for BC_CONDITION in generic categorized; do
  "$BC_PYTHON" scripts/bc.py manifest \
    --config "configs/qwen27b-sql-correction-$BC_CONDITION.json" \
    --model-lock "$BC_CORRECTION_LOCK" \
    --output "$BC_CORRECTION_DIR/$BC_CONDITION-manifest.json"
done
)
printf 'Save this directory: %s\n' "$BC_CORRECTION_DIR"
```

Start with `BC_CONDITION=generic`. For each condition, dry-run then manually
submit the one-GPU preflight with `experiments/submit_gpu_preflight.sh`, using
`--cluster "$BC_CORRECTION_CLUSTER"`,
`--manifest "$BC_CORRECTION_DIR/$BC_CONDITION-manifest.json"` and
`--model-lock "$BC_CORRECTION_LOCK"`. Review its completed report. Then dry-run
and manually submit `experiments/submit_pilot.sh` with the same arguments and
`--concurrency 1`. Finish the generic campaign before selecting `categorized`.
Use the actual cluster-config output_root and each manifest experiment_id for
run paths. Do not infer GPU availability from historical preflights.

After both campaigns finish, set `BC_CORRECTION_GENERIC_OUTPUT` and
`BC_CORRECTION_CATEGORIZED_OUTPUT` to their returned output paths, then:

```bash
"$BC_PYTHON" scripts/bc.py correction-audit \
  --generic-run "$BC_CORRECTION_GENERIC_OUTPUT" \
  --feedback-run "$BC_CORRECTION_CATEGORIZED_OUTPUT" \
  --output "$BC_CORRECTION_DIR/comparison.json"
```

No job has been submitted by this implementation. GPU results remain pending.
