# Native 27B context feasibility follow-up — 2026-09-21

## Evidence and decision

User-reported 27B synthetic probe result: 4/4 passed; this is one synthetic source
group, not general competence or a matched causal model-size comparison.
Renewed individual solar references and joint pair passed positive, reset,
integrity, missing-obligation and corruption controls under SQLite 3.45.1.

Native experiment `15465896c46c6daedf3098ef3200c696331cd6bdbcd2996996de72152a84ec4e`
stopped before scoring both tasks. `solar_2` made 11 calls (36383 work),
`solar_M_3` made 8 (26082 work); total 62465. No tool rejections or selected
artifacts. All recorded generations completed their constraint and stopped at
EOS. Private-journal exception extracts confirm the worker context guard fired
for both: input plus reserved 2048 output exceeded 8192. Success is unknown,
not 0/2. The current runtime calls these `infrastructure_failed` and the shard
retryable, but unchanged resubmission is inappropriate for this deterministic
configured-limit failure. Historical labels and charges are preserved.

The input read sequence is not available locally. `competence-audit` now exports
hashed public-read targets, offsets, repeat counts, observation character/byte
sizes, and recorded context-limit events. It exports no document bodies, SQL,
reference or test material. Inspect that evidence BEFORE submitting another run.
An offline audit does not execute the model or change historical results.

New profile `qwen35-27b-native-context16k` permits only the two individual native
solar tasks, single/clean, seed 0, one shard. Context is 16384 (14336 input plus
2048 reserved output). Actions remain 12, total surrogate work 100000 per task;
no history truncation, forced completion, retrieval changes, budget increase,
pair GPU evaluation, attack or policy campaign. Extra re-prefill remains charged.
A larger context can still hit the work cap or fail to solve the tasks.

CPU qualification explicitly binds context. The old 8K qualified lock cannot
qualify 16K. Existing staged weights are reused without download. The preflight
already sizes synthetic history from the configured allowance; it now targets
14336 input tokens for this profile. Early EOS still does not establish worst-case
16384-token cache fit. A100 80GB fit at this length remains unmeasured.

## Browser workflow after reviewing, committing and transferring the changes

Retain existing BC27_SOLAR (renewed data), BC27_SOLAR_OUTPUT (failed 8K run),
BC27_NA_CLUSTER and BC_PYTHON variables. Do not replace old files. First audit:

```bash
export BC27_CONTEXT="$(mktemp -d "$BC_STORAGE/diagnostics/native-context16k.XXXXXX")"
"$BC_PYTHON" scripts/bc.py competence-audit --run "$BC27_SOLAR_OUTPUT" \
  --output "$BC27_CONTEXT/old-read-audit.json"
```

For a compact upload from the Jupyter file browser, save only the read audit:

```bash
"$BC_PYTHON" - <<'PYTHON'
import json
import os
import tempfile
from pathlib import Path
root = Path(os.environ["BC27_CONTEXT"])
report = json.loads((root / "old-read-audit.json").read_text())
small = {"experiment_id": report["experiment_id"], "tasks": [
    {k: task.get(k) for k in ("task", "status", "read_history")}
    for task in report["tasks"]]}
with tempfile.NamedTemporaryFile(mode="w", prefix="solar-read-audit-",
        suffix=".private.json", dir=Path.home()/"Beyond-Consensus", delete=False) as f:
    json.dump(small, f, indent=2)
    f.write("\n")
    print(f.name)
PYTHON
```

Review read_history for both tasks. Repeated reads alone do not prove a bug;
inspect whether offsets differ and whether large observations explain growth.
Record the evidence before GPU submission; no remote read sequence is presumed.
Prepare the condition and freeze the clean source for CPU qualification:

```bash
(
set -euo pipefail
test -z "$(git status --porcelain)"
"$BC_PYTHON" scripts/bc.py validation-config \
  --profile qwen35-27b-native-context16k \
  --data-manifest "$BC27_SOLAR/native-validated.private.json" \
  --output "$BC27_CONTEXT/config.json"
mkdir "$BC27_CONTEXT/source"
git archive --format=tar HEAD | tar -xf - -C "$BC27_CONTEXT/source"
git rev-parse HEAD > "$BC27_CONTEXT/source-commit.txt"
chmod -R a-w "$BC27_CONTEXT/source"
cat > "$BC27_CONTEXT/qualify.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?CPU allocation required}"
cd "$BC27_CONTEXT/source"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$BC_PYTHON" -I scripts/check_action_constraints.py \
  --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json" \
  --context-limit 16384 --output "$BC27_CONTEXT/qualification.json" \
  --qualified-lock "$BC27_CONTEXT/qualified-model-lock.json"
SH
bash -n "$BC27_CONTEXT/qualify.sh"
)
```

Manual CPU submission using the previously used CPU partition:

```bash
sbatch --partition=PA100q --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=01:00:00 --output="$BC27_CONTEXT/cpu.out" \
  --error="$BC27_CONTEXT/cpu.err" "$BC27_CONTEXT/qualify.sh"
```

After CPU completion inspect qualification status/context and errors. No source
or package updates between qualification and GPU submission. Then:

```bash
"$BC_PYTHON" scripts/bc.py manifest --config "$BC27_CONTEXT/config.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json" \
  --output "$BC27_CONTEXT/manifest.json"
bash experiments/submit_gpu_preflight.sh --cluster "$BC27_NA_CLUSTER" \
  --manifest "$BC27_CONTEXT/manifest.json" \
  --model-lock "$BC27_CONTEXT/qualified-model-lock.json" --dry-run
```

Only after review submit that preflight by removing `--dry-run`. Inspect its
actual input/cache length, memory, placement, completion and command_failed.
Do not submit the two native episodes until read-audit and preflight review.
The shared registry remains mandatory. This document launches nothing.

## Follow-up results (2026-09-21)

The user subsequently supplied a passing 16K A100 80GB preflight and two completed
native failures at the 12-action cap. The read audit showed no repeated reads.
This supersedes pending-GPU statements above. See [NATIVE_ACTIONS24.md](NATIVE_ACTIONS24.md)
for exact evidence and the separately authorized next condition.
