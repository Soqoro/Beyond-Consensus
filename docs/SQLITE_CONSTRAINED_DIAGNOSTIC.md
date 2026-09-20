# Four-probe constrained-action diagnostic

## Evidence and scope

The reasoning/2048 run `3996c58d44658d42f2d94fd08517884c606e068b798aac077118365d995dda63`
completed 1/4 probes at 30715 work. Only view passed. All 15 generations stopped
at EOS. Aggregate repeatedly used unsupported function/grouping structure; CASE
and join emitted invalid JSON. No failed action reached SQL execution. This
measures difficulty producing the bespoke action representation, not underlying
SQL competence. No further output/action increase is planned.

The new `configs/sqlite-tool-compatibility-constrained.json` retains the same
four tasks, pinned Qwen3.5-4B, thinking enabled, 2048 shared reasoning/action token
cap, 8192 context, 12 actions, 100000 work per episode, single/clean seed 0 and one
GPU shard. It adds `model.action_constraint=sqlite-json-schema-v1`. Existing
configs stay unconstrained. This mode is gated to this bounded diagnostic;
no native, SILO, attack or policy campaign is enabled.

The public action schema is generic: no task data, expected rows, gold SQL,
artifact IDs or suggested solutions are compiled into it. The model still selects
the tool, names, joins, functions, expressions, values and final artifact ID.
Generation uses declared property order and at most two whitespace characters
between elements. Preparation is excluded in this implementation-only condition.
Runtime checks still enforce bindings, identifiers, node/depth/resource limits,
SQL semantics and final correctness. Structural constraints do not guarantee a
correct query, an existing artifact ID, successful execution or task completion.

An optional, pinned XGrammar 0.1.32 processor masks invalid next tokens only after
`</think>` appears in the **generated suffix**, ignoring delimiters in the prompt.
Reasoning is not constrained or forcibly stopped. Every call starts a fresh
matcher. Thinking and actions keep their one shared token allowance. EOS before
the reasoning close, truncation or an incomplete final action causes rejection;
there is no auto-repair, solver, token injection or unconstrained fallback.
Schema hash, decoder version, mode and accounting are bound to manifests,
calibration, runtime metadata and result condition labels. Historical manifests
remain readable by hashing their serialized model configuration.

### Cost and validation limits

Each model call reserves an additional 30 CPU seconds × `tool_charge` (300 work
with the default rules), within the existing total budget and reserve floor.
Matcher setup, gate/mask processing and final schema validation are measured;
charged work is `ceil(process_cpu_seconds) * tool_charge`. Unknown/failed work
retains the reservation. The processor checks its allowance between callbacks;
this is not an OS-enforced CPU resource boundary. Overruns fail the run and retain
uncertain work. Model inference remains token-charged, with device timing logged.
One-time compilation of the task-independent public grammar/tokenizer is logged
as static setup CPU separately. No task-specific grammar compilation is done.

Local tests use stdlib schema validation and scripted CPU workers/decoder doubles.
This workspace has no torch/transformers/xgrammar stack or pinned tokenizer, so
**native grammar compilation, token masks and GPU behavior are unverified here**.
The mandatory next step below checks real token masks on the cluster CPU, without
weights or SQL. A failed check stops before manifest creation/submission. Optional
dependency installation occurs online once; never from a batch job. Native clean
runs remain paused; their prior CPU reference validation must also be refreshed
before any later native experiment.

The adapter follows the versioned [XGrammar compiler API](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/python/xgrammar/compiler.py),
[tokenizer API](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/python/xgrammar/tokenizer_info.py)
and [Transformers processor](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/python/xgrammar/contrib/hf.py).

## 1. Prepare the browser terminal after local commit/push

Use one session. Stop on errors; do not rerun historical GPU commands.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
mkdir -p "$BC_STORAGE/diagnostics"
export BC_CONSTRAINED_DIR="$(mktemp -d "$BC_STORAGE/diagnostics/sqlite-constrained.XXXXXX")"
export TMPDIR="$BC_STORAGE/tmp"
export PIP_CACHE_DIR="$BC_STORAGE/cache/pip"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR"
printf 'Keep this directory: %s\n' "$BC_CONSTRAINED_DIR"
```

## 2. Install the optional decoder without upgrading existing packages

Capture exact installed package versions as constraints, including the current
CUDA-specific torch build. If resolution conflicts, stop and inspect the conflict.
No model weights or datasets are downloaded by this step.

```bash
(
set -euo pipefail
"$BC_PYTHON" - <<'PY'
import importlib.metadata
import os
import re
from pathlib import Path

versions = {}
for distribution in importlib.metadata.distributions():
    name = distribution.metadata['Name']
    if name and re.fullmatch(r'[A-Za-z0-9_.-]+', name):
        versions[name] = distribution.version
path = Path(os.environ['BC_CONSTRAINED_DIR']) / 'installed-constraints.txt'
with path.open('x') as stream:
    stream.write(''.join(f'{name}=={versions[name]}\n' for name in sorted(versions)))
print(path)
PY

"$BC_PYTHON" -m pip install --only-binary=:all: \
  --constraint "$BC_CONSTRAINED_DIR/installed-constraints.txt" \
  --requirement requirements-constrained.txt
"$BC_PYTHON" -m pip check
"$BC_PYTHON" -m pip freeze > "$BC_CONSTRAINED_DIR/environment-after.txt"
)
```

## 3. Qualify the real decoder on CPU, then plan and dry-run

This loads the already staged tokenizer, not model weights. It tests positive
aggregate/join/CASE/view structures, malformed and duplicate-key rejections,
real per-token masks, EOS exclusion before completion, and the reasoning boundary.
It uses independent `demo_*` syntax controls, no task or reference inputs.

```bash
(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
  git status --short
  printf 'Stop: use a clean committed checkout.\n'
  exit 1
fi
test -f "$BC_MODEL_LOCK"
test -f "$BC_CLUSTER"

"$BC_PYTHON" -I scripts/check_action_constraints.py \
  --model-lock "$BC_MODEL_LOCK" \
  --output "$BC_CONSTRAINED_DIR/cpu-qualification.json"

"$BC_PYTHON" scripts/bc.py manifest \
  --config configs/sqlite-tool-compatibility-constrained.json \
  --model-lock "$BC_MODEL_LOCK" \
  --output "$BC_CONSTRAINED_DIR/manifest.json"

"$BC_PYTHON" scripts/bc.py diagnostic-costs \
  --manifest "$BC_CONSTRAINED_DIR/manifest.json" \
  --output "$BC_CONSTRAINED_DIR/planned-costs.json"
"$BC_PYTHON" -m json.tool "$BC_CONSTRAINED_DIR/planned-costs.json"

bash experiments/submit_pilot.sh \
  --cluster "$BC_CLUSTER" \
  --manifest "$BC_CONSTRAINED_DIR/manifest.json" \
  --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1 --dry-run
)
```

Expect a passed CPU qualification, four episodes, 2048 output tokens, maximum
400000 work and array `0-0%1`. Planning caps do not predict actual decoder cost.
The login CPU check does not establish compute-node/GPU compatibility.

## 4. Submit once, after step 3 succeeds

The shared registry and scheduler checks still apply. No direct sbatch bypass.

```bash
bash experiments/submit_pilot.sh \
  --cluster "$BC_CLUSTER" \
  --manifest "$BC_CONSTRAINED_DIR/manifest.json" \
  --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1
squeue -u "$USER"
```

## 5. After completion

```bash
export BC_CONSTRAINED_ID="$("$BC_PYTHON" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' \
  "$BC_CONSTRAINED_DIR/manifest.json")"
export BC_CONSTRAINED_OUTPUT="$BC_STORAGE/outputs/$BC_CONSTRAINED_ID"

"$BC_PYTHON" scripts/bc.py aggregate --output "$BC_CONSTRAINED_OUTPUT"
tail -n 60 "$BC_CONSTRAINED_OUTPUT"/logs/*.err
"$BC_PYTHON" scripts/bc.py diagnostic-costs \
  --run "$BC_CONSTRAINED_OUTPUT" \
  --output "$BC_CONSTRAINED_DIR/observed-costs.json"
"$BC_PYTHON" -m json.tool "$BC_CONSTRAINED_DIR/observed-costs.json"

"$BC_PYTHON" - <<'PY'
import json
import os
from collections import Counter
from pathlib import Path

for path in sorted(Path(os.environ['BC_CONSTRAINED_OUTPUT']).glob('episodes/*/result.json')):
    result = json.loads(path.read_text())
    state = json.loads((path.parent/'checkpoint.json').read_text())
    generations = [e for e in state['store']['events'] if e['type']=='generation_metadata']
    decoder = [e for e in state['ledger']['entries'] if e['kind']=='constrained_decoding']
    print(json.dumps({
        'task': result['task_id'], 'status': result['status'], 'success': result['success'],
        'charged_work': result['costs']['spent'],
        'tool_rejections': result['metrics'].get('tool_rejections'),
        'decoder_work': sum(e['work'] for e in decoder),
        'decoder_cpu_seconds': [e.get('cpu_seconds') for e in decoder],
        'reasoning_tokens': [e.get('reasoning_tokens') for e in generations],
        'constraint_complete': [e.get('details',{}).get('constraint_complete') for e in generations],
        'mask_calls': [e.get('details',{}).get('constraint_mask_calls') for e in generations],
        'stops': dict(Counter(e.get('details',{}).get('finish_reason','unknown') for e in generations)),
    }, indent=2))
PY
```

Send qualification, aggregate, per-probe and cost reports before another run.
Four passes would support considering fresh native CPU validation and a bounded
clean native control. Any failure needs classification before changing model or
interface. No automatic retry, budget increase or broader campaign is authorized.
