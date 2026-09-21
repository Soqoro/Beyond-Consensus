# Two native solar tasks: 24-action feasibility condition

Prepared 2026-09-21. User-authorized implementation only; no new GPU jobs run.

## Evidence motivating this condition

The user supplied the 16K preflight (job 1079697): A100-SXM4-80GB, one GPU,
14336 input tokens plus 89 generated tokens, completed JSON action, SQLite OK,
peak reserved 62295900160 bytes. This tests the reached cache length (14424),
not a full 2048-token response at maximum input. CPU qualification passed
10 positive/four negative controls for context 16384.

Native run `64b9dbbf253cfec70c4c12fe4ce1efa5fcf297e8044ca91caa1549931bfd699e`
completed 0/2, without context-limit failures. Both implementation operations
ended `action_limit` at 12 calls. `solar_2` spent 42654 work on source/schema/
catalogue and nine document reads, creating no artifact. `solar_M_3` spent 70469:
nine reads, one capped/malformed response, then two successful SQL executions
creating view artifacts. Neither view was explicitly selected. Invalidation
marked both invalid and restored w0 to its initial context. Only that initial
snapshot remains: the later action text is unavailable in the final checkpoint.
Creation/executor success does not establish semantic correctness. The 0/2 and
113123 total work remain unchanged; the earlier 8K failures retain 62465 work.
These are two tasks from one database, not independent cross-domain evidence.

## Change and limitations

`qwen35-27b-native-context16k-actions24` changes the maximum actions from 12 to 24.
All other resolved settings match the preceding native16k profile apart from
name/profile labels: same 27B revision, BF16, deterministic decoding, thinking,
16384 total context, 2048 output, 100000 total work per task, malformed retries,
two individual single/clean solar tasks, seed 0 and one shard. No new retrieval,
forced final action, automatic artifact selection, history truncation or scoring
change. All extra model/tool/re-prefill work remains charged. The work/context
cap can bind before 24 actions; this is a feasibility condition, not a promise
of enough budget or a recovery-policy comparison. No automatic further increase.

A private `context_archives` field preserves a deep diagnostic copy before
context reset/restoration. It is separate from `snapshots`, never read by the
worker or recovery selection, and never supplied as model history. Existing
checkpoints without archives still load. No historical missing text is invented.
`competence-audit` reports sanitized archived action types, operation counts and
read metadata separately from current contexts. Copies may overlap; their action
counts must not be summed. No private body, SQL, literal or raw model response
is exported. Runtime private checkpoints retain the actual history. Ordinary
provenance, restoration, budgets and evaluation remain unchanged.

## Browser workflow after review, commit/push and pull

Keep the environment unchanged. The model/decoder qualification implementation
and context have not changed in this patch, so the existing 16K qualified lock
can be reused if the submission guard validates it. An unrelated package/source
change that invalidates the key requires fresh CPU qualification, never bypass.
Use a new manifest/output identity; never resume the failed 12-action run.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC27_CONTEXT="$BC_STORAGE/diagnostics/native-context16k.nwUsv4"
export BC27_NA_CLUSTER="$PWD/configs/cluster.qwen27b-na100.local.json"
export BC27_ACTIONS="$(mktemp -d "$BC_STORAGE/diagnostics/native-actions24.XXXXXX")"
```

Resolve the already validated data path from the previous config. Do not search
for or regenerate reference material. Create the new condition and planned costs:

```bash
(
set -euo pipefail
test -z "$(git status --porcelain)"
BC27_DATA="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["data_manifest"])' "$BC27_CONTEXT/config.json")"
test -f "$BC27_DATA"
"$BC_PYTHON" scripts/bc.py validation-config \
  --profile qwen35-27b-native-context16k-actions24 \
  --data-manifest "$BC27_DATA" --output "$BC27_ACTIONS/config.json"
"$BC_PYTHON" scripts/bc.py manifest --config "$BC27_ACTIONS/config.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json" \
  --output "$BC27_ACTIONS/manifest.json"
"$BC_PYTHON" scripts/bc.py diagnostic-costs --manifest "$BC27_ACTIONS/manifest.json" \
  --output "$BC27_ACTIONS/planned-costs.json"
bash experiments/submit_gpu_preflight.sh --cluster "$BC27_NA_CLUSTER" \
  --manifest "$BC27_ACTIONS/manifest.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json" --dry-run
)
```

Review two planned episodes, one GPU, NA100q and the new output ID. Then manually
submit a preflight for the new frozen source/manifest:

```bash
bash experiments/submit_gpu_preflight.sh --cluster "$BC27_NA_CLUSTER" \
  --manifest "$BC27_ACTIONS/manifest.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json"
```

After it finishes, inspect the new preflight report; do not run collection early:

```bash
export BC27_ACTIONS_ID="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' "$BC27_ACTIONS/manifest.json")"
export BC27_ACTIONS_OUTPUT="$("$BC_PYTHON" -c 'import json,sys; from pathlib import Path; print(Path(json.load(open(sys.argv[1]))["output_root"])/sys.argv[2])' "$BC27_NA_CLUSTER" "$BC27_ACTIONS_ID")"
"$BC_PYTHON" -m json.tool "$BC27_ACTIONS_OUTPUT-preflight/preflight.json"
tail -n 40 "$BC27_ACTIONS_OUTPUT-preflight"/logs/*.err
```

Only after preflight review, separately dry-run and manually submit the two tasks:

```bash
bash experiments/submit_pilot.sh --cluster "$BC27_NA_CLUSTER" \
  --manifest "$BC27_ACTIONS/manifest.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json" --concurrency 1 --dry-run
```

Remove `--dry-run` only after reviewing the submission. Shared registry, immutable
snapshots and one active campaign remain enforced. No pair/attack/policy campaign.

After completion use fresh report paths. Export only these sanitized reports:

```bash
export BC27_ACTION_REPORT="$(mktemp -d "$BC27_ACTIONS/results.XXXXXX")"
(
set -euo pipefail
"$BC_PYTHON" scripts/bc.py aggregate --output "$BC27_ACTIONS_OUTPUT" \
  > "$BC27_ACTION_REPORT/aggregate.json"
"$BC_PYTHON" scripts/bc.py competence-audit --run "$BC27_ACTIONS_OUTPUT" \
  --output "$BC27_ACTION_REPORT/audit.json"
"$BC_PYTHON" scripts/bc.py diagnostic-costs --run "$BC27_ACTIONS_OUTPUT" \
  --output "$BC27_ACTION_REPORT/costs.json"
"$BC_PYTHON" - <<'PY'
import json
import os
import tempfile
from pathlib import Path
root = Path(os.environ['BC27_ACTION_REPORT'])
report = {name: json.loads((root/file).read_text()) for name, file in
          {'aggregate':'aggregate.json', 'competence_audit':'audit.json', 'observed_costs':'costs.json'}.items()}
with tempfile.NamedTemporaryFile(mode='w', prefix='solar-actions24-', suffix='.private.json',
        dir=Path.home()/'Beyond-Consensus', delete=False) as f:
    json.dump(report, f, indent=2)
    f.write('\n')
    print('Upload:', f.name)
PY
)
```
