# Recoverability research gate — 2026-09-18

## Current decision after cluster follow-up

The user completed the historical ledger audit and both bounded SILO conditions.
Original and explicit actual-carry interfaces both scored **0/8 complete tasks
and 101/480 values**. Carry improved some local consistency but cost 6.8% more.
Pause further runs of this 4B/no-thinking SILO setting, including the larger
diagnostic/measurement batteries. The one additional interface condition has
been used; a reasoning/model sweep is not the next step.

The user-reported historical audit reconciled all eight recovery/JIT pairs:
each 256-unit gap is entirely finite-search charges, with zero non-search
residual. This supersedes the earlier unconfirmed attribution below. Full
provenance, limitations and the comparison are recorded in
[VALIDATION.md](VALIDATION.md#cluster-follow-up-reported-by-the-user-2026-09-18).

**Native follow-up:** the solar files, author material and private review are
staged; both individual references passed cluster CPU controls and their one
joint pair passed locally. Preflight 1077667 passed. The two-task model control
1077671 completed but scored 0/2: both workers exhausted 12 actions rereading
the requirement, without documents, SQL or submissions. This is one source
group, not a broad competence measurement. See
[the traces and interface correction](VALIDATION.md#solar-native-model-control-read-loop-2026-09-18).

The document-catalogue correction was then deployed and run as array 1077718.
It still failed 0/2: one worker discovered relevant documents but repeated reads
and emitted a malformed simulated conversation; the other read documents in
sequence. Neither attempted SQL or submission. Charged work increased 25.7%.
The EOS correction then passed preflight 1078003. Array 1078005 still scored
0/2 with both artifacts missing: 22 generations stopped at tokenizer EOS 248046;
two query attempts were malformed before hitting the output cap. The view worker
continued reading until its action limit. Charged work was 73320. The old stop
mismatch is resolved; it does not explain the remaining failures.

The subsequent budget audit measured 623/376 tokens including one stop for the
reviewed native query/view, both fitting 768. A 24-action comparison still failed
0/2 at 131348 work: the query repeated malformed actions until its retry cap,
and the view consumed all actions reading. Stop increasing those limits.

The user authorized preparing [four synthetic tool-compatibility probes](SQLITE_TOOL_DIAGNOSTIC.md).
This is the current next step: supply synthetic schemas directly, keep the same
restricted tools and model settings, and separate construction/submission from
document discovery. No native answers enter that diagnostic. No model run has
been performed locally. Passing probes would not establish native competence.
A second native pair and broader policy gates remain unmet.

## Prior implementation plan and decision rationale

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

At the implementation checkpoint, the user had not run the preceding cycle's
browser commands and no new remote observations were available. The follow-up
above supersedes that execution status; the scientific rationale below is retained.
No commit, push, job submission or large download is authorized by this update.

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

**Follow-up:** the user supplied the saved-ledger audit. All eight matched pairs
reconcile a 256-unit search difference and zero non-search residual. The account
below describes the earlier reproduction and audit design; candidate counts and
calibration origin are still not inferred from aggregate charges alone.

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
mechanism, not the historical cluster result. The separate user-reported audit
now provides the historical charge attribution; raw ledgers remain remote.

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

**Completed:** the original eight controls and the single actual-carry follow-up
both failed complete-task competence. The following is the frozen initial design,
not a request to rerun it. Costs are now observed (173439 and 185156 respectively).

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

Before execution, costs were unmeasured: report eight per-episode caps and the 384 primary
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

Use [the synthetic diagnostic runbook](SQLITE_TOOL_DIAGNOSTIC.md) now. The budget
audit and EOS sequences below are historical, already completed steps.

### Solar budget audit

After committing/pushing the audit script locally, run the following in the
browser terminal. This reads the existing validated private manifest, compiles
its reviewed reference trees without executing SQL, and loads only the pinned
tokenizer in the existing environment. It does not load model weights, submit
jobs, download files or send reference content to a worker. The report remains
outside Git and contains sizes/counts rather than reference expressions.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_SOLAR_CHECK="$BC_STORAGE/private/livesqlbench/solar-check.NatDlH"
export BC_SOLAR_AUDIT="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-budget.XXXXXX")"

"$BC_PYTHON" -I scripts/audit_sqlite_budget.py \
  --data-manifest "$BC_SOLAR_CHECK/native-validated.private.json" \
  --model-lock "$BC_MODEL_LOCK" \
  --tokenizer-python "$BC_PYTHON" \
  --action-cap 12 \
  --output-cap 768 \
  --output "$BC_SOLAR_AUDIT/budget-audit.json"
```

Share the printed report. The default mode without the two tokenizer arguments
uses standard-library CPU code and explicitly leaves token sizes unmeasured.

Interpretation rules:

- `content_plus_one_stop_tokens` measures one compact serialization of the
  already-reviewed artifact action, including one terminal token. It omits extra
  reasoning/delimiters and is not a guarantee of generated length. A count over
  768 demonstrates that representation cannot finish in that allowance; it does
  not rule out shorter equivalent representations. A fitting reference is not
  evidence that the model can discover or emit it.
- Four assumed actions cover contract, schema, creation/query and final artifact
  submission. With one catalogue page, 12 actions leave seven document-page slots
  and no additional retries if all seven are used. Each extra catalogue page,
  repeated read or malformed attempt consumes another slot. Required end-to-end
  model work also includes charged prompt re-prefills and tool observations;
  this audit does not claim that token/action fit implies total-work or context fit.
- Full-document page counts reproduce the runtime's 4000-character paging; a
  catalogue page contains at most 64 titles. Reading all documents is a scenario,
  not a requirement. Reading schema plus columns is another scenario, not a
  gold-selected route; no required KB shortlist is derived from evaluation data.
- If a known reference does not fit, define and separately authorize a fresh,
  bounded budget condition with explicit output/context/action/total-work costs.
  If it fits, the current failures still require better task/tool execution;
  do not call additional budget a proven fix. No automatic GPU command follows.
- Analysis CPU and tokenizer-process CPU time are reported separately. These
  offline costs do not rewrite historical episode ledgers or calibrate recovery.

### Solar turn-stopping correction

Historical sequence, completed in preflight 1078003 and array 1078005. Do not
repeat it; the budget audit above is current. Original instructions follow.

Review and commit/push the backend correction and its tests/docs locally, then
run this in the cluster browser terminal. Reuse the validated private task input
and model lock; the correction supplies runtime generation options and does not
edit or download model metadata. Keep the existing model, prompts and caps.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
source "$BC_STORAGE/envs/bc-gpu-py312/bin/activate"
export BC_PYTHON="$(command -v python)"
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
export BC_SOLAR_CHECK="$BC_STORAGE/private/livesqlbench/solar-check.NatDlH"
export BC_SOLAR_EOS="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-eos.XXXXXX")"

(
  set -eu
  test -z "$(git status --porcelain)"
  test -f "$BC_SOLAR_CHECK/native-validated.private.json"
  test -f "$BC_MODEL_LOCK"
  test -f "$BC_CLUSTER"
  python - <<'PY'
from pathlib import Path
source = Path("src/beyond_consensus/models/transformers_backend.py").read_text()
if 'GENERATION_POLICY = "tokenizer-turn-eos-v1"' not in source:
    raise SystemExit("Stop: pull the reviewed turn-stopping correction first")
PY
  python scripts/bc.py validation-config --profile qwen35-4b-control \
    --data-manifest "$BC_SOLAR_CHECK/native-validated.private.json" \
    --output "$BC_SOLAR_EOS/config.json"
  python scripts/bc.py manifest --config "$BC_SOLAR_EOS/config.json" \
    --model-lock "$BC_MODEL_LOCK" --output "$BC_SOLAR_EOS/manifest.json"
  python scripts/bc.py diagnostic-costs --manifest "$BC_SOLAR_EOS/manifest.json" \
    --output "$BC_SOLAR_EOS/planned-costs.json"
  python -m json.tool "$BC_SOLAR_EOS/planned-costs.json"
  bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
    --manifest "$BC_SOLAR_EOS/manifest.json" --model-lock "$BC_MODEL_LOCK" --dry-run
)
```

Expect two planned episodes and a new experiment ID; stop at the dry run.
After authorized preflight, inspect `runtime.generation_tokens`: expected
`policy=tokenizer-turn-eos-v1`, `eos_token_id=[248044,248046]` and padding 248044
for the reported checkpoint. `generation.diagnostics` also reports effective
IDs and `last_generated_token_id`; an EOS stop can use either supported stop.
The ready JSON and SQLite executor must still pass before the two-task pilot.
Use the shared registry and at most one concurrent GPU for this check. Do not
resume either failed old manifest or launch a larger policy/model campaign.

### Solar metadata audit

Completed historical audit; the turn-stopping correction above is the current
next step. The revised two-task control had completed and failed. Inspect the
existing pinned metadata in the browser terminal. This uses only the standard
library, reads no weights, changes no files and submits no job. A metadata match
does not alone certify inference or resolve the cause of simulated dialogue.

```bash
export BC_MODEL_LOCK=/dataset/suaq0001/beyond-consensus/models/Qwen--Qwen3.5-4B/model-lock.json

python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

lock = json.loads(Path(os.environ["BC_MODEL_LOCK"]).read_text())
model = Path(lock["model_path"])
tokenizer = Path(lock["tokenizer_path"])
print("REVISIONS:", lock["revision"], lock["tokenizer_revision"])

generation_path = model / "generation_config.json"
generation = json.loads(generation_path.read_text()) if generation_path.is_file() else {"missing": True}
print("GENERATION CONFIG:", json.dumps(generation, indent=2))
config = json.loads((model / "config.json").read_text())
for name, section in (("model", config), ("text", config.get("text_config", {}))):
    print(name, {k: section.get(k) for k in ("bos_token_id", "eos_token_id", "pad_token_id")})

tc = json.loads((tokenizer / "tokenizer_config.json").read_text())
print("TOKENIZER SPECIALS:", json.dumps({k: tc.get(k) for k in
    ("bos_token", "eos_token", "pad_token", "add_bos_token", "add_eos_token")}, indent=2))
for token_id, entry in tc.get("added_tokens_decoder", {}).items():
    content = entry.get("content", "")
    if any(marker in content for marker in ("think", "im_start", "im_end", "endoftext")):
        print("SPECIAL TOKEN:", token_id, repr(content), "special=", entry.get("special"))

path = tokenizer / "chat_template.jinja"
if path.is_file():
    data = path.read_bytes()
    print("TEMPLATE SHA256:", hashlib.sha256(data).hexdigest())
    print("CHAT TEMPLATE:\n" + data.decode())
else:
    print("CHAT TEMPLATE:", json.dumps(tc.get("chat_template"), indent=2))
PY
```

Review this output before proposing a new condition. The decoded transcript
does not retain all original special-token IDs, so do not infer an EOS bug from
the printed `user`/`assistant` strings alone. Do not repair multi-object model
responses by executing their first JSON action; the strict rejection is correct.

### Solar read-loop correction

Historical instructions for the now-completed second control (0/2). For the
current next step use the metadata audit above.

Review and commit/push the local code/tests/docs first using the usual manual
Git workflow. The changed shared prompt/tool observations require a fresh
manifest; do not retry the terminal failures in `solar-control.YYPkSx`.
The private CPU validation manifest and model lock are reused unchanged.

Then, in the cluster browser terminal with `bc-gpu-py312` active:

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_SOLAR_CHECK="$BC_STORAGE/private/livesqlbench/solar-check.NatDlH"
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
export BC_SOLAR_RECHECK="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-interface.XXXXXX")"

(
  set -eu
  test -z "$(git status --porcelain)"
  test -f "$BC_SOLAR_CHECK/native-validated.private.json"
  test -f "$BC_MODEL_LOCK"
  test -f "$BC_CLUSTER"
  python - <<'PY'
from pathlib import Path
source = Path("src/beyond_consensus/runtime/data_domain.py").read_text()
if 'elif tool == "list_documents":' not in source:
    raise SystemExit("Stop: pull the reviewed document-discovery correction first")
PY
  python scripts/bc.py validation-config --profile qwen35-4b-control \
    --data-manifest "$BC_SOLAR_CHECK/native-validated.private.json" \
    --output "$BC_SOLAR_RECHECK/config.json"
  python scripts/bc.py manifest --config "$BC_SOLAR_RECHECK/config.json" \
    --model-lock "$BC_MODEL_LOCK" --output "$BC_SOLAR_RECHECK/manifest.json"
  python scripts/bc.py diagnostic-costs --manifest "$BC_SOLAR_RECHECK/manifest.json" \
    --output "$BC_SOLAR_RECHECK/planned-costs.json"
  python -m json.tool "$BC_SOLAR_RECHECK/planned-costs.json"
  bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
    --manifest "$BC_SOLAR_RECHECK/manifest.json" \
    --model-lock "$BC_MODEL_LOCK" --dry-run
)
```

Expect exactly two planned single/clean episodes and a new experiment ID.
Stop at this dry run. A later authorized preflight/pilot uses the same new
manifest and the shared registry, at one concurrent GPU. No larger caps or
model changes are part of this correction. A second failure is preserved and
inspected for progress/document use before considering any further condition;
passing these two development tasks alone would not open the broader policy gate.

### Solar clean-model control preparation

Historical preparation for the now-completed failed control. Use the correction
section above for the current next step. The individual solar references passed
cluster CPU validation in `solar-check.NatDlH`; this prepared two single/clean
episodes at the unchanged 4B/no-thinking settings. It is one database group,
not an independent two-source benchmark. Competence/pair/policy gates remain pending.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_SOLAR_CHECK="$BC_STORAGE/private/livesqlbench/solar-check.NatDlH"
export BC_MODEL_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
export BC_CLUSTER=configs/cluster.pa100.local.json
export BC_PYTHON="$(command -v python)"
export BC_SOLAR_GPU="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-control.XXXXXX")"
(
  set -eu
  python scripts/bc.py validation-config --profile qwen35-4b-control \
    --data-manifest "$BC_SOLAR_CHECK/native-validated.private.json" \
    --output "$BC_SOLAR_GPU/config.json"
  python scripts/bc.py manifest --config "$BC_SOLAR_GPU/config.json" \
    --model-lock "$BC_MODEL_LOCK" --output "$BC_SOLAR_GPU/manifest.json"
  python scripts/bc.py diagnostic-costs --manifest "$BC_SOLAR_GPU/manifest.json" \
    --output "$BC_SOLAR_GPU/planned-costs.json"
  python -m json.tool "$BC_SOLAR_GPU/planned-costs.json"
  bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
    --manifest "$BC_SOLAR_GPU/manifest.json" \
    --model-lock "$BC_MODEL_LOCK" --dry-run
)
```

Expect two planned episodes; preflight requests one GPU. Costs are caps until
real model execution is observed. Stop at the scheduler dry run. After separately
authorized preflight succeeds, the existing `submit_pilot.sh` path can execute
the same manifest with `--concurrency 1`. Preserve any failed or capped model
outputs; do not change settings or select easier tasks based on those results.

### Solar review transfer and registration

The user has completed public/material staging in `staging.L7bFVF`; the generic
inventory instructions below are retained as earlier prerequisites. Both solar
typed references and their one joint pair passed local CPU controls. Cluster
replay is still pending. The two-pair research gate is incomplete and no GPU
competence or policy run follows automatically.

Save the completed private review from
`/tmp/bc-author-materials.f0n5jtmc/solar-review-v1/solar-review.private.json`,
then upload it through Jupyter beside the cluster checkout's README. This is a
reviewed strict result-comparison adaptation; its notes explicitly distinguish
the upstream sampled/tolerant tests. Preserve the earlier unapproved template.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_SQLITE_ROOT="$BC_STORAGE/datasets/livesqlbench-0664a2f"
export BC_SQLITE_MATERIALS="$BC_STORAGE/private/livesqlbench/materials.private.jsonl"
export BC_SOLAR_CHECK="$(mktemp -d "$BC_STORAGE/private/livesqlbench/solar-check.XXXXXX")"
(
  set -eu
  printf '%s  %s\n' \
    '78c2ccc691573f73aae9b38b26416fdced1b3d05f54a36e23a673607624ed31a' \
    'solar-review.private.json' | sha256sum --check -
  # Copy to a new private directory; do not overwrite a previous review.
  cp -- solar-review.private.json "$BC_SOLAR_CHECK/solar-review.private.json"
  chmod 600 "$BC_SOLAR_CHECK/solar-review.private.json"
  cmp -- solar-review.private.json "$BC_SOLAR_CHECK/solar-review.private.json"
  python scripts/bc.py sqlite-stage --root "$BC_SQLITE_ROOT" \
    --materials "$BC_SQLITE_MATERIALS" \
    --review "$BC_SOLAR_CHECK/solar-review.private.json" \
    --output "$BC_SOLAR_CHECK/reviewed-stage.json" \
    > "$BC_SOLAR_CHECK/inspection.json"
  python - <<'PY'
import json
import os
from pathlib import Path
root = Path(os.environ["BC_SOLAR_CHECK"])
report = json.loads((root / "inspection.json").read_text())
print(json.dumps({"check_directory": str(root), "tasks": [
    task for task in report["tasks"] if task["id"] in {"solar_2", "solar_M_3"}
]}, indent=2))
PY
)
```

`candidate_requires_validation` is expected after registration. It is not a
reference success. The private upload remains ignored in the checkout; the
registered copy is outside it. Keep only that outside copy when organizing files.

### Prepare solar CPU batch replay (dry run only)

Use the same reviewed source commit as the existing cluster checkout and preserve
a read-only source archive. This job runs exactly two native reference controls
and no model. The configured partition is a starting point, not a claim that the
site permits CPU-only work there; the scheduler dry run checks that request.
No GPU is requested. Run after the review registration above succeeds.

```bash
export BC_SOLAR_PYTHON="$(command -v python)"
export BC_SOLAR_PARTITION="$(python -c 'import json; print(json.load(open("configs/cluster.pa100.local.json"))["partition"])')"
(
  set -euo pipefail
  : "${BC_SOLAR_CHECK:?Complete solar review registration first}"
  test -z "$(git status --porcelain)"
  test -f "$BC_SOLAR_CHECK/reviewed-stage.json"
  mkdir "$BC_SOLAR_CHECK/source"
  git archive --format=tar HEAD | tar -xf - -C "$BC_SOLAR_CHECK/source"
  git rev-parse HEAD > "$BC_SOLAR_CHECK/source-commit.txt"
  chmod -R a-w "$BC_SOLAR_CHECK/source"
  cat > "$BC_SOLAR_CHECK/reference-job.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Run inside a CPU batch allocation}"
cd "$BC_SOLAR_CHECK/source"
"$BC_SOLAR_PYTHON" -I scripts/bc.py sqlite-readiness \
  --staged "$BC_SOLAR_CHECK/reviewed-stage.json" \
  --output "$BC_SOLAR_CHECK/readiness.json"
"$BC_SOLAR_PYTHON" -I scripts/bc.py sqlite-validate \
  --staged "$BC_SOLAR_CHECK/reviewed-stage.json" \
  --task-ids solar_2 solar_M_3 --count 2 \
  --output "$BC_SOLAR_CHECK/native-validated.private.json"
SH
  bash -n "$BC_SOLAR_CHECK/reference-job.sh"
  sbatch --test-only --partition="$BC_SOLAR_PARTITION" \
    --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:10:00 \
    --job-name=bc-solar-reference \
    --output="$BC_SOLAR_CHECK/reference-%j.out" \
    --error="$BC_SOLAR_CHECK/reference-%j.err" \
    "$BC_SOLAR_CHECK/reference-job.sh"
)
```

Stop at the dry run and inspect the scheduler response. Actual batch submission
is a separate user action. Failed/partial runs require new output paths; preserve
the frozen source and review rather than regenerating them from model outcomes.

### Browser terminal: inspect existing native materials

Use the existing checkout/environment. The paths below are runbook defaults,
not verified cluster inventory. If staging is elsewhere, set `BC_NATIVE_STAGE`
to that actual manifest before running. This reads public metadata and private
material/review records through `sqlite-inspect`, printing only status/reason
counts. It neither executes SQL/model work nor hashes large database files.
Missing default paths do not prove files are absent elsewhere.

```bash
: "${BC_STORAGE:?Set BC_STORAGE to the existing dataset storage directory}"
export BC_NATIVE_STAGE="${BC_NATIVE_STAGE:-$BC_STORAGE/sqlite-stage-public.json}"
python - <<'PY'
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

stage = Path(os.environ["BC_NATIVE_STAGE"])
metadata = Path(os.environ["BC_STORAGE"]) / "datasets/livesqlbench-0664a2f/livesqlbench_data_sqlite.jsonl"
print(json.dumps({"staging_path": str(stage), "staging_present": stage.is_file(),
                  "default_metadata_path": str(metadata), "default_metadata_present": metadata.is_file()}))
if stage.is_file():
    inspection = subprocess.run(
        [sys.executable, "scripts/bc.py", "sqlite-inspect", "--staged", str(stage)],
        text=True, capture_output=True)
    if inspection.returncode:
        print("Inspection failed; inspect the staging paths, release hashes and record format locally.")
        raise SystemExit(inspection.returncode)
    report = json.loads(inspection.stdout)
    tasks = report["tasks"]
    print(json.dumps({"metadata_records": len(tasks), "scored_ready": report["scored_ready"],
        "statuses": dict(Counter(t["status"] for t in tasks)),
        "blocking_reasons": dict(Counter(r for t in tasks for r in t["reasons"]))}, indent=2))
else:
    print("Locate an existing staging manifest or the actual database/material paths before staging.")
PY
```

If author references/tests or review are missing, obtain/review those specific
materials; keep the tasks unscored. Do not fill them with fixture or model answers.
Once files are present, follow
[the existing native CPU gate](VALIDATION_CYCLE.md#3-native-gate-only-when-the-missing-files-are-present):
immutable staging and readiness (large database hashing in a CPU allocation),
reviewed reference controls on up to ten supported development tasks, then two
actual compatible pairs. Inspection alone does not verify database contents,
supported translations or scoring. Preserve earlier manifests/reports and use
new output paths. GPU competence follows those gates; no native policy comparison
or job submission is implied here.

## Historical command sequence — completed SILO screen

The commands below preserve the earlier plan for reproducibility. The ledger
audit, full control and one interface follow-up have already been run by the
user. Do not recreate those campaigns or overwrite their frozen files.

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
locks belong in Git. The historical browser sequence used the existing
`bc-gpu-py312` environment.

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

- **Continue now:** inspect existing native staging and material/review availability.
- **Completed:** historical charge reconciliation and both eight-source SILO conditions; preserve results.
- **Continue native validation when ready:** supported CPU references and actual pairs, then clean-model competence with separate job authorization.
- **Stop for missing native materials/support:** obtain/review the specific prerequisite; keep excluded tasks unscored.
- **Stop before native policy comparison:** reference, competence, material workflow and cost gates must pass first.
- **Stop broad campaigns:** no 320-episode, full 64-diagnostic, 96-operation, adaptive attack or model sweep.
- **Stop repeated SILO tuning:** the original screen and one interface comparison failed; this 4B/no-thinking setting is paused.
