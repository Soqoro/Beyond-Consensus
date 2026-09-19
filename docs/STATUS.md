# Implementation status and handoff

## Current checkpoint: synthetic tools failed; view validation corrected (2026-09-19)

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
