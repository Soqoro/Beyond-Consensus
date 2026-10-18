#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} == --help ]]; then
    printf 'Usage: %s [--dry-run] SOURCE_ROOT PYTHON SUBCOMMAND [arguments...]\n' "$0"
    exit 0
fi
dry=false
if [[ ${1:-} == --dry-run ]]; then
    dry=true
    shift
fi
if [[ $# -lt 3 ]]; then
    printf 'Usage: %s SOURCE_ROOT PYTHON SUBCOMMAND [arguments...]\n' "$0" >&2
    exit 2
fi
source_root="$1"
worker_python="$2"
shift 2
if [[ ! -s "$source_root/scripts/worker_selection.py" || ! -x "$worker_python" ]]; then
    printf 'Missing frozen source or Python executable.\n' >&2
    exit 2
fi
cd "$source_root"
if "$dry"; then
    printf '%q ' "$worker_python" -I scripts/worker_selection.py "$@"
    printf '\n'
    exit 0
fi
exec "$worker_python" -I scripts/worker_selection.py "$@"
