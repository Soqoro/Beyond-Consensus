# Normal guarded qualification: evidence review

## Reported result

On 15 October 2026, the user supplied the following completed qualification:

- Experiment: `5dd357626b3ad6a3677f6bca7ca1b7e548557c1b86fe6a7c03fdc91a701c96a0`.
- Job: `1097545_0`, completed, exit `0:0`, elapsed 5:22.
- Hardware: NVIDIA A100-SXM4-80GB; one model instance.
- Outcome: `passed_observed_cases`, 3/3 synthetic calls passed.
- Total: 17521 input-plus-output tokens, zero uncertain tokens, 318.633 seconds wall time.

| Case | Input | Output | Reasoning subset | CPU cap debit (seconds) |
| --- | ---: | ---: | ---: | ---: |
| Nested mapping | 91 | 601 | 556 | 49.1283 |
| Escaped keys | 95 | 1559 | 1510 | 122.9545 |
| Long-context mapping | 14335 | 840 | 795 | 75.3657 |

All ended at EOS, passed strict parsing, completed the constraint, and reported
no accelerator exception. Reasoning is included in output usage, not added again.
The three CPU debits total approximately 247.4484 seconds; wall time is separate.
No task execution was permitted. Worst-case fit remains unestablished.

This follows the separately approved matched diagnostic. Its user-supplied
summary reported both native and guarded arms completing both synthetic calls
under launch blocking, with 4692 total tokens and zero uncertainty. That did not
reproduce the historical failure under the diagnostic treatment. The original
failed attempt and its uncertain work remain unchanged; its cause remains unknown.

## Next: audit existing files on Jupyter

After pushing this audit implementation, run this complete block. It uses a
fresh report directory, never submits work, and does not modify the frozen
qualification source or historical outputs. An incompatible current checkout
is reported separately from a successful historical observation.

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only

BC_AUDIT_STORAGE=/dataset/suaq0001/beyond-consensus
BC_AUDIT_PYTHON="$BC_AUDIT_STORAGE/envs/bc-gpu-py312/bin/python"
BC_AUDIT_RUN="$BC_AUDIT_STORAGE/outputs/qwen27b-na100/5dd357626b3ad6a3677f6bca7ca1b7e548557c1b86fe6a7c03fdc91a701c96a0-preflight"
BC_NORMAL_AUDIT="$(mktemp -d "$BC_AUDIT_STORAGE/diagnostics/rr-normal-audit.XXXXXX")"

printf 'Audit directory: %s\n' "$BC_NORMAL_AUDIT"
"$BC_AUDIT_PYTHON" -I scripts/audit_rr_unique_normal.py \
  --run "$BC_AUDIT_RUN" \
  --snapshots "$BC_AUDIT_STORAGE/snapshots" \
  --output "$BC_NORMAL_AUDIT/audit.json"
)
```

Return the printed audit JSON. If the command fails, retain the directory and
return the error; do not rerun the GPU probe or change the historical files.
The command uses the existing Python environment and needs no GPU allocation.

## What the auditor establishes

It checks the full saved manifest/report and its resolved snapshot, lock,
settings, package and template bindings, three completed calls, reconciled
resource events, memory observations, and current decoder/core compatibility.
It does not certify independent authenticity or scheduler completion. Full
response text was not retained in the normal report, so it cannot independently
reparse response semantics. The frozen runner rejects launch blocking, but no
independent launch-environment trace was saved. These limits are explicit in the
returned audit.

## Sampled task study remains a separate step

The existing catalog summary reports six CPU-qualified plans: independent,
grouped and shared organizations for each of Jaffle payment release and GitHub
multioperation integration. The prepared scope is twelve conditions: a clean
and one seeded meaningful-owner loss branch per plan. CPU reference success is
not model competence. Ordinary clean failure must not remove the fault branch.

The existing proposal remains blocked and must not be edited in place. A future
execution packet needs the full normal audit, catalog/source compatibility,
current adapter controls, implemented shared-runner integration, and exact
approval of the twelve-condition scope. Independent task/source review deferrals
remain labelled development limitations. No approval is inferred from this
synthetic result. This change implements only the evidence-audit step.
