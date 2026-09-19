# Synthetic SQLite tool-compatibility diagnostic

## Decision and limits

Native solar control with 24 actions still produced no required artifacts.
The query worker stopped after three malformed attempts; the view worker spent
all 24 actions reading. The reviewed answers fit 768 tokens. Pause native reruns
and isolate basic construction/submission on smaller synthetic tasks.

| Probe | Public requirement | Terminal check |
| --- | --- | --- |
| Aggregate | Sum and count entries by department, with specified aliases | All groups, values, aliases and order |
| Join | Entry ID, department name and amount using the supplied relationship | All joined rows, aliases and order |
| CASE | Positive/negative/zero classification | All rows, labels, aliases and order |
| View | Named view of ID and amount plus three; submit its artifact ID | Required view exists and returns all required columns/values |

The task text supplies schemas, relationship and requirements directly. There
are no discovery documents, native tasks, reference-selected hints or reference
trees in worker views. The shared SQL instructions, parser, malformed retry
limit, restricted executor, version binding, public monitor and budget accounting
remain in use. Correctness is terminal-only; creation without final submission
fails. No text is repaired or compiled from raw model SQL. Scoring checks results,
not whether an otherwise equivalent solution uses a particular syntactic operator.

Exactly four single/clean episodes, seed 0, share one synthetic source group.
Each episode has a fresh context and one required artifact; four persistent
worker identities remain available and the single policy uses w0. One frozen
model instance is reused within the one GPU shard. The configured model is the
existing pinned Qwen3.5-4B, BF16, deterministic, no thinking, 8192 context,
768 output tokens, 12 actions and 100000 total work per episode. Maximum total
allowance is 400000; the primary action bound is 48. All reads, model re-prefills,
malformed attempts, SQL operations, monitoring and evaluation stay charged.

The explicit suite selector is `sqlite_fixture_suite=tool_compatibility_v1`.
The adaptation, scorer, access regime and diagnostic mode distinguish this suite
from arithmetic fixtures, native/pair SQLite and SILO. All scores are development
diagnostics, not benchmark or recovery claims. The standard mock compiler is
not a solver for these probes; CPU tests use an explicitly injected scripted
worker. No runtime reference solver is added to the model adapter.

Passing the probes would demonstrate these limited operations on simple data;
it would not show that document discovery is the sole native bottleneck.
Failures should be split into malformed actions, execution rejection, missing
submission and wrong final results before choosing another condition. Do not
automatically widen the campaign or change model/decoding/budget settings.

## 1. Prepare in the browser terminal

First review, commit and push the local changes. Then use the already installed
cluster environment and model lock. No new model/data download is needed.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
mkdir -p "$BC_STORAGE/diagnostics"
export BC_TOOLS_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/sqlite-tools.XXXXXX")"

(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
  git status --short
  printf 'Stop: use a clean committed checkout before submission.\n'
  exit 1
fi
test -f "$BC_MODEL_LOCK"
test -f "$BC_CLUSTER"

"$BC_PYTHON" scripts/bc.py manifest \
  --config configs/sqlite-tool-compatibility.json \
  --model-lock "$BC_MODEL_LOCK" \
  --output "$BC_TOOLS_DIR/manifest.json"

"$BC_PYTHON" scripts/bc.py diagnostic-costs \
  --manifest "$BC_TOOLS_DIR/manifest.json" \
  --output "$BC_TOOLS_DIR/planned-costs.json"

"$BC_PYTHON" -m json.tool "$BC_TOOLS_DIR/planned-costs.json"

bash experiments/submit_pilot.sh \
  --cluster "$BC_CLUSTER" \
  --manifest "$BC_TOOLS_DIR/manifest.json" \
  --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1 \
  --dry-run
)
```

Expect four episodes, one array element `0-0%1`, one GPU and 400000 maximum work.
This uses the previously validated model/runtime; no separate model preflight
is scheduled. The normal shared registry and scheduler checks still apply.

## 2. Submit the bounded diagnostic

After the preparation/dry run succeeds:

```bash
bash experiments/submit_pilot.sh \
  --cluster "$BC_CLUSTER" \
  --manifest "$BC_TOOLS_DIR/manifest.json" \
  --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1

squeue -u "$USER"
```

## 3. After the job completes

```bash
export BC_TOOLS_ID="$("$BC_PYTHON" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' \
  "$BC_TOOLS_DIR/manifest.json")"
export BC_TOOLS_OUTPUT="$BC_STORAGE/outputs/$BC_TOOLS_ID"

"$BC_PYTHON" scripts/bc.py aggregate --output "$BC_TOOLS_OUTPUT"
tail -n 60 "$BC_TOOLS_OUTPUT"/logs/*.err

"$BC_PYTHON" scripts/bc.py diagnostic-costs \
  --run "$BC_TOOLS_OUTPUT" \
  --output "$BC_TOOLS_DIR/observed-costs.json"

"$BC_PYTHON" -m json.tool "$BC_TOOLS_DIR/observed-costs.json"

"$BC_PYTHON" - <<'PY'
import json
import os
from collections import Counter
from pathlib import Path

root = Path(os.environ["BC_TOOLS_OUTPUT"])
for path in sorted(root.glob("episodes/*/result.json")):
    result = json.loads(path.read_text())
    store = json.loads((path.parent / "checkpoint.json").read_text())["store"]
    events = store["events"]
    journal = [json.loads(line) for line in
               (path.parent / "events.jsonl").read_text().splitlines()]
    print(json.dumps({
        "task": result["task_id"],
        "status": result["status"],
        "success": result["success"],
        "charged_work": result["costs"]["spent"],
        "tool_rejections": result["metrics"].get("tool_rejections"),
        "event_counts": dict(Counter(e["type"] for e in events)),
        "operation_outcomes": [
            {k: e.get(k) for k in ("operation", "outcome", "measured_work")}
            for e in journal if e["type"] == "operation"
        ],
        "generation_stops": dict(Counter(
            e.get("details", {}).get("finish_reason", "unknown")
            for e in events if e["type"] == "generation_metadata"
        )),
    }, indent=2))
PY
```

Keep the per-probe report alongside the aggregate and measured costs. No automatic
retry follows a completed scientific failure. None of these GPU commands were
executed during local implementation.
