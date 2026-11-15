# MedQA planner run — user-authorised pinned mirror

The user instructed: “just treat this as the original medqa and proceed with the experiments.” This supersedes the earlier source-admission blocker for this exact development pilot. It authorises use of the frozen mirror and the currently prepared twelve-call planner stage. It does not establish archive equivalence, certify underlying rights, authorise a different source or select/launch the later worker composites.

The new optional source-review exception is bound to the existing dataset hash and cohort. Its factual fields must remain `not_independently_verified` and `unresolved`; the admission decision is distinct from those facts. No prompts, source IDs, model settings, task-selection policy or resource caps change. Old pending/blocked packets remain intact. No additional approval is requested for this already authorised planner scope.

Limits: 12 calls, one per question, no retry/correction, 3,072 output tokens/call, context 16,384, aggregate hard cap 196,608 tokens, one hour on HPCAIq, one >=80GB GPU, 4 CPUs, 128GB RAM. Exact measured reservations total 53,646 tokens. The shared registry/scheduler guard remains mandatory; another active/pending GPU campaign can block submission. Do not cancel unrelated work or bypass the guard.

## Local transfer

Check the staged list first. Do not include unrelated staged files in this commit.

```bash
cd /home/gnoriq/repos/Beyond-Consensus
git diff --cached --name-only
git add -- src/bc_phase2/medqa_planner_launch.py tests/test_medqa_planner_launch.py docs/MEDQA_AUTHORIZED_PLANNER_COMMANDS.md
git diff --cached --stat
git commit -m "Record scoped user acceptance of pinned MedQA development mirror"
git push origin HEAD
```

## Jupyter: bind the exception, record the existing approval, and submit once

This reuses the measured requests and original inventory receipt from the existing bound packet. It does not repeat selection or tokenizer preparation. It records the user's current decision under the new exact scope digest, preserving previous evidence. It also saves an approval/manifest review before any scheduler action.

```bash
(
set -euo pipefail
umask 077
cd "$HOME/Beyond-Consensus"
git pull --ff-only

export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MEDQA_RUN="$(mktemp -d "$BC_STORAGE/diagnostics/medqa-planner-approved.XXXXXX")"
printf 'Run preparation: %s\n' "$BC_MEDQA_RUN"

scontrol show partition HPCAIq -o > "$BC_MEDQA_RUN/partition.txt"

"$BC_PYTHON" -B - <<'PY'
import getpass,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'src'))
from bc_phase2 import medqa_planner_launch as launch
from bc_phase2.medqa_development import PLAN_LIMITS

root=Path(os.environ['BC_MEDQA_RUN'])
old=Path(os.environ['BC_STORAGE'])/'diagnostics/medqa-planner-launch.oBZzRa/bound/manifest.disabled.json'
previous=json.loads(old.read_text())
if previous['scope_digest']!='9da30a6fc1ec0dc386d9e37e90f9696019aeaed9f6d5b2b6a894cb6d36f8e800':
    raise SystemExit('STOP: unexpected parent scope')
if launch.digest(previous['scope'])!=previous['scope_digest']:
    raise SystemExit('STOP: changed parent scope')
inputs=previous['binding_inputs']
inputs['config_data']['output_root']=str(root/'outputs')
inputs['partition_record']=(root/'partition.txt').read_text()
review=dict(inputs['source_review'])
review.update(
    reviewer=getpass.getuser(),reviewed_at=datetime.now(timezone.utc).isoformat(),
    evidence_reference='User instruction in Beyond Consensus conversation; see docs/MEDQA_AUTHORIZED_PLANNER_COMMANDS.md',
    admission_exception={
        'policy':launch.MIRROR_POLICY,
        'authorization_quote':'just treat this as the original medqa and proceed with the experiments.',
        'scope':'frozen_12_source_planner_only',
    },
)
inputs['source_review']=review
manifest=launch.bind(**inputs)
if manifest['blockers'] or manifest['scope']['resources']!=PLAN_LIMITS:
    raise SystemExit('STOP: unexpected blockers or resources')
if PLAN_LIMITS!={'maximum_calls':12,'context':16384,'input_cap':13312,'output_cap':3072,
                'token_cap':196608,'wall_seconds':3600,'physical_gpus':1,'cpus':4,
                'host_memory_gb':128,'minimum_vram_bytes':80000000000}:
    raise SystemExit('STOP: authorised limits changed')
summary=launch.review(manifest)
approval=dict(summary['approval_template'])
approval.update(decision='approved',reviewer=getpass.getuser(),
    reviewed_at=datetime.now(timezone.utc).isoformat(),
    statement_transmission_authorized=True,GPU_spending_authorized=True)
release=launch.approve(manifest,approval)
for name,value in [('source-review.json',review),('manifest.disabled.json',manifest),
                   ('review.json',summary),('approval.json',approval),('release.json',release)]:
    with (root/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps({'directory':str(root),'scope_digest':manifest['scope_digest'],
    'cohort_digest':launch.COHORT,'blockers':manifest['blockers'],'limits':PLAN_LIMITS,
    'source_policy':launch.MIRROR_POLICY,'approval_recorded':True,
    'model_executed':False,'submitted':False},indent=2))
PY

"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_RUN/release.json" --dry-run \
  --output "$BC_MEDQA_RUN/submission-dry-run.json"

"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_RUN/release.json" \
  --output "$BC_MEDQA_RUN/submission.json"

cat "$BC_MEDQA_RUN/submission.json"
printf '\nRun preparation: %s\n' "$BC_MEDQA_RUN"
)
```

If the scheduler guard blocks another GPU campaign, the scope preparation and approval remain saved. Do not repeat the whole block or overwrite receipts. Use the printed directory to inspect the failure and establish whether submission occurred before any further action. A failed/uncertain submission is not permission to retry. New output paths do not reset the cohort no-retry guard.

The resulting job stops after the twelve planning attempts (or an accounting/integrity/resource stop), retaining invalid/unsupported responses and unrun rows. Later profiling/recovery requires actual reviewed task contracts and its own concrete worker scope; the planner job does not chain into that stage.

## Validation of this amendment

43 focused tests passed in 14.525 seconds (MedQA launch, next-results adapter, historical screening and natural launch). The added regression verifies that the explicit user exception permits this exact cohort while retaining unresolved factual fields; it rejects changed source/cohort hashes, broader exception scope, altered authorisation text, missing reviewer identity and false verified labels. Existing pending reviews remain blocked without the exception. All 22 shell checks passed; CLI help passed with site packages disabled; documented command syntax and `git diff --check` passed. Evidence is under `outputs/medqa-mirror-policy-review/`. No real model, scheduler, data download, commit or push was executed locally.
