# Implementation status and handoff

## Current decision: pause for progress review (2026-09-22)

The user requested review before running the prepared correction comparison.
[PROGRESS_REPORT_2026-09-22.md](PROGRESS_REPORT_2026-09-22.md) consolidates reported
cluster results, local checks, failure attribution and unresolved research gates.
Latest 27B synthetic feedback-enabled result: 4/4 at 21327 work, zero rejections;
feedback benefit is untested. Latest native solar result remains 0/2. No recovery
advantage has been established. Paired correction code is prepared and reportedly
pushed, but no submission/result has been reported. Pause further submissions
until the user decides the next step; earlier runbooks remain reference material.

## Prior continuation: paired correction diagnostic (2026-09-22)

The user-reported feedback-enabled run `ef260dc9...` passed 4/4 at 21327 work,
with zero rejections and reconciled ledgers. It did not exercise feedback and
matches the earlier synthetic total; native competence remains 0/2. The user
approved a separate two-draft × two-feedback-condition diagnostic. Frozen invalid
drafts are executed and charged before model turns, count against action/retry
limits, and are never labelled model output. Only feedback and condition labels
differ between the paired configs. Native and recovery enablement remain blocked.
See [SQLITE_CORRECTION_DIAGNOSTIC.md](SQLITE_CORRECTION_DIAGNOSTIC.md).
The paired read-only audit checks matched inputs and separates supplied-draft
rejections from model rejections. Local scripted controls passed; GPU results are
pending. No job, download, commit or push occurred in this implementation.

## Prior continuation: opt-in execution feedback (2026-09-22)

Implemented `sqlite-errors-v1` for the four synthetic tool probes only, with legacy
feedback as the default. Fixed categories/hints contain no raw SQL error text or
hidden evaluation information. Charges and retry limits are unchanged; correction
requires another charged model action. Manifest/calibration identity and aggregate
conditions distinguish the option. See [SQLITE_ERROR_FEEDBACK.md](SQLITE_ERROR_FEEDBACK.md)
and `configs/qwen27b-sql-error-feedback.json`. Scripted CPU checks passed; actual
model behavior is unmeasured. No GPU submissions, native enablement, commits or
pushes occurred. Native competence and the research comparison gate remain unmet.

## Prior continuation: public interface audit (2026-09-22)

The user-reported offline replay classified both query errors as unresolved
columns and confirmed the submitted view's comparison failure. Its 150 replay
work is separate from historical 171715 work (0/2). Public candidate inspection
identified missing source aliases/incomplete query structure and a multiplication
in place of division. See [SQLITE_INTERFACE_AUDIT.md](SQLITE_INTERFACE_AUDIT.md).
The shared instructions cover basic query syntax, but worker query failures lose
execution detail in a generic rejection. Three synthetic controls verify name
resolution, function arity and arithmetic preservation. No runtime/prompt/scorer
changes or GPU submissions occurred; improved feedback is a proposed fresh
condition, not an established remedy. Native competence remains unmet.

## Prior continuation: offline failure audit (2026-09-22)

The 24-action native run completed 0/2 at 171715 work. Solar_2 exhausted retries
after a capped response and two SQL execution errors; solar_M_3 submitted a
publicly valid view that failed terminal comparisons. Native competence remains
unestablished. Further GPU runs and budget increases are paused. The user
requested a bounded CPU replay: [NATIVE_FAILURE_AUDIT.md](NATIVE_FAILURE_AUDIT.md)
records the evidence, separate replay accounting and browser commands. No native
replay has run here; no worker feedback, scoring or executor policy is changed.


## Prior continuation: native 24-action condition (2026-09-21)

User-reported 27B synthetic competence passed 4/4; 16K preflight passed on A100
80GB. The two native16k episodes completed 0/2 at 113123 work: both hit the
12-action limit. Solar query read only; solar view created two executable views
but never selected a required artifact. Neither view has established correctness.
These reports supersede the unexecuted status of the historical checkpoints below.
[The new runbook](NATIVE_ACTIONS24.md) prepares only two single/clean native tasks
at 24 actions, preserving 100000 work and all other limits/scoring. Private
context archives support later diagnostics without influencing recovery snapshots.
No 24-action result exists, no job was launched here, and broader research stays
paused. Gate A remains unmet for these native tasks; gate B remains separate.


## Historical implementation checkpoint: opt-in 27B competence path (2026-09-20)

The user selected post-trained Qwen3.5-27B and skipped 9B after the audit.
[The ordered runbook](QWEN27B_COMPETENCE.md) prepares staging, fresh CPU qualification,
one full A100/H100 80-GB-class GPU preflight, exactly four existing single/clean
SQL probes, and later renewed solar references/two individual native controls.
No download, job, commit or push has been performed. No 27B fit/competence result
exists. Existing 4B defaults and historical observations remain unchanged.
The actual historical resolved 4B manifest/ledger is absent locally: comparison
is unmatched until raw evidence and source compatibility are reviewed.
The pin is `fc05daec18b0a78c049392ed2e771dde82bdf654`; loader source supports the
existing Transformers 5.3.0 interface, but real checkpoint qualification remains
pending. New shared accounting fields expose reservation/release without changing
charges. SILO, policy campaigns, calibration and broader expansion stay paused.
Gate A (clean worker competence) and gate B (meaningful decomposition/fair research
comparison) both remain open; passing A never establishes B.

## Prior checkpoint: audit pause after constrained run (2026-09-20)

The user requests a progress audit before choosing further work. Read the
[consolidated progress report](PROGRESS_REPORT_2026-09-20.md). It separates
cluster reports, local software checks, interpretations and outstanding evidence.

Cluster CPU decoder qualification passed six positive/four negative controls.
The subsequent constrained four-probe run completed **1/4 correct tasks** at
**28649** charged work; public integration passed **3/4**. View passed. CASE had
correct values but omitted `sign_label`; aggregate used addition instead of
sum/count; join repeated aliases and then exhausted two reasoning generations.
No recovery benefit, native competence or stronger-model result is established.
This supersedes earlier statements that decoder/GPU qualification was pending.

**Pause new experiments, model selection/downloads and interface tuning until the
user finishes the audit.** Prior runbooks describe historical procedures, not a
new submission instruction. Latest actual job/node/GPU details and full remote
ledger reconciliation remain missing from the supplied evidence. This update is
documentation only and launches no job.

## Prior checkpoint: reasoning scored 1/4; constrained actions prepared (2026-09-20)

The user-reported reasoning/2048 run
`3996c58d44658d42f2d94fd08517884c606e068b798aac077118365d995dda63`
passed only the view probe: **1/4**, **30715** charged work, all 15 generations
stopping at EOS. Aggregate used unsupported function/grouping forms; CASE and
join produced invalid JSON. Each failed after three rejected actions, before SQL
execution. These failures measure model/interface compatibility, not SQL reasoning
or recovery-policy quality. Further token/action increases are paused.

The user authorized the opt-in `sqlite-json-schema-v1` action mode and
`configs/sqlite-tool-compatibility-constrained.json`. Same four tasks, model,
thinking, 2048 shared output cap, context, action and total budgets; one GPU shard.
A pinned optional XGrammar decoder constrains action syntax after the generated
reasoning close. No task/gold data or valid artifact IDs enter its grammar. Runtime
SQL checks and terminal correctness remain separate. Fixed property order, bounded
whitespace, decoder overhead and this changed interface are explicit limitations.
A 300-work decoder allowance is reserved per call and reconciled from measured
CPU time within the existing budget; failed/unknown work remains charged.

[The new ordered runbook](SQLITE_CONSTRAINED_DIAGNOSTIC.md) first installs the
optional decoder while constraining existing packages, then checks actual token
masks on CPU with the staged tokenizer. This workspace lacks the optional stack;
native mask/compilation and GPU results remain unverified. Stdlib CPU tests use
scripted workers and test doubles. Do not submit if CPU qualification fails.
No GPU job, model download or push was performed locally. Native/SILO/policy runs
remain paused. Earlier runbooks below are historical; do not repeat them.

## Prior checkpoint: synthetic tools failed; view validation corrected (2026-09-19)

The user-reported four-probe Qwen3.5-4B/no-thinking run completed **0/4** at
**23786** charged work. All 16 generations stopped at EOS. Aggregate/join/CASE
failed construction or submission; the view was accepted despite a missing
FROM clause and required alias. This identifies both model/interface failures
and a public validation defect; it does not establish general model incapacity.

The executor now resolves every view with a zero-row read and disables SQLite's
legacy quoted-identifier-to-string fallback. Explicit public output names are
checked without rows or hidden evaluator information. The synthetic view's
structured contract now repeats its already public required column names.
Rejected views create no artifact and remain charged. Valid shape still does
not imply correct values; terminal scoring remains separate.

The user authorized preparing one fresh four-probe condition:
`configs/sqlite-tool-compatibility-reasoning.json`, pinned Qwen3.5-4B,
**thinking enabled, 2048 total generated tokens per call including reasoning**,
8192 context, 12 actions, 100000 work per episode, one shard/GPU. The old config
is preserved. This comparison changes reasoning, output allowance, public view
validation and structured contract presentation; it cannot isolate thinking.
The executor capability fingerprint changes, so prior native validation must be
repeated on CPU before any later native run. No reference material enters workers.

Follow [the updated runbook](SQLITE_TOOL_DIAGNOSTIC.md). Four passes would permit
considering a bounded native clean retry after fresh reference validation;
otherwise inspect failures once and reassess model/interface compatibility.
Native/pair/recovery competence remains unmet. Reasoning GPU results are pending;
no GPU job, push or download was performed locally.

## Prior checkpoint: native setting paused; synthetic tool diagnostic prepared (2026-09-19)

The cluster budget audit measured complete reviewed actions at **623 / 376 tokens
including one stop** for `solar_2` / `solar_M_3`, both below 768. Catalogue plus
contract/schema/creation/submission leaves seven document-page slots at 12 actions;
reading full schema and columns alone consumes those seven pages. These are
representation and conditional route measurements, not model competence.

The user then ran the authorized 24-action condition, array **1078011**, experiment
`5f4bcf452b24b0b2f267cb9c327e8742042034dd02692ac872c87154c342ff4a`.
It remained **0/2**, with both artifacts missing, at **131348** work (+79.1%).
`solar_2` stopped as `malformed` after 13 calls (10 reads, three identical capped
query attempts with JSON failure at column 256). `solar_M_3` used all 24 calls
reading and stopped as `action_limit`. Neither produced an artifact.

Pause further native action-limit increases and identical runs. The user authorized
preparing a four-probe synthetic compatibility diagnostic: aggregate/aliases,
join, CASE, and view creation/submission. The schema, relationship and natural-
language requirements are supplied directly. No solution trees or expected rows
enter worker views. It reuses the restricted executor, shared SQL instructions,
strict parser, normal accounting and terminal evaluator boundary. Each probe has
one output and a fresh episode/context; all four identities still exist, and one
model instance is reused on the single GPU shard. Defaults stay 12 actions,
768 output tokens, 8192 context, no thinking and 100000 work per episode.

The opt-in config is `configs/sqlite-tool-compatibility.json`, with an explicit
`sqlite_fixture_suite=tool_compatibility_v1`. Other configs retain arithmetic
fixtures by default. Labels `bc_sqlite_tool_compatibility_v1`,
`bc-sqlite-tools-v1`, and `synthetic_schema_supplied` keep these scores separate
from native/pair/arithmetic/SILO observations. Four probes share one synthetic
source group. Passing these simpler tasks would not prove native competence;
failure would not establish general model incapacity or a recovery-policy effect.
GPU results are pending. No job, push or download was performed locally.
See [the diagnostic runbook](SQLITE_TOOL_DIAGNOSTIC.md) and
[the validation record](VALIDATION.md#synthetic-tool-compatibility-diagnostic-2026-09-19).

## Prior checkpoint: stopping fixed; native budget audit pending (2026-09-19)

User-reported preflight **1078003** stopped at tokenizer EOS 248046 using
`[248044,248046]`. Array **1078005**, experiment
`cfb6d97fed8222c496b256acffa5880b3ba00a78cab355da0193ba575cd90fd3`,
completed **0/2**, both required artifacts missing, at **73320** charged work.
Of 24 generations, 22 stopped at 248046 and two hit the 768-token cap.
`solar_M_3` consumed all 12 actions reading. `solar_2` attempted a query twice;
both identical outputs were malformed at character 256, before truncation, and
also used unsupported expressions and nonexistent tables. Neither query executed.
The stopping correction is operationally verified; clean competence remains unmet.

The local read-only audit confirms four assumed actions for contract/schema/
creation/submission plus catalogue and document pages. One catalogue page leaves
seven of 12 actions for document pages and retries. This is conditional accounting,
not a necessary minimum or an independently selected successful read plan.
The validated reference trees and pinned tokenizer are unavailable locally in
this session; exact reference token counts remain **unmeasured**. Use the new
[CPU budget audit](RESEARCH_GATE.md#solar-budget-audit) on the cluster, without
weights, inference, SQL execution or jobs. Its private report includes only sizes,
public page counts and separately measured analysis costs, never reference text.
Reference-size fit does not prove model competence, and an oversized reference
is not a proof that every equivalent query is too long. No cap/model/prompt/scorer
change or further campaign is made. See [the evidence](VALIDATION.md#solar-post-eos-control-and-budget-audit-2026-09-19).

## Prior checkpoint: tokenizer/model stopping mismatch found (2026-09-19)

The user's pinned metadata identifies model text-config EOS **248044** as
`<|endoftext|>`, but tokenizer EOS **248046** as `<|im_end|>`, the chat template's
assistant-turn delimiter. There is no staged `generation_config.json`. The
backend previously supplied no explicit EOS override. This is a concrete
stopping mismatch and a plausible explanation for generated extra dialogue;
historical decoded text does not retain raw special-token IDs, so it cannot
prove that every failed turn crossed an actual delimiter.

The backend now explicitly passes the union of the loaded model's stop IDs and
the verified tokenizer turn-end ID, preserving existing model stops. Padding
falls back to the tokenizer's ID. Effective IDs and the final generated token
are logged; all generated tokens remain charged. Real calibration compatibility
binds `tokenizer-turn-eos-v1`. Pinned model/tokenizer files, prompts, sampling,
reasoning, action/output/context caps, evaluator and restricted tools are unchanged.

Focused CPU tests exercise the old continuation and corrected boundary using a
scripted token stream, plus invalid-token rejection and calibration binding.
Full suite: 167 tests (166 passed, one existing opt-in skip); shell, compilation,
isolated stdlib CLI and documentation syntax checks passed.
GPU improvement is untested; both earlier native controls remain 0/2. Next
review/deploy the correction and prepare a fresh two-task manifest, first checking
effective EOS IDs in the guarded preflight. No broad campaign or SILO rerun.
See [the metadata and correction](VALIDATION.md#tokenizer-turn-stopping-correction-2026-09-19).

## Prior checkpoint: document discovery progressed; solar still fails 0/2 (2026-09-18)

User-reported run array 1077718, experiment
`754c06ed06a51174619455ced15d592db875cbbdca1c39f15f157808801643c4`,
completed both tasks with both required artifacts missing. `solar_2` used the
public catalogue and read four relevant definitions, then repeated those reads.
One generation produced a simulated multi-role conversation, exhausted 768 output
tokens and was rejected as extra JSON data. `solar_M_3` skipped the catalogue,
reread its contract once and read `kb-0` through `kb-8` sequentially. Neither
attempted SQL/view creation or submission; both exhausted 12 actions.

Charged work: 40824 + 30665 = 71489, versus 56867 previously (+25.7%).
The interface enabled useful discovery in one trace but did not establish
competence. The length-limited output was not a truncated SQL solution.
Pause further identical/prompt-only GPU reruns and larger campaigns. Next inspect
the frozen tokenizer/chat-template/stopping metadata without loading weights;
the trace does not by itself prove a template or EOS defect, or general model
incapacity. A subsequent model/decoding/budget condition needs an explicit design.
Runtime, model settings and scoring are unchanged in this documentation update.
See [the follow-up trace record](VALIDATION.md#solar-document-discovery-follow-up-2026-09-18).

## Prior checkpoint: solar clean control exhausted actions on repeated reads (2026-09-18)

User-reported GPU preflight 1077667 passed. Run array 1077671 completed both
native solar tasks but scored **0/2** with both required artifacts missing.
Experiment: `39194c9de0eafc3e98c9cf02393afd7483f39476e36b61addf6afc2c6556b9f4`.
Each trace reads its own contract, inspects the schema, then rereads that contract
ten times. There are no document reads, SQL attempts, submissions or tool
rejections. All 24 generations ended with EOS, well below context/output caps.
This establishes an action-loop failure, not an evaluated wrong SQL query.
Charged work totals 56867 across the two completed failures.

The shared SQLite interface now removes the schema's repeated contract-read cue
and provides a charged, paged public-document title catalogue. Supporting-source
reminders remain; titles are not filtered/ranked using requirements or gold.
No model, decoding, action/budget cap, scorer or executor access changed. The
schema cue is a plausible contributor, not a demonstrated causal explanation.
Whether the correction improves real-model behavior is untested.

Local checks: 163 tests (162 passed, one existing opt-in skip), nine shell files,
compilation, isolated stdlib help and documentation syntax passed. The public
solar catalogue fits in one bounded observation; no GPU was run locally.

Next review/commit/push the correction, then create a fresh two-task manifest
with the same validated native inputs and frozen model settings. Stop at the
guarded GPU preflight dry run. Historical failures, the SILO pause, and broader
pair/policy gates remain. See [the trace and validation record](VALIDATION.md#solar-native-model-control-read-loop-2026-09-18).

## Prior checkpoint: solar CPU controls passed on cluster (2026-09-18)

The user reports `command_failed=false`, two admitted native tasks, and
`status=validated` for both `solar_2` and `solar_M_3`. Positive references, reset
repeatability, source integrity, missing-obligation rejection and corrupted-
obligation rejection all passed. The result is
`/dataset/suaq0001/beyond-consensus/private/livesqlbench/solar-check.NatDlH/native-validated.private.json`.
The actual batch job ID was not supplied; 1077655 was the preceding scheduler
dry-run identifier and is not recorded as an executed job.

Next prepare exactly two full single/clean model episodes with the frozen
`qwen35-4b-control` profile and the existing model lock, then run the guarded
GPU preflight dry run. These two tasks share one database source group. No model
competence, cluster pair result or second validated pair is established yet.
No broader policy comparison is ready. The strict scorer adaptation and SILO
pause remain unchanged. See [the reported cluster result](VALIDATION.md#solar-cluster-cpu-result-reported-by-the-user-2026-09-18).

## Prior checkpoint: solar references reviewed and locally validated (2026-09-18)

The user reports the private merged material hash verified on the cluster and
the four pinned solar files staged. The unapproved template is under
`/dataset/suaq0001/beyond-consensus/private/livesqlbench/staging.L7bFVF/`.

Offline manual review translated `solar_2` and `solar_M_3` into the existing
restricted SELECT/view trees. Both passed local CPU reference, reset, source
integrity, missing-obligation and corrupted-obligation controls. Their joint
two-obligation pair also passed locally. This is **two tasks from one database
group and one pair**, not the planned two-pair gate or model competence. The
pair command requested two and correctly reports one missing candidate slot.

The review preserves the pinned author SQL expressions, all outputs and full
result sets. It uses the existing strict result-comparison adaptation: the
author's view test samples rows with tolerance and different intermediate
rounding, so full upstream evaluator equivalence is not claimed. No upstream
Python test functions or raw downloaded SQL were executed. No scorer, budget,
limit or runtime code changed. All SQL ran through the fixed restricted executor.

Next upload the completed private review, register it, then reproduce the native
reference controls in a CPU batch job on the cluster. No cluster job has been
submitted by the assistant. See [the validation record](VALIDATION.md#solar-reference-review-and-local-cpu-controls-2026-09-18)
and [the current commands](RESEARCH_GATE.md#solar-review-transfer-and-registration).
The SILO setting remains paused and the broader native policy gate remains incomplete.

## Prior checkpoint: author supplement received (2026-09-18)

The user supplied the authors' JSONL supplement. All 270 unique IDs join exactly
to the hash-verified pinned public metadata. A private merged file was produced
outside Git, preserving all public fields and replacing only `sol_sql`,
`test_cases` and `external_knowledge`. The raw upload is now ignored by Git.

Under the existing nonempty-material checks, 268 records have complete nonempty
solution entries, 92 have tests, and 90 pass both presence checks. Two solution
records contain blank entries; 178 Query records have empty tests. No missing
material was filled in or removed. The proposed `crypto_M_2 + crypto_8` pair
remains blocked because `crypto_8` has no tests under the current gate.

This clears the supplement-format/ID-join prerequisite only. No database, SQL or
author Python test was executed. Databases, private evaluator translations and
reference/pair validation remain pending. Matching IDs do not certify semantic
compatibility with the pinned release. See [the inspection record](VALIDATION.md#author-supplement-inspection-2026-09-18).
Next transfer the merged private material to the cluster outside Git, verify its
hash, then stage the required public database files and review supported tasks.
The current SILO setting remains paused.

## Prior checkpoint: native materials next; SILO setting paused (2026-09-18)

The user completed the saved-ledger audit, eight original SILO controls and one
comparison using `submitted_final_value_v1` on the same eight development sources.
Both conditions completed with public checks passing, but scored **0/8 tasks and
101/480 values**. Explicit carry reduced local increment errors from 21 to 7 and
improved incoming-state consistency from 1/24 to 6/24 later segments; charged work
rose from 173439 to 185156 (+6.8%). All eight u1 boundaries remained inconsistent.
These are user-reported development observations, not confirmatory results or
evidence of recovery-policy performance. Detailed provenance and denominators are
in [VALIDATION.md](VALIDATION.md#cluster-follow-up-reported-by-the-user-2026-09-18).

The historical audit reconciled all eight matched recovery/JIT pairs: each
256-unit gap is a finite-search charge difference with zero non-search residual.
This confirms recorded accounting, not measured GPU time or an advantage.

Pause additional runs of the current 4B/no-thinking SILO setting. Continue native
SQLite material inspection, reviewed CPU references and actual pair validation
before clean-model competence. Local readiness remains `scoring_unavailable`
without a staging manifest; current cluster file availability is unknown. Follow
[the next commands](RESEARCH_GATE.md#ordered-next-commands). No scientific code,
defaults or scorer behavior changed in this documentation update.

## Prior checkpoint: recoverability research gate implementation (2026-09-18)

See [RESEARCH_GATE.md](RESEARCH_GATE.md) for the structural audit, precise deferral
assumptions, remaining cost gaps and narrowed command sequence. No preceding-cycle
browser commands have been run by the user. Historical remote ledger attribution
and native material/reference/model gates remain pending.

The 32 candidates are two exposure labels times 16 backup masks with fixed owners
and unit outputs. Linked numeric fixtures have two material dependency workflows;
independent SQLite fixtures and SILO have one. Opt-in organization conditions
expose the existing numeric alternatives with common JIT and a common configured
reserve. They do not implement native intermediate-view generation or certify a
native organization optimizer. Missing native variation/calibration fails closed.

The read-only ledger audit now reconciles stage entries and matched recovery/JIT
gaps without fabricating absent candidate/state/operation observations. The
`silo-battery --full-only` path prepares just eight original full controls; reuse
of frozen inputs is supported. Defaults, terminal failures, restricted SQLite,
four identities/one frozen model per shard and Slurm guards remain intact.

Local suite: **160 tests, 159 passed and one existing legacy integration skip**.
No cluster/GPU execution, real native validation, commit, push or download occurred.

## Prior checkpoint: bounded validation tooling (2026-09-17)

The incremental cycle is implemented locally; see
[VALIDATION_CYCLE.md](VALIDATION_CYCLE.md) for findings, the scientific conflict
and exact ordered commands, and [VALIDATION.md](VALIDATION.md) for test outcomes.
Prior changes and all reported cluster successes/failures below remain intact.

- Native: sanitized per-task readiness, at-most-ten deterministic development
  reference controls, reset/integrity/scorer diagnostics and two-candidate pair
  counts. Real native/pair validation remains blocked by unstaged databases and
  unapproved/missing author solutions/tests; only synthetic controls ran locally.
- Allocation: opt-in candidate/scenario traces, immutable ledger reconciliation
  and operation-cost measurements through the existing runner. Current equal
  allowance reproduction visits 256 recovery states versus zero JIT states.
  Matching the old aggregate gap is not raw-ledger verification.
- Scientific conflict: the current additive catalogue permits identical JIT
  preparation after an alarm; no preparation weakly dominates advance preparation.
  A strict nonzero selection cannot be honestly manufactured by cheaper warm
  costs alone. Actual preparation execution/restoration and JIT parity are tested
  separately with explicitly constructed behavior. No optimizer objective changed.
- SILO: offline attribution, generation/context metadata, frozen fresh-source
  full/local/actual-boundary modes, optional actual-final-value serialization,
  explicit 4B control/reasoning and unresolved 9B profiles. Default prompts/model
  and the structural monitor remain unchanged. Eight diagnostic sources imply
  at most 64 executions per condition; two separate confirmation sources are held
  out. No new real-model competence result exists.
- Metrics: public coverage/shape/integration, missing artifacts, evaluator,
  semantic correctness and execution status are separate additive observations.
  Legacy integration failure remains readable; historical absent facts are null.
- No jobs, large downloads, commits, pushes or messages to dataset authors.
  Cluster validation and the historical complete-ledger audit are pending.
- Final local validation: **151 tests (150 passed, one existing legacy opt-in
  skip), 28 focused tests passed, all nine shell checks passed**, plus compilation,
  diff hygiene and isolated stdlib CLI help. These are local engineering results.

## Migration checkpoint and cluster history (2026-09-17)

The latest attached implementation request supersedes CooperBench as the required
backend. We remain on Slurm; PBS and external-hosting paths are not active plans.
The required scope is executable data workflows. The prior uncommitted progress
and delegation evidence below is retained as history.

- Implemented: restricted SELECT/view trees and fixed CPU executor; SQLite
  fixture episodes through existing policies/accounting/provenance; pinned nested
  view bindings and common charged replay of surviving query templates.
- Implemented: local native staging/inspection, exact-record review scaffolds,
  reference and negative controls, common-state pair validation, and v2 manifests.
- Implemented: Prefix Sum/Pipeline Hash SILO adaptation with four workers,
  explicit protected/no-copy access, public-input/scorer parity checks and all
  original output obligations. Communication changes are labelled explicitly.
- Preserved: numeric diagnostics, original model/dependency settings, A/B budget
  separation, Slurm registry, one GPU per shard, four-GPU guard and snapshots.
- Locally validated: 123 tests (122 passed, one opt-in legacy sandbox skip), nine
  shell files, bounded CPU fixture/SILO mock CLI execution and missing-material
  failure paths. These are engineering checks, not model/benchmark results.
- User-reported cluster check: SQLite/model preflight job 1076633 passed on an
  A100 40 GB. After two failed smokes and the source-ID/JSON-action corrections,
  the third single-worker fixture smoke passed (1/1, all four outputs retained).
- User-reported pilot job 1076661 completed 32/32 episodes. Every policy passed
  2/4 clean tasks; ordinary/JIT/recovery passed 1/4 withholding tasks and
  replication passed 4/4. All episodes stayed below the 100,000-work cap with
  no reported reserve violations. Preparation was zero; replication costs
  include four planned duplicates per episode. No recovery advantage is shown.
- Confirmed diagnosis: ordinary clean fixture 0/u3 and fixture 1/u2 both read
  u0 instead of their assigned contract, then generated and submitted their own
  wrong query. Ordinary fixture-0 withholding repair repeated malformed column
  alias JSON three times. Public assignment reminders and column-syntax guidance
  were added; source access, strict parsing, accounting and scoring remain
  unchanged. See
  [the trace evidence and change](VALIDATION.md#assignment-reminders-and-column-alias-guidance-2026-09-17).
- Latest SQLite pilot result: revised pilot `d9813ae5...`, using four GPUs in
  `PA100q`, passed **32/32 episodes**: all four policies passed 4/4 clean and
  4/4 withholding tasks. No integration failures, false alarms, missing episodes
  or reserve violations were reported; preparation work remained zero. The
  bounded fixture competence/recovery check and grouped cost audit passed.
  Replication used 69.47% more total work than ordinary on clean tasks and
  22.87% more under withholding, with equal success. Four tool rejections were
  recorded (one per clean policy group); none occurred under withholding.
  Recovery selected no preparation and showed no success or total-cost advantage
  over ordinary/JIT.
  These are four synthetic source groups, not native benchmark findings. See
  [the successful pilot](VALIDATION.md#second-sqlite-fixture-pilot-passed-2026-09-17).
- First SILO Prefix Sum single/clean GPU smoke `9d2b2a4a...` completed but failed
  (0/1 success, no retained artifacts, full coverage, no reserve violations).
  Eight generated inputs validated beforehand. The trace confirms 12 rejected
  preparation outlines during implementation, with no source/shard reads or
  arithmetic answers. Explicit SILO action examples and operation-specific
  rejection guidance were added. This is not a recovery-policy comparison. See
  [the smoke record](VALIDATION.md#first-silo-prefix-sum-gpu-smoke-failed-2026-09-17).
- Second SILO smoke `055d8a4b...` completed with four retained segment artifacts,
  no public alarm and no repair work, but still 0/1 successes. The trace confirms
  zero tool rejections, public integration true and only 3/60 correct numerical
  outputs (0/4 complete segments). Local accumulation/scorer replay confirms
  arithmetic/indexing and incorrect predecessor carry use. Shared instructions
  were updated to state the public scalar recurrence and a model-performed
  increment check. Numerical tool
  feedback, model settings, input sizes and scoring remain unchanged. See
  [the second smoke](VALIDATION.md#second-silo-smoke-retained-all-segments-but-failed-scoring-2026-09-17).
- Third SILO smoke `9a7b999f...`, after the recurrence clarification, still
  completed with 0/1 successes, four retained artifacts and no public alarm or
  repair work. Its trace confirms 21581 work, zero tool rejections and public
  integration true. Accuracy improved from 3/60 to 15/60 values (u0 fully
  correct), but later segments still use wrong carries and have local arithmetic
  errors. Local scorer replay agrees. Pause prompt-only reruns and larger SILO
  pilots; a separately labelled model/reasoning competence condition would need
  an explicit change to the frozen setup. No runtime/configuration changes were
  made during this review. See
  [the third smoke](VALIDATION.md#third-silo-smoke-still-failed-complete-task-scoring-2026-09-17).
- Blocked externally: native benchmark validation needs actual databases,
  author-supplied nonempty solutions/tests and reviewed restricted translations.
  No actual native tasks or pairs have been validated. The crypto pair remains
  a candidate. Native/paired SQLite runs remain unexecuted; SILO clean model
  competence remains unestablished after the failed smoke.
- Deferred: new-environment semantic sabotage remains code-gated; this fixture
  pass does not enable it. Remaining SILO families, E2–E5, adaptive attacks and
  grouped inferential statistics are also deferred.

See [MIGRATION_SQLITE_SILO.md](MIGRATION_SQLITE_SILO.md) for M0–M4, precise subset
limitations, source pins, scorer differences and exact next commands. Local
test outcomes are recorded in [VALIDATION.md](VALIDATION.md).

## Historical checkpoint: delegation blocker and prior progress

The user's preceding request was to document the results and delegation problem.
Alternative hosting and migration work is deferred; no PBS, local-PC, Colab,
remote-sandbox or rented-GPU deployment has been validated or selected for execution.

- **Working:** Qwen3.5-4B GPU preflight, corrected single-task fixture smoke (1/1),
  and two 32-episode fixture pilots (32/32 each), all reported by the user.
- **Scientific interpretation:** no advance-preparation work or demonstrated
  recovery-policy advantage in those pilots. Repeated clean controls are not
  independent tasks. These are fixture results, not CooperBench results.
- **Partial containment evidence:** the basic Alpine probe passed on Jupyter and
  node13, but did not qualify the full coding sandbox.
- **Direct delegation blocked:** `sandbox-inspect` found no usable delegated
  cgroup v2 parent on Jupyter or inside Slurm job `1076414` on node13.
- **Inherited limits insufficient in the observed allocation:** job `1076418`
  requested 2 GiB but had `memory.max=max` and `memory.swap.max=max` at every
  readable ancestor. Its job cgroups lacked `pids.max`; higher groups were
  unlimited. CPU confinement to logical CPUs `24,152` was present.
- **Still pending:** a qualified repository sandbox, actual task image/source
  controls, and the first real clean CooperBench E0 episode. Four-policy coding
  execution remains unimplemented.

Writable delegation is required by the legacy repository adapter, not by the research
question itself. An alternative must establish equivalent tested resource and
isolation boundaries; none has been implemented. The existing fail-closed checks
remain in effect. See the [delegation evidence](VALIDATION.md#user-reported-delegation-and-inherited-resource-probes)
and [handoff](../handoff.md) for the exact observations and deferred options.

## Plan and bounded milestones

1. **A — CPU foundation:** schemas, accounting, provenance, bounded model/tool
   execution, terminal evaluation, mock episodes and regression tests.
2. **B — Model/cluster support:** inspected official interfaces, lazy Transformers
   backend, explicit staging, GPU diagnostics, Slurm dry runs and commit snapshots.
3. **C — Research behavior:** four policies, finite robust allocation, selective
   reconstruction, separate A/B protocols, manifests/resume/reporting and a
   versioned CooperBench loader with guarded execution.

## Delivered

- `src/beyond_consensus/`: typed records and strict JSON configuration; `bc` CLI;
  injected model and runtime components; deterministic mock and one real backend.
- Complete numeric workflow episodes and a clean single-agent E0 baseline.
- Ordinary fallback, JIT indexing/planning/reconstruction, independent selective
  replication, recovery allocation with optional preparation and reserves.
- Model/tool/search reservations, full re-prefill and retry charges, bounded attack
  timeouts, independent attacker accounting, public audit and terminal evaluation.
- Artifact/message dependencies, selective invalidation and context snapshots.
- Finite allocation and reconstruction with shared prerequisite accounting,
  comparison to an independent tiny-case oracle, and explicit search-limit status.
- Measured development calibration command and prediction errors; uncalibrated
  status and confirmatory-claim blocking when appropriate.
- Protocol A end-to-end execution; executable CPU Protocol B capture/comparison.
- Full planned manifests, deterministic IDs, grouped splits, task sharding,
  append-only events, atomic results, conservative checkpoint/resume, complete
  coverage reports and small sanitized exports.
- Model/data staging commands; offline, single-device Qwen backend and preflight.
- Slurm helpers with one shared per-user submission guard, immutable commit
  archives, resolved input hashes, environment inventory and no editable imports.
- CPU CI, platform-neutral Python entrypoint, pinned dependency specifications,
  LF enforcement, configuration templates, profiles and the browser-terminal runbook.
- Opt-in Apptainer/cgroup adapter, qualification/review commands and a clean
  integrated coding E0 worker/evaluator. CPU tests inject sandbox responses;
  actual cgroup/container qualification and a real coding episode remain pending.

## Legacy coding boundaries and deferred work

**C is complete for typed fixtures and manifest integration, not for real coding
experiments.** The exact external prerequisite is an approved, tested cluster
sandbox. The site must establish denied network/home/credential access, resource
limits, isolated workers and evaluator, and absent hidden tests/reference patches
including Git history. No such capability was available here. Docker/Apptainer
presence alone is insufficient. The loader fails closed; it does not execute a
stub and mark it successful.

The user subsequently reported a successful basic Apptainer probe on Jupyter
and supplied successful compute-node probe logs from `node13` (kernel
`6.8.0-51-generic`, private Apptainer `1.5.3-3.el8`). The probe checked an explicit
writable work mount, absence of two tested host paths, and a separate network
namespace with no routes. This establishes basic container operation on that
node, not the full sandbox contract above. Credential/socket isolation, resource
enforcement, worker/evaluator separation and hidden-material exclusion remain
unvalidated. See [VALIDATION.md](VALIDATION.md) for the image identity and evidence.

The clean coding E0 adapter and joint evaluator are now implemented behind
explicit image/site qualification, source review and baseline/reference controls.
They remain unvalidated on the cluster and cannot run from the old Alpine probe
alone. Four-policy coding decomposition/cost calibration cannot be inferred from
numeric fixtures and remains unimplemented. See [CODING_SANDBOX.md](CODING_SANDBOX.md)
for exact gates and commands. Real GPU fixed-state capture, restored-context reconstruction
routes, oracle localization, adaptive attacks, dependency-poisoning sweeps,
cross-family/Gemma validation, grouped confidence intervals, and E2–E5 are deferred.

Initial implementation validation used CPU and scheduler mocks only. Subsequent
user-provided cluster logs report a successful Qwen3.5-4B preflight on an A100
40 GB, followed by a completed but unsuccessful single-task fixture episode.
After correcting the invalid JSON examples, the user reported a successful
single-task GPU episode and two successful 32-episode fixture pilots: clean
versus withholding, and clean versus artifact sabotage. No advance preparation
was used; these runs do not establish a recovery-policy advantage. They do not
validate real repository isolation or CooperBench execution. See
[VALIDATION.md](VALIDATION.md) for the reported hardware, revision and limitations.

## Conflicts and scientific choices

- The repository initially contained only a README. No manuscript or AAI PDF was
  found in the repository or available local attachments. The supplied request is
  the scientific specification; its AAI facts are recorded as a documentation
  snapshot, not current scheduler information. No unavailable manuscript constraint
  is claimed to have been checked.
- The initial implementation followed the requested Slurm/browser workflow.
  The user later considered PBS H200 migration, then local/remote alternatives,
  then requested documentation first. The latest attached request now explicitly
  selects restricted SQLite/SILO data workflows on the original Slurm system.
  Historical PBS/hosting discussion is superseded; delegation stays a legacy
  repository-execution issue.
- The model card's mutable development installation example is replaced by an
  inspected release pin, with GPU validation explicitly pending.
- CooperBench's upstream namespace/commit observations differed across cached web
  pages and live metadata. `MODELS_AND_DATA.md` records both observations. Import
  requires explicit version metadata instead of silently equating them.
- Immutable source fixtures can make JIT as effective and cheaper. The default
  allocator is allowed to choose no preparation. Mock demonstrations provide no
  evidence that recovery improves research-task success.

## Validation

See `docs/VALIDATION.md` for the exact commands and outcomes from this workspace.
Regression tests exercise accounting, exposure, provenance, allocation, final-output
coverage, grouped splits, resume, protocol separation, sandbox blocking, sanitization,
and scheduler mocks. The opt-in repository-isolation integration test is skipped
without an explicit cluster sandbox profile; it executes real probes when one is supplied.

Next local commands and the separate online-cluster sequence are in
[LOCAL_TO_SLURM.md](LOCAL_TO_SLURM.md). Stop before experiments until the user has
reviewed the implementation, configured actual site facts and authorized submission.

## Separate native context feasibility condition (2026-09-21)

See [NATIVE_CONTEXT16K.md](NATIVE_CONTEXT16K.md) for the user-reported two
8K context-limit failures (62465 work, neither task scored), sanitized offline
read audit, and opt-in 16K qualification/preflight workflow. Defaults, historical
results, scoring, action/work caps and history handling remain unchanged.
The new condition has not run on a GPU. No recovery-policy conclusion follows.

### 2026-09-22: SQL input and finite graph implementation phase

The user authorized bounded local implementation after the review. The optional
SQL-text front end lowers to the unchanged restricted IR/executor, with separate
compiler and decoder qualification, matched native config preparation from the
actual historical manifest, and read-only comparison commands. Finite synthetic
plans now change units/prerequisites/owners in the existing episode engine and
use its JIT repair. A bounded generation API and selector are implemented and CPU-tested; real-model
generation, compatible calibration and native graph eligibility remain unqualified. Native
policy campaigns and supplied-draft correction stay paused. No new GPU results,
submissions, private-data downloads or commits were made.

See [phase scope, limitations and exact commands](SQL_INTERFACE_AND_DECOMPOSITION_PHASE.md).

### 2026-09-23: cluster SQL-text qualification blocked

User reports compiler qualification and 16K tree grammar qualification passed in
`sql-interface.lkdzxn`. SQL-text qualification stopped with `Valid action token
was masked`; no text qualification, native reference check or matched plan was
produced. Root cause is unresolved. The offline checker now reports the fixed
synthetic control, rejected token and independent whole-string grammar acceptance
on this failure. Grammar, runtime policy and qualification requirements are unchanged.
A fresh CPU-only text probe is needed; no GPU comparison is ready.

Follow-up probe `sql-text-mask.Q8UTqw` rejects control 1 at token 20 (34821),
including independent whole-string acceptance. It fails at JSON-escaped quotes
in a synthetic SQL payload. Inspected XGrammar v0.1.32 `GenerateString` source:
its min/maxLength production excludes backslashes and provides no escape branch.
The SQL-text decoder now uses ordinary JSON strings for `select_sql` only; the
runtime schema retains 16384 characters and the compiler retains 16384 UTF-8
bytes. Generation caps are unchanged. The decoder projection hash and length
policy are recorded in the text contract, so qualification must be renewed.
Quote/backslash/newline/Unicode CPU qualifier controls were added. Actual pinned
XGrammar/Qwen acceptance remains pending; no GPU run is authorized by this patch.

### Historical feedback resolution after successful CPU qualifications

User's `sql-interface-escapes.odflct` passed reference representability for both
solar tasks after completing preceding grammar/reference steps, then stopped at
matched configuration preparation because the historical config predates the
`sqlite_error_feedback` field. The supplied provenance is commit
`6e650d6468dd3b03ebca19a40c5a08c50a61e8db`, source digest
`d2ad7fc02b2fad1779809dbbfa97d17e64e5da7542185ee391db4a8618e571cd`, config hash
`8f306961f925d8082caf028743201e7c562d773aa487ebf1fdad4b0657d4a93b`.
Local Git reconstruction matches that complete source digest. Historical worker
error handling uses generic SQL failure feedback; the configurable alternative
was introduced in `a8d748d`. Matched-plan preparation resolves only this exact
experiment/source/config tuple to `generic`, records evidence and both historical
and resolved config hashes, and never rewrites the input manifest. Other omissions
remain blocked. Decoder/compiler/evaluator implementations did not change in this
compatibility patch. No native GPU comparison results have been reported.

### SQL-text GPU preflight 1080859: blocked probe, not native execution

User-supplied report for text experiment
`6b4e708894c9885f312473a5a05ff39f9bcdb6c0dbc3efd207d84799e623437c`
shows `command_failed=true` and `sql_frontend_probe.passed=false`. Qwen27B loaded
on A100-SXM4-80GB. Inspect-schema probes completed, including 14336 input tokens
and 89 generated tokens (early EOS); peak reserved memory was 62300094464 bytes.
The fixed executor smoke passed. Worst-case fit remains unestablished.
The SQL-query probe's exception branch discarded its generated action, so the
report cannot identify the failed envelope/compilation/execution stage. Updated
reporting retains this synthetic generation, failure stage and available compiler
and executor details. Prompt, caps and pass criteria are unchanged. Decoder lock
qualification fingerprints include the backend file: fresh CPU qualifications,
manifests and preflight are required for this source. No native comparison run
or model-competence conclusion follows from the failed preflight.

### SQL-text probe generation limit identified

The user-reported preflight for experiment
`2b78e29935a33d9ac8aec75d025f68e3b7ba5092da41877a83ff5c479b1b9dee`
failed before SQL compilation: 2048 output tokens, `finish_reason=length_limit`,
`constraint_complete=false`, zero constraint mask calls. The captured text debates
flat versus nested tool parameters. Its reasoning token partition is unknown;
no exact reasoning-token count is inferred. The original user-only preflight
prompt did not explicitly declare top-level envelope fields. An opt-in synthetic
probe prompt correction now specifies these fields and the public synthetic
schema, without providing the answer. It is labelled `explicit-flat-envelope-v2`
and records its prompt hash. Model/reasoning settings, token/work caps and native
worker prompts remain unchanged. Unfinished generations are classified before
JSON parsing and cannot invoke the compiler. This is a changed preflight prompt,
not a recovered success or a native competence result. Fresh backend qualification
is required; paired native runs remain paused.

### Completed matched interface development comparison and naming audit

User-provided read-only audit reports matching recorded fields for fresh tree
experiment `a11a562d9af5e460c728f5dcf68c18a381a3bf5bc29ec3267f36a71ead918341`
and SQL-text experiment
`a84f67659e998a2164836a8e66c2e8f06fecdda5a6e66805c72fbe563478143b`.
Both have two completed episodes with no missing shards. Tree: solar_2 failed
without an artifact (88572 work); solar_M_3 submitted but incorrect (83153 work).
Text: solar_2 failed without an artifact (80083 work); solar_M_3 passed (54388
work, zero tool rejections). Total charged work: tree 171725, text 134471,
including 60 text-compiler work. Uploaded ledger rows reconcile exactly.
These are repeatedly inspected tasks in one database, not confirmatory evidence
or a recovery-policy result.

The separately extracted rejected SQL matched compiler input hash
`193cc4a19c35292755351cd0685d1e15ba7c654e77a300cca12d6790e4582586`.
It treated table/ID-column pairs as qualified table names. Worker-visible schema
correctly distinguished table keys from column lists; public column documentation
used database|table|column paths. No evidence establishes that documentation
caused the confusion. The rejected query was also only a partial calculation;
it was never a successfully submitted complete answer. The text system prompt
retained a tree-only column example, an independently observed interface defect.

Implemented SQL-text-only naming instructions, labelled
`sqlite-sql-text-names-v2`, and removed the trailing tree column example from that
mode. Generic examples only: no benchmark names, joins, formulas or reference
answers were added. Default tree/SILO instructions, compiler/executor policy,
scoring and budget settings are unchanged. Any subsequent execution is a fresh
prompt condition with a new source-bound manifest, not a revision of the above
scores. No job, model generation, commit or push was performed locally.

### Naming follow-up and unsubmitted candidate audit (2026-09-23)

User-reported experiment
`0050bdb57f765b37009c875dfdc8062cfa20f9a0e3195bf6f14da508527f63fa`
retains 1/2 success: solar_2 failed (94959 work), solar_M_3 passed (56232).
Total 151191 is 12.4% above the previous SQL-text arm's 134471, with unchanged
success count. The solar_2 trace shows two compiler rejections, then successful
compilation/execution returning 1000 rows. It could not reserve the next model
call (15072 plus 300 decoder allowance; 5081 remaining). No required artifact
was submitted, and the intermediate query artifact was invalidated. This is
confirmed budget termination, not evidence that the query was correct.

Added an explicit `native-failure-audit --candidate-artifact` offline option for
an unselected, unbound solar_2 query. It checks recorded creation/execution hashes,
replays the unchanged IR through the bounded executor, checks recorded rows, and
runs the existing reviewed submitted-report comparisons. Invalidated status is
reported without changing it; no submission, worker feedback or historical score
write occurs. Replay work remains separate. No candidate correctness result is
yet available. See [UNSUBMITTED_CANDIDATE_AUDIT.md](UNSUBMITTED_CANDIDATE_AUDIT.md).
