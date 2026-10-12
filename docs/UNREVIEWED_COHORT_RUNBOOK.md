# Four-task unreviewed development run

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
