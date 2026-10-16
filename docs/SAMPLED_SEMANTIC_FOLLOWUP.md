# Sampled organization results and synthetic follow-up

Date: 2026-10-16. Read-only inspection of user-supplied export for experiment
`a6b820857f765fb3a4841b696e120f00e662c523be31744e5ed3cc6452d97ba4`.
The export was inspected locally; scheduler records and original cluster files
were not independently accessed. No model, SQL replay, or rescore was performed.

## Recorded outcomes

| Task | Authored organization | Clean | Seeded owner loss |
|---|---|---|---|
| Jaffle payment release | Independent | failed | failed |
| Jaffle payment release | Grouped | failed | resource exhausted |
| Jaffle payment release | Shared | passed | failed |
| GitHub multioperation | Independent | passed | failed |
| GitHub multioperation | Grouped | passed | passed |
| GitHub multioperation | Shared | failed | passed |

All twelve conditions are represented and contract-conformant; all six loss
interventions triggered. Reported uncertain tokens/CPU are zero. Three clean
branches pass, two fault branches pass. Of the three clean successes, only
GitHub grouped also passes under loss. GitHub shared's fault success has a
failed clean counterpart. This does not establish a beneficial effect of loss.
There were zero generated planner calls. The six organizations are correlated
variants within two development tasks, not independent samples or evidence of
planner superiority. Existing review deferrals and uncalibrated caps remain.

## Artifact-level findings

Five failed Jaffle branches use COUNT(order.id), optionally wrapped in COALESCE,
after joining raw payments. Multiple payment rows duplicate order IDs. The
successful shared clean branch uses COUNT(DISTINCT order.id). The independent
fault replacement repeats the same overcounting expression. These are saved
artifact observations consistent with recorded customer_summary failures;
no counterfactual query was run.

Independent fault reconciliation classifies the null row of a customer without
orders as an unpaid order. Grouped clean reconciliation additionally counts
paid orders over raw payment rows. Grouped fault fails to bind reconciliation:
two length-limited responses, a SQL rejection and eventual admission failure
are recorded. The final requested call reserved 11958 tokens with 11941 left;
actual recorded usage is 88059 tokens and 1150.545 CPU seconds. Unused tokens
do not imply another full call could be admitted.

GitHub independent fault publishes repository_summary fields errors/errors_2
instead of topics/language_bytes and update_topics field name instead of names.
Shared clean's repair publishes errors/errors_bytes. The wrong mappings also
name those keys in their own output schemas. Input paths can be plausible while
the resulting task interface is wrong. The saved artifacts do not identify why
the model selected those keys, or prove a decoder defect.

Public alarms are not hidden evaluation. Independent/grouped Jaffle clean have
no alarm despite semantic failures. GitHub independent fault alarms on missing
topics_response, not its erroneous mappings. Independent clean repairs its
summary successfully; shared clean repairs it incorrectly. Do not feed hidden
checks back to workers or expand the monitor silently to fix these observations.

## Prepared synthetic design

`scripts/prepare_rr_semantic_diagnostic.py --output FRESH_PATH` writes an
explicitly non-executable `rr-semantic-diagnostic-design-v1` packet. This is
CPU design preparation, not a manifest accepted by the submission system.

Three prospective one-call cases use invented customers/orders/payments and
neutral mapping names:

1. **Order granularity:** count orders once and all payment records, retaining
   customers without orders. Repeated equal payment amounts distinguish SUM
   from an incorrect SUM(DISTINCT amount) shortcut.
2. **Unpaid boundary:** distinguish an unpaid order, a zero-valued payment, and
   a customer with no orders.
3. **Mapping field names:** produce exact labels/size_bytes keys from declared
   input paths. Self-declared schema validity and task contract correctness
   must be recorded separately.

Independent Python reference arithmetic and counterexample controls are
implemented. They do not run the production SQL compiler, schema validator,
executor, monitor, GPU, or task engine. They are deliberately labelled as
mechanism controls, not runtime qualification. Positive SQL/reference artifacts
and production monitor controls must still be prepared and checked before a
GPU manifest can exist. Public cases exclude control outcomes and expected rows;
a future runner must pass only the case, never the entire private packet.

Proposed bounds: three model calls total, no planner calls, no retry, pool seven,
one GPU, context 16384/output 2048, separate 16384-token and 1200-CPU-second
ledger per case. These are synthetic diagnostics, not an end-to-end recovery or
matched clean/F experiment. Monitoring coverage is observed offline without
changing worker feedback. Model generation, compiler, tool and analysis expenses
must remain separate and charged in their appropriate ledgers.

The packet records unresolved production executor/monitor controls, exact lock
and tokenizer footprint, shared execution adapter, and exact GPU approval.
Do not pass it to `bc.py submit`, remove its blockers, or substitute historical
qualification for compatibility checks. No experiment is launched by preparing
this design. A future GPU implementation must use the existing shared registry,
frozen runtime, strict parsing, approved child executors, and saved responses.

## Local preparation command

```bash
python -I scripts/prepare_rr_semantic_diagnostic.py \
  --output /tmp/rr-semantic-design.json
```

Use a fresh output path each time. No optional GPU libraries or downloads are
needed. Historical artifacts and model behavior are unchanged.

## Production control stage

The `--production-controls` option now runs seven authored controls through
pool-seven AssignmentScopes, Environment publication, the pinned SQL compiler
child, approved IR executor, schema/mapping child, and unchanged public monitor.
Three positive programs must pass independent semantic checks. Four negatives
(raw order count, distinct payment amount, no-order null row, wrong mapping keys)
must fail semantic checks while passing public monitoring. Thus a control run
passes only if it demonstrates the monitor's specific coverage limitation as
well as positive feasibility. These are CPU control outcomes, not model scores.

Each control has a fresh environment and separate resource ledger. Literal
fixture creation is harness-owned; candidate SQL never executes on the host.
The report retains compiler/executor status, charged CPU, uncertainty, runtime
versions and implementation hashes. Missing pinned prerequisites produce a
saved blocked report and exit code 2, never a qualification pass. No report is
sent back to a worker. The private controls are not included in observations.

Local production execution is blocked by missing pinned optional dependencies.
The actual child-path test is therefore skipped locally; cluster execution must
pass all seven cases. Exact lock/footprint and submission adapter remain pending.
The design packet retains its blockers until a future proposal verifies evidence.

After pushing, run this CPU-only preparation in the Jupyter terminal:

```bash
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_SEMANTIC="$(mktemp -d "$BC_STORAGE/diagnostics/rr-semantic-controls.XXXXXX")"
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: keep exports outside Git before freezing source.\n'
    exit 1
fi
git rev-parse HEAD > "$BC_SEMANTIC/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_SEMANTIC/source"
git -C "$BC_SEMANTIC/source" checkout --detach "$(cat "$BC_SEMANTIC/source-commit.txt")"
cat > "$BC_SEMANTIC/controls.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd "$BC_SEMANTIC/source"
test "$(git rev-parse HEAD)" = "$(cat "$BC_SEMANTIC/source-commit.txt")"
"$BC_PYTHON" -I scripts/prepare_rr_semantic_diagnostic.py \
  --production-controls --output "$BC_SEMANTIC/controls.json"
SH
bash -n "$BC_SEMANTIC/controls.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=00:20:00 --export=ALL \
  --job-name=rr-semantic-cpu --chdir="$BC_SEMANTIC/source" \
  --output="$BC_SEMANTIC/cpu.out" --error="$BC_SEMANTIC/cpu.err" \
  "$BC_SEMANTIC/controls.sh" > "$BC_SEMANTIC/cpu-job.txt"
printf 'Directory: %s\n' "$BC_SEMANTIC"
cat "$BC_SEMANTIC/cpu-job.txt"
)
```

PA100q is a previously used CPU partition, not a statement of current
availability. Once finished:

```bash
sacct -j "$(cut -d';' -f1 "$BC_SEMANTIC/cpu-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
cat "$BC_SEMANTIC/cpu.out"
tail -n 40 "$BC_SEMANTIC/cpu.err"
"$BC_PYTHON" -m json.tool "$BC_SEMANTIC/controls.json"
```

Preserve failed and blocked reports. This CPU script requests no GPU and cannot
submit a child job; it does not authorize a GPU diagnostic or retry old tasks.
