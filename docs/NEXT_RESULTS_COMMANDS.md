# Exact commands for the staged next-results preparation

No command here was submitted to Slurm during implementation. Do not overwrite earlier evidence or reset the registry. Use a fresh output directory. The source repository contains unrelated work; the transfer below stages only this change. Review any pre-existing staged files before committing.

## Local checkout: transfer only these changes

```bash
cd /home/gnoriq/repos/Beyond-Consensus
git diff --cached --name-only
git add -- \
  src/bc_phase2/composite_math.py \
  src/bc_phase2/composite_dice_next.py \
  src/bc_phase2/composite_dice_next_launch.py \
  src/bc_phase2/medqa_development.py \
  scripts/composite_dice_next.py \
  scripts/medqa_development.py \
  experiments/run_composite_dice_next.sbatch \
  tests/test_next_results.py \
  docs/DICE_INTERFACE_DELTA.md \
  docs/NEXT_RESULTS_HANDOFF.md \
  docs/NEXT_RESULTS_APPROVAL.md \
  docs/NEXT_RESULTS_COMMANDS.md
git diff --cached --stat
git commit -m "Prepare bounded dice refresh, next MATH wave and MedQA adapter"
git push origin HEAD
```

Do not add `outputs/`, datasets, model files or private receipts. These commands assume the previously accepted shared dependencies are already transferred; they do not stage unrelated untracked infrastructure.

## Jupyter: disabled MATH preparation only

This reads the already-authorised historical statement/profile evidence and local deployment metadata. It does not load a model or submit a job. Preserve this terminal's exported variables.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_NEXT_PARENT="$BC_STORAGE/diagnostics/composite-common-derivation.R4n0cE"
export BC_NEXT="$(mktemp -d "$BC_STORAGE/diagnostics/dice-next-math.XXXXXX")"

(
set -euo pipefail
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
parent = Path(os.environ['BC_NEXT_PARENT'])
out = Path(os.environ['BC_NEXT'])
receipt = json.loads((parent / 'submission.json').read_text())
run = Path(receipt['output'])
snapshot = Path(receipt['snapshot'])
manifest = json.loads((run / 'manifest.json').read_text())
config = dict(manifest['release']['manifest']['scope']['cluster'])
assert config['partition'] == 'HPCAIq'
assert config['time'] == '04:00:00'
assert config['memory_gb'] == 128
config['output_root'] = str(out / 'outputs')
with (out / 'cluster.json').open('x') as f:
    json.dump(config, f, indent=2)
with (out / 'parent-paths.json').open('x') as f:
    json.dump({'run': str(run), 'snapshot': str(snapshot)}, f)
PY

BC_NEXT_RUN="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["run"])' "$BC_NEXT/parent-paths.json")"
BC_NEXT_SNAPSHOT="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["snapshot"])' "$BC_NEXT/parent-paths.json")"

"$BC_PYTHON" -I -B scripts/composite_dice_next.py prepare \
  --parent-run "$BC_NEXT_RUN" \
  --parent-snapshot "$BC_NEXT_SNAPSHOT" \
  --cluster "$BC_NEXT/cluster.json" \
  --output "$BC_NEXT/bound"

scontrol show partition HPCAIq -o > "$BC_NEXT/partition.txt"
sinfo -p HPCAIq -N -o '%N %P %t %G' > "$BC_NEXT/nodes.txt"
squeue --array -u "$USER" -o '%.22i %.12P %.20j %.2t %.10M %R' > "$BC_NEXT/queue.txt"
cat "$BC_NEXT/bound/summary.json"
printf 'Preparation directory: %s\n' "$BC_NEXT"
)
```

If the historical receipt is missing, stop and locate its original receipt; do not guess another snapshot or waive checks. Send the preparation summary for exact approval. If any profile compatibility check fails, preserve the failure and inspect it rather than rebuilding all prices or bypassing the check.

## Only after explicit approval of the prepared scope

Set `BC_APPROVED_SCOPE` to the exact digest approved by the user. This block records that external decision; it is not itself a request or grant of approval.

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
: "${BC_NEXT:?Use the prepared directory above}"
: "${BC_PYTHON:?Use the verified execution Python}"
: "${BC_APPROVED_SCOPE:?Set the exact newly approved digest}"
export BC_APPROVED_SCOPE

"$BC_PYTHON" - <<'PY'
import getpass,json,os
from datetime import datetime, timezone
from pathlib import Path
root=Path(os.environ['BC_NEXT'])
a=json.loads((root/'bound/approval.pending.json').read_text())
assert a['scope_digest']==os.environ['BC_APPROVED_SCOPE']
assert a['decision']=='pending'
a.update(decision='approved',reviewer=getpass.getuser(),
         reviewed_at=datetime.now(timezone.utc).isoformat(),
         source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
with (root/'approval.json').open('x') as f:
    json.dump(a,f,indent=2)
PY

"$BC_PYTHON" -I -B scripts/composite_dice_next.py approve \
  --manifest "$BC_NEXT/bound/MANIFEST.disabled.json" \
  --approval "$BC_NEXT/approval.json" \
  --output "$BC_NEXT/release.json"

"$BC_PYTHON" -I -B scripts/composite_dice_next.py submit \
  --release "$BC_NEXT/release.json" --dry-run \
  --output "$BC_NEXT/submission-dry-run.json"

"$BC_PYTHON" -I -B scripts/composite_dice_next.py submit \
  --release "$BC_NEXT/release.json" \
  --output "$BC_NEXT/submission.json"
)
```

Submission goes through the shared registry and frozen snapshot. A failed/uncertain submission is not permission to rerun this block. Existing receipt files are exclusive writes.

## MedQA: source-dependent offline commands, no launch

After a user-authorised source path and verified provenance JSON exist, intake is:

```bash
"$BC_PYTHON" -I -B scripts/medqa_development.py intake \
  --source "$BC_MEDQA_DEV_FILE" \
  --provenance "$BC_MEDQA_SOURCE_RECEIPT" \
  --output "$BC_MEDQA_NEW_INTAKE"
```

The receipt requires `read_authorized: true`, `dataset: "MedQA-USMLE"`, `language: "English"`, `variant: "four-option"`, `split: "dev"`, and verified `revision`, `artifact`, `sha256`, `terms_reference`, `source_verification`. Do not fill these with guesses. The output includes separate public cohort/requests and evaluator-private labels. Keep the latter out of model views and Git.

After the separately approved twelve-call planning stage and one completed human review:

```bash
"$BC_PYTHON" -I -B scripts/medqa_development.py reviewed-wave \
  --cohort "$BC_MEDQA_COHORT" --plans "$BC_MEDQA_PLANS" \
  --reviews "$BC_MEDQA_REVIEWS" --output "$BC_MEDQA_WORKER_MANIFEST"
```

This freezes actual supported bundles and limits, still disabled. There is no MedQA live launch command yet because its source, rendered requests and reviewed contracts are unavailable. This is the concrete source-dependent remaining binding, not authorisation to improvise a backend or launch the generic maximum.
