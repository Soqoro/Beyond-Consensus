# Offline native failure replay — 2026-09-22

## Recorded result

User-supplied run `13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981`
used the 24-action/16K condition and completed 0/2 at 171715 work. Solar_2 used
16 calls and 88562 work: call 14 was capped, calls 15/16 returned SQLite
`semantic_error`, and three rejections ended the operation as `malformed`.
Evaluation reported missing obligations. Solar_M_3 used 13 calls and 83153 work,
selected a view, passed public integration, but failed terminal exact and native
subset comparisons. No context or action limit bound this run. We have not
identified the specific execution defect or incorrect view expression.

Further GPU reruns and limit increases are paused. The new `native-failure-audit`
is a CPU-only diagnostic for those two completed native episodes. It never
updates historical results or supplies feedback to workers. It uses the exact
historical executor, binding and scorer implementations (verified against the
immutable source snapshot), recorded database hashes, original SQLite runtime,
limits, selected artifacts and reviewed comparisons. Changed/missing inputs
block the audit; they are not evidence of model failure.

Two recorded failed unbound read queries are replayed at most once each. If
current action history cannot align with the recorded generations, report it
unavailable; do not reconstruct missing text. Bound queries are explicitly
unsupported by this narrow query diagnostic. Selected-bundle replay uses the
existing version-binding logic. Up to eight reviewed checks per obligation are
compared using the same exact and native-subset comparison functions. SQL rows,
identifiers, query bodies, raw errors and expected answers stay private. Only
fixed error categories/statuses and indexed check booleans are exported. This
is reviewed adaptation scoring, not arbitrary upstream Python test execution.

The fixed diagnostic child calls the existing restricted `_child` executor,
including copied databases, authorizer, compiler, resource bounds and no extension
loading. Its only different failure behavior is an allowlisted error category
(e.g. unresolved column or aggregate misuse). The worker executor and worker
error messages are unchanged. It is not an OS sandbox. Successful private
outputs are consumed inside the offline audit and omitted from its report.

Each child invocation charges recorded tool rate × recorded CPU allowance,
even on failure, into a separate replay ledger capped at 40 invocations. Parent
CPU, child CPU and wall time are also reported. Historical 171715 work is never
replaced or combined silently with replay costs. No answer-guided patch or
follow-up model execution is performed. The audit can identify failed check
indices; it does not necessarily diagnose the exact faulty expression.

## Manual CPU Slurm workflow

After reviewing, committing/pushing and pulling the changes, use the existing
Python environment. No GPU allocation or model staging/qualification is needed.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_FAILURE_RUN="$BC_STORAGE/outputs/qwen27b-na100/13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981"
export BC_FAILURE_AUDIT="$(mktemp -d "$BC_STORAGE/diagnostics/native-failure-audit.XXXXXX")"
(
set -euo pipefail
test -z "$(git status --porcelain)"
test -f "$BC_FAILURE_RUN/manifest.json"
mkdir "$BC_FAILURE_AUDIT/source"
git archive --format=tar HEAD | tar -xf - -C "$BC_FAILURE_AUDIT/source"
git rev-parse HEAD > "$BC_FAILURE_AUDIT/source-commit.txt"
chmod -R a-w "$BC_FAILURE_AUDIT/source"
cat > "$BC_FAILURE_AUDIT/audit.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?CPU allocation required}"
cd "$BC_FAILURE_AUDIT/source"
"$BC_PYTHON" -I scripts/bc.py native-failure-audit \
  --run "$BC_FAILURE_RUN" --output "$BC_FAILURE_AUDIT/report.private.json"
SH
bash -n "$BC_FAILURE_AUDIT/audit.sh"
)
printf 'Save this directory: %s\n' "$BC_FAILURE_AUDIT"
```

Submit manually, requesting no GPU:

```bash
sbatch --partition=PA100q --nodes=1 --ntasks=1 --cpus-per-task=2 \
  --mem=8G --time=00:30:00 --job-name=bc-native-failure-audit \
  --output="$BC_FAILURE_AUDIT/audit.out" --error="$BC_FAILURE_AUDIT/audit.err" \
  "$BC_FAILURE_AUDIT/audit.sh"
squeue -u "$USER"
```

After completion, copy the sanitized report to a unique browser-download file:

```bash
"$BC_PYTHON" - <<'PY'
import json
import os
import tempfile
from pathlib import Path
report = json.loads((Path(os.environ['BC_FAILURE_AUDIT'])/'report.private.json').read_text())
with tempfile.NamedTemporaryFile(mode='w', prefix='native-failure-replay-', suffix='.private.json',
        dir=Path.home()/'Beyond-Consensus', delete=False) as f:
    json.dump(report, f, indent=2)
    f.write('\n')
    print('Upload:', f.name)
PY
tail -n 40 "$BC_FAILURE_AUDIT/audit.err"
```

Stop on errors. Do not upload the historical manifests, database, checkpoint,
raw private context or reference files. No native task replay results have been
obtained locally; wait for the CPU report before choosing further work.
