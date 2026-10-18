# Three-call semantic diagnostic: results and compiler audit

Date: 2026-10-16. Experiment:
`254b92bc02c5733cfeff6e0b4d46fca608b0aeba01228e9390a192f22b2cbdf5`.
Reported runtime Slurm job: `1098514`, array task 0.

## Evidence boundary

This audit inspects the user-pasted report fragment and current compiler source;
it does not independently access the cluster or replay generated SQL. The paste
starts inside the first case's evaluator ledger, so it is not a complete JSON
archive. Its SHA256 is
`1990cd00dbd3702bf6a68482130836cee388c0c6f8e8890b021775a2bcc6e377`.
The report records snapshot
`c92a931589bc4914061ba90cd19745484f189498ddb49383a86011ccb44dad7f`.
Snapshot inventory and scheduler completion have not been independently verified
in this audit. Preserve the full cluster `semantic-report.json` and manifest.

## Observed results

| Case | Execution | Public monitor | Semantic check | Input + output tokens |
|---|---|---|---|---:|
| order_grain | completed, executor ok | passed | passed | 3200 |
| unpaid_boundary | SQL construction rejected | not reached | not measured | 3391 |
| mapping_keys | completed, executor ok | passed | failed | 2846 |

All three responses reached EOS with complete constrained output. The report
lists no missing cases, zero uncertain tokens, and 313.112 seconds wall time on
NVIDIA A100-SXM4-80GB. Summing the three visible task ledgers gives 9437 tokens
and 227.400 CPU cap-debit seconds. Each visible task ledger has zero uncertain
CPU and no outstanding token reservations. Terminal evaluation has separate
ledgers; process CPU is an overlapping observation and must not be added to
task CPU. Overall `completed` means the diagnostic finished, not three successes.

The correct order-grain query used `COUNT(DISTINCT o.id)`, counted payment
records separately, and summed payment amounts without DISTINCT. This shows
success on this invented instance, not general robustness to join fanout.

The mapping used `label` and `bytes` instead of required `labels` and
`size_bytes`. Its output schema repeated the same wrong names. Consequently,
public shape/self-schema checking passed while the independent semantic check
failed. This reproduces the structural-validity/task-correctness distinction;
it does not identify a decoder cause.

## Exact unpaid-boundary rejection

The saved `compiler_feedback.validation` records:

```json
{
  "capability": "rr-sql-capability-v1",
  "code": "case_else_required",
  "operator": "Case",
  "path": "sql.ast"
}
```

Both generated expressions omit ELSE:

```sql
COUNT(DISTINCT CASE WHEN p.order_id IS NOT NULL THEN o.id END)
COUNT(DISTINCT CASE WHEN o.id IS NOT NULL AND p.order_id IS NULL THEN o.id END)
```

`src/restricted_artifacts/sql_text.py` advertises searched CASE with explicit
ELSE, lists implicit CASE ELSE as unsupported, and raises
`LoweringRejected('case_else_required', 'Case')` when the default is absent.
`tests/test_rr_interface.py`,
`CompilerContracts.test_supported_and_unsupported_examples_exact_child_feedback`,
already covers this rejection code for a CASE without ELSE.

Thus the observed rejection matches the declared restricted SQL contract. It
is not evidence of a parser crash, COUNT DISTINCT failure, or incorrect unpaid
classification. The model's semantic ability on this case remains unresolved
because execution never occurred. No compiler relaxation or automatic rewrite
is justified by this record. In particular, do not add an ELSE to the historical
query and count the result as a model success.

## Decision and next experiment planning

Preserve one semantic pass, one contract rejection and one semantic failure as
separate outcomes. No historical scores, worker prompts, public monitor, parser,
or runtime behavior change in this audit. No GPU retry is needed to identify
the rejection: its exact diagnostic is already in the saved trace.

These are three post-hoc synthetic cases, one call per case, without repair or
model planning. They do not estimate recovery effectiveness, planner quality,
held-out competence, or decoder causality. Before further GPU work, choose the
question: SQL contract adherence, exact mapping-key adherence, or end-to-end
recovery. A change in prompt, syntax allowance, or call budget would be a new
prospective condition, not a continuation or correction of these observations.

## Follow-up: public prompt construction audit

Static inspection traces `rr_semantic_run.observation` through
`Environment.observation` and `engine.worker_messages`. The synthetic environment
enables `rr-interface-reliability-v1`; worker_messages appends worker_contract
to the system message. That contract includes sql_capability, whose expression
description requires explicit ELSE and whose unsupported list includes implicit
CASE ELSE. Thus the prompt-building code supplies this restriction; it is not
only a private compiler rule. This is source inspection, not an independent
reconstruction of the saved token sequence against the frozen snapshot.

The mapping task request explicitly requires labels and size_bytes and forbids
extra fields. It is present in the public request and supplied sources; the
assignment also carries the request in its interface declaration. There is no
task instruction to rename those keys to label or bytes.

However, `interface.publications()` supplies a generic mapping example with the
output key label (and a generic schema example also uses label). The observed
wrong key label therefore overlaps a system-message syntax example. This is a
possible example-copying influence, not proof of causation. The inspected generic
examples do not explain the second wrong key bytes. Do not attribute either error
to guarded decoding from this single response.

## Proposed next diagnostic: mapping-example sensitivity

Prioritize a narrow prompt comparison over changing the compiler or rerunning
the cohort. Prepare, but do not execute, a prospective two-arm mapping-only
diagnostic:

- Baseline: the current public task and current generic publication examples.
- Treatment: the same messages, except rename the example output key label to
  neutral_example_field consistently in both generic schema and mapping examples.
  Keep the actual task keys, input paths, values and requested output unchanged.

Use one fresh call per arm, the same frozen worker/guarded decoder, context/output
caps, one GPU, no repair or retries, and separate ledgers. Re-measure both prompts
and record hashes. The tokenizer lengths may differ and must be reported rather
than assumed equal. Both arms are new observations; the historical mapping result
is not reused as the baseline. Evaluation stays private and the public monitor
stays unchanged. No gold answer or corrected mapping is supplied to either arm.

Report exact output keys, execution/public-monitor/semantic outcomes, completion
and usage independently. Two deterministic calls on one selected task can reveal
response sensitivity to this example edit; they cannot estimate population
effects, prove that the old error was caused by the example, or establish decoder
causality. If both fail, that does not rule out example influence generally.

This is a design recommendation only: no adapter, approval receipt, manifest or
GPU job was created. Do not modify the shared interface examples globally for
this experiment; an eventual diagnostic must isolate the treatment and preserve
historical behavior. Keep unpaid-boundary contract adherence as a separate
question, rather than bundle a SQL change into this comparison.
