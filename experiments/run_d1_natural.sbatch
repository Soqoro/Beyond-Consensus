#!/usr/bin/env bash
# Usage: run_d1_natural.sbatch SNAPSHOT OUTPUT ENV_PYTHON [--dry-run]
set -euo pipefail
if [[ "${1:-}" == --help ]]; then
  echo 'Usage: run_d1_natural.sbatch SNAPSHOT OUTPUT ENV_PYTHON [--dry-run]'
  exit 0
fi
if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo 'Expected snapshot, output and Python; use --help' >&2
  exit 2
fi
if [[ "${4:-}" == --dry-run ]]; then
  printf 'Natural-screen snapshot: %s\nOutput: %s\nPython: %s\n' "$1" "$2" "$3"
  exit 0
fi
if [[ $# -eq 4 ]]; then
  echo 'Unknown argument' >&2
  exit 2
fi
: "${SLURM_JOB_ID:?Requires a Slurm allocation}"
: "${CUDA_VISIBLE_DEVICES:?Requires Slurm GPU visibility}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
exec "$3" -I -B "$1/scripts/launch_d1_natural.py" run-allocated --output "$2"
