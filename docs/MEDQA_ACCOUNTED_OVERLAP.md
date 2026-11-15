# MedQA: user-authorised accounted GPU overlap

The user explicitly requested concurrent GPU submissions after the MedQA dry run rejected external job 1122666. This narrowly supersedes the one-active-campaign rule for this MedQA launch: external and registered jobs may coexist when their reported active/pending physical GPU reservations plus this new one-GPU job total at most four. Four jobs are not necessarily four GPUs. No job is cancelled, no unknown accounting is assumed zero, and Slurm still decides placement/availability.

The shared guard now offers an opt-in `allow_accounted_overlap=True, requested_gpus=1`. Default callers retain their previous exclusive behavior. Every active/pending array element is conservatively counted, even if an array has a serial throttle. Unknown ReqTRES, uncertain submissions, or registered jobs absent from squeue without terminal confirmation still block. Admission is an observation of scheduler state, not a lock over submissions from unrelated applications; the allocated job rechecks the aggregate before dispatch.

The MedQA scope binds `accounted-overlap-four-gpu-v1`, and uses that policy at submission and runtime. Its own allocation remains one GPU. Submission appends to registry jobs instead of falsely moving other jobs to completed history. Cohort no-retry, snapshot hashes, environment, source integrity, exact approvals, request limits and all other checks remain unchanged. The general scheduler library's default exclusivity and historical releases are preserved.

## Existing attempt

`medqa-planner-approved.kw1yXa` scope `c7c4ff84f72a827f326a9957f6a293def0d57e257db486245d73946d0396eaa7` failed in the dry-run guard before snapshot creation or sbatch. Its approval remains evidence of the user's decision; its files, including the potentially empty dry-run receipt, must not be overwritten. Prepare a new scope for the explicitly requested scheduler-policy change, using those existing binding inputs. No new source/tokenizer preparation is needed.

## Local transfer

Check for unrelated staged changes first.

```bash
cd /home/gnoriq/repos/Beyond-Consensus
git diff --cached --name-only
git add -- src/beyond_consensus/experiments/cluster.py src/bc_phase2/medqa_planner_launch.py tests/test_cluster.py tests/test_medqa_planner_launch.py docs/MEDQA_ACCOUNTED_OVERLAP.md
git diff --cached --stat
git commit -m "Allow accounted four-GPU overlap for MedQA planner launch"
git push origin HEAD
```

## Jupyter: rebind and submit once

```bash
(
set -euo pipefail
umask 077
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MEDQA_RUN="$(mktemp -d "$BC_STORAGE/diagnostics/medqa-planner-overlap.XXXXXX")"
printf 'New preparation: %s\n' "$BC_MEDQA_RUN"
scontrol show partition HPCAIq -o > "$BC_MEDQA_RUN/partition.txt"
"$BC_PYTHON" -B - <<'PY'
import getpass,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'src'))
from bc_phase2 import medqa_planner_launch as launch
root=Path(os.environ['BC_MEDQA_RUN'])
old=Path(os.environ['BC_STORAGE'])/'diagnostics/medqa-planner-approved.kw1yXa'
previous=json.loads((old/'manifest.disabled.json').read_text())
if previous['scope_digest']!='c7c4ff84f72a827f326a9957f6a293def0d57e257db486245d73946d0396eaa7':
    raise SystemExit('STOP: unexpected previous scope')
if launch.digest(previous['scope'])!=previous['scope_digest']:
    raise SystemExit('STOP: previous scope integrity mismatch')
receipt=old/'submission.json'
if receipt.exists():
    raise SystemExit('STOP: submission record exists; reconcile it before proceeding')
a=json.loads((old/'approval.json').read_text())
if (a.get('decision')!='approved' or a.get('scope_digest')!=previous['scope_digest']
    or a.get('statement_transmission_authorized') is not True or a.get('GPU_spending_authorized') is not True):
    raise SystemExit('STOP: missing prior approval')
inputs=previous['binding_inputs']
inputs['config_data']['output_root']=str(root/'outputs')
inputs['partition_record']=(root/'partition.txt').read_text()
manifest=launch.bind(**inputs)
if manifest['blockers'] or manifest['scope']['resources']!=previous['scope']['resources']:
    raise SystemExit('STOP: blockers or changed experimental limits')
expected={'version':'accounted-overlap-four-gpu-v1','maximum_user_gpus':4,
          'requested_gpus':1,'allow_accounted_external_jobs':True}
if manifest['scope'].get('scheduler_policy')!=expected:
    raise SystemExit('STOP: unexpected scheduler policy')
summary=launch.review(manifest)
approval=dict(summary['approval_template'])
approval.update(decision='approved',reviewer=getpass.getuser(),
    reviewed_at=datetime.now(timezone.utc).isoformat(),
    statement_transmission_authorized=True,GPU_spending_authorized=True)
release=launch.approve(manifest,approval)
for name,value in [('manifest.disabled.json',manifest),('review.json',summary),
                   ('approval.json',approval),('release.json',release),
                   ('authorization-context.json',{'parent_scope':previous['scope_digest'],
                    'user_instruction':'Allow multi gpu jobs submission, my slurm allows me to submit 4 consecutive jobs at once.',
                    'interpretation':'accounted simultaneous physical GPU reservations at most four; MedQA uses one'})]:
    with (root/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps({'directory':str(root),'scope_digest':manifest['scope_digest'],
    'scheduler_policy':expected,'limits':manifest['scope']['resources'],
    'approval_recorded':True,'model_executed':False,'submitted':False},indent=2))
PY
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_RUN/release.json" --dry-run \
  --output "$BC_MEDQA_RUN/submission-dry-run.json"
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_RUN/release.json" \
  --output "$BC_MEDQA_RUN/submission.json"
cat "$BC_MEDQA_RUN/submission.json"
printf '\nRun directory: %s\n' "$BC_MEDQA_RUN"
)
```

Do not repeat the block on failure. Preserve the printed directory and receipt/error. This authorisation covers the unchanged twelve-question planner job, not a larger MedQA worker experiment. No actual Slurm state was queried locally during implementation.

## Offline validation

51 focused tests passed in 2.647 seconds: `test_cluster`, `test_medqa_planner_launch`, `test_math500_screen_launch`, `test_d1_natural_launch`. Coverage includes legacy exclusivity, 1+1 and 3+1 GPU admission, 4+1 rejection, multi-GPU/array counts, missing/unknown accounting, uncertain submissions, runtime aggregate checks, and preservation of another registered job during successful submission. All 22 shell checks and standard-library-only CLI help passed. Documented shell and Python command syntax passed. Evidence: `outputs/medqa-overlap-review/`. No real scheduler/model operation or commit/push was performed.
