#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: submit_pilot.sh --cluster LOCAL.json --manifest MANIFEST.json --model-lock LOCK.json [--concurrency 1..4] [--dry-run]"
  exit 0
fi
BC_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${BC_PYTHON:-python3}" "$BC_REPO/scripts/bc.py" submit "$@"
