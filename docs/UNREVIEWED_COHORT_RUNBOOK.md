# Four-task unreviewed development run

## Three-call response reconstruction — 14 October 2026

This separate diagnostic does not repeat the cohort. Commit/push the diagnostic
adapter, freeze a fresh checkout on the cluster, then run the no-skip
`scripts/check_rr_cohort.py --output NEW/controls.json` on a CPU allocation from
that checkout. Its control set includes test_rr_response_probe.py. The existing
worker/planner locks from rr-response-diagnostics.2O5s92 may be reused only when
the preparation/submission compatibility checks accept them. The original export
must be supplied explicitly; keep private exports outside Git.

From the frozen checkout, prepare using actual paths:

```bash
"$BC_PYTHON" -I scripts/prepare_rr_response_probe.py \
  --export "$BC_RESPONSE_EXPORT" \
  --controls "$BC_RESPONSE/controls.json" \
  --worker-lock "$BC_DIAG/cpu/worker-lock.json" \
  --planner-lock "$BC_DIAG/cpu/planner-lock.json" \
  --preflight-run "$BC_RESPONSE_PREFLIGHT" \
  --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_RESPONSE/manifest.json"
```

BC_DIAG is the completed response-diagnostics qualification directory;
BC_RESPONSE is a fresh preparation/output directory. BC_RESPONSE_PREFLIGHT is
the output path in BC_DIAG/preflight-submission.json. Preparation verifies saved
snapshot evidence and selects exactly three calls, with separate task-input
labels. It does not load weights or execute any returned artifact. There is no
exact-rendered-prompt reproduction claim. The model receives no corrected answers.

Submit only through `scripts/bc.py submit --mode run --concurrency 1`, supplying
this manifest, the same worker lock and the selected NA100q cluster config. Use
`--dry-run` first and retain the receipt. No preflight mode, retry, override or
queued campaign is accepted. Inspect `response-diagnostic.json` in the returned
output directory after completion; `bc.py aggregate --output RUN` also returns
this diagnostic report. A parsed response is not a valid-artifact or correctness
claim. There are no episode scores and no cohort result replacement. An interrupted
or completed attempt cannot be submitted again under this manifest.


## Interface-reliability revision — current handoff, 12 October 2026

The first cohort completed: see [the trace audit](RICH_COHORT_TRACE_AUDIT_2026-10-12.md).
The commands in this section prepare a **new** combined interface revision,
`rr-interface-reliability-v1`. The older instructions below are retained as
historical instructions and must not be used to reuse an old approval or grammar.

The task requests, source/task/private hashes, terminal evaluator and scoped JIT
are unchanged. Interface hashes live in configurations/manifests, not task cards.
Source/runtime bindings and configuration/proposal IDs change. Original resolved
settings were checked against the uploaded cohort export: seed index 1 and its
four seed streams, uniform meaningful-owner selection, 8 planner calls / 2
revisions, 24 actions/units, pool 7, context 16384, worker 2048 / planner 6144,
100000 tokens / 1200 CPU seconds. Both planners get the same revised worker
contract in primary and repair. Requirement allocation still has zero model calls.

Four tasks × two planners × clean/F = 16 scheduled conditions. Task-major order
is Jaffle, Energy, topics, multioperation; planner order is requirement-level then
prompted-open; clean precedes F. Invalid planning retains two failed conditions
without worker execution. Wrong clean answers do not cancel F. Maximum logical
ceilings are 1600000 tokens / 19200 CPU seconds, with separate qualification and
terminal evaluation overhead. Review/rights status stays pending/deferred and
`confirmatory` stays false. No retry, seed search, extra targets or training.

### Local validation for this revision

Python 3.12.7; no model inference or cluster submission:

| Check | Result |
| --- | --- |
| Full `unittest discover -s tests -v` | 473 tests: 442 passed, 31 skipped; no failures/errors |
| Pinned `scripts/check_rr_cohort.py` | 127 passed; zero skips/failures/errors |
| Pinned `tests.test_sql_text` | 4 passed |
| New pinned `tests.test_rr_interface` | 16 passed, also included in the 127 controls |
| `scripts/check_shell.py` | All 10 shell files passed |
| `compileall`, `git diff --check`, `python -I -S scripts/bc.py --help` | Passed |
| Runbook Bash syntax | All 13 blocks parsed; none submitted/executed |

Thirty full-suite skips require optional pinned SQL/schema child dependencies;
the remaining skip is the separate legacy container qualification. Relevant
compiler, schema, cohort and scoped-recovery controls passed in the pinned CPU
environment. Exact Qwen tokenizer/XGrammar and GPU checks remain **pending**.
The local test reports are development checks, not reusable cluster locks.

Reproduce local checks (the optional environment path is workstation-specific):

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
/tmp/bc-rich-cpu/bin/python -m unittest tests.test_sql_text tests.test_rr_interface -v
BC_LOCAL_CHECKS="$(mktemp -d /tmp/rr-interface-controls.XXXXXX)"
/tmp/bc-rich-cpu/bin/python scripts/check_rr_cohort.py --output "$BC_LOCAL_CHECKS/controls.json"
```

### A. Freeze and submit CPU qualification

Run after reviewing/committing/pushing the implementation. This session has not
submitted any cluster job. Use one terminal; save the printed directory. Inspect
partition availability before running `sbatch`. This uses the existing wrapper
with an explicit source root, not Slurm's spool directory. It renews role grammars,
all task/public-feedback footprints and public terminal-ID grammar checks, then
prepares exactly four task-free GPU probes. It does not load model weights.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_DEV_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_BASE_LOCK="$BC_STORAGE/diagnostics/rr-rich-cohort.5tpWjC/cpu/worker-lock.json"
export BC_DEV="$(mktemp -d "$BC_STORAGE/diagnostics/rr-interface-v1.XXXXXX")"
export BC_DEV_CLUSTER="$BC_DEV/cluster.json"
(
set -euo pipefail
set -o noclobber
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: preserve exports outside Git and review local changes.\n'
    exit 1
fi
test -x "$BC_PYTHON"
test -s "$BC_BASE_LOCK"
git rev-parse HEAD > "$BC_DEV/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_DEV/source"
git -C "$BC_DEV/source" checkout --detach "$(cat "$BC_DEV/source-commit.txt")"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
c=json.loads(Path('configs/cluster.qwen27b-na100.local.json').read_text())
c['partition']='HPCAIq'
c['output_root']=str(Path(os.environ['BC_DEV'])/'outputs')
with Path(os.environ['BC_DEV_CLUSTER']).open('x') as f:json.dump(c,f,indent=2)
PY
sinfo -p PA100q,HPCAIq -N -o '%N %P %t %G'
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 --job-name=rr-interface-cpu \
  --chdir="$BC_DEV/source" --output="$BC_DEV/cpu.out" --error="$BC_DEV/cpu.err" \
  "$BC_DEV/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_DEV/source" --cohort-controls --rich-only --interface-reliability \
  --sources "$BC_DEV_SOURCES" --model-lock "$BC_BASE_LOCK" --output "$BC_DEV/cpu" \
  > "$BC_DEV/cpu-job.txt"
cat "$BC_DEV/cpu-job.txt"
printf 'Save directory: %s\n' "$BC_DEV"
)
```

```bash
sacct -j "$(cut -d';' -f1 "$BC_DEV/cpu-job.txt")" --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_DEV/cpu.err"
```

Proceed only after `COMPLETED 0:0`. CPU doubles and compiler tests are not model
competence. Missing tokenizer/XGrammar, grammar rejection, changed bindings or
prompt overflow are blockers; there is no instructions-only fallback. Do not
increase caps or drop a failed case.

### B. One four-probe GPU preflight

HPCAIq previously supplied a full A100 80GB PCIe allocation. Availability and
hardware are checked again; this is not a claim about current queue state.
Use the **same selected cluster config** for qualification and the cohort.
Preflight is separate task-free work, not one of the 16 study conditions.

```bash
(
set -euo pipefail
cd "$BC_DEV/source"
test -s "$BC_DEV/cpu/interface-preflight-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_DEV_CLUSTER" --manifest "$BC_DEV/cpu/interface-preflight-manifest.json" \
  --model-lock "$BC_DEV/cpu/worker-lock.json" --dry-run
)
```

After inspecting the dry run, submit the preflight once through the registry:

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_DEV/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_DEV_CLUSTER" --manifest "$BC_DEV/cpu/interface-preflight-manifest.json" \
  --model-lock "$BC_DEV/cpu/worker-lock.json" > "$BC_DEV/preflight-submission.json"
cat "$BC_DEV/preflight-submission.json"
)
export BC_DEV_PREFLIGHT="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["output"])' "$BC_DEV/preflight-submission.json")"
export BC_DEV_PREFLIGHT_JOB="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job_id"])' "$BC_DEV/preflight-submission.json")"
sacct -j "$BC_DEV_PREFLIGHT_JOB" --format=JobID,State,ExitCode,Elapsed
```

Wait for completion, then inspect `preflight.json`. It must report all four cases
passed, zero uncertain tokens and `command_failed: false`. Observed cases do not
establish universal worst-case memory fit. Do not rerun on ordinary probe failure.

### C. Audit new evidence and prepare the prospective proposal

```bash
(
set -euo pipefail
cd "$BC_DEV/source"
"$BC_PYTHON" -I scripts/bc.py rr-open-footprint-audit \
  --run "$BC_DEV_PREFLIGHT" --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_DEV/footprint-audit.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_DEV'])
def read(p):return json.loads(p.read_text())
tasks=('jaffle-payment-release','energy-single-indicator-release',
       'github-topics-client-package','github-multioperation-integration')
e={'controls':read(r/'cpu/cohort-controls.json'),'footprint_audit':read(r/'footprint-audit.json'),
   'tasks':{t:read(r/'cpu'/f'{t}.json') for t in tasks},
   'task_footprints':{t:read(r/'cpu'/f'{t}-footprint.json') for t in tasks},'reviews':{}}
with (r/'evidence.json').open('x') as f:json.dump(e,f,indent=2)
PY
"$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest \
  --lane rich_development_unreviewed --interface-profile rr-interface-reliability-v1 \
  --sources "$BC_DEV_SOURCES" --model-lock "$BC_DEV/cpu/worker-lock.json" \
  --planner-lock "$BC_DEV/cpu/planner-lock.json" --evidence "$BC_DEV/evidence.json" \
  --output "$BC_DEV/proposal.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
  --manifest "$BC_DEV/proposal.json" --model-lock "$BC_DEV/cpu/worker-lock.json" \
  --output "$BC_DEV/review.json"
"$BC_PYTHON" -m json.tool "$BC_DEV/review.json"
)
```

This creates the exact prospective ID only after real cluster qualification.
No local draft ID substitutes for it. A **new exact-scope approval** is required
by the existing `rr-cohort-approve` mechanism. The implementation/preparation
instruction does not reuse the previous run's approval. Show the proposal and
review to the user; after approval of this concrete scope, use the existing
approval-record block in historical section 4 below with this new `BC_DEV`.
It records execution consent, never independent task/rights review. Technical
blockers must be empty. Preserve pending reviews.

### D. Finite run, monitoring, interrupted coverage and export

After the new approval is bound, use sections 5 and 6 below unchanged, with the
new `BC_DEV`, `BC_DEV_CLUSTER` and approved manifest. Those are the actual CLI
commands for concurrency-one submission, `sacct`, aggregation and public/private
exports. They do not silently retry a started shard. **There is no retry/resume
command for started cohort configurations**: inspect/export interrupted coverage;
resume only never-started work through the existing guarded submission path if
its checks permit it. Infrastructure/accounting/integrity defects pause the study;
ordinary semantic, budget and validly recorded planning failures remain results.

Do not run the historical CPU/lock reuse instructions in sections 1–3 below.
Do not change code, prompts or grammar halfway through the new cohort. Keep the
old result unchanged and report any new result as a combined interface revision,
not causal evidence for any one fix. Stop after the finite study for review.

---

## Historical pre-revision handoff (retained; superseded above)

Date: 2026-10-12. The user explicitly instructed proceeding after the audit,
deferring review. This handoff does not invent reviewers, evidence or rights
clearance. The earlier reviewed `rich_pilot` lane remains strict. Use the new
`rich_development_unreviewed` lane only for this bounded development comparison.

Four tasks, eight task/planner configurations, maximum sixteen clean/F branches;
concurrency one, no retry, no stock rerun. Worker cap 2048, planner cap 6144,
context 16384, seven logical identities, unchanged per-branch 100000 token and
1200 CPU-second caps. Pending source/provider rights remain unresolved.

## 1. After committing and pushing, freeze on Jupyter

Run each block once in the same terminal. Stop on error. All output stays outside
Git. Existing datasets, compatible role locks and audited GPU evidence are reused;
no new download or GPU qualification is requested automatically.

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_PREVIOUS="$BC_STORAGE/diagnostics/rr-four-task.y6a46O"
export BC_DEV_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_DEV_CLUSTER="$HOME/Beyond-Consensus/configs/cluster.qwen27b-na100.local.json"
export BC_DEV_PREFLIGHT="$BC_STORAGE/outputs/qwen27b-na100/e923cb200f4835deb8457fe14e7bf50ee488b5b8be5d5070819bbaf75954f8e1-preflight"
export BC_DEV="$(mktemp -d "$BC_STORAGE/diagnostics/rr-four-unreviewed.XXXXXX")"
(
set -euo pipefail
set -o noclobber
git pull --ff-only
if test -n "$(git status --porcelain)"; then
    git status --short
    printf 'STOP: preserve exports outside Git and review local edits.\n'
    exit 1
fi
for path in "$BC_PYTHON" "$BC_PREVIOUS/cpu/worker-lock.json" \
    "$BC_PREVIOUS/cpu/planner-lock.json" "$BC_DEV_CLUSTER"
do
    if ! test -s "$path"; then printf 'STOP: missing %s\n' "$path"; exit 1; fi
done
git rev-parse HEAD > "$BC_DEV/source-commit.txt"
git clone --no-hardlinks "$PWD" "$BC_DEV/source"
git -C "$BC_DEV/source" checkout --detach "$(cat "$BC_DEV/source-commit.txt")"
sbatch --parsable --partition=PA100q --nodes=1 --ntasks=1 \
  --cpus-per-task=4 --mem=32G --time=02:00:00 --job-name=rr-dev-cpu \
  --chdir="$BC_DEV/source" --output="$BC_DEV/cpu.out" --error="$BC_DEV/cpu.err" \
  "$BC_DEV/source/experiments/qualify_reporecourse.sh" \
  --repo-root "$BC_DEV/source" --cohort-controls --rich-only \
  --sources "$BC_DEV_SOURCES" --output "$BC_DEV/cpu" \
  --worker-lock "$BC_PREVIOUS/cpu/worker-lock.json" \
  --planner-lock "$BC_PREVIOUS/cpu/planner-lock.json" > "$BC_DEV/cpu-job.txt"
cat "$BC_DEV/cpu-job.txt"
)
printf 'Keep this directory: %s\n' "$BC_DEV"
```

## 2. Wait for CPU completion

```bash
sacct -j "$(cut -d';' -f1 "$BC_DEV/cpu-job.txt")" \
  --format=JobID,State,ExitCode,Elapsed
tail -n 40 "$BC_DEV/cpu.err"
```

Proceed only after `COMPLETED 0:0`. The new admission controls renew the changed
source contract; old reports are not rewritten to pass it.

## 3. Audit existing GPU evidence and prepare the exact proposal

```bash
(
set -euo pipefail
cd "$BC_DEV/source"
"$BC_PYTHON" -I scripts/bc.py rr-open-footprint-audit \
  --run "$BC_DEV_PREFLIGHT" --snapshots "$BC_STORAGE/snapshots" \
  --output "$BC_DEV/footprint-audit.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_DEV'])
tasks=('jaffle-payment-release','energy-single-indicator-release',
       'github-topics-client-package','github-multioperation-integration')
def read(p): return json.loads(p.read_text())
controls=read(r/'cpu/cohort-controls.json')
if controls['status']!='passed' or any(controls[k] for k in ('skipped','failures','errors')):
    raise SystemExit('STOP: CPU controls failed')
if read(r/'cpu/role-lock-reuse.json')['status']!='compatible':
    raise SystemExit('STOP: incompatible role locks')
e={'controls':controls,'tasks':{t:read(r/'cpu'/f'{t}.json') for t in tasks},
   'task_footprints':{t:read(r/'cpu'/f'{t}-footprint.json') for t in tasks},
   'footprint_audit':read(r/'footprint-audit.json'),'reviews':{}}
for t in tasks:
    if e['tasks'][t]['status']!='cpu_qualified_review_pending' or e['task_footprints'][t]['status']!='passed':
        raise SystemExit('STOP: task qualification failed: '+t)
with (r/'evidence.json').open('x') as h:
    json.dump(e,h,indent=2);h.write('\n')
PY
"$BC_PYTHON" -I scripts/bc.py rr-cohort-manifest \
  --lane rich_development_unreviewed --sources "$BC_DEV_SOURCES" \
  --model-lock "$BC_DEV/cpu/worker-lock.json" --planner-lock "$BC_DEV/cpu/planner-lock.json" \
  --evidence "$BC_DEV/evidence.json" --output "$BC_DEV/proposal.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-review \
  --manifest "$BC_DEV/proposal.json" --model-lock "$BC_DEV/cpu/worker-lock.json" \
  --output "$BC_DEV/review.json"
"$BC_PYTHON" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['BC_DEV']);d=json.loads((r/'review.json').read_text())
print(json.dumps({k:d[k] for k in ('experiment_id','lane','limitations','blockers','approval_template')},indent=2))
if d['blockers']:raise SystemExit('STOP: technical prerequisites remain blocked')
PY
)
```

Pending task and rights fields are generated as pending records in the manifest.
Do not edit them into fictitious approvals. New lane and limitations are included
in the manifest identity and exact approval scope.

## 4. Record the already-authorized bounded development run

The user has authorized this scope and review deferral. This records that
authorization under the user's cluster account; it is not an independent review.
The command does not request another decision or approve a broader campaign.

```bash
(
set -euo pipefail
cd "$BC_DEV/source"
"$BC_PYTHON" - <<'PY'
import getpass, json, os
from datetime import datetime, timezone
from pathlib import Path
r=Path(os.environ['BC_DEV']);d=json.loads((r/'review.json').read_text())
if d['blockers'] or d['lane']!='rich_development_unreviewed':
    raise SystemExit('STOP: unexpected lane or technical blockers')
a=d['approval_template']
if a['maximum_execution_branches']!=16:raise SystemExit('STOP: scope differs')
a.update(decision='approved',reviewer=getpass.getuser(),reviewed_at=datetime.now(timezone.utc).isoformat())
with (r/'approval.json').open('x') as h:json.dump(a,h,indent=2);h.write('\n')
PY
"$BC_PYTHON" -I scripts/bc.py rr-cohort-approve \
  --manifest "$BC_DEV/proposal.json" --model-lock "$BC_DEV/cpu/worker-lock.json" \
  --approval "$BC_DEV/approval.json" --output "$BC_DEV/approved-manifest.json"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_DEV_CLUSTER" --manifest "$BC_DEV/approved-manifest.json" \
  --model-lock "$BC_DEV/cpu/worker-lock.json" --dry-run
)
```

## 5. Submit once after successful dry run

```bash
(
set -euo pipefail
set -o noclobber
cd "$BC_DEV/source"
"$BC_PYTHON" -I scripts/bc.py submit --mode run --concurrency 1 \
  --cluster "$BC_DEV_CLUSTER" --manifest "$BC_DEV/approved-manifest.json" \
  --model-lock "$BC_DEV/cpu/worker-lock.json" > "$BC_DEV/run-submission.json"
cat "$BC_DEV/run-submission.json"
)
```

Do not repeat submission after a started attempt. Existing scheduler/registry,
fixed ordering, pause-on-infrastructure and no-retry controls remain active.
Do not change partitions after hardware-bound qualification without checking
the existing compatibility gate. A failed gate needs inspection, not bypass.

## 6. Monitor and export after completion

```bash
export BC_DEV_JOB="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["job_id"])' "$BC_DEV/run-submission.json")"
export BC_DEV_OUTPUT="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["output"])' "$BC_DEV/run-submission.json")"
sacct -j "$BC_DEV_JOB" --format=JobID,State,ExitCode,Elapsed
```

After all array tasks finish, export once to a fresh directory. If interrupted,
the same read-only commands preserve missing/failed rows; they do not resume.

```bash
export BC_DEV_RESULTS="$(mktemp -d "$BC_DEV/results.XXXXXX")"
(
set -euo pipefail
cd "$BC_DEV/source"
"$BC_PYTHON" -I scripts/bc.py aggregate --output "$BC_DEV_OUTPUT" \
  > "$BC_DEV_RESULTS/aggregate.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-export --run "$BC_DEV_OUTPUT" \
  --output "$BC_DEV_RESULTS/audit.private.json"
"$BC_PYTHON" -I scripts/bc.py rr-cohort-export --run "$BC_DEV_OUTPUT" --public \
  --output "$BC_DEV_RESULTS/public.json"
printf 'Results directory: %s\n' "$BC_DEV_RESULTS"
)
```

Reports retain `lane=rich_development_unreviewed`, `review_status=deferred_by_user`
and unresolved-review limitations. Scores remain development observations;
neither review clearance nor population inference follows from success.

## Local verification before handoff

- Full standard-library suite: 457 tests, 428 passed and 29 optional skips;
  no failures or errors.
- Pinned cohort controls: 111 passed, zero skips, failures or errors.
- Focused cohort suite: 32 tests, 31 passed and one optional skip (covered by
  the pinned controls).
- All 10 shell files passed the shell checker. All seven Bash blocks in this
  runbook parsed with `bash -n`. CLI help passed under `python -I -S`.
- New tests cover exact approval/limit binding, pending review preservation,
  public export labels, rejection of invented approvals, and equality of all
  non-review blockers between reviewed and unreviewed lanes.

No model inference, cluster submission, commit or push was performed locally.


## Decoder boundary audit after response reconstruction (2026-10-14)

Do not repeat the three model calls or launch another cohort. The next diagnostic
is a CPU-only synthetic matcher/parser comparison. Freeze the pushed checkout
and run the following inside a CPU batch allocation (Python 3.12 environment
with the existing pinned tokenizer/XGrammar dependencies). Use a fresh output:

```bash
"$BC_PYTHON" -I scripts/probe_decoder_boundary.py \
  --model-lock /dataset/suaq0001/beyond-consensus/diagnostics/rr-response-diagnostics.2O5s92/cpu/worker-lock.json \
  --output "$BC_BOUNDARY/decoder-boundary.json"
```

The Slurm wrapper must explicitly `cd` to the frozen source directory; it must
not derive the source path from its spooled script location. This program uses
no model weights, GPU, task sources, hidden evaluator or historical response.
It first reuses the existing metadata/version and baseline decoder controls.
Its `observed` status means the synthetic comparison completed, not that the
runtime parser and grammar necessarily agree on duplicate-key texts. Inspect
`cases` (direct matcher, EOS and both gated routes) and `errors` together. Save
this report separately; it cannot replace a qualified lock or historical score.


## Prospective unique-key worker CPU qualification (2026-10-14)

After freezing the pushed source, first run the no-skip cohort CPU controls
(which now include `test_unique_keys.py`). Then, in the same CPU batch environment
with pinned optional dependencies, use a fresh output directory:

```bash
"$BC_PYTHON" -I scripts/check_action_constraints.py \
  --model-lock /dataset/suaq0001/beyond-consensus/diagnostics/rr-response-diagnostics.2O5s92/cpu/worker-lock.json \
  --action-constraint reporecourse-json-unique-v1-pool-7 \
  --context-limit 16384 \
  --output-cap 2048 \
  --output "$BC_UNIQUE/worker-grammar.json" \
  --qualified-lock "$BC_UNIQUE/worker-lock.json"
```

The input lock supplies staged metadata, not authorization for the new mode.
Inspect `unique_key_controls.status`, all case rows, CPU times and the ordinary
qualification status. Preserve the old lock/report. No model, task data or SQL
is used by this grammar qualification. A native positive control rejection or
CPU allowance failure is a blocker, not permission to loosen the parser, raise
caps or bypass the guard. This step does not submit or authorize a cohort; a
new GPU footprint and prospective mode-bound run preparation remain separate.

Implementation API reference: pinned [XGrammar v0.1.32 TokenizerInfo](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/python/xgrammar/tokenizer_info.py)
provides decoded vocabulary bytes; the [HF processor](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/python/xgrammar/contrib/hf.py)
is initialized when the reasoning gate activates. No dependency upgrade is made.
