# Prospective richer-task pilot — implementation and review

## User-directed unreviewed development lane — 2026-10-12

After the audit, the user explicitly instructed proceeding with the four-task
experiments while deferring review. The opt-in `rich_development_unreviewed`
lane implements that instruction; `rich_pilot` and historical approvals retain
their existing review gates. This is a deliberate conflict with the earlier
no-waiver policy below, not a claim that independent or source/provider-rights
reviews occurred. All four pending, hash-bound review records remain pending.
The exact run approval accepts the deferral limitations. Aggregate and public
exports label the lane and deferred review status. No rights clearance is inferred.

Scope remains four tasks, two planners, at most 16 clean/F branches, concurrency
one, no retry or stock rerun. Source integrity, CPU controls, role locks, GPU
probe compatibility, scope, accounting and scheduling gates remain enforced.
Cluster CPU controls must renew against the changed admission code. The earlier
cluster result at `rr-four-task.y6a46O` passed 109 controls and all four footprints;
it is preserved, not edited into fresh qualification. No new model outcome or
submission is recorded here. See [the executable handoff](UNREVIEWED_COHORT_RUNBOOK.md).


Updated: 2026-10-12. Status: **four richer tasks executable; independent task/rights review and refreshed cluster CPU evidence pending**.

## Four-task comparison preparation — 2026-10-12

**Current disposition: implementation complete; cohort execution blocked on genuine
review receipts and refreshed cluster CPU/task-footprint evidence.** This section
supersedes the October 8 commands below. The prospective stock milestone is
complete: do not rerun stock. This session is local-only; no Slurm job, model
inference, training, commit or push was performed.

### Inventory and author review

Author self-review: Codex, implementation author, 2026-10-12. Scope: the public
contracts, pinned source slices, bounded interpreter, executable references and
negative controls. This is **not** an independent review, a rights determination,
or a signed human receipt. The dated October 11 review is retained as history.

| Task / version | Useful outputs and semantic breadth | Two executable author witnesses | Current evidence and admission |
| --- | --- | --- | --- |
| `jaffle-payment-release` / `0.2-rich-1` | Four related data-dependent views: per-order payments, customer totals, method totals, reconciliation. Moderate aggregation breadth; demo data, not real accounting. | Independent 4 units; shared 5 with a per-order relation consumed by three outputs. Artifacts actually differ. | Both pass on verified staged seeds plus authored variants; 8 missing/wrong controls pass. Independent task and rights receipts pending. |
| `energy-single-indicator-release` / `0.2-rich-1` | Five outputs: generation rows, window totals, coverage, exclusions, constant field contract. Small/moderate single-indicator job; the constant contract is documentation, not a fifth numerical problem. | Independent 5 units; shared 6 with selected-row relation and three consumers. | Both pass on authored fixtures locally. Earlier cluster staged-source success remains historical; renewed same-submission controls must use that staged data. Task, rights and underlying-provider review pending. |
| `github-topics-client-package` / `0.2-rich-1` | Four outputs: request/response validators and two field-renaming mappings. Small, related array semantics. | Independent 4 units; shared 5 with executable array-schema bindings. | Both pass using pinned topics material, 10 missing/wrong controls pass. Task and rights receipts pending. |
| `github-multioperation-integration` / `0.2-rich-2` | Five outputs: topics request/response validators, languages response validator, combined repository summary, outbound topics body. Moderate: arrays versus arbitrary-key integer objects; no claim of six-agent difficulty. | Independent 5 units; shared 6, with four actual bindings to one array-schema helper. | Both pass using the new pinned closure, 41 terminal checks per organization, 13 missing/wrong controls. Task and rights receipts pending. |

There are four executable candidates and **three source groups**. Both API cards
use `github/rest-api-description`. The first three public/private file hashes and
versions are unchanged. The old `blocked-api-integration.json` is historical;
it is not a fifth task and is not used as an executable fallback.

For all four, cross-output checks evaluate one explicitly bound submission.
Destructive tests copy that submission. Wrong semantics are republished through
the trusted publisher so valid receipts reach the evaluator; a corrupt version
hash alone is not counted as a semantic mutant. No JIT or worker regeneration
rescues the controls. Source/reset checks remain separate. Python SQL expectations
are independent reductions; both organizations still share the restricted
compiler/executor, and API tests share the bounded interpreter. Correlated
implementation defects remain possible.

#### Inspected second operation and source closure

At GitHub revision `4377b4f4845badf28d13464dfb3042c6cf0e3a1f`, inspected
`GET /repos/{owner}/{repo}/languages` alongside `PUT /repos/{owner}/{repo}/topics`.
Both have required string owner/repo path parameters. GET has **no invented
request body**. Its 200 response is an object with arbitrary keys and integer
values; empty objects are allowed, null/string/boolean/nonintegral values fail.
The pinned schema declares no minimum: the offline validator therefore accepts
negative integers and integral JSON numbers. It does not enforce unstated live
server semantics. Topics preserve the existing required `names` array of strings,
case/order/duplicates, empty arrays and allowed extra schema properties.

The new offline consumer combines both responses as `topics` and `language_bytes`;
the outbound topics body keeps only `names`. Mapping inputs are bounded to 128
names and 128 language entries; these bounds are not imposed on the validators.
Mappings preserve all accepted dictionary entries. Cross-output fixtures cover
empty and boundary inputs, integer distinctions, missing fields, unrelated fields
and end-to-end composition. No live API calls or repository scripts execute.

New pack `github-metadata` preserves the old `github` pack. Its two operations
and complete local component closure are selected by public API paths, never by
reference answers. Owner/repo parameters, referenced examples, success/error
schemas and responses are retained. Unsupported/external refs fail staging.
Only the documented success payloads are the task's validator outputs.

- Upstream specification: 12,964,430 bytes, SHA256
  `b8ca03764f54058ec40e2b61e048a4518ee88e943ac04d393b1757094c895aad`.
- New retained closure: 3,839 bytes, SHA256
  `a0899be4025fc3632482762492ea45fbe95943af5cd57d8a2c19007edefa819d`.
- Public task file SHA256:
  `44811d31ffcf3bd248c224bc64442b169fb366beaf3b6b1801b6d162dc0721af`.
- Complete upstream/retained/license pins are in
  [source_registry.json](../benchmarks/reporecourse/source_registry.json).
  Sources staged under `/tmp` locally; no downloaded source data added to Git.

### Readiness and exact remaining actions

| Gate | State | Action / responsible evidence |
| --- | --- | --- |
| Fourth task expressible in current artifact language | CPU references pass | Independent reviewer checks the new public contract and negative cases; no language expansion. |
| Independent task review, all four | **Missing** | Four task-hash-bound receipts with independent reviewer identity/role, date, evidence and `this_cohort_only` scope. CPU success and user experiment consent are insufficient. |
| Source rights, all four | **Missing** | Source-hash-bound attributed rights reviewer, role, date and documented basis covering each task's adaptation. Two GitHub cards share a source, but each receipt must cover its task. |
| Energy provider terms | **Missing** | Review retained electricity-generation provenance and applicable original-provider terms. Existing OWID license does not resolve this. See [source attribution](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md). |
| Current controls and final task footprints | Local controls run; cluster renewal pending | Run the existing CPU wrapper below on all four final cards and pinned staged sources. Measure public prompts plus evaluator-side reference serialization; no private reference text is exported. |
| Worker/planner grammar | Existing locks reusable if exact compatibility passes | Wrapper checks fingerprints, versions, 7 identities, context and role caps. Does not fabricate new grammar test results. |
| GPU footprint | Reuse compatible `e923cb…` evidence | Read-only audit and exact probe-contract comparison below. Offline task/evaluator/report changes require CPU controls; worker/engine/scope/grammar/backend/resource changes still block reuse. No automatic extra GPU probe. |
| Cohort approval | User authorized this bounded phase; exact manifest not frozen yet | Fill exact proposal approval after all blockers resolve. No engineering review waiver is accepted for `rich_pilot`. No repeated per-branch permission. |

### Frozen design and reporting

Task order is Jaffle, Energy, topics, multioperation; within each, requirement-level
then prompted-open; within each valid plan, clean then its prospectively sampled F.
Eight configuration shards, concurrency **one**, sixteen scheduled logical
conditions. A shard refuses to start ahead of an unfinished predecessor. Slurm
array ordering is not assumed: an out-of-order dispatch stops before generation
and needs inspection; never automatically resubmit it as a new scientific attempt.
The first task's four scheduled conditions are the operational checkpoint; no
extra smoke task or clean-success gate is introduced.

Requirement-level uses public requirements, cyclic assignment over seven workers,
measured allocation CPU and zero model tokens. Prompted-open has one sequence
per task, up to eight calls with two structural revisions; no witness menu.
Both use max 24 units and 24 actions per assignment, the existing public rejection
feedback, fresh assignment contexts, original-source access, version bindings,
public monitor and common scoped JIT. Later history overflow still fails rather
than silently truncating. Worker model, scorer and caps do not change by planner.

Envelope: Qwen3.5-27B revision `fc05daec18b0a78c049392ed2e771dde82bdf654`, BF16,
thinking on, deterministic decoding, context 16384, worker output 2048 and planner
output 6144. One frozen model on a full qualified 80-GB-class GPU per shard.
Seven logical identities; fewer active owners allowed. Each branch has 100000
logical tokens and 1200 charged CPU seconds. Aggregate cap sums 1.6 million tokens
and 19200 CPU seconds are not wall/GPU forecasts or calibrated B0.

Seed index 1 uses the existing separate hashed planner/execution/target/attack
streams. Tasks are an explicitly ordered census, not sampled using a fabricated
additional task RNG. Task identity is bound into each configuration/request.
Deterministic decoding does not create independent seed replications. One owner
is uniformly drawn from the frozen plan's meaningful terminal/ancestor producers
before clean outcomes; idle identities are excluded. No clean-pass filtering,
hidden-score targeting, retargeting, or reuse of clean artifacts in F.

Summary retains scheduled clean/F rows for invalid planning (failure with no
invented target/worker execution), unrun/interrupted rows, all-run costs,
uncertain/reserved usage, correctness, conformance and cap status separately.
It reports declared imports, observed reads, saved executable bindings, original
source use, repair assignments and scope overlays. A binding is not proof of
causal necessity; an artifact read is not an execution binding.
`source_only_versions` means no saved executable artifact bindings; constants
also meet that definition. Source-read events must be consulted separately. Per-source and
per-task/planner/track completion accompany costs from failures as well as successes.
Unknown costs stay unknown. Post-alarm costs are a subset of totals. Physical
planning reuse and per-branch logical planning inheritance remain distinct.

**Current results for the proposed comparison:** all eight task/planner
configurations, and therefore all sixteen conditions, are unrun. There are no
new planner costs, F outcomes, success rates or calibration estimates to report.
The completed stock evidence below remains separate. This preparation resolves
a missing executable-task/qualification gap, not which planner is better.

### Prospective result ledger (before execution)

| Task | Requirement clean | Requirement F | Prompted clean | Prompted F | New model costs |
| --- | --- | --- | --- | --- | --- |
| Jaffle payment release | Unrun | Unrun; target unresolved | Unrun | Unrun; target unresolved | Unmeasured |
| Energy single indicator | Unrun | Unrun; target unresolved | Unrun | Unrun; target unresolved | Unmeasured |
| GitHub topics | Unrun | Unrun; target unresolved | Unrun | Unrun; target unresolved | Unmeasured |
| GitHub multioperation | Unrun | Unrun; target unresolved | Unrun | Unrun; target unresolved | Unmeasured |

Coverage is 0/16 observed, not a 0% success estimate. No invalid plans, budget
failures, interventions or successful recoveries have yet been observed in this
cohort. Planning/primary/post-alarm totals and conformance are unknown. The
permission and review blockers above precede worker execution.

### Local verification record (2026-10-12)

Worktree base: `e9139a401efd900a0a96e08ad1fc0c01dd3f11f3`; changes are
uncommitted. Existing uncommitted reporting fixes and both October 11 review
files were preserved. This is not a claim that a later cluster HEAD is current.

| Check | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 455 tests: 426 passed, 29 skipped; no failures/errors. |
| Pinned `scripts/check_rr_cohort.py` | 109 passed, zero skips/failures/errors on the unchanged final code tree. |
| Pinned additional runtime/Track F/SQL tests | 56 passed, zero skips. |
| New richer-task focused suite | 9 passed with pinned dependencies, including valid-receipt semantic mutants. |
| Final cohort reporting/review focused suite | 30 tests: 29 passed; its one optional execution test is covered by the pinned cohort suite. |
| `python scripts/check_shell.py` | 10 shell files pass; LF, strict handling, help/dry-run and `bash -n`. |
| Current runbook blocks | All 9 cluster handoff blocks and the local verification block pass `bash -n`; cluster dispatch is not executed locally. |
| `python -m compileall -q src tests scripts` | Passed. |
| `git diff --check` | Passed. |
| `python -I -S scripts/bc.py --help` | Passed with site packages disabled. |

Pinned child dependencies were SQLGlot 27.28.1, jsonschema 4.25.1 and
referencing 0.36.2 in `/tmp/bc-rich-cpu`. No model weights or tokenizer are present
locally. Staged-source qualification ran locally for Jaffle and both GitHub
cards. Energy source qualification and final tokenizer measurements are explicit
cluster prerequisites; fixture tests do not substitute for them.

The standard-library skips are listed below. All 28 optional CPU cases were
subsequently exercised by the pinned cohort or additional suites; the separate
legacy container/cgroup sandbox test remains skipped without an explicitly
approved sandbox profile. That legacy sandbox is not required by this data path.

- `test_reporecourse.PublicSQLInterfaceTests.test_actual_compiler_distinguishes_undeclared_object.test_actual_compiler_distinguishes_undeclared_object`
- `test_reporecourse.VerticalTests.test_all_baselines_clean_and_announced_loss.test_all_baselines_clean_and_announced_loss`
- `test_reporecourse.VerticalTests.test_both_families_witnesses_and_negatives.test_both_families_witnesses_and_negatives`
- `test_reporecourse.VerticalTests.test_existing_journal_runner_adapter_with_explicit_test_backend.test_existing_journal_runner_adapter_with_explicit_test_backend`
- `test_reporecourse.VerticalTests.test_fixed_state_graph_and_equal_remaining.test_fixed_state_graph_and_equal_remaining`
- `test_reporecourse.VerticalTests.test_independent_benchmark_execution_without_bc.test_independent_benchmark_execution_without_bc`
- `test_reporecourse.VerticalTests.test_replica_checkpoint_preserves_primary_and_resumes.test_replica_checkpoint_preserves_primary_and_resumes`
- `test_reporecourse.VerticalTests.test_resume_and_latest_bound_not_best.test_resume_and_latest_bound_not_best`
- `test_reporecourse.VerticalTests.test_schema_rebind_reuses_program_preserves_exposure.test_schema_rebind_reuses_program_preserves_exposure`
- `test_reporecourse.VerticalTests.test_shared_plan_repair_and_no_forced_regeneration.test_shared_plan_repair_and_no_forced_regeneration`
- `test_reporecourse_scoped.ActualExecutionTests.test_both_families_all_topologies_pools_2_and_8_and_loss.test_both_families_all_topologies_pools_2_and_8_and_loss`
- `test_reporecourse_scoped.ActualExecutionTests.test_generated_plan_to_restricted_execution_through_model_interfaces.test_generated_plan_to_restricted_execution_through_model_interfaces`
- `test_reporecourse_scoped.ActualExecutionTests.test_stock_old_reuse_denied_corrected_and_wrong_conformant.test_stock_old_reuse_denied_corrected_and_wrong_conformant`
- `test_reporecourse_track_f.ExecutorControls.test_actual_journal_runner_three_shards_and_overcap_correctness.test_actual_journal_runner_three_shards_and_overcap_correctness`
- `test_reporecourse_track_f.ExecutorControls.test_both_losses_resume_visibility_wrong_repair.test_both_losses_resume_visibility_wrong_repair`
- `test_reporecourse_v2.ExecutableFamilies.test_both_families_all_pools_reference_clean_and_loss.test_both_families_all_pools_reference_clean_and_loss`
- `test_reporecourse_v2.ExecutableFamilies.test_common_jit_rebinds_unchanged_consumer_without_model_call.test_common_jit_rebinds_unchanged_consumer_without_model_call`
- `test_repository.RealSandboxTests.test_actual_isolation_and_cleanup.test_actual_isolation_and_cleanup`
- `test_rr_cohort.Prospective.test_both_planners_use_actual_scoped_engine_and_common_repair.test_both_planners_use_actual_scoped_engine_and_common_repair`
- `test_rr_open_clean.Boundaries.test_actual_scoped_engine_with_shared_model_interface_double.test_actual_scoped_engine_with_shared_model_interface_double`
- `test_rr_open_fault.Contracts.test_both_faults_real_engine_with_cpu_backend_double.test_both_faults_real_engine_with_cpu_backend_double`
- `test_rr_rich_tasks.Cards.test_actual_schema_both_extreme_mutants_fail.test_actual_schema_both_extreme_mutants_fail`
- `test_rr_rich_tasks.Cards.test_both_families_two_real_reference_paths_and_reset.test_both_families_two_real_reference_paths_and_reset`
- `test_rr_rich_tasks.Cards.test_fault_persistent_loss_and_originals_not_starved.test_fault_persistent_loss_and_originals_not_starved`
- `test_rr_rich_tasks.Cards.test_missing_output_not_rescued_and_changed_source_rejected.test_missing_output_not_rescued_and_changed_source_rejected`
- `test_rr_rich_tasks.Cards.test_multioperation_distinct_artifacts_and_same_bundle_mutants.test_multioperation_distinct_artifacts_and_same_bundle_mutants`
- `test_sql_text.CompilerTests.test_rejects_and_resource_bounds.test_rejects_and_resource_bounds`
- `test_sql_text.CompilerTests.test_runtime_fail_closed_charges_and_wrong_query.test_runtime_fail_closed_charges_and_wrong_query`
- `test_sql_text.CompilerTests.test_synthetic_semantic_parity.test_synthetic_semantic_parity`

One intermediate 109-test control run failed `frozen_runtime_changed` because a
reporting module was edited while its reference matrix was still running. The
rejection was retained and diagnosed; the final control run was performed with
code edits stopped. No runtime hash check or resource bound was weakened. A
standalone additional-test invocation initially omitted `PYTHONPATH=src` and
failed import; the corrected invocation passed all 56 tests. These are local
software checks, not scientific attempts or model retries.

Exact local checks (the optional interpreter path refers to this session's
pinned environment):

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
BC_LOCAL_CONTROLS="$(mktemp -d /tmp/rr-cohort-controls.XXXXXX)"
/tmp/bc-rich-cpu/bin/python scripts/check_rr_cohort.py \
  --output "$BC_LOCAL_CONTROLS/controls.json"
PYTHONPATH=src /tmp/bc-rich-cpu/bin/python -m unittest \
  tests.test_reporecourse tests.test_reporecourse_track_f tests.test_sql_text -v
```

Do not change code while the hash-bound controls run. Local JSON evidence and
logs remain outside Git. A fresh frozen cluster checkout must produce its own
controls and task-footprint records before approval; local test counts are not
substitutes for those source-bound receipts.


### Current browser-terminal handoff (run in order)

The user reviews and commits/pushes the local diff first. These commands use
existing staged assets and the existing runner. All reports stay outside Git.
Do not use the historical stock/submission commands further below.

#### 1. Freeze the pushed source and stage only the new bounded slice

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RICH="$BC_STORAGE/diagnostics/rr-rich-cohort.5tpWjC"
export BC_FOUR_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_FOUR_CLUSTER="$HOME/Beyond-Consensus/configs/cluster.qwen27b-na100.local.json"
export BC_FOUR="$(mktemp -d "$BC_STORAGE/diagnostics/rr-four-task.XXXXXX")"
(
set -euo pipefail
set -o noclobber
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: preserve exports outside Git and review local edits.\n'
    exit 1
fi
test -x "$BC_PYTHON"
test -s "$BC_RICH/cpu/worker-lock.json"
test -s "$BC_RICH/cpu/planner-lock.json"
test -s "$BC_FOUR_CLUSTER"
git rev-parse HEAD > "$BC_FOUR/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_FOUR/source"
git -C "$BC_FOUR/source" checkout --detach "$(cat "$BC_FOUR/source-commit.txt")"
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py rr-source-plan --packs github-metadata \
  --sources "$BC_FOUR_SOURCES" --output "$BC_FOUR/source-plan.json"
"$BC_PYTHON" -m json.tool "$BC_FOUR/source-plan.json"
)
printf 'Keep this directory: %s\n' "$BC_FOUR"
```

Inspect that the plan contains only the pinned `github-metadata` pack with the
12,964,430-byte specification plus the bounded README/license. Then:

```bash
(
set -euo pipefail
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py rr-stage --packs github-metadata \
  --sources "$BC_FOUR_SOURCES" --output "$BC_FOUR/source-stage.json"
)
```

#### 2. CPU qualification in an allocation, reusing compatible role locks

```bash
(
set -euo pipefail
set -o noclobber
test -s "$BC_FOUR/source/experiments/qualify_reporecourse.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 --job-name=rr-four-cpu \
  --chdir="$BC_FOUR/source" --output="$BC_FOUR/cpu.out" --error="$BC_FOUR/cpu.err" \
  "$BC_FOUR/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_FOUR/source" --cohort-controls --rich-only \
  --sources "$BC_FOUR_SOURCES" --output "$BC_FOUR/cpu" \
  --worker-lock "$BC_RICH/cpu/worker-lock.json" \
  --planner-lock "$BC_RICH/cpu/planner-lock.json" > "$BC_FOUR/cpu-job.txt"
cat "$BC_FOUR/cpu-job.txt"
)
```

After completion:

```bash
sacct -j "$(cut -d';' -f1 "$BC_FOUR/cpu-job.txt")" --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_FOUR/cpu.err"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_FOUR'])/'cpu'
for name in ('cohort-controls','role-lock-reuse','jaffle-payment-release',
             'energy-single-indicator-release','github-topics-client-package',
             'github-multioperation-integration'):
    p=r/(name+'.json')
    d=json.loads(p.read_text())
    print(name, d.get('status'))
    expected='passed' if name=='cohort-controls' else 'compatible' if name=='role-lock-reuse' else 'cpu_qualified_review_pending'
    if d.get('status')!=expected: raise SystemExit('STOP: CPU prerequisite failed')
    if name not in ('cohort-controls','role-lock-reuse'):
        f=json.loads((r/(name+'-footprint.json')).read_text())
        if f.get('status')!='passed': raise SystemExit('STOP: footprint failed: '+name)
print('Four technical qualifications present; review receipts remain separate.')
PY
```

No automatic cap increase or requalification loop follows a failed footprint.
The new output measurements use representative full-width version IDs and one
stop token. They do not prove all reasoning/history/tokenizations fit.

#### 3. Reuse audited task-free GPU evidence; assemble a blocked review packet

```bash
export BC_FOUR_PREFLIGHT="$BC_STORAGE/outputs/qwen27b-na100/e923cb200f4835deb8457fe14e7bf50ee488b5b8be5d5070819bbaf75954f8e1-preflight"
(
set -euo pipefail
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py rr-open-footprint-audit \
  --run "$BC_FOUR_PREFLIGHT" --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_FOUR/footprint-audit.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_FOUR'])
tasks=('jaffle-payment-release','energy-single-indicator-release',
       'github-topics-client-package','github-multioperation-integration')
def read(p): return json.loads(p.read_text())
e={'controls':read(r/'cpu/cohort-controls.json'),
   'tasks':{t:read(r/'cpu'/f'{t}.json') for t in tasks},
   'task_footprints':{t:read(r/'cpu'/f'{t}-footprint.json') for t in tasks},
   'footprint_audit':read(r/'footprint-audit.json'), 'reviews':{}}
with (r/'evidence.pending.json').open('x') as h: json.dump(e,h,indent=2);h.write('\n')
PY
"$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest --lane rich_pilot \
  --sources "$BC_FOUR_SOURCES" --model-lock "$BC_FOUR/cpu/worker-lock.json" \
  --planner-lock "$BC_FOUR/cpu/planner-lock.json" \
  --evidence "$BC_FOUR/evidence.pending.json" --output "$BC_FOUR/proposal.pending.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
  --manifest "$BC_FOUR/proposal.pending.json" --model-lock "$BC_FOUR/cpu/worker-lock.json" \
  --output "$BC_FOUR/review.pending.json"
"$BC_PYTHON" -m json.tool "$BC_FOUR/review.pending.json"
)
```

**Stop here for the four independent task and attributed rights receipts.**
`task_review_templates` contains exact task/source hashes and pending fields.
Reviewers supply their genuine identities, roles, dates and evidence; Energy
also needs `underlying_providers=approved` with its documented basis. Save a JSON
object keyed by all four task IDs as `$BC_FOUR/reviews.json`. Do not substitute the
campaign user's consent for an independent reviewer or turn CPU success into
rights clearance. This gate comes from the four-task specification and the
existing source/provider protocol, not a new blanket legal requirement.

#### 4. Freeze reviewed evidence and the exact authorized scope

Only with genuine completed receipts:

```bash
(
set -euo pipefail
cd "$BC_FOUR/source"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_FOUR'])
e=json.loads((r/'evidence.pending.json').read_text())
e['reviews']=json.loads((r/'reviews.json').read_text())
if set(e['reviews'])!=set(e['tasks']): raise SystemExit('STOP: all four reviews required')
with (r/'evidence.json').open('x') as h: json.dump(e,h,indent=2);h.write('\n')
PY
"$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest --lane rich_pilot \
  --sources "$BC_FOUR_SOURCES" --model-lock "$BC_FOUR/cpu/worker-lock.json" \
  --planner-lock "$BC_FOUR/cpu/planner-lock.json" \
  --evidence "$BC_FOUR/evidence.json" --output "$BC_FOUR/proposal.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
  --manifest "$BC_FOUR/proposal.json" --model-lock "$BC_FOUR/cpu/worker-lock.json" \
  --output "$BC_FOUR/review.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_FOUR']);review=json.loads((r/'review.json').read_text())
print(json.dumps(review,indent=2))
if review['blockers']: raise SystemExit('STOP: resolve listed blockers; no partial cohort')
p=json.loads((r/'proposal.json').read_text())
assert p['lane']=='rich_pilot' and len(p['configurations'])==8
assert p['maximum_execution_branches']==16 and p['maximum_model_planning_sequences']==4
print('Ready for exact cohort approval; no model executed.')
PY
)
```

The user has authorized this bounded phase. Record that authorization against
the now-reviewable `approval_template` as `$BC_FOUR/approval.json`, changing only
`decision` to `approved`, and supplying the actual approving person's `reviewer`
and ISO `reviewed_at`. Preserve every scope hash and limitation. This is campaign
approval, distinct from the independent receipts above.

```bash
(
set -euo pipefail
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-approve \
  --manifest "$BC_FOUR/proposal.json" --model-lock "$BC_FOUR/cpu/worker-lock.json" \
  --approval "$BC_FOUR/approval.json" --output "$BC_FOUR/approved-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_FOUR_CLUSTER" --manifest "$BC_FOUR/approved-manifest.json" \
  --model-lock "$BC_FOUR/cpu/worker-lock.json" --dry-run
)
```

Inspect the eight-shard `%1` request and existing full-GPU qualification. Do not
change model, partition/device class, budgets or frozen source while running.
If scheduler inspection blocks another campaign, wait; do not bypass it.

#### 5. Submit once, observe, and export

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_FOUR_CLUSTER" --manifest "$BC_FOUR/approved-manifest.json" \
  --model-lock "$BC_FOUR/cpu/worker-lock.json" > "$BC_FOUR/run-submission.json"
cat "$BC_FOUR/run-submission.json"
)
export BC_FOUR_JOB="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job_id"])' "$BC_FOUR/run-submission.json")"
export BC_FOUR_OUTPUT="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["output"])' "$BC_FOUR/run-submission.json")"
squeue --array -j "$BC_FOUR_JOB" -o '%.22i %.12P %.20j %.2t %.10M %R'
sacct -j "$BC_FOUR_JOB" --format=JobID,State,ExitCode,Elapsed
```

No automatic resume command is supplied: the current prospective adapter
intentionally rejects a started configuration rather than regenerating planning.
Checkpoints are retained for read-only interrupted accounting. If interrupted,
export first and review whether a separately approved, provenance-preserving
resumption is supported; a fresh same-labelled attempt is prohibited. Ordinary
completed semantic failure, invalid planning or exhausted budgets do not request
a scientific retry and do not cancel later scheduled conditions. Integrity,
accounting, cleanup or conformance failures pause remaining work.

After terminal jobs, or for a read-only interruption review:

```bash
export BC_FOUR_RESULTS="$(mktemp -d "$BC_FOUR/results.XXXXXX")"
(
set -euo pipefail
cd "$BC_FOUR/source"
"$BC_PYTHON" -I scripts/bc.py aggregate --output "$BC_FOUR_OUTPUT" \
  > "$BC_FOUR_RESULTS/aggregate.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-export --run "$BC_FOUR_OUTPUT" \
  --output "$BC_FOUR_RESULTS/audit.private.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-export --run "$BC_FOUR_OUTPUT" --public \
  --output "$BC_FOUR_RESULTS/cohort.public.json"
printf 'Review files: %s\n' "$BC_FOUR_RESULTS"
)
```

The public export separates public planner inputs from future outcome metrics;
it omits execution states, private journals, raw hidden checks and review receipts.
The private audit retains actual journals, failed/invalid/unrun configurations and
plan trajectories. Neither authorizes training. Do not publish the private file.

After outcomes, prepare one **review-only B0 proposal per family/common worker
setup** from all configurations: terminal statuses, complete/conformant/within-cap
flags, actual and uncertain tokens/CPU, censored caps, planning and post-alarm
subsets, and per-source counts. Leave the proposed representative B0 unselected
until evidence suffices; never fit one favorable budget per planner/owner count.
A lower-cap filter of old traces is an offline diagnostic, not a new planning run.
No additional sweep or GPU experiment is authorized by this handoff.


## Prospective stock result (2026-10-11 review)

User-supplied export for experiment
`e10d7ffbe1335f578745c36cbbeb2828d73046d0ed9c51fa672d35a80a31aa72`
records one prompted-open planning sequence and three completed branches. The
user reports Slurm job 1092937_0 completed 0:0 in 12:45. Uploaded export SHA256:
`e5be83787cf2344316e0a73f407d9d29e04afe864f4edce0bb4a291d0d27d26b`.
This is supplied evidence, not independent remote filesystem authentication.
No model or SQL was executed during this local review. Raw traces stay outside Git.

| Branch | Correct / conformant / within caps | Tokens | CPU debit seconds |
| --- | --- | ---: | ---: |
| Clean | Yes / yes / yes | 9120 | 169.303781757 |
| F(w0) | Yes / yes / yes | 11849 | 196.625777765 |
| F(w1) | Yes / yes / yes | 12723 | 211.657250723 |

Both stock_report and zero_report passed the recorded terminal checks in every
branch. Uncertain token/CPU usage was zero; no configurations were missing.
Each branch had the same 100000-token/1200-CPU-second engineering caps. Planning
used two model calls (one rejected response), 3005 tokens and 103.476834250 CPU
seconds. These planning charges are already included in each branch total.

The frozen plan used two units, two meaningful owners and one declared edge
in a pool of seven identities. Targets were frozen before execution. F(w0)
triggered loss before publication and repaired u0 with w1, then u1 with w2.
F(w1) retained the stock artifact and repaired u1 with w0. The second unit read
the producer artifact but its query used the original stock table: a permitted
information dependency is not proof of a necessary executable dependency.

This meets the narrow prospective stock protocol milestone. It is one synthetic
task and one plan, not three independent samples, a planner comparison, B0, or
a general robustness result. Independent task review remains pending. Historical
conditional clean/F observations remain separate; their approvals are not reused.

### Reporting correction

Generic aggregate/status appended a legacy episode-hash coverage check after
the cohort reader had validated the manifest hash, producing the misleading
message "Result changed provenance; cannot resubmit". Cohort coverage now uses
the cohort reader, including saved schedules and interrupted/unrun coverage.
Changed provenance still fails; terminal invalid plans are not retry candidates.
The existing no-retry submission gate, historical scores and ledgers are unchanged.
Old snapshots remain immutable; the cohort-specific exporter can read this run.

### Richer-task review readiness

The reported cluster qualification at commit
`e9139a401efd900a0a96e08ad1fc0c01dd3f11f3` passed 99 controls without skips and
qualified stock plus the three implemented richer cards as review-pending.
All four public prompt footprints and both role grammars passed. Renewed GPU
footprint experiment `e923cb200f4835deb8457fe14e7bf50ee488b5b8be5d5070819bbaf75954f8e1`
passed all five observed cases on A100-SXM4-80GB (15373 tokens). This is observed
qualification, not worst-case fit or task competence. Energy CPU qualification
was reported on the cluster; the earlier local source-download limitation below
remains historical, not a claim that the cluster qualification is missing.

| Candidate | Remaining review or implementation requirement |
| --- | --- |
| Jaffle payment release | Hash-bound task usefulness/semantics review and attributed rights receipt; demo grounding remains explicit. |
| Energy single indicator | Task review and rights receipt covering underlying providers; passing CPU controls does not establish provider clearance. |
| GitHub topics client package | Task review and attributed rights receipt; offline client semantics remain separate from server behavior. |
| GitHub multioperation integration | Missing second operation and bounded source closure, public contract, two executable references and controls; then qualification and review. |

The configured richer lane requires all four candidates. Do not silently shrink
it to three or mark pending independent reviews approved. A smaller cohort would
require an explicit revised design and fresh scope-bound proposal. No new jobs,
source downloads, task approvals or experiment permissions are created here.

The detailed local design review and fourth-candidate completion requirements
are in [RICH_TASK_REVIEW_2026-10-11.md](RICH_TASK_REVIEW_2026-10-11.md).
This review does not mark independent or rights receipts approved.

## Original implementation record (2026-10-08)

## Milestones

| Milestone | Delivered | Remaining gate |
| --- | --- | --- |
| M0: prospective coverage | One generic cohort adapter freezes one planning outcome and the target schedule before execution. Wrong clean answers do not remove fault branches. | New stock protocol check has not run. |
| M1: task content | Three executable cards across three source groups; two private organizations each. A fourth, larger API candidate has a precise source-slice blocker. | Independent usefulness/rights review; actual energy-source qualification; fourth card authoring. |
| M2: matched pilot | Requirement-level allocation and existing prompted open planner use the same scoped Engine, workers, public monitor, JIT, resource ledger and terminal evaluator. | Public prompt measurements, renewed role locks and compatible GPU footprint, exact cohort approval. |
| M3: staged execution | Stock and rich proposal/review commands, shared-registry submission routing and full-coverage exports. | User review, commit/push, CPU jobs, separately authorized GPU qualification and task submissions. |

No GPU model execution, Slurm submission, training, commit or push was performed
in this implementation. Historical clean and conditional-loss records are
unchanged. The preceding report remains [PROGRESS_REPORT_2026-10-08.md](PROGRESS_REPORT_2026-10-08.md).

## Task cards and evidence

Public requests are in [rich/public](../benchmarks/reporecourse/rich/public);
private executable references and tests are in [rich/private](../benchmarks/reporecourse/rich/private).
Only the public loader feeds planners/workers. Authored outlines are removed
from planner inputs; their unit counts below are author-side diagnostics.

| Candidate | Grounding / outputs | Private alternatives (units, import edges, depth) | CPU evidence and blockers |
| --- | --- | --- | --- |
| `jaffle-payment-release` | Demo-grounded Jaffle: `order_payments`, `customer_summary`, `method_summary`, `reconciliation` | Independent (4, 0, 1); shared per-order aggregate (5, 3, 2) | Both references pass on the pinned staged seeds and authored variants; eight missing/semantic controls pass. Independent review and rights receipt pending. |
| `energy-single-indicator-release` | OWID: `generation_report`, `window_summary`, `coverage_report`, `exclusions`, `field_contract` | Independent (5, 0, 1); shared selected-row relation (6, 3, 2) | Both paths pass on explicitly authored fixtures. Actual retained energy data were not downloaded locally. Underlying-provider rights and independent review pending. |
| `github-topics-client-package` | GitHub REST description: request/response validators, inbound consumer and outbound body mapping | Independent (4, 0, 1); shared array schema (5, 4, 2) | Both references pass on the actual pinned topics slice; ten missing/semantic/accept-all/reject-all controls pass. Independent review and rights receipt pending. |
| `github-multioperation-integration` | Larger API authoring target in the **same GitHub source group** | Not finalized; no runnable references | Current retained slice contains one PUT operation. A second operation and its complete bounded dependency closure are absent. Six proposed roles are placeholders, not admitted obligations. |

There are **three implemented cards, not four admitted tasks**. The rich pilot
retains all four scheduled candidate identities and remains blocked; it never
silently shrinks to three after seeing outcomes. Only the first three have
task version `0.2-rich-1`. The fourth is `draft-unexecutable-1`.

### Semantics and scope

- Jaffle uses integer **recorded-payment cents**, including every recorded
  status. Equal-valued distinct payments remain distinct. Zero payments,
  unpaid orders, customers with no orders and empty inputs have explicit rules.
  No refund, revenue recognition, outstanding balance or order-price inference.
  Four fixture variants include the staged source, not four benchmark tasks.
- Energy uses the actually retained single indicator, `electricity_generation`
  in TWh. DNK/FIN, 2019–2022; null measurements are omitted, zero is valid,
  absent rows are not imputed. Country/year/missing exclusions have public
  precedence. Numeric comparison tolerance is public: absolute 1e-9 TWh and
  relative 1e-12; counts/text remain exact. Three fixture variants include a
  staged-source slot and authored boundary/all-null cases. No cross-indicator
  or per-country provider attribution is invented.
- GitHub uses the actual `PUT /repos/{owner}/{repo}/topics` request and response
  `names` arrays. Empty arrays and extra properties follow the inspected slice;
  null is invalid. Mappings preserve order, case and duplicate strings, rename
  `names`/`topics`, and drop unrelated fields when constructing the body. Mapping
  inputs are publicly bounded. This is an offline client package, not server
  behavior or a general OpenAPI translator. Positive/negative examples and a
  bundle-level round trip test all four outputs together.
- Cross-output consistency constrains results, not implementation sharing.
  Independent valid construction is accepted. References are SQL text lowered
  to the existing approved IR or bounded schemas/mappings. The language was
  not expanded; no reference implementation enters an online worker tool.
- Python expected-result reductions are independent of reference SQL. Both
  organizations still share the same compiler/executor/evaluator: correlated
  implementation defects remain possible, and CPU checks are not independent
  human review or model competence.

### Source inspection

Exact allowlists, byte counts, SHA-256 values and retained transformations stay
in [source_registry.json](../benchmarks/reporecourse/source_registry.json).
[SOURCES_AND_LICENSES.md](../benchmarks/reporecourse/SOURCES_AND_LICENSES.md)
contains attribution and unresolved rights. New cards reference these pins:

| Source group | Commit | Locally inspected material |
| --- | --- | --- |
| `dbt-labs/jaffle_shop_duckdb` | `36bde6cba69d962b83be1d52fc65a0dce1cb4ebb` | All bounded allowlisted docs/seeds: 37,563 upstream bytes; retained tables 8,372 bytes. Apache-2.0 file inspected, independent review pending. |
| `owid/energy-data` | `7e387a16f70a510e433f8aac7efeac6faa1e5059` | README 14,526 bytes and codebook 45,793 bytes only. Existing extraction specifies three columns and a 334-byte retained table. The 9,229,369-byte upstream CSV was not fetched. OWID and underlying-provider terms remain distinct. |
| `github/rest-api-description` | `4377b4f4845badf28d13464dfb3042c6cf0e3a1f` | One bounded 12,964,430-byte schema document plus README/license; deterministic topics slice 1,605 bytes, SHA-256 `1fbc4198b6f2a0f9ff9c61b3e076a422cf6ae3c9b90b738cdd46ba27ac517554`. MIT file inspected; no second operation staged. |

Source content stayed outside Git. Downloaded repository files were treated as
data; no upstream setup hooks or source code were executed.

## Prospective protocol and settings

The core is [cohort.py](../src/reporecourse/cohort.py), routed by
[rr_cohort.py](../src/beyond_consensus/experiments/rr_cohort.py) through existing
manifest, runner, aggregate and Slurm/registry components. It reuses
`v2.PromptedPlanner`, `v2.requirement_plan`, `v2.resolve_branches`, the existing
Engine, AssignmentScopes, immutable artifact store, Resources and evaluator.

1. Commit task/source/evaluator hashes, settings, separate planner/execution/
   target RNG streams, seed index 1, stopping policy and branch rule.
2. Run exactly one planning sequence, with the existing bounded structural
   revision allowance (at most eight calls). The deterministic default allocates
   terminal requirements in public order, cyclically over the seven identities;
   it incurs measured CPU and zero invented model tokens. Neither method name
   is a worker instruction. The prompted planner retains its existing prompt
   and full bounded-plan language, without an authored-plan menu.
3. Freeze valid or invalid planning. Resolve meaningful owners (terminal units
   and their ancestors) and persist the full branch schedule **before clean
   evaluation**. Invalid planning stays a failed configuration with target N/A,
   without fabricated worker episodes.
4. Each branch starts from original sources and the frozen plan/ledger. Charge
   the same actual planning ledger once in each branch; record physical reuse
   separately. Branch outputs and hidden scores are not sibling inputs.
5. Completed wrong answers and cap failures retain subsequent F branches.
   Infrastructure, integrity, conformance/accounting defects or interruption
   pause remaining branches/configurations. Existing started records prevent
   retry; read-only aggregation reconstructs interrupted/unrun coverage.

| Setting | Frozen or changed |
| --- | --- |
| Worker/model | Unchanged Qwen/Qwen3.5-27B, revision `fc05daec18b0a78c049392ed2e771dde82bdf654`, BF16, thinking, `do_sample=false` |
| Context and output | 16384 context; worker 2048, planner 6144. No truncation, offload or quantization. |
| Identities / hardware | Pool seven; fewer active owners allowed. One shared model and allocated full 80-GB-class GPU; sequential contexts, no claimed parallel GPU speedup. Software pools 2–8 retained. |
| Resources | 100000 logical tokens / 1200 charged CPU seconds **per end-to-end branch**; uncalibrated engineering caps, not B0. Terminal private evaluation reported separately. |
| Monitor / recovery | Same public checks and scoped common JIT in both methods; retained artifacts and cheap authorized rebinding/reexecution remain available. |
| Changes | New prospective manifests, task content/evaluation, cohort reporting and measured execution-parent overhead. Runtime/source hashes change; new qualification and experiment identities required. |
| Historical evidence | Original clean/conditional F observations and approvals unchanged; not imported as prospective observations. |

| Lane | Configurations | Model planning sequences | Maximum branches | Maximum logical tokens / charged CPU |
| --- | ---: | ---: | ---: | --- |
| Stock protocol check | 1 prompted, seed 1 | 1 | 8: clean + all meaningful owners | 800000 / 9600 seconds |
| Rich characterization | 4 tasks × 2 planners | 4 | 16: clean + one seeded uniform meaningful-owner F each | 1600000 / 19200 seconds |

These are upper bounds, not runtime forecasts. Seed 1 with deterministic decoding
is not an independent stochastic sample. One sampled target is not worst-case
robustness; different plans can have different owners and fault fractions.

## Current validation

Final local checks on the current implementation:

| Check | Result |
| --- | --- |
| Default Python 3.12.7 full suite | 445 tests run: 417 passed, 28 skipped; 69.355 seconds |
| Pinned prospective/scoped/reference controls | 99 passed, zero skips/failures/errors; 216.134 seconds |
| Additional legacy RepoRecourse, Track F and SQL compiler integration | 56 passed, zero skips/failures/errors; 51.319 seconds |
| Shell checker | 10 shell files passed |
| Compileall, diff whitespace, isolated stdlib CLI help | Passed |
| Handoff shell examples | All 13 Bash blocks parsed with `bash -n` |

The default skips are: `test_reporecourse` (10), `test_reporecourse_scoped` (3),
`test_reporecourse_track_f` (2), `test_reporecourse_v2` (2), `test_rr_cohort` (1),
`test_rr_open_clean` (1), `test_rr_open_fault` (1), `test_rr_rich_tasks` (4), and
`test_sql_text` (3), all due to absent optional pinned CPU dependencies in the
default environment; **all 27 ran successfully in the isolated pinned CPU
environment**. The remaining skip is
`test_repository.RealSandboxTests.test_actual_isolation_and_cleanup`, requiring
an explicitly approved container/cgroup sandbox profile. That unrelated legacy
path was not enabled. The complete skip names are retained in `unittest.log`.

The isolated environment uses Python 3.12.7, SQLGlot 27.28.1, jsonschema 4.25.1
and referencing 0.36.2. These pass counts overlap the default suite; do not add
them as independent observations. Model/tokenizer qualification was not run
locally because its actual assets are on the cluster.

Review artifacts are in the ignored local directory
[outputs/rr-rich-review-2026-10-08](../outputs/rr-rich-review-2026-10-08):
`inventory.json`, `cohort-controls.json`, individual source qualifications,
`unittest.log`, `pinned-controls.log`, and `legacy-integration.log`.
CPU-evidenced manifests and blocker reports are:

- `stock.cpu-evidenced.json` / `stock.cpu-review.json`: proposal
  `2dbbc0cbd7d59bbcbeb655e1add3cf525bcf85f6d4bae93b8f3db3da40cec928`.
- `rich.cpu-evidenced.json` / `rich.cpu-review.json`: proposal
  `81cdc46834f5e241aff7ee9a667c09da5155c460011f696ee43ffda16dcf71ec`.

These are actual locally built configurations with fixed model/resource settings,
source/task hashes and current CPU evidence; role locks, task reviews and GPU
evidence are explicitly absent. They are **not executable approvals**. They use
local temporary source paths and an uncommitted worktree source hash; regenerate
them on the reviewed cluster checkout. No successful Slurm preview is claimed:
the shared-submission tests verify blocking before any scheduler call when
evidence/approval is missing. All task-execution flags remain false.

Executable source qualification is separate from authored-fixture tests. Local
energy fixture passes do not clear its missing actual-source or provider gates.
Public prompt scenarios cover initial assignments and one-source reads; they
are not a proof that every later history fits. The displayed qualification
budget is fixed for reproducible hashes; actual execution budgets are never
reset. Grammar/tokenizer and GPU footprint measurements are still required on
the cluster with the real locks.

Changed implementation files are the new portable `cohort.py` and
`rich_tasks.py`, the BC `rr_cohort.py` adapter, task/evaluator/v2 integration,
existing CLI/manifest/runner/aggregate/cluster routing, the existing frozen CPU
wrapper, `check_rr_cohort.py`, two focused test modules and the rich task cards.
Existing documentation changes were preserved; this document is the consolidated
new milestone and handoff, with links from STATUS, the open runbook and v0.2.

## Historical October 8 browser-terminal handoff (do not rerun)

### 1. Review locally, then commit/push manually

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
git status --short
```

Review the files and commit/push yourself. Keep exported reports outside the
checkout. No commit or push is performed by these commands.

### 2. Pull and freeze source on Jupyter; submit CPU qualification

The following is a CPU job, not task/model execution. Use the current pinned
environment (SQLGlot 27.28.1, jsonschema 4.25.1, referencing 0.36.2 plus existing
tokenizer/grammar packages). Missing dependencies fail qualification.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RICH_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_RICH_BASE_LOCK="$BC_STORAGE/diagnostics/rr-planner6144.7KFOb8/cpu/worker-lock.json"
export BC_RICH="$(mktemp -d "$BC_STORAGE/diagnostics/rr-rich-cohort.XXXXXX")"
(
set -euo pipefail
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: preserve exports outside the checkout and commit intended changes.\n'
    exit 1
fi
test -x "$BC_PYTHON"
test -s "$BC_RICH_BASE_LOCK"
git rev-parse HEAD > "$BC_RICH/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_RICH/source"
git -C "$BC_RICH/source" checkout --detach "$(cat "$BC_RICH/source-commit.txt")"
test -s "$BC_RICH/source/experiments/qualify_reporecourse.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 --job-name=rr-rich-cpu \
  --chdir="$BC_RICH/source" --output="$BC_RICH/cpu.out" --error="$BC_RICH/cpu.err" \
  "$BC_RICH/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_RICH/source" --cohort-controls \
  --sources "$BC_RICH_SOURCES" --model-lock "$BC_RICH_BASE_LOCK" \
  --output "$BC_RICH/cpu" > "$BC_RICH/cpu-job.txt"
cat "$BC_RICH/cpu-job.txt"
printf 'Directory: %s\n' "$BC_RICH"
)
```

The explicit source root avoids the Slurm-spool working-directory failure.
Partition availability is not assumed; inspect it before submission. No source
pack is downloaded by this wrapper. Missing energy produces a blocked report.

After completion:

```bash
sacct -j "$(cut -d';' -f1 "$BC_RICH/cpu-job.txt")" --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_RICH/cpu.err"
ls -l "$BC_RICH/cpu"
```

### 3. Prepare both blocked templates now

This is read-only setup/manifest creation. It does not select targets or run a
model. The stock lane is first; the rich template deliberately retains the
blocked fourth candidate.

```bash
(
set -euo pipefail
cd "$BC_RICH/source"
for lane in stock_protocol rich_pilot; do
  "$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest \
    --lane "$lane" --sources "$BC_RICH_SOURCES" \
    --model-lock "$BC_RICH/cpu/worker-lock.json" \
    --planner-lock "$BC_RICH/cpu/planner-lock.json" \
    --output "$BC_RICH/$lane.template.json"
  "$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
    --manifest "$BC_RICH/$lane.template.json" \
    --model-lock "$BC_RICH/cpu/worker-lock.json" \
    --output "$BC_RICH/$lane.blockers.json"
done
)
```

### 4. Renew task-free GPU footprint separately

Current execution hashes changed. Historical successful footprint v3 is a
record, not automatic qualification of this runtime. Extract only its original
blocked engineering proposal, then regenerate all current qualification cases.

```bash
export BC_RICH_OLD_PREFLIGHT="$BC_STORAGE/outputs/qwen27b-na100/2c87a3340e7d3e47542c64191528ecc0e9cacfc2cd393756d1c26e325eb79c21-preflight"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_RICH'])
old = json.loads((Path(os.environ['BC_RICH_OLD_PREFLIGHT'])/'manifest.json').read_text())
with (root/'footprint-proposal.json').open('x') as f:
    json.dump(old['cpu_packet']['proposal'], f, indent=2)
PY
cat > "$BC_RICH/footprint-cpu.sh" <<'SH'
#!/bin/bash
set -euo pipefail
: "${SLURM_JOB_ID:?CPU allocation required}"
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/prepare_rr_open_footprint.py \
  --proposal "$BC_RICH/footprint-proposal.json" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" \
  --planner-lock "$BC_RICH/cpu/planner-lock.json" \
  --planner-output-cap 6144 --measure --output "$BC_RICH/footprint-cpu.json"
"$BC_PYTHON" -I scripts/bc.py rr-open-footprint-manifest \
  --packet "$BC_RICH/footprint-cpu.json" --model-lock "$BC_RICH/cpu/worker-lock.json" \
  --output "$BC_RICH/footprint-manifest.json"
SH
bash -n "$BC_RICH/footprint-cpu.sh"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=01:00:00 --chdir="$BC_RICH/source" \
  --output="$BC_RICH/footprint-cpu.out" --error="$BC_RICH/footprint-cpu.err" \
  "$BC_RICH/footprint-cpu.sh"
```

After its CPU job passes, choose an inspected cluster configuration for a full
80-GB-class allocation. The existing local NA100 configuration is shown, not a
claim about current queue availability. All GPU commands below are **manual,
separately user-authorized actions**, not commands already executed here.

```bash
export BC_RICH_CLUSTER="$HOME/Beyond-Consensus/configs/cluster.qwen27b-na100.local.json"
(
set -euo pipefail
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RICH_CLUSTER" --manifest "$BC_RICH/footprint-manifest.json" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" --dry-run
)
```

After explicit approval of this GPU qualification, submit **once**:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RICH_CLUSTER" --manifest "$BC_RICH/footprint-manifest.json" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" > "$BC_RICH/footprint-submission.json"
cat "$BC_RICH/footprint-submission.json"
)
```

Wait for completion and a passing report. Audit the actual output path from
that receipt:

```bash
export BC_RICH_PREFLIGHT_OUTPUT="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["output"])' "$BC_RICH/footprint-submission.json")"
"$BC_PYTHON" -I "$BC_RICH/source/scripts/bc.py" rr-open-footprint-audit \
  --run "$BC_RICH_PREFLIGHT_OUTPUT" --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_RICH/footprint-audit.json"
```

`BC_RICH_PREFLIGHT_OUTPUT` must be the actual receipt's `output` field. Do not
substitute the historical run. If another GPU type is selected, task runs must
match that newly audited allocation. Existing scheduler/global registry checks
remain enabled; no bypass or batch self-submission.

### 5. Assemble evidence and review exact task/rights scope

For each lane, create `LANE.evidence.json` with the following keys containing
the **full reports**, not filenames or edited summaries:

| Key | Content |
| --- | --- |
| `controls` | `cpu/cohort-controls.json` |
| `tasks[TASK]` | `cpu/TASK.json`, current task hashes and reference qualification |
| `task_footprints[TASK]` | `cpu/TASK-footprint.json`, current public tokenizer measurements |
| `footprint_audit` | Fresh `footprint-audit.json` |
| `reviews[TASK]` | Attributed receipt described below |

Each task receipt binds `task_hash` from its CPU report, `reviewer`,
`reviewed_at`, `scope: this_cohort_only`, `decision: approved`,
`independent_review: approved`, `rights: approved` and a specific `rights_basis`.
An explicitly reviewed `decision: engineering_exception` instead requires
`independent_review: pending` and
`limitations_accepted: [independent_review_pending, development_engineering_only]`.
It **cannot waive rights**. Energy additionally requires
`underlying_providers: approved`. Do not fill these with invented approvals.

Stock requires only its exact task receipt. Rich requires all four; candidate D
must first be authored and independently reviewed under a new version. New code
or task content requires fresh matched evidence, not editing an approved manifest.

This prepares both evidence files with **pending**, unattributed review records;
it supplies no approval. Edit only after the actual review, keeping the original
CPU/footprint reports unchanged.

```bash
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['BC_RICH'])
def read(path):
    return json.loads(path.read_text())
lanes = {
    'stock_protocol': ['synthetic-stock'],
    'rich_pilot': ['jaffle-payment-release', 'energy-single-indicator-release',
                   'github-topics-client-package', 'github-multioperation-integration'],
}
for lane, tasks in lanes.items():
    e = {'controls': read(root/'cpu/cohort-controls.json'),
         'footprint_audit': read(root/'footprint-audit.json'),
         'tasks': {}, 'task_footprints': {}, 'reviews': {}}
    for task in tasks:
        q = root/'cpu'/f'{task}.json'
        f = root/'cpu'/f'{task}-footprint.json'
        if q.is_file(): e['tasks'][task] = read(q)
        if f.is_file(): e['task_footprints'][task] = read(f)
        e['reviews'][task] = {
            'task_hash': e['tasks'].get(task, {}).get('task_hash'),
            'scope': 'this_cohort_only', 'decision': 'pending',
            'reviewer': None, 'reviewed_at': None,
            'independent_review': 'pending', 'rights': 'pending', 'rights_basis': None,
        }
        if task == 'energy-single-indicator-release':
            e['reviews'][task]['underlying_providers'] = 'pending'
    with (root/f'{lane}.evidence.json').open('x') as handle:
        json.dump(e, handle, indent=2)
PY
```

The commands after evidence assembly are identical for both lanes:

```bash
export BC_RICH_LANE=stock_protocol
(
set -euo pipefail
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest \
  --lane "$BC_RICH_LANE" --sources "$BC_RICH_SOURCES" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" --planner-lock "$BC_RICH/cpu/planner-lock.json" \
  --evidence "$BC_RICH/$BC_RICH_LANE.evidence.json" --output "$BC_RICH/$BC_RICH_LANE.proposal.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
  --manifest "$BC_RICH/$BC_RICH_LANE.proposal.json" --model-lock "$BC_RICH/cpu/worker-lock.json" \
  --output "$BC_RICH/$BC_RICH_LANE.review.json"
)
```

Review `blockers` and the concrete `approval_template`. After all blockers are
resolved and the user approves that exact cohort, save the attributed completed
template as `stock_protocol.approval.json`. Existing clean/F approvals do not
authorize this new sequence.

```bash
(
set -euo pipefail
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-approve \
  --manifest "$BC_RICH/$BC_RICH_LANE.proposal.json" --model-lock "$BC_RICH/cpu/worker-lock.json" \
  --approval "$BC_RICH/$BC_RICH_LANE.approval.json" --output "$BC_RICH/$BC_RICH_LANE.approved.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_RICH_CLUSTER" --manifest "$BC_RICH/$BC_RICH_LANE.approved.json" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" --dry-run
)
```

Only after reviewing that dry run and authorizing the exact task cohort:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_RICH_CLUSTER" --manifest "$BC_RICH/$BC_RICH_LANE.approved.json" \
  --model-lock "$BC_RICH/cpu/worker-lock.json" > "$BC_RICH/$BC_RICH_LANE.submission.json"
cat "$BC_RICH/$BC_RICH_LANE.submission.json"
)
```

Each configuration shard runs its precommitted branches sequentially on one
model instance. Do not regenerate planning or resubmit started shards. Preserve
and inspect failures. Review the stock check before separately preparing and
approving `BC_RICH_LANE=rich_pilot`; it is not an automatic next job.

### 6. Read-only analysis

Set `BC_RICH_RUN` from the actual submission receipt's output. Keep exports in a
fresh analysis directory, including failed and unrun configurations.

```bash
export BC_RICH_RUN="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["output"])' "$BC_RICH/$BC_RICH_LANE.submission.json")"
export BC_RICH_ANALYSIS="$(mktemp -d "$BC_RICH/results.XXXXXX")"
(
set -euo pipefail
cd "$BC_RICH/source"
"$BC_PYTHON" -I scripts/bc.py aggregate --output "$BC_RICH_RUN" > "$BC_RICH_ANALYSIS/aggregate.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-export \
  --run "$BC_RICH_RUN" --output "$BC_RICH_ANALYSIS/cohort-export.json"
)
```

Exports separate public planner inputs from future outcome labels and retain raw
planning/branch journals. They do not authorize training or promote private
references into public inputs. An absent result is visible as unrun/interrupted;
analysis does not resume computation.

## Pilot decision record

Use one row per task/planner and nested clean/F rows. Include source group,
grounding, task/review versions, required outputs, planned units, meaningful
owners, pool, depth, allowed/observed imports and ownership concentration;
planning validity/rejections/calls/tokens/CPU; correctness, conformance, budget
and status separately; target/fault fraction/event/progress; retained/rebound/
reexecuted/regenerated work; primary/post-alarm/total and uncertain usage.
The exporter retains events so missing telemetry is not silently called zero.
Do not add overlapping component totals a second time to the ledger.

Report within-task fault means before averaging tasks. Invalid planning is a
configuration failure with no target; unresolved infrastructure or missing rows
keep aggregates unresolved. Retain semantic failures and capped runs in costs.

- Clean success in both families plus intelligible reached-loss repairs supports
  considering a larger **development** sample, not a learned-planner advantage.
- Mostly wrong clean results: classify task, worker, representation and cap
  failures; pause expansion, without an endless task-specific prompt loop.
- Small teams win or organizations converge: preserve that result. No agent
  bonus, artificial repair penalty, or task filtering to make a method win.
- Runtime/accounting defects: preserve records, patch with regression controls,
  and use a new matched version. F-only tests concern availability recovery,
  not general adversarial security. No SFT/RL or paper-scale sweep is approved.
