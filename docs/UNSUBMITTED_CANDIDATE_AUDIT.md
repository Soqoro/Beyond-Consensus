# Offline unsubmitted candidate audit

The naming follow-up stopped before final submission. This diagnostic asks only
whether its exact recorded query matches the existing reviewed comparisons. It
does not turn the failed episode into a success or feed terminal results to a
worker. It does not execute raw worker SQL: the recorded approved IR goes to the
same fixed, bounded SQLite child. No reference text or rows are exported.

The explicit candidate must be an unselected solar_2 query, without view bindings,
with complete recorded provenance, a creation event, and matching successful
primary execution and content execution hashes. Existing run/snapshot/database/
runtime/scorer checks still apply. Only solar_2 is replayed in candidate mode.
A mismatch of replayed and recorded rows stops comparison. Every SQL call has a
separate replay charge; original ledger and scores are immutable. This is a
reviewed-adaptation diagnostic, not full upstream evaluator parity or competence.

## Jupyter terminal after committing/pushing and pulling this change

Run once to freeze source and submit a CPU job (no GPU requested):

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_CANDIDATE_RUN="$BC_STORAGE/outputs/qwen27b-na100/0050bdb57f765b37009c875dfdc8062cfa20f9a0e3195bf6f14da508527f63fa"
(
set -euo pipefail
umask 077
test -z "$(git status --porcelain)"
test -f "$BC_CANDIDATE_RUN/manifest.json"
BC_CANDIDATE_DIR="$(mktemp -d "$PWD/candidate-audit.XXXXXX")"
export BC_CANDIDATE_DIR
printf '/%s/\n' "$(basename "$BC_CANDIDATE_DIR")" >> .git/info/exclude
mkdir "$BC_CANDIDATE_DIR/source"
git archive HEAD | tar -xf - -C "$BC_CANDIDATE_DIR/source"
git rev-parse HEAD > "$BC_CANDIDATE_DIR/source-commit.txt"
chmod -R a-w "$BC_CANDIDATE_DIR/source"
cat > "$BC_CANDIDATE_DIR/audit.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
cd "$BC_CANDIDATE_DIR/source"
"$BC_PYTHON" -I scripts/bc.py native-failure-audit \
  --run "$BC_CANDIDATE_RUN" \
  --candidate-artifact d4572fb4546632572af9a7e1d4d97451a2ad6fc573eebe7768155c3610841d3e \
  --output "$BC_CANDIDATE_DIR/candidate.private.json"
SH
bash -n "$BC_CANDIDATE_DIR/audit.sh"
sbatch --partition=NA100q --nodes=1 --ntasks=1 --cpus-per-task=2 \
  --mem=4G --time=00:10:00 \
  --output="$BC_CANDIDATE_DIR/cpu.out" --error="$BC_CANDIDATE_DIR/cpu.err" \
  "$BC_CANDIDATE_DIR/audit.sh"
printf 'After completion, upload: %s/candidate.private.json\n' "$BC_CANDIDATE_DIR"
)
```

The folder is inside the repository for GUI download and excluded locally from
Git. Do not force-add it. Preserve the private inputs, frozen source and report.
If historical implementation checks fail, report that failure; do not disable
checks or rewrite the original run. A report of unavailable replay or mismatched
rows is not a candidate correctness result. Do not rerun into the same report path.
