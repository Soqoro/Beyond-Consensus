# Beyond Consensus — progress and results for review

**Date:** 2026-09-23  
**Decision:** pause new submissions for review. The user reports that the synthetic
aggregation GPU preflight is already in progress; its outcome is pending.  
**Scope:** consolidated research history, with detailed updates since the
[September 22 review](PROGRESS_REPORT_2026-09-22.md).

## 1. Executive summary

The research question is whether recovery-aware delegation improves complete-task
success after contributor compromise at the same total work allowance.
**That advantage has not been demonstrated.**

The clearest recent advance is a completed interface comparison: on the two
repeatedly inspected native solar tasks, the fresh JSON-tree control scored
**0/2**, while the SQL-text interface scored **1/2**, using less charged work.
The previously failing view task now passes under SQL text. This is a useful
local development result, not evidence of general SQL competence or recovery.

A later naming-prompt correction retained **1/2**, increased work by **12.4%**,
and helped the query task reach an executable artifact. That task still exhausted
its budget before submission. A separate CPU audit established that the exact
unsubmitted candidate also failed the reviewed comparison. Consequently, final
submission alone would not have rescued this result.

The project remains at a **clean-worker competence and task-interface validation
stage**. The new two-task synthetic aggregation diagnostic is prepared and pushed;
its preflight is pending. No model task results for it are available. Review
should happen before starting those episodes or expanding the campaign.

## 2. What has been built

### Reproducible execution and accounting

- Pinned model/tokenizer staging and qualified model locks.
- Frozen manifests/source snapshots, per-episode journals and checkpoints,
  complete coverage reporting and bounded resume behavior.
- Browser-terminal Slurm workflow with a shared per-user registry, one active
  campaign and at most four GPUs; recent diagnostics use one GPU shard.
- Four persistent identities sharing one frozen model per allocated GPU.
  Single-worker controls do not measure four-worker cooperation.
- Charged input/output tokens, tools, retries, discarded work, planning,
  monitoring, compilation and constrained decoding. Reported work is a surrogate,
  not dollars, FLOPs or GPU-hours.
- Separation of public monitoring, attacker truth and hidden evaluation.
  Offline analyses do not change historical scores or feed results to workers.

### Environment and task changes

CooperBench repository execution did not qualify on the inspected Slurm setup:
basic container isolation probes passed, but the required resource-isolation
contract did not. The active path moved to restricted SQLite data tools and a
labelled recoverable-contributor SILO adaptation. These tools are not an OS
sandbox. No PBS/cloud/personal-PC migration was completed.

SQLite supports restricted query/view artifacts, exact version bindings, public
schema/document access, explicit final submission and reviewed complete-output
checks. Author material stays private. Arbitrary upstream Python tests are not
executed; native results belong to the reviewed `bc_livesql_native_v1` adaptation,
not a claim of full upstream evaluator parity.

### Recent interface work

The optional SQL-text interface parses and lowers supported SELECT strings into
the existing approved query representation. Worker SQL is never executed directly.
JSON-tree defaults remain available. Compiler controls, grammar qualification,
native reference representability and GPU preflight are separate gates.

Work addressed escaped-string grammar rejection, ambiguous preflight action
format, missing historical feedback settings, insufficient failure reporting and
table/column naming instructions. The SQL-text grammar preserves runtime string
bounds. Historical settings were explicitly resolved and fresh comparison arms
were run; the old native control was not reused as a matched arm.

## 3. Evidence across the project

Earlier values below are carried forward from the September 22 report and its
cited user reports; they were not rerun for this document.

| Area / condition | Result | Meaning |
| --- | --- | --- |
| Numeric workflow campaigns | Reported 32/32 clean/withholding and 32/32 clean/sabotage | Engineering fixture checks |
| Corrected arithmetic SQLite pilot | 32/32 across four policies and two conditions | Fixture paths work; no success advantage for recovery |
| SILO original interface | 0/8 complete tasks; 101/480 correct values | Clean competence inadequate in tested setting |
| SILO actual submitted-carry interface | 0/8; 101/480 correct values | Better local consistency did not improve complete success |
| 4B synthetic SQL, no thinking | 0/4; 23786 work | Construction/submission failures |
| 4B synthetic SQL, thinking | 1/4; 30715 work | More reasoning did not resolve most failures |
| 4B synthetic SQL, constrained | 1/4; 28649 work | Valid structure did not imply correct semantics |
| 27B synthetic SQL, constrained | 4/4; 21327 work | Basic competence on four inspected synthetic tasks |
| 27B synthetic SQL, categorized feedback | 4/4; 21327 work, zero rejections | Feedback was not exercised; no demonstrated feedback benefit |
| 27B native 8K | Both executions unscored after context guard | Runtime/configuration failure, not two scored wrong answers |
| 27B native 16K / 12 actions | 0/2; 113123 work | No final artifacts within action allowance |
| Earlier 27B native 16K / 24 actions | 0/2; 171715 work | Query construction and view semantics failed |
| Fresh matched JSON-tree arm | 0/2; 171725 work | Current comparison control |
| Fresh matched SQL-text arm | 1/2; 134471 work | Local interface improvement |
| SQL-text naming follow-up | 1/2; 151191 work | Same success count, higher work |
| New synthetic aggregation diagnostic | Preflight pending; no task results | Prepared experiment only |

The two 24-action tree totals (171715 and 171725) belong to different experiments;
they are not interchangeable. The paired supplied-draft correction diagnostic
also exists, but no completed comparison result has been supplied in this record.

### What the policy fixtures actually showed

Four episodes per cell in the corrected SQLite pilot:

| Policy | Clean / withholding success | Mean clean work | Mean withholding work |
| --- | --- | ---: | ---: |
| Ordinary | 4/4 and 4/4 | 22111 | 21715.5 |
| JIT | 4/4 and 4/4 | 22111 | 21711.5 |
| Recovery | 4/4 and 4/4 | 22367 | 21967.5 |
| Replication | 4/4 and 4/4 | 37470.75 | 26682 |

No advance preparations were selected. The audited 256-work recovery/JIT
difference was finite-search overhead. Replication cost more without raising
success. This does not prove recovery is generally inferior; these fixtures did
not establish the intended preparation benefit.

## 4. Recent native results in detail

All three conditions below use the same two repeatedly inspected solar tasks
from one database group. They are development observations, not held-out trials.

| Condition | solar_2 | solar_M_3 | Total work |
| --- | --- | --- | ---: |
| Matched JSON-tree | Failed, no final artifact; 88572 | Submitted but incorrect; 83153 | 171725 |
| Matched SQL-text | Failed, no final artifact; 80083 | Passed; 54388 | 134471 |
| SQL-text naming follow-up | Failed, no final artifact; 94959 | Passed; 56232 | 151191 |

The reported comparison audit matched recorded settings outside the declared
interface treatment. SQL text used approximately **21.7% less work** than the
fresh tree arm. The treatment includes syntax documentation, decoding schema
and compiler costs; this does not isolate one causal component. Two tasks in
one database cannot establish a population success rate or parameter-size effect.

### Naming follow-up: failure sequence established

For solar_2:

1. The final three queries used direct table names and documented join keys.
   The earlier qualified-table naming error was absent from those actions.
2. Two constructions were rejected. Both used simple CASE sorting, outside the
   advertised searched-CASE subset. The third used supported syntax.
3. The third query compiled and executed, creating an artifact with 1000 rows.
4. The next model reservation needed 15072 work plus a 300 decoder allowance,
   but only 5081 remained. Execution moved to partial-work auditing.
5. No final required artifact was selected. The intermediate version was
   invalidated, and the episode remained unsuccessful.

All 13 generations ended at EOS, without an output-token-limit stop. Restored
context explained an apparent zero current-action count; the archived history
preserved the actual actions. The 300-work allowance is not a newly chosen
research reserve fraction.

### Offline candidate replay: semantic failure established

The exact unsubmitted artifact was replayed through the same bounded executor
under historical implementation/runtime checks. Recorded rows reproduced exactly.
Candidate and reference checks both executed successfully, but **exact match and
native comparison were both false**. The artifact was not promoted or revalidated;
historical success remains false.

This analysis cost **60 separate replay work** (two calls at 30 each), with
reported parent CPU 0.2491s, child CPU 0.1902s and wall time 0.8462s. Those costs
are not added to or substituted for the historical 151191 work. Earlier native
failure replay cost 150 separately; neither replay creates a new model result.

### Public query review: likely risks, not complete causal attribution

[The public review](SOLAR_QUERY_PUBLIC_AUDIT.md) found formulas and urgency rules
broadly consistent with the supplied public definitions. However, summing after
joining independent maintenance and alert detail tables can multiply monetary
totals. Ratios may remain plausible even when both numerator and denominator are
inflated. Inner-join coverage and null/zero handling are additional uncertainties.

Actual detail multiplicities and which output cells failed are not yet measured.
The public documents inspected were exported from the earlier SQL-text arm;
the follow-up's identical document exposure was not independently established.
No hidden reference contents were inspected for that review, and no corrected
benchmark answer was given to the model. More budget might permit correction,
but merely submitting the current candidate would not pass the reviewed check.

## 5. Hardware and engineering evidence

Qwen3.5-27B staging pins revision
`fc05daec18b0a78c049392ed2e771dde82bdf654`. Reported qualified runs use A100 80GB,
Python 3.12.10, torch 2.10.0+cu126, Transformers 5.3.0 and XGrammar 0.1.32.
SQL-text parsing uses SQLGlot 27.28.1. Cluster availability is not inferred from
old node listings.

The prior SQL-text GPU preflight passed the explicit action-envelope probe:
977 output tokens, including 939 reasoning tokens; completed constrained action;
compiler/executor status ok. Peak reserved memory in that report was 62302191616
bytes. Long-context preflight observations ended early and do not establish every
worst-case generation length. A passing synthetic preflight is not task competence.

Latest local implementation validation: **235 tests, 4 skipped**, plus nine shell
files and documentation shell syntax checks. Correct, duplicated-aggregation,
wrong-alias and missing-submission scripted controls behave as intended. Scripted
controls are software validation, not empirical model successes.

## 6. Current pending diagnostic and review boundary

The prepared `aggregation_v1` suite has two tasks on one synthetic source group:

- Payment totals for every team.
- Payment totals plus independent total/critical notice counts.

Frozen inputs include unequal detail counts, repeated equal payments, a team with
no notices and a team with no payments. Expected outputs are computed independently
in Python at terminal scoring. Public schemas and requirements are supplied, with
no native references, answer queries or document-retrieval requirement.

Settings: 27B SQL text, generic feedback, single/clean seed 0, Protocol A,
8192 context, 2048 output including reasoning, 12 actions, two malformed retries,
100000 work per task, one GPU shard. This is deliberately a bounded synthetic
condition, not a matched native 16K/24-action comparison. The two-episode cap is
200000; actual work is unknown.

**Latest user update:** the preflight is running. Its result and the new condition's
model-task performance are unknown. CPU qualification reports for this particular
cluster setup have not been supplied in this review message. Do not describe the
model diagnostic as passed or completed based on local tests or submission alone.

Previously supplied commands include a later pilot submission. **Pause before
that step while reviewing this report.** Let the already submitted preflight
finish and preserve its logs; this review does not request cancelling it or
launching another job. The diagnostic's run procedure remains in
[SQLITE_AGGREGATION_DIAGNOSTIC.md](SQLITE_AGGREGATION_DIAGNOSTIC.md).

## 7. What we can and cannot conclude

**Established within the reported development conditions:**

- The pipeline can run the frozen 27B model and score restricted artifacts.
- Basic synthetic SQL probes passed with 27B.
- SQL text produced a native view success where the fresh tree control failed.
- Naming-follow-up query execution succeeded, but budget blocked submission.
- That query's candidate also failed reviewed semantic comparison.

**Not established:**

- General native SQL or SILO competence, or full upstream evaluator parity.
- Recovery-aware delegation outperforming ordinary, JIT or replication policies.
- A measured benefit from advance preparation or general model-generated
  decomposition. Finite graph execution remains synthetic/mock/JIT-only.
- Join multiplication as the measured cause of the native mismatch.
- That more budget, another prompt revision or a larger model will solve it.
- Statistical generalization from these repeatedly inspected tasks.

The broader methodological issues remain: clean competence, meaningful legal
workflow variation, compatible measured calibration, and independent evaluation
groups must precede a credible native policy comparison. Under limited additive
cost assumptions JIT may defer the same preparation; a recovery advantage cannot
be created by assuming cheap reconstruction or forcing preparations.

## 8. Decisions for the review

| Decision | Question to settle |
| --- | --- |
| Run the prepared two-task diagnostic after preflight | Is this narrow aggregation uncertainty worth measuring before more native work? |
| Revisit decomposition/policy design now | Does the proposed environment permit a meaningful recovery advantage even with competent workers? |
| Freeze the interface and broaden task validation later | What new independent groups and stopping criteria would support generalization? |
| Pause or reduce scope | Has interface debugging displaced the main research question enough to warrant a scope change? |

A synthetic pass would show competence on those supplied-schema tasks, not native
success. A failure would motivate per-task classification (construction, semantics,
submission or resource limits), not automatic budget escalation. Preflight failure
would be an engineering result only. None of these outcomes automatically opens
native policy campaigns.

## 9. Recent experiment index and preservation

| Condition | Experiment ID |
| --- | --- |
| Earlier native 24-action tree | `13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981` |
| Fresh matched tree | `a11a562d9af5e460c728f5dcf68c18a381a3bf5bc29ec3267f36a71ead918341` |
| Fresh matched SQL text | `a84f67659e998a2164836a8e66c2e8f06fecdda5a6e66805c72fbe563478143b` |
| Naming follow-up | `0050bdb57f765b37009c875dfdc8062cfa20f9a0e3195bf6f14da508527f63fa` |
| Aggregation diagnostic | Identifier not yet supplied in this review |

Preserve manifests, locks, frozen source, runtime/preflight reports, ledgers,
checkpoints, context archives and immutable offline reports. Keep datasets,
references, private outputs and environments out of Git. Do not sum rows in this
report as a comprehensive project compute total: coverage is incomplete and
conditions share tasks; hardware timing is also incomplete.

Cluster findings are user-supplied evidence, not direct remote inspection by the
assistant. This report reads existing records and changes documentation only;
it runs no model/SQL, downloads nothing, changes no scientific scores or budgets,
and submits no jobs. The earlier reports remain dated historical checkpoints.
