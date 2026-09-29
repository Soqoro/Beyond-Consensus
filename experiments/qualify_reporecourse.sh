#!/usr/bin/env bash
# CPU-only, explicit user-triggered qualification. Never self-submits.
set -euo pipefail
usage() {
    cat <<'EOF'
Usage: qualify_reporecourse.sh --sources DIR --output NEW_DIR [--model-lock FILE] [--local] [--dry-run] [--track-f-controls] [--v2-controls] [--pool-count N]
CPU pack/reference checks; optional pinned-tokenizer grammar qualification.
Use sbatch on the cluster. --local allows explicit workstation CPU checks.
EOF
}
sources=''
output=''
model_lock=''
local_run=false
dry=false
track_f=false
v2=false
pool_count=4
while (($#)); do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --dry-run) dry=true; shift ;;
        --local) local_run=true; shift ;;
        --v2-controls) v2=true; shift ;;
        --pool-count) (($# >= 2)) || exit 2; pool_count="$2"; shift 2 ;;
        --track-f-controls) track_f=true; shift ;;
        --sources|--output|--model-lock)
            (($# >= 2)) || { usage >&2; exit 2; }
            case "$1" in
                --sources) sources="$2" ;;
                --output) output="$2" ;;
                --model-lock) model_lock="$2" ;;
            esac
            shift 2 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if "$dry"; then
    printf 'CPU qualification only: reference alternatives, negatives, compiler; optional model-specific decoder. No model weights or GPU jobs.\n'
    exit 0
fi
[[ -n "$sources" && -n "$output" ]] || { usage >&2; exit 2; }
if ! "$local_run"; then
    : "${SLURM_JOB_ID:?Use a CPU batch allocation, or explicitly --local on a workstation}"
fi
: "${BC_PYTHON:?Set BC_PYTHON to the Python 3.12+ environment with pinned optional CPU dependencies}"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
[[ ! -e "$output" ]] || { printf 'Use a fresh output directory.\n' >&2; exit 2; }
mkdir -p -- "$output"
"$BC_PYTHON" -I scripts/bc.py rr-readiness --sources "$sources" --output "$output/readiness.json"
if "$v2"; then
    if "$track_f"; then printf 'Choose v2 controls or legacy Track F, not both.\n' >&2; exit 2; fi
    [[ "$pool_count" =~ ^[2-8]$ ]] || { printf 'Pool must be 2..8.\n' >&2; exit 2; }
    PYTHONPATH="$repo_root/src" "$BC_PYTHON" - <<'PYV2'
import unittest
from reporecourse.track_f_controls import PINS
from reporecourse.qualification import runtime_versions
actual=runtime_versions()
if any(actual.get(k)!=v for k,v in PINS.items()):raise SystemExit('Pinned CPU dependencies required')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests',pattern='test_reporecourse_v2.py'))
if not r.wasSuccessful() or r.skipped:raise SystemExit('v2 controls must pass without skips')
PYV2
    "$BC_PYTHON" -I scripts/rr_v2.py qualify --sources "$sources" --output "$output/v2-fixtures.json"
    "$BC_PYTHON" - "$output/v2-fixtures.json" <<'PYCHECK'
import json,sys
if json.load(open(sys.argv[1]))['status']!='passed':raise SystemExit('v2 fixture qualification failed')
PYCHECK
    if [[ -n "$model_lock" ]]; then
        for role in json plan; do
            "$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$model_lock" --context-limit 16384 \
                --action-constraint "reporecourse-$role-v2-pool-$pool_count" \
                --output "$output/grammar-$role-pool-$pool_count.json" \
                --qualified-lock "$output/model-lock-$role-pool-$pool_count.json"
        done
    fi
    printf 'v2 CPU controls only; task review, B0, model competence and memory qualification remain pending.\n'
    exit 0
fi
if "$track_f"; then
    # Fail on relevant skips; a previous revision's approvals are insufficient.
    "$BC_PYTHON" - <<'PYTEST'
import sys, unittest
sys.path.insert(0, 'src')
from reporecourse.track_f_controls import PINS
from reporecourse.qualification import runtime_versions
actual = runtime_versions()
if any(actual.get(k) != v for k, v in PINS.items()):
    raise SystemExit(f"Pinned CPU qualification blocked: required={PINS}, actual={actual}")
suite = unittest.TestSuite()
for pattern in ('test_reporecourse.py', 'test_reporecourse_track_f.py', 'test_sql_text.py'):
    suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful() or result.skipped:
    raise SystemExit('Track F CPU qualification requires every relevant test to run and pass')
PYTEST
    "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" \
        --task jaffle-recorded-payments --track-f-controls --output "$output/jaffle-recorded-payments.json"
else
    for task in synthetic-stock synthetic-nullable jaffle-recorded-payments energy-generation-coverage github-topics-consumer; do
        "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" --task "$task" --output "$output/$task.json"
    done
fi
"$BC_PYTHON" -I scripts/check_sql_frontend.py --output "$output/compiler.json"
if [[ -n "$model_lock" ]]; then
    "$BC_PYTHON" -I scripts/check_action_constraints.py \
        --model-lock "$model_lock" --context-limit 16384 \
        --action-constraint reporecourse-json-v1 \
        --output "$output/grammar.json" --qualified-lock "$output/model-lock.json"
fi
printf 'CPU qualification reports: %s\n' "$output"
