# Synthetic aggregation findings — 2026-09-24

## Recorded outcome

User-supplied aggregate, competence audit and selected-artifact inspection identify
experiment `79d94d4217740a37c4b01c4cf2d12a47fc5689ab3391c5c48f952f181c2b44d1`.
Both episodes completed, submitted required artifacts and passed public
integration. There were no tool rejections, repairs or missing required artifacts.

| Task | Semantic result | Charged work | Model calls |
| --- | --- | ---: | ---: |
| sqlite-aggregation-payments | Passed | 5271 | 3 |
| sqlite-aggregation-independent_details | Failed | 5814 | 3 |
| Total | 1/2 | 11085 | 6 |

Both per-task ledgers reconcile with zero residual. Total work is summed from
those ledgers; a separate combined cost report was not supplied. The diagnostic
has one synthetic source group, seed 0, single/clean Protocol A, SQL-text interface,
8192 context, 2048 output, 12 actions and 100000 work per task. It is not a matched
comparison with the native 16K/24-action solar condition.

## Confirmed mechanism in the executed artifact

The failed task's selected approved query tree joins teams to payments and to
notices independently, then groups by team. It computes SUM(payment amount),
COUNT(notice ID), and SUM of a critical-notice indicator on the joined rows.
This multiplies independent detail rows before aggregation.

| Team | Payment records | Notice records | Expected amount / notices / critical | Stored amount / notices / critical |
| --- | ---: | ---: | --- | --- |
| 1 | 3 | 2 | 25 / 2 / 1 | 50 / 6 / 3 |
| 2 | 2 | 3 | 9 / 3 / 1 | 27 / 6 / 2 |
| 3 | 1 | 0 | 4 / 0 / 0 | 4 / 0 / 0 |
| 4 | 0 | 1 | 0 / 1 / 0 | 0 / 1 / 0 |

Team 1 has six combinations: each payment appears twice and each notice three
times. Team 2 also has six combinations: each payment appears three times and
each notice twice. These multiplicities account for all differing values in the
supplied rows. The no-notice and no-payment cases are correct. Output names and
ordering are correct; the audit reports both ordered and multiset value mismatch.
The failure is not explained by output aliasing, missing submission or exhausted
budget. Public artifact validity means usable provenance/structure, not correct
semantics.

The selected artifact is
`a758bba4424a29e12b125280254467a64ad5875b00c6a546de9fa40a1f79560a`
in episode
`9df5141366f305bc87e4d1383f0ee3682fbf77e58a7a7da9958fb52736d38d53`.
Its bindings are empty and its recorded validity is true. The extraction did not
match an original SQL action (`submitted_query_actions=[]`). Therefore the above
attribution is to the stored executable representation and observed values; no
claim of a newly verified raw-SQL-to-IR round trip is made. Missing action text
does not negate the directly inspectable join/aggregation structure.

## Interpretation and limits

Independent per-team aggregation before combining detail results is the general
relational approach that avoids this multiplication. This is a reviewer finding,
not a new worker hint or repaired benchmark solution. No artifact was rewritten,
submitted, rescored or supplied to another model call.

This establishes one specific clean-task semantic failure under this model and
interface. It does not establish universal model inability or a population failure
rate. It supports investigating the analogous structure in solar_2, but actual
native cardinalities and mismatch attribution remain unmeasured. The synthetic
result does not convert that native hypothesis into a demonstrated cause.

The earlier export error (`Unknown tool compatibility probe`) was in offline
competence-report routing. That fix selected the suite's own Python expectations;
it changed neither model execution nor terminal scoring. The re-export succeeded.
No native or historical 4B eligibility comparison is inferred from this suite.

## Accounting and decision

Artifact extraction was read-only, with no SQL/model execution and reported
analysis CPU 0.001803113s. The competence audit reported CPU 0.024689017s. Both
are separate analysis, not additions to the 11085 historical episode work.
The original GPU runs remain the only model evidence here.

Pause further experiments for review. In particular, this report does not
increase budgets, edit worker prompts, add a correction run or enable native
policy campaigns. The research advantage of recovery-aware delegation remains
unestablished. See the [full review](PROGRESS_REPORT_2026-09-24.md).
