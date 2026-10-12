# Four-task cohort: results and failure-trace audit

Date: 12 October 2026

## Executive summary

The first richer four-task comparison has completed. The requirement-level planner achieved **one clean success out of four tasks** and **no fault-branch successes out of four**. The prompted planner achieved **no successes**: three tasks failed during planning, and the remaining task failed in both execution branches.

The traces identify concrete interface problems worth addressing before another comparison:

1. All nine rejected planning responses used artifact names where `outputs` requires terminal obligation IDs.
2. Of 69 recorded schema/mapping contract rejections, 68 passed JSON strings where objects were required.
3. All 25 rejected Energy SQL actions contained `IN` predicates, which the restricted compiler does not support; some also used `BETWEEN`.
4. Jaffle fault recovery rebuilt three individually correct outputs but did not complete the reconciliation output. Complete-task failure remains correct under the existing evaluator.

These findings support improving public instructions and rejection feedback. They do not establish that interface changes will make the tasks succeed, or that model capability is the only limitation.

## Evidence and scope

- Experiment: `b9f84bc78966300bfd615ff4c54a140ae9d238a371e26c157bd5c3ecc8f9f5a6`.
- Evidence: user-supplied `read_only_real_run_export_including_failed_and_unrun` export, attached as `842ce04c-99ee-4826-aec5-a33d4950b87e/Pasted text.txt`.
- Export SHA256: `4454209a4d82f998eb3c9f483d6a4e504b68131f8030af729a86c0bd24dd73ec`.
- Lane: `rich_development_unreviewed`; review status: `deferred_by_user`; confirmatory: false.
- Four tasks, three source groups: the two GitHub tasks share a source group.
- Eight planner/task configurations, with a maximum of 16 clean/fault branches. No configurations are missing.

This audit inspected saved responses, action traces, evaluation records and resource ledgers, with local implementation code used to interpret contracts. It did not independently authenticate the live cluster snapshot. No model or SQL was executed, no candidate was repaired, and no historical score changed. The export's `model_executed: false` describes the export operation, not the original experiment.

This report supersedes the **pre-run status** in `AUDIT_REPORT_2026-10-12.md`; that earlier report remains a historical record.

## Results

| Task | Requirement-level clean | Requirement-level F | Prompted clean | Prompted F |
| --- | --- | --- | --- | --- |
| Jaffle payment release | Success | Failed | Invalid planning | Invalid planning |
| Energy single-indicator release | Resource exhausted | Resource exhausted | Invalid planning | Invalid planning |
| GitHub topics client package | Failed | Failed | Invalid planning | Invalid planning |
| GitHub multioperation integration | Failed | Failed | Failed | Resource exhausted |

Planning failures remain in the end-to-end denominator: they are not missing runs or eligible exclusions. Three invalid planning configurations account for six planned branch conditions without execution. Ten branches executed; all ten were reported contract-conformant. All five executed F branches triggered the intervention, targeting `w1` in this run. Conformance and intervention delivery do not imply correctness.

The requirement-level condition is a reference decomposition, not an independently successful generated planner. Its planning used no model calls. Prompted planning used ten physical calls: three rejected calls on each of three tasks, and one accepted call on multioperation integration.

## Failure audit

### 1. Planner output IDs: repeated, poorly explained contract failures

All nine rejected responses received feedback `{"error":"output"}`. Their unit `outputs` fields contained helper or artifact names:

- Jaffle: `schema_understanding` in all three attempts.
- Energy: `source_schema` and `filtered_energy_data` in all three attempts.
- Topics: `source_read` or `sources`, plus artifact aliases such as `request_schema` and `consumer_mapping`, instead of the required terminal IDs.

The validator in `src/reporecourse/v2.py` requires `outputs` to be a subset of required output IDs. Helper artifact names belong in `produces`; helper-only units need `outputs: []`. `terminal_bindings` connects terminal obligations to produced artifacts.

The public planner message lists these fields and requires terminal coverage, but does not plainly explain this distinction for `outputs`. Repeating the error string `output` gives little help identifying the offending unit or correcting its structure.

**Assessment:** the recorded rejections agree with the validator. The public explanation and feedback are inadequate for this repeated error. The final `plan_schema` status and empty saved terminal plan should not be interpreted as evidence that the model literally returned an empty object. Other plan defects could remain after fixing the output IDs; no corrected-plan replay was performed.

### 2. Schema and mapping objects were repeatedly encoded as strings

Recorded API contract failures comprise:

| Rejection | Content type | Count |
| --- | --- | ---: |
| `schema_keyword` | String | 49 |
| `mapping_contract` | String | 19 |
| `mapping_contract` | Object | 1 |

Thus **68 of 69** such rejections supplied the wrong outer content type. For illustration, a schema publication needs `"content":{"type":"object"}`, not `"content":"{\"type\":\"object\"}"`.

`schema_keyword` covers both a non-object and unsupported keys. Here all 49 recorded schema failures were strings, so the error label alone would misleadingly suggest unsupported JSON Schema keywords. The remaining object-valued mapping failure lacked the required top-level `output_schema`; it was nested inside `fields` instead.

No source-read actions appear in the six API execution-branch trajectories. However, the tool contract is automatically included in worker messages, so this does **not** mean the workers never received the contract. It already says SQL content is a string and schema/mapping content is an object.

**Assessment:** prospective format-specific examples, stronger envelope constraints where compatible, and precise type errors are justified. Automatically decoding historical strings would change the accepted-action contract and is not part of this audit.

### 3. Energy repeatedly attempted unsupported SQL

The clean branch recorded 14 SQL construction rejections; the F branch recorded 11. All 25 rejected actions contained `IN` predicates, including `NOT IN`; eight clean and five F actions also contained `BETWEEN`.

The compiler's explicit expression allowlist in `src/restricted_artifacts/sql_text.py` does not support these constructs. It also requires an explicit `ELSE` in searched `CASE`. The public contract broadly lists supported SELECT features but does not clearly enumerate these exclusions and requirements.

Both Energy branches read table information six times. The evidence therefore does not support diagnosing the failures simply as lack of source access. The static audit identifies unsupported constructs, but does not establish the exact first compiler exception for every action: the saved rejection category is broader, and no SQL was replayed.

The CPU ledger attributes approximately 99.7% of both Energy totals to `model_host_including_decoder_and_tokenization`:

- Clean: 1182.40 of 1185.79 CPU seconds.
- F: 1171.57 of 1174.22 CPU seconds.

These are charged CPU quantities, not SQL execution time or GPU wall time. Resource exhaustion can occur below the 1200-second cap when the next operation cannot be admitted within the remaining allowance.

**Assessment:** clarify the exact public SQL subset before treating a larger budget as the solution. Repeated invalid actions consume substantial model-side resources.

### 4. Jaffle F recovered useful work but failed complete integration

The final fault-branch bundle bound `order_payments`, `customer_summary` and `method_summary`; `reconciliation` was missing. The saved evaluator contains 12 passing individual checks—three outputs across four fixtures—and four failed cross-output consistency checks.

The evaluator marks all obligations false when complete-bundle consistency fails. Consequently, the final all-false obligation summary does not mean every reconstructed output was individually wrong.

The branch recorded one unavailable-worker failure, five SQL rejections and one malformed JSON action. Rejected reconciliation queries included unsupported `IN` subqueries or searched `CASE` without explicit `ELSE`.

**Assessment:** retain the failed complete-task score, but distinguish successful partial reconstruction from failure to finish the required bundle. No partial score was substituted for the historical score.

## Resource accounting

| Task / planner | Clean tokens | F tokens | Clean CPU seconds | F CPU seconds |
| --- | ---: | ---: | ---: | ---: |
| Jaffle / requirement | 37,255 | 90,658 | 330.24 | 1017.04 |
| Energy / requirement | 52,434 | 47,882 | 1185.79 | 1174.22 |
| Topics / requirement | 10,690 | 27,871 | 284.55 | 639.41 |
| Multioperation / requirement | 48,944 | 28,023 | 1125.82 | 594.15 |
| Multioperation / prompted | 44,834 | 51,000 | 849.83 | 1197.51 |

The ten branch totals sum to **439,591 logical tokens** and **8398.57 CPU seconds**. The three failed planning configurations additionally consumed 31,390 physical planning tokens and 1398.58 CPU seconds. The accepted prompted plan consumed 2665 tokens and 118.44 CPU seconds, logically included in each of its two branch totals; physical reuse must remain separate. These quantities must not be added and labelled physical campaign consumption without reconciling reuse. Reported uncertain usage was zero.

## Recommended next work

Before another experiment, prepare a prospective interface revision:

1. Explain `outputs`, `produces` and `terminal_bindings` explicitly, with helper and terminal examples. Return bounded, actionable validation errors containing the offending public field and permitted terminal IDs.
2. Distinguish wrong content type from unsupported schema keywords. Check whether format-specific publication constraints can prevent JSON-string schemas and mappings without narrowing valid artifact semantics.
3. Document the compiler's exact supported operators and explicit-`ELSE` requirement. Keep lowering to the approved IR; do not silently rewrite unsupported worker SQL.
4. Add focused controls for these observed interface failures, then renew affected qualifications and freeze a new manifest before any rerun.
5. Keep the current failed and unexecuted conditions in the historical result. Any new comparison must be labelled an interface revision, not a continuation that replaces failures.

No implementation change or new experiment is included in this audit. The current evidence supports targeted interface work, not a planner-superiority claim, calibrated-budget result, or population-level estimate. Task and rights reviews remain deferred, and these repeatedly inspected development tasks cannot serve as untouched confirmation data.
