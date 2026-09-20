# Synthetic SQLite tool-compatibility diagnostic

**Historical runbook:** this reasoning/2048 condition completed 1/4 at 30715
work. Use the [constrained-action continuation](SQLITE_CONSTRAINED_DIAGNOSTIC.md)
for the current CPU qualification and run sequence. Preserve the old reports.

## Decision and limits

The first four-probe no-thinking run completed **0/4**, with 23786 charged work
and all 16 generations stopping at EOS. Aggregate/join/CASE failed action
construction or submission. A view missing FROM and a required alias was accepted
by public validation, then failed terminal evaluation.

The next authorized condition uses the same pinned model and four tasks, with
**thinking enabled and 2048 generated tokens per call, including reasoning**.
The executor now resolves views with a zero-row read, disables SQLite's legacy
quoted-string fallback, and checks explicitly public column names. The view's
structured source contract repeats names already stated in its public requirement.
Invalid views return `invalid_view` and create no artifact. These checks expose
no expected values and do not prove semantic correctness or every runtime case.
Other contracts without explicit public output names retain terminal alias checks.

This changes reasoning, output allowance, validation and public presentation;
it does **not** isolate a thinking effect. Historical failures stay frozen.
Changed executor capabilities invalidate prior native validation fingerprints:
repeat CPU reference controls before any future native run. No native retry is
part of these commands.

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
existing pinned Qwen3.5-4B, BF16, deterministic, thinking enabled, 8192 context,
2048 total output tokens, 12 actions and 100000 total work per episode. Maximum total
allowance is 400000; the primary action bound is 48. All reads, model re-prefills,
malformed attempts, SQL operations, monitoring and evaluation stay charged.

The 2048-token reservation leaves at most 6144 input tokens per model call.
Context and total-work limits still apply; no silent truncation is added.

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
export BC_TOOLS_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/sqlite-tools-reasoning.XXXXXX")"

(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
  git status --short
  printf 'Stop: use a clean committed checkout before submission.\n'
  exit 1
fi
test -f "$BC_MODEL_LOCK"
test -f "$BC_CLUSTER"

# Read-only CPU capability check; no weights or SQL workload are loaded.
"$BC_PYTHON" -I - <<'PYTHON'
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from beyond_consensus.runtime.sqlite_executor import capabilities
caps = capabilities()
print(json.dumps(caps, indent=2))
assert caps["double_quoted_strings_disabled"], "SQLite DQS controls unavailable"
assert caps["view_validation"] == "zero-row-v1"
PYTHON

"$BC_PYTHON" scripts/bc.py manifest \
  --config configs/sqlite-tool-compatibility-reasoning.json \
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
This reuses existing weights. The capability check above verifies the login
environment; compute-node capability checks still apply at execution. No separate
GPU preflight is scheduled. The normal shared registry and scheduler checks still apply.

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
        "output_tokens": sum(e.get("output_tokens", 0) for e in events
                             if e["type"] == "generation_metadata"),
        "reasoning_tokens": [e.get("reasoning_tokens") for e in events
                             if e["type"] == "generation_metadata"],
        "generation_stops": dict(Counter(
            e.get("details", {}).get("finish_reason", "unknown")
            for e in events if e["type"] == "generation_metadata"
        )),
    }, indent=2))
PY
```

If all four probes pass, consider a bounded native clean retry after fresh CPU
reference validation. If any fail, inspect the trace once for malformed actions,
invalid views, cap/context exhaustion, missing submission or wrong values before
choosing a different model/interface condition. Do not automatically increase
budgets or launch a recovery campaign. Unknown reasoning counts remain unknown.

Keep the per-probe report alongside the aggregate and measured costs. No automatic
retry follows a completed scientific failure. None of these GPU commands were
executed during local implementation.
