# Frozen synthetic aggregation diagnostic

**2026-09-24 status:** completed at 1/2; join duplication confirmed in the
failed synthetic artifact. See [findings](SQLITE_AGGREGATION_FINDINGS_2026-09-24.md)
and the [full review](PROGRESS_REPORT_2026-09-24.md). Further runs are paused;
the commands below are the preserved procedure, not a request to repeat it.

## Question and limits

Can the frozen 27B model produce correct totals when independent detail tables
share a parent key? This is a synthetic competence diagnostic, not a native
benchmark, a matched comparison with solar, or a policy/recovery experiment.
There are two tasks on one database/source group:

1. Payment totals for every team, including teams without payments.
2. The same totals plus total and critical notice counts per team.

The trusted fixture has unequal detail counts, repeated equal payment amounts,
a team with payments but no notices, and a team with notices but no payments.
Expected rows are computed independently in Python, only during terminal scoring.
Workers receive public schemas, relationships and output requirements, no solution
query or expected values. The shared tool interface and explicit artifact
submission contract are unchanged. Query inspection and retries remain charged.

Config: `configs/qwen27b-aggregation.json`. Exactly two single/clean episodes,
seed 0, one shard, Protocol A, generic feedback, SQL-text interface, 12 actions,
two malformed retries, 100000 work per episode, thinking enabled, 2048 output
including reasoning, 8192 context. This intentionally uses the existing bounded
synthetic context/action settings, not the native 16K/24-action condition.
No document retrieval is needed. The primary action bound is 24 across the suite;
200000 is a cap, not predicted consumption. Default JSON-tree/native profiles
are unchanged. No native references, calibration, preparation, attacks or model
planning are used. The completed model result is linked above.

Scripted CPU controls test correct results, duplicated sums from an extra detail
join, wrong aliases and missing final submission. They are harness tests only.
The fixture hash includes schema and all data. An implicit mock solver is blocked;
CPU tests inject their scripted worker explicitly. Do not interpret synthetic
passes as proof that the native failure was caused by join multiplicity.

## Ordered browser-terminal workflow after push/pull

Use the existing Python environment with SQLGlot 27.28.1 and XGrammar 0.1.32.
No model download is required. Run each stage only after the previous job passes.
The submission wrappers preserve the shared registry and one-campaign rule.

### 1. Freeze source and qualify on CPU

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_AGG_CLUSTER="$PWD/configs/cluster.qwen27b-na100.local.json"
export BC_AGG_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json"
export BC_AGG_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/sqlite-aggregation.XXXXXX")"
(
set -euo pipefail
umask 077
test -z "$(git status --porcelain)"
test -f "$BC_AGG_CLUSTER"
test -f "$BC_AGG_LOCK"
mkdir "$BC_AGG_DIR/source"
git archive HEAD | tar -xf - -C "$BC_AGG_DIR/source"
git rev-parse HEAD > "$BC_AGG_DIR/source-commit.txt"
chmod -R a-w "$BC_AGG_DIR/source"
cat > "$BC_AGG_DIR/qualify.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
cd "$BC_AGG_DIR/source"
"$BC_PYTHON" -m unittest tests.test_sqlite_aggregation -v
"$BC_PYTHON" scripts/check_sql_frontend.py --output "$BC_AGG_DIR/compiler.json"
"$BC_PYTHON" -I scripts/check_action_constraints.py \
  --model-lock "$BC_AGG_LOCK" --context-limit 8192 \
  --action-constraint sqlite-sql-text-v1 --frontend-report "$BC_AGG_DIR/compiler.json" \
  --output "$BC_AGG_DIR/grammar.json" --qualified-lock "$BC_AGG_DIR/model-lock.json"
SH
bash -n "$BC_AGG_DIR/qualify.sh"
sbatch --partition=NA100q --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=00:30:00 --output="$BC_AGG_DIR/cpu.out" \
  --error="$BC_AGG_DIR/cpu.err" "$BC_AGG_DIR/qualify.sh"
printf 'Directory: %s\n' "$BC_AGG_DIR"
)
```

### 2. After CPU qualification completes, manifest and GPU preflight

```bash
(
set -euo pipefail
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_AGG_DIR'])
for name in ('compiler.json', 'grammar.json'):
    if json.loads((root/name).read_text())['status'] != 'passed':
        raise SystemExit('Qualification failed: ' + name)
PY
"$BC_PYTHON" scripts/bc.py manifest --config configs/qwen27b-aggregation.json \
  --model-lock "$BC_AGG_DIR/model-lock.json" --output "$BC_AGG_DIR/manifest.json"
"$BC_PYTHON" scripts/bc.py diagnostic-costs --manifest "$BC_AGG_DIR/manifest.json" \
  --output "$BC_AGG_DIR/planned-costs.json"
bash experiments/submit_gpu_preflight.sh --cluster "$BC_AGG_CLUSTER" \
  --manifest "$BC_AGG_DIR/manifest.json" --model-lock "$BC_AGG_DIR/model-lock.json" --dry-run
)
```

Review the dry-run partition and one-GPU request, then submit the same preflight
command without `--dry-run`. Read its `preflight.json` and stderr after completion;
require `command_failed=false` and `sql_frontend_probe.passed=true`.

### 3. After preflight passes, submit the two-task diagnostic

```bash
bash experiments/submit_pilot.sh --cluster "$BC_AGG_CLUSTER" \
  --manifest "$BC_AGG_DIR/manifest.json" --model-lock "$BC_AGG_DIR/model-lock.json" \
  --concurrency 1 --dry-run
```

Review, then remove `--dry-run` to submit. Preserve the returned output path.
No other campaign should be active. After completion set `BC_AGG_OUTPUT` to that
exact path and run:

```bash
(
set -euo pipefail
umask 077
: "${BC_AGG_OUTPUT:?Set to the submitted diagnostic output directory}"
export BC_AGG_RESULTS="$(mktemp -d "$PWD/aggregation-results.XXXXXX")"
printf '/%s/\n' "$(basename "$BC_AGG_RESULTS")" >> .git/info/exclude
"$BC_PYTHON" scripts/bc.py aggregate --output "$BC_AGG_OUTPUT" > "$BC_AGG_RESULTS/aggregate.json"
"$BC_PYTHON" scripts/bc.py competence-audit --run "$BC_AGG_OUTPUT" --output "$BC_AGG_RESULTS/audit.json"
"$BC_PYTHON" scripts/bc.py diagnostic-costs --run "$BC_AGG_OUTPUT" --output "$BC_AGG_RESULTS/costs.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_AGG_RESULTS'])
report = {name: json.loads((root/(name+'.json')).read_text()) for name in ('aggregate','audit','costs')}
with (root/'results.private.json').open('x') as f:
    json.dump(report, f, indent=2)
print('Upload:', root/'results.private.json')
PY
)
```

This new local Git-excluded results folder is accessible through the repository
GUI. Keep all outcomes, including failures. Stop after this diagnostic for review;
no automatic expansion, native rerun or policy campaign is enabled.
