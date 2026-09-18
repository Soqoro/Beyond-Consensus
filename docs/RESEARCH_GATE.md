# Recoverability research gate — 2026-09-18

## Implementation plan

1. Count actual candidate structures separately from preparation/replica masks,
   names and owners. Expose existing material dependency alternatives through
   an opt-in, common-JIT condition; retain legacy behavior.
2. Strengthen read-only saved-ledger reconciliation, separating observed charges
   from current-code reproductions and unknown historical facts.
3. Reuse native readiness/reference gates and prepare only eight fresh SILO full
   controls. Preserve previously frozen sources; do not prepare the other
   battery/measurement campaigns by default.
4. Test execution/provenance, unchanged defaults and fail-closed gates; verify
   documentation shell blocks and generated scripts. Record actual outcomes.

The user has not run the preceding cycle's browser-terminal commands. No new
cluster result, remote ledger audit or native validation is available. The local
checkout was clean at the start of this task. Existing historical records remain
unchanged. No commit, push, job submission or large download is authorized here.

Detailed prior tooling and manual native prerequisites are in
[VALIDATION_CYCLE.md](VALIDATION_CYCLE.md); historical results are in
[VALIDATION.md](VALIDATION.md). This document controls the narrower next step.

## Decision 1: what the planner chooses

The local `planning-audit` inspects the actual ordered catalogue in
`policies/core.py:candidate_plans/common_units`. For four-unit examples:

| Distinct count | Independent numeric / SQLite fixture | Linked numeric fixture | SILO full |
| --- | ---: | ---: | ---: |
| Candidates including masks and boundary labels | 32 | 32 | 32 |
| Required terminal obligations | 4 | 4 | 4 |
| Terminal-obligation sets / unit-boundary sets | 1 / 1 | 1 / 1 | 1 / 1 |
| Dependency graphs / primary workflows including reads | 1 / 1 | 2 / 2 | 1 / 1 |
| Serial primary execution orders | 1 | 1 | 1 |
| Owner assignments | 1 | 1 | 1 |
| Preparation masks | 16 | 16 | 16 |
| Material plans including preparation | 16 | 32 | 16 |
| Configured reserve values | 1 | 1 | 1 |
| Newly introduced intermediate units | 0 | 0 | 0 |

The 32 candidates are **two boundary labels × 16 backup masks**, not 32 task
decompositions. Replication applies those masks to duplicates instead of advance
preparation. Owners remain `u0:w0, u1:w1, u2:w2, u3:w3`. Reserve is configured,
not optimized. SILO preserves its predecessor chain under either label.

Concrete existing material alternative: in numeric fixture-01, `context_linked`
passes the selected u0 version into u2 and u3; `isolated_contract` omits those
reads and reconstructs from permitted source contracts. Outputs and execution
order remain u0–u3. `EpisodeEngine.primary` and `WorkerLoop.run` charge the actual
reads/prefill and bind parents; identity invalidation propagates to descendants.
This is a real **dependency-exposure** difference, not a different unit partition
or a new reusable-view plan. Structural checks do not establish semantics.

Because this limited material alternative already exists, it is exposed rather
than replaced with a new search framework. Opt-in `RunConfig.organization` values
`fixed_isolated`, `fixed_linked`, and `select_boundary` use **policy jit**, the same
post-alarm cold/index/outline/prepared catalogue, four identities, total cap and
configured reserve fraction. `select_boundary` evaluates only the two existing
primary workflows, with no advance preparations. Search itself remains charged.
Defaults stay `legacy`; legacy recovery/JIT reserve differences are preserved.
New conditions change manifest/calibration provenance and cannot resume old runs.

These opt-in executions are currently admitted only for numeric fixtures with
different graphs. Independent fixtures/SILO fail an explicit readiness gate;
native alternatives remain blocked pending legality and measured-cost validation.
The tests prescribe fixture structures; they are not real-model plan generation.
**Native recovery-aware decomposition selection is not research-ready.** No
native intermediate-view generator or favorable operation costs were invented.
Any future generated native candidates must come from the actual frozen model
through charged calls using public requirements/schema/documents only, with at
most 2–4 structurally valid plans retaining every terminal obligation. Neither
gold SQL nor hidden tests may enter that path. No such GPU call is authorized now.

## Decision 2: scope of preparation deferral and budget gaps

For a fixed primary workflow and diagnosis, suppose inputs, operations and
eligible identities remain available after the alarm; costs are additive; there
is no separate recovery deadline; and preparation benefits neither primary work
nor detection. Then JIT can buy the surviving useful preparations and follow the
same repair schedule:

`JIT_repair(s) <= preparation(P) + prepared_repair(P,s)`.

This is a feasible-schedule/cost statement for the declared catalogue. The actual
recovery objective in `planning/allocation.py` minimizes
`max_s(base + repair(s))`, with coefficient one on both terms. Under the assumptions,
same primary cost and exact additive search, the empty plan weakly dominates;
first-visited empty candidates retain ties. Replication has a different,
lexicographic objective and is not covered by that objective conclusion.
Expensive reading, a larger model or a realistic database alone does not change
the argument. Primary reuse, changed organization or phase-specific availability
would change its assumptions and must be measured explicitly.

This is **not universal dominance of task-success probability**: finite search,
uncertain estimates, context differences and stochastic model execution are not
an exact deterministic cost model. `exact_finite` is limited to the enumerated
catalogue; exhausted searches do not certify global optimality.

Predicted, reserved and realized work must remain separate:

- Predictions: one common cold estimate per unit, preparation estimate per item,
  and route costs. Checking, integration and search overhead are **unmodeled/null**.
  Primary savings from reuse and extra artifact-interface/prefill costs are not
  separately modeled. This cannot identify a useful native organization optimum.
- Legacy recovery feasibility checks base and worst total against cap, but does
  not apply reserve in `solve_allocation`. Replication uses `cap - reserve` for
  primary feasibility. Legacy JIT has no configured upfront floor. The opt-in
  organization arms share the same reserve rule and primary feasibility floor;
  this is a separately versioned treatment, not a historical accounting fix.
- Runtime charges catalogue setup, visited search states, all model/tool work,
  repeated reads/prefill, audit, replay, integration and final evaluation. It
  protects the primary floor, then uses remaining budget. Prediction feasibility
  does not prevent actual exhaustion. Search-state units are surrogate work,
  not measured GPU seconds or generated tokens. No charge was removed or retuned.

## Decision 3: historical 256 units

Reported fixture evidence remains 32/32 successes, zero preparation and recovery
minus JIT work of 256 in each condition. The earlier constructed-cost reproduction
is 32 candidates × four excluded identities × two visited states. It is not the
remote ledger. The checked-in pilot has no calibration file; actual historical
resolved calibration origin remains unconfirmed without saved evidence.

`allocation-audit` now reports each episode's stage entries, totals, search charges,
recorded states/candidate count when available, executed preparation/replica events,
config/source/calibration identities and missing evidence. It pairs task/seed/
condition across recovery and JIT, checks ledger/provenance consistency, and reports
search difference and residual stage costs. It marks the entire gap explained only
when the recorded charges reconcile. Unknown counts stay unknown; legitimate
repeated charges remain in place. Derived reports have their own source/hash/CPU
provenance and never modify results. A mock saved-ledger regression confirms the
mechanism, not the historical cluster result. The browser audit below is the first
cluster action after pulling the reviewed code.

## Decision 4: native SQLite is the application priority

The local readiness report is `scoring_unavailable`: no staged native manifest,
actual source databases or approved author materials are registered here. The
historical 270-record inspection has not been rerun. No native ready/scored count
or task-pair compatibility is inferred from fixtures.

Required manual dependencies are immutable databases and all permitted schema/KB
documents, nonempty author reference/test records from the pinned release, exact
record hashes, and a truthful private review translating supported checks. The
executor accepts the bounded SELECT/view tree only; raw SQL, arbitrary Python,
writes and nonempty setup/cleanup remain unsupported. The scorer is a reviewed
result-comparison adaptation (including its documented duplicate/NULL/ordering/
tolerance behavior), not full upstream evaluator parity.

Follow [the existing native gate](VALIDATION_CYCLE.md#3-native-gate-only-when-the-missing-files-are-present):
stage/review → CPU reference controls on up to 5–10 supported development tasks →
two actual compatible pairs → single/clean model competence. Both pair obligations
must pass on one submission/state. Database/shared-source splits, excluded
candidates and reasons stay visible. `crypto_M_2 + crypto_8` remains a candidate;
a second pair must be identified from actual requirements/compatibility, never
from comparative policy success. Heavy file hashing and controls use a CPU job.

## Decision 5: only eight full SILO controls initially

`silo-battery --full-only` creates only `full.json` and `plan.json`: eight original
II-11 tasks, one seed, single/clean, original access/scoring. It does not create
local, boundary, confirmation or operation-measurement campaigns. `--reuse-full`
validates/reuses an existing frozen eight-task manifest without consulting outcomes.
Prior seeds 0–7 and supplied exclusion manifests are excluded by content; only
development groups are admitted. Unknown external overlap cannot be certified.

The local deterministic freeze used seeds **1001, 1002, 1003, 1007, 1008, 1011,
1013, 1014**, matching the previous procedure. Its prior temporary files were not
available in this session. Full group/content IDs are in the generated plan.
Pinned `qwen35-4b-control` remains BF16, no thinking, 8192 context and 768 generated
tokens. No longer generation or prompt change was introduced.

Costs are currently unmeasured: report eight per-episode caps and the 384 primary
action bound (8 × 4 × 12); an action may include charged prefill/tools. Do not call
these bounds measured estimates or assume hardware from a partition label. The
existing preflight records allocated device/memory and respects CUDA_VISIBLE_DEVICES.

After completion, aggregate and run `silo-analyze`: coverage/shape, global and
per-value correctness, incoming-state consistency, local increments, inherited
wrong predecessors, token/stopping/limit metadata and actual hardware. Eight
sources are a feasibility screen, not reliable benchmark competence evidence.
Select only necessary local/boundary cases afterward, retaining unavailable
predecessor denominators; failure-conditioned subsets are diagnostic. Actual
wrong predecessor values must remain wrong.

At most **one additional competence condition** may be proposed after this screen:
if protocol/shape passes, arithmetic failures persist and generations are not
capped, consider same-checkpoint reasoning only after template verification, a
new profile/manifest and preflight. Change no interface simultaneously. A reasoning
generation ending at its output cap is inconclusive about arithmetic competence.
Boundary-only symptoms may instead justify the existing actual-final-value
serialization; choose one factor, not both. No follow-up runs are prepared here.
If bounded competence remains poor, pause this SILO family.

## Blocked native pilot specification

| Organization | Recovery permission |
| --- | --- |
| Fixed/default | Strong JIT |
| Fixed/default | Advance preparation enabled |
| Recovery-aware | Same strong JIT |
| Recovery-aware | Advance preparation enabled |

Start only with the two organization + JIT arms on a few validated development
pairs, clean and withholding. Keep model, four identities, access, audit,
compromise bound, total budget and reserve-selection rule fixed. Invalidation
targets an identity and its recorded descendants, not one convenient unit. The
current fixed attack draws an identity uniformly; a future policy-aware exposure
comparison must re-evaluate placement per plan and label/charge that attacker.
Do not reuse incompatible corrupted intermediate states across decompositions.
Protocol B applies only within a common decomposition/primary trace; historical
preparation remains visible and it is not a total-efficiency claim.

Add preparation arms only if they are meaningful and auditable. They may select
none and collapse to the same effective policy; report that rather than forcing
distinct outcomes. Prescribed preparation is a diagnostic. Any apparent benefit
needs attribution to primary reuse, organization, cost/access asymmetry, search,
stochastic execution or accounting. Small matched-operation calibration may be
proposed separately; no 96-operation campaign is authorized or prepared here.

Execution remains blocked until **all five gates** pass: native references;
observed clean-model competence; at least two legal material workflows; explicit
cost predictions/reserve/full charged budget; frozen method/prompt/calibration/
manifest provenance. There are no fabricated runnable native pilot rows.

## Ordered next commands

### Local review, then manual commit/push

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python scripts/check_docs_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
export BC_LOCAL_GATE="$(mktemp -d /tmp/bc-research-gate.XXXXXX)"
python scripts/bc.py planning-audit --config configs/numeric-pilot.json --output "$BC_LOCAL_GATE/numeric-plans.json"
python scripts/bc.py planning-audit --config configs/pilot.json --output "$BC_LOCAL_GATE/sqlite-plans.json"
python scripts/bc.py sqlite-readiness --output "$BC_LOCAL_GATE/native-readiness.json"
git status --short
git diff
```

The user reviews, commits and pushes. No data, environments, reports or model
locks belong in Git. Earlier browser commands have not been run; start here after
the reviewed code is pushed, in the existing `bc-gpu-py312` environment.

### Browser terminal: pull, audit, then prepare eight controls

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
export BC_GATE="$(mktemp -d "$BC_STORAGE/research-gate.XXXXXX")"
python scripts/bc.py allocation-audit \
  --run "$BC_STORAGE/outputs/d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd" \
  --output "$BC_GATE/pilot-ledgers.json"
python -m json.tool "$BC_GATE/pilot-ledgers.json"
python scripts/bc.py silo-battery --full-only \
  --exclude "$BC_STORAGE/silo-prefix.json" --output-root "$BC_GATE/silo"
python scripts/bc.py validation-config --profile qwen35-4b-control \
  --data-manifest "$BC_GATE/silo/full.json" --output "$BC_GATE/silo/control.json"
python scripts/bc.py manifest --config "$BC_GATE/silo/control.json" \
  --model-lock "$BC_MODEL_LOCK" --output "$BC_GATE/silo/control-manifest.json"
python scripts/bc.py diagnostic-costs --manifest "$BC_GATE/silo/control-manifest.json" \
  --output "$BC_GATE/silo/planned-costs.json"
python -m json.tool "$BC_GATE/silo/planned-costs.json"
sinfo -N -O NodeHost,Partition,StateCompact,Gres,GresUsed
test -f "$BC_CLUSTER"
bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_GATE/silo/control-manifest.json" --model-lock "$BC_MODEL_LOCK" --dry-run
bash experiments/submit_pilot.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_GATE/silo/control-manifest.json" --model-lock "$BC_MODEL_LOCK" \
  --concurrency 1 --dry-run
```

Use the existing profile matching current authorized resources; the default path
above names the user's prior working profile, not a claim of present availability.
If full sources were already frozen, add `--reuse-full "$BC_PRIOR_FULL"` with its
actual path to the one `silo-battery --full-only` command. Do not include that same
manifest among exclusions. The original full contents are preserved.

### Only after separate authorization: preflight, inspect, then control

The following are prepared instructions, not actions executed by this task. Run
preflight first and review its result before separately submitting the control:

```bash
bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_GATE/silo/control-manifest.json" --model-lock "$BC_MODEL_LOCK"
export BC_CONTROL_ID="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' "$BC_GATE/silo/control-manifest.json")"
export BC_CONTROL_OUTPUT="$BC_STORAGE/outputs/$BC_CONTROL_ID"
```

After that job completes:

```bash
python -m json.tool "$BC_CONTROL_OUTPUT-preflight/preflight.json"
```

After preflight review and authorization:

```bash
bash experiments/submit_pilot.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_GATE/silo/control-manifest.json" --model-lock "$BC_MODEL_LOCK" --concurrency 1
```

After the control completes:

```bash
python scripts/bc.py aggregate --output "$BC_CONTROL_OUTPUT"
python scripts/bc.py silo-analyze --run "$BC_CONTROL_OUTPUT" --output "$BC_GATE/silo-analysis.json"
python scripts/bc.py diagnostic-costs --run "$BC_CONTROL_OUTPUT" --output "$BC_GATE/measured-costs.json"
```

The shared registry/scheduler inspection and immutable snapshots remain required.
Each shard uses one GPU and one frozen model; this workflow initially allows one
concurrent shard, always subject to the shared four-GPU maximum and active-campaign
guard. There is no submission loop or batch self-submission.

### Native files available: resume the existing reference gate

```bash
python scripts/bc.py sqlite-readiness --staged "$BC_STORAGE/sqlite-stage-public.json" \
  --output "$BC_GATE/native-readiness.json"
```

For heavy files run this in a CPU allocation. The actual staging/review and
source-pinned CPU job commands remain in
[VALIDATION_CYCLE.md, native gate](VALIDATION_CYCLE.md#3-native-gate-only-when-the-missing-files-are-present).
They include `sqlite-stage`, `sqlite-review-template`, `sqlite-validate --up-to
--count 10` and `sqlite-pairs --count 2`. Set `BC_CYCLE="$BC_GATE"` when using
those commands. Inspect/review missing materials first; stop at `sbatch --test-only`.
No native task or pair is implied ready by these prepared commands.

## STOP / CONTINUE

- **Continue now locally:** review tests, structural audit and gates. User commits/pushes.
- **Continue after pull:** read-only historical ledger audit; inspect residuals and missing evidence.
- **Continue only when authorized:** one-GPU preflight, then eight SILO full controls.
- **Stop for missing native materials/support:** obtain/review the specific prerequisite; keep excluded tasks unscored.
- **Stop before native policy comparison:** reference, competence, material workflow and cost gates must pass first.
- **Stop broad campaigns:** no 320-episode, full 64-diagnostic, 96-operation, adaptive attack or model sweep.
- **Stop repeated SILO tuning:** inspect the eight-source screen; at most one separately justified additional condition, then pause the family if competence stays poor.
