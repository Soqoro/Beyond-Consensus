# Common derivation-first wave: disabled launch packet

The new recipe uses the same four frozen wave-one workloads (n=2,4,6,8,
K=2, slot 1), source statements, A/C permissions, NEUTRAL assignments and
NEUTRAL/JOINT comparison. It moves derivation/justification first in every
worker schema. It does not redraw NEUTRAL or introduce new mathematical tasks.

The parent is scope
`bb51d1cb2a3f8914d9f8b0f6e1c4c52f0a21eb273be9b33c9c856c45845c5f37`.
The CPU-qualified interface is
`b84ad5cf4a2e41f39e34ef7601010832c8d4495a1121a25a4bf355e30d207802`.

## Proposed scope requiring new approval

- Qwen3.5-27B, revision `fc05daec18b0a78c049392ed2e771dde82bdf654`,
  same pinned non-thinking deterministic transport and model inventory.
- 16 fresh profiling calls covering every permitted component/operation mode.
  Zero historical, diagnostic or evaluation prices reused.
- At most 176 fresh evaluation calls: clean and one all-owner R0 sweep per
  distinct organisation. Identical organisations share observations explicitly.
- Total ceiling **192 calls / 3,145,728 input-plus-output tokens**.
- Per call: 13,312 input tokens, 3,072 generated tokens, 16,384 context.
- HPCAIq: one NVIDIA A100 80GB PCIe, minimum 80,000,000,000 bytes VRAM,
  four CPUs, 128 GB host memory, four hours including startup.
- Existing solver: 30 seconds per condition, one thread, seed zero.
- One registered attempt; no automatic retry, timeout extension or later wave.

The earlier 185-call approval and six-call diagnostic approval do not cover
this new scope. Preparation writes an exact digest and pending approval;
it cannot load a model or submit a job.

## Qualification and limitations

User-reported CPU qualification passed all nine distinct schemas, covering
14 tasks and 16 profile entries, in 13.83 CPU / 14.40 wall seconds.
Preparation checks the saved schema probes, pinned metadata, template and
implementation hashes. It does not repeat tokenizer qualification.

Full requests containing future generated parents cannot be premeasured.
The existing journal renders and checks each request before generation and
reserves its input plus output allowance. This is not worst-case fit evidence.

Four hours may leave some work unrun: the earlier recipe used 3h52m57s and
this proposal requires seven additional fresh profiles. Such outcomes must
remain unrun/incomplete, with no automatic continuation. Wrong answers remain
recorded. Existing gecko route-completeness and producer/consumer overlap
concerns remain limitations, not established mathematical qualification.

## Jupyter preparation (no model or job)

After transferring the listed source changes, run:

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_COMMON="$(mktemp -d "$BC_STORAGE/diagnostics/composite-common-derivation.XXXXXX")"
export BC_COMMON_PARENT="$BC_STORAGE/diagnostics/composite-scaling-hpcai.fAfBoz/outputs/composite-bb51d1cb2a3f8914d9f8b0f6e1c4c52f0a21eb273be9b33c9c856c45845c5f37"
printf 'Preparation directory: %s\n' "$BC_COMMON"
git rev-parse HEAD > "$BC_COMMON/source-commit.txt"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root=Path(os.environ['BC_COMMON'])
parent=Path(os.environ['BC_COMMON_PARENT'])
c=json.loads((parent/'manifest.json').read_text())['release']['manifest']['scope']['cluster']
assert c['partition']=='HPCAIq' and c['time']=='04:00:00'
c['output_root']=str(root/'outputs')
with (root/'cluster.json').open('x') as f:
    json.dump(c,f,indent=2)
    f.write('\n')
PY
"$BC_PYTHON" -I -B scripts/composite_common_derivation_pilot.py prepare \
  --parent-run "$BC_COMMON_PARENT" \
  --cluster "$BC_COMMON/cluster.json" \
  --qualification "$BC_STORAGE/diagnostics/composite-common-derivation-cpu.QBpau0/qualification.json" \
  --output "$BC_COMMON/bound"
scontrol show partition HPCAIq -o > "$BC_COMMON/partition.txt"
sinfo -p HPCAIq -N -o '%N %P %t %G' > "$BC_COMMON/nodes.txt"
squeue --array -u "$USER" -o '%.22i %.12P %.20j %.2t %.10M %R' > "$BC_COMMON/queue.txt"
cat "$BC_COMMON/nodes.txt"
cat "$BC_COMMON/queue.txt"
printf 'Manifest: %s\n' "$BC_COMMON/bound/MANIFEST.disabled.json"
)
```

Return the summary and scheduler output for exact scope approval. Pending
approval must explicitly cover source transmission, existing contract limitations
and the new 192-call GPU recipe. No approval is recorded by these commands.

## Exact launch command, only after scope approval

The `approve` CLI consumes the separately completed, scope-matching approval
JSON and emits `approved-release.json`. The launch command then is:

```bash
"$BC_PYTHON" -I -B scripts/composite_common_derivation_pilot.py submit \
  --release "$BC_COMMON/approved-release.json" \
  --output "$BC_COMMON/submission.json"
```

The shared registry, scheduler inspection, snapshot inventory, allocation,
GPU-access probe, source hashes and model inventory remain enforced. The
submission receipt is exclusively created. Do not rerun after an uncertain
submission or overwrite prior receipts.
