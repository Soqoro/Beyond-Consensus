#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: submit_gpu_preflight.sh --cluster LOCAL.json --manifest MANIFEST.json --model-lock LOCK.json [--dry-run]"
  exit 0
fi
for arg in "$@"; do
  if [[ "$arg" == --mode || "$arg" == --mode=* || "$arg" == --concurrency || "$arg" == --concurrency=* ]]; then
    echo "Preflight uses one GPU; mode/concurrency overrides are not accepted" >&2
    exit 2
  fi
done
BC_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${BC_PYTHON:-python3}" "$BC_REPO/scripts/bc.py" submit --mode preflight "$@"
