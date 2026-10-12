# Richer-task design review

Date: 2026-10-11. Scope: local public-contract and implementation review.
Decision: retain the three implemented cards as engineering candidates; the
four-task pilot is not ready for execution. This document is not an independent
review receipt, rights clearance, or experiment approval.

## Evidence and boundaries

Reviewed the three public task files, blocked fourth-candidate record,
`rich_tasks.py` expectation/composition functions, terminal evaluator, task loader,
planner-input construction, and richer-task controls. No private reference
solutions were copied into this report or into worker/planner inputs. No new
model run, SQL replay, source download, task edit, or task-version change was made.
The cluster's CPU and footprint successes are supplied evidence recorded in
[RICH_COHORT_PILOT.md](RICH_COHORT_PILOT.md), not independently reproduced here.

Public-file SHA256 values (these are file hashes, not qualification task hashes):

| Task | Public file SHA256 |
| --- | --- |
| Jaffle payment release | `c776bc882e3b88ed800259c1ca60b0e2417369d04f9fc744ae53235738d30038` |
| Energy single indicator | `9b16708cb0f9bb4b53fbb78b673e2e60d293513888fa0a10f81f287c62912e26` |
| GitHub topics client | `f6afd1b630ff1153e92e19f4e220047467f8817a84aa21eb3b16d54baf99a6a7` |

## 1. Jaffle payment release

The four outputs have a coherent consumer use: order-level payments, customer
summary, payment-method totals, and reconciliation. The public contract fixes
integer cents, inclusion of every recorded status, distinct equal-valued payments,
unpaid orders, customers without orders, sorting, and empty-input behavior.
The Python expectation code follows those rules, including counting a paid order
by payment-record presence rather than positive amount. The terminal evaluator
checks each output and bundle consistency separately from public monitoring.

Design limitation: several outputs repeat related aggregation work. A shared
per-order relation is useful but not required; independent implementations must
remain valid. Four outputs do not imply four substantively independent features
or an inherent four-worker optimum. Demo grounding cannot support claims about
real accounting systems or historical repository maintenance.

Review disposition: retain unchanged for bounded engineering review. A reviewer
must attest usefulness, source adaptation, and the exact task version; an
attributed rights receipt remains required. This local review does not supply it.

## 2. Energy single-indicator release

The five-output contract distinguishes selected measurements, observed-year
sums, present-row coverage, excluded rows, and a field contract. Real zero is
retained, null is omitted, and absent calendar years are not counted as present
null rows. Country-before-year-before-null exclusion precedence and public
floating tolerances are explicit. The expectation implementation follows these
choices; per-output checks are supplemented by reconciliation checks.

Design limitations: this is one indicator for two countries in a fixed window.
The field contract is a constant documentation obligation, not a fifth numerical
analysis. A larger output count must not be presented as five equally difficult
subtasks. The source guarantees at least one in-window row per selected country;
this is not a general missing-country reporting task.

Review disposition: retain the semantics, but keep execution blocked on task
review and underlying-provider rights evidence. The reported successful source
CPU qualification resolves a technical evidence gap; it does not establish
provider permission. Existing repository attribution records remain the basis
for identifying the outstanding review, not a new legal determination.

## 3. GitHub topics client package

The request makes its offline adaptation explicit: two shape validators and
inbound/outbound mappings, preserving case, order, duplicates and empty arrays.
It distinguishes unknown properties allowed by the selected schemas from extra
fields dropped by the mappings. Mapping inputs are bounded without imposing
that bound on validators. Terminal checks include a cross-output round trip.

Design limitations: request and response use the same names-array shape, and
both mappings are simple field renamings. The four obligations are useful bundle
checks but limited evidence of broad API integration difficulty. The task does
not contact GitHub, test server normalization, or implement a general OpenAPI
translator. It shares a source group with the fourth candidate.

Review disposition: retain as a small API engineering candidate. Do not expand
its difficulty claims to compensate for the missing fourth task. Attributed
rights and independent task review are still pending.

## 4. Fourth API candidate: completion requirements

`github-multioperation-integration` remains `draft-unexecutable-1`. Its six
listed outputs are proposed roles, not finalized obligations. The retained
source slice contains one PUT operation; no second operation or closure is
available through the approved task loader. There are no executable references.

Complete these steps in order before admitting it:

1. Inspect a bounded additional operation at the existing immutable source
   revision. Record the exact operation, parameters/body/responses and complete
   referenced-schema closure. Do not guess an operation from its name.
2. Review its source/rights evidence and bounded staging transformation. Preserve
   the existing topics slice and historical pins; version any new source contract.
3. Write a concrete offline user request with meaningful distinct deliverables,
   explicit supported semantics, input bounds and cross-output obligations.
   Do not duplicate validators merely to reach six outputs.
4. Verify that all semantics fit the existing schema/mapping/SQL tools. Unsupported
   constructs require a separately reviewed language change or a different task.
5. Supply two executable reference organizations, independent expected behavior,
   per-output negative controls, composition controls and original-source access.
6. Qualify source integrity, restricted execution, planner-visible input isolation,
   both reference organizations, and public prompt footprint under a new version.
7. Obtain the task-specific review/rights receipt, then rebuild the whole matched
   cohort proposal with compatible controls and exact scope approval.

This is an authoring specification, not fabricated source content. The fourth
candidate would add task breadth within GitHub, not a fourth source group.

## Experimental interpretation and next decision

The prospective synthetic-stock result establishes that planning, precommitted
branching and recovery can run end to end. It does not choose the best planner,
calibrate B0, validate these richer tasks, or establish independent task review.

Keep the four-candidate scope while completing the fourth task. Do not silently
run only the easiest admitted subset. If the user instead chooses a smaller
pilot, write a new explicit scope before any richer-task results and rebuild its
proposal/approval; preserve the original blocked scope as history.

For either design, keep requirement-level versus prompted-open planning matched
on workers, public inputs, common scoped JIT and total budget. Record planning
failure and unrun branches, average fault outcomes within each task/plan, and
report source groups. Useful reporting must distinguish output count, generated
units, active owners, declared edges, actual reads and executable bindings.
No independent-branch confidence interval or planner-superiority claim follows
from this small development pilot.

Next concrete work is bounded fourth-source inspection and task authoring, plus
attributed review of the three existing cards. There is no new GPU command to
run from this document. Existing stock approval is consumed by its completed run.
