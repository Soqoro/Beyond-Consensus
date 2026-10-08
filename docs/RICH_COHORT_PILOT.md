# Prospective richer-task pilot — implementation and review

Date: 2026-10-08. Status: **implemented locally; execution blocked pending evidence and review**.

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

## Browser-terminal handoff

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
