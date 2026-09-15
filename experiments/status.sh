#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: status.sh --output RUN_DIR [--jobs PROJECT_JOB_ID ...] [--dry-run]"
  exit 0
fi
BC_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${BC_PYTHON:-python3}" "$BC_REPO/scripts/bc.py" status "$@"
