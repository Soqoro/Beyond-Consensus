#!/usr/bin/env bash
# All resource requests are validated sbatch CLI arguments, not expanded directives.
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: run_shard.sbatch SNAPSHOT OUTPUT run|preflight resume|retry ENV_PYTHON [--dry-run]"
  exit 0
fi
if [[ $# -lt 5 || $# -gt 6 ]]; then
  echo "Expected snapshot, output, mode, resume setting, and environment Python; use --help" >&2
  exit 2
fi
BC_SNAPSHOT="$1"
BC_OUTPUT="$2"
BC_MODE="$3"
BC_RESUME="$4"
BC_ENV_PYTHON="$5"
if [[ "$BC_MODE" != run && "$BC_MODE" != preflight ]] || [[ "$BC_RESUME" != resume && "$BC_RESUME" != retry ]]; then
  echo "Invalid batch mode or resume setting" >&2
  exit 2
fi
if [[ "${6:-}" == "--dry-run" ]]; then
  printf 'Snapshot: %s\nOutput: %s\nMode: %s\nDevice: assigned CUDA_VISIBLE_DEVICES (preserved)\n' "$BC_SNAPSHOT" "$BC_OUTPUT" "$BC_MODE"
  exit 0
fi
if [[ $# -eq 6 ]]; then
  echo "Unknown sixth argument" >&2
  exit 2
fi
: "${SLURM_JOB_ID:?Requires a Slurm allocation}"
: "${CUDA_VISIBLE_DEVICES:?Requires Slurm GPU visibility}"
BC_ARGS=(batch --snapshot "$BC_SNAPSHOT" --output "$BC_OUTPUT" --mode "$BC_MODE")
if [[ "$BC_RESUME" == retry ]]; then
  BC_ARGS+=(--retry)
fi
# exec preserves the job's exit code and delivers TERM to the Python boundary handler.
exec "$BC_ENV_PYTHON" -I -B "$BC_SNAPSHOT/scripts/bc.py" "${BC_ARGS[@]}"
