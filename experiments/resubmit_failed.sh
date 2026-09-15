#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: resubmit_failed.sh --snapshot SNAPSHOT_DIR [--concurrency 1..4] [--dry-run]"
  exit 0
fi
BC_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${BC_PYTHON:-python3}" "$BC_REPO/scripts/bc.py" resubmit "$@"
