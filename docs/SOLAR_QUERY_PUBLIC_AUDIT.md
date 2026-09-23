# Solar query review using public requirements (2026-09-23)

## Outcome and scope

The exact unsubmitted solar_2 candidate failed the existing reviewed comparison.
The CPU replay reproduced its recorded rows, so this is not merely a missing
final-submission problem. Historical experiment
`0050bdb57f765b37009c875dfdc8062cfa20f9a0e3195bf6f14da508527f63fa`
remains 1/2 successful. No model, SQL or benchmark database was executed in this
static review. No worker prompt, compiler, budget or scorer was changed.

This review identifies a structural aggregation risk and an interface mismatch.
It does **not** establish which row/column caused the failed comparison, or that
fixing one issue would produce a correct answer. No corrected benchmark solution
is supplied to a worker. Do not use this repeatedly inspected pair as held-out
competence evidence.

## Evidence and provenance

- User-supplied stopping trace for episode
  `f85084078dedf56d9a441d3f8e77166e04957f39474c1a20405bc47e22fa9354`:
  two rejected constructions, then one successful execution and no final
  submission. Candidate version:
  `d4572fb4546632572af9a7e1d4d97451a2ad6fc573eebe7768155c3610841d3e`.
- User-supplied offline audit: replayed rows match the recorded rows; candidate
  and reference execution statuses are both `ok`; both exact and native
  comparison are false. Candidate remains invalidated and unpromoted.
  Replay work is 60, separate from historical work; analysis CPU 0.249082723s,
  child CPU 0.190158s, wall 0.8461656830040738s. Source revision:
  `b1d338d6dff70ca9160ad3c005343d801f5a4f82:dbe5b6ed661499e611ecd11f7a66dee897587e55105887f423b5518754d3bd48`.
- Public requirements, schema, column meanings and KB definitions were supplied
  in the earlier SQL-text arm's worker-visible transcript, experiment
  `a84f67659e998a2164836a8e66c2e8f06fecdda5a6e66805c72fbe563478143b`.
  This supplies public review material, not proof that the follow-up read the
  identical pages. A follow-up-specific read comparison has not been performed.
- Local compiler inspection: `runtime/sql_text.py`, expression handling for
  CASE. Only searched CASE is lowered. No private reference SQL, oracle knowledge,
  expected rows or upstream Python tests were read for this review.

## Findings

| Area | Observed candidate behavior | Assessment |
| --- | --- | --- |
| Table names and joins | Uses source tables directly, linking maintenance and alerts independently to the plant key | Names and stated key relationships agree with the public column descriptions; earlier qualified-table confusion is absent |
| Metric formulas | Cost components are summed; cost and revenue are divided by capacity; MROI divides revenue rate by cost efficiency | Algebraic form agrees with the public definitions, conditional on correct aggregation, null and zero handling |
| Priority | Tests for any critical alert, then combines it with MROI > 2 | Branch precedence agrees with the public four-level urgency definition |
| Ordering | Numeric urgency rank ascending, then MROI descending | Agrees with the stated priority order at the expression level |
| Aggregation | Sums maintenance values after joining both detail tables | Can multiply monetary totals when a plant has multiple alerts; actual multiplicities have not been measured |
| Coverage | Inner join to maintenance | Excludes plants without maintenance records; whether such rows exist or are required by the reviewed comparison is unestablished |
| Null/zero handling | Adds cost components before SUM; divides without explicit zero/null handling | Can lose partially populated costs or produce null ratios. Actual data and intended exceptional-case rules have not been established |
| Construction retries | First two actions use simple CASE in ORDER BY; third uses searched CASE | First two contain syntax outside the advertised compiler subset; third was accepted. This identifies a rejection trigger, not a complete parser replay of every possible rejection |
| Completion | Query artifact created, but next model reservation fails | Proven budget termination before the required explicit submission |

### Why the aggregation deserves attention

Joining two independent detail tables before summing produces combinations.
For a purely illustrative plant with two maintenance amounts (10 and 20) and
three alerts, the join has six rows and sums 90 instead of 30. This is a
relational counterexample, not a measurement of the solar database.

With non-null values and the same duplication factor, revenue and cost totals
can both inflate while their ratio (MROI) remains unchanged. Thus apparently
plausible MROI/priority output does not validate the requested monetary totals,
cost efficiency or revenue loss rate. An any-critical-alert MAX can also remain
unchanged under duplication. The failed reference check alone does not identify
this as the actual cause; database cardinalities and per-column mismatches were
not exported by that check.

### Why the compiler retries are a separate issue

The first two queries sort using a simple CASE expression (a selector followed
by WHEN values). The published tool subset supports searched CASE (WHEN boolean
conditions). The compiler rejects a CASE selector rather than silently rewriting
it. The accepted third query uses searched conditions. This is an interface
restriction encountered by the model; it does not establish that the compiler
corrupted the accepted query's meaning. Aliases or subqueries should not be
blamed on this evidence alone.

### What the budget result means

After the accepted query, the next model call needed 15072 work plus a 300-work
decoder allowance, with 5081 remaining. The final 94959 historical work includes
subsequent checking. The 300 in that message is not a new research reserve
fraction. More budget would permit more work, but merely submitting the existing
candidate would still fail the observed reviewed comparison.

## Decision for review

Keep native policy campaigns and automatic budget escalation paused. The evidence
now separates compiler compatibility costs, completion budget exhaustion, and an
incorrect executable candidate. It does not isolate a single general model defect.

If another diagnostic is approved, prefer a frozen, schema-supplied synthetic
probe with independent one-to-many detail tables and unequal detail counts,
including a no-alert case. Give public requirements without an answer query;
use independent expected totals. Such a probe can test aggregation competence
without exposing a native reference or repeatedly tuning on solar_2. It must be
labelled synthetic, charge all task-specific work, and retain the same explicit
submission contract. This is a proposal only: no new suite, model run, scheduler
submission, or changed worker guidance is part of this review.
