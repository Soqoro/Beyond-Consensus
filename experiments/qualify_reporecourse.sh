#!/usr/bin/env bash
# CPU-only, explicit user-triggered qualification. Never self-submits.
set -euo pipefail
usage() {
    cat <<'EOF'
Usage: qualify_reporecourse.sh --sources DIR --output NEW_DIR [--model-lock FILE] [--local] [--dry-run]
CPU pack/reference checks; optional pinned-tokenizer grammar qualification.
Use sbatch on the cluster. --local allows explicit workstation CPU checks.
EOF
}
sources=''
output=''
model_lock=''
local_run=false
dry=false
while (($#)); do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --dry-run) dry=true; shift ;;
        --local) local_run=true; shift ;;
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
for task in synthetic-stock synthetic-nullable jaffle-recorded-payments energy-generation-coverage github-topics-consumer; do
    "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" --task "$task" --output "$output/$task.json"
done
"$BC_PYTHON" -I scripts/check_sql_frontend.py --output "$output/compiler.json"
if [[ -n "$model_lock" ]]; then
    "$BC_PYTHON" -I scripts/check_action_constraints.py \
        --model-lock "$model_lock" --context-limit 16384 \
        --action-constraint reporecourse-json-v1 \
        --output "$output/grammar.json" --qualified-lock "$output/model-lock.json"
fi
printf 'CPU qualification reports: %s\n' "$output"
