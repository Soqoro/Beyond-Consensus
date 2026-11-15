# MedQA role-specific worker v2: bounded launch packet

This is a new prospective scope, not a resubmission of job 1122728. That run remains profile-blocked: four calls, 5,777 tokens; NEUTRAL and JOINT unrun. Its old approval is not transferable.

Only worker instruction text changes: intermediate tasks receive no terminal option-label directive; terminal tasks receive only their own output directive. Shared model, source options, responsibilities, graph, neutral grouping, schema fields and numeric limits remain unchanged. All five profile prices are fresh because both role prompts changed. No answer from the failed response is used.

Exactly one composite: dev/row/339 (one task), dev/row/970 (two), dev/row/479 (two). Contracts are in `configs/phase2/medqa_worker_first_v1.json`. They are reviewer-authored, solution-free translations of the original plans. Contract acceptance is recorded with the final scope approval, not fabricated by preparation.

Exactly NEUTRAL versus JOINT, n=4, K=2, mean-first, one clean execution and all four R0 owner repairs per distinct organisation. A and C are fixed; only B can change. Neutral is deterministically frozen before prices. Five fresh profile calls; no historical medical or MATH price reuse. Up to 28 evaluation calls, **33 new worker calls total**, 540,672 tokens, 3,072 output / 13,312 input / 16,384 context, one >=80 GB GPU, four CPUs, 128 GB host RAM, four hours on HPCAIq. Solver: 30 seconds, one thread, seed zero. Shared per-user registry counts accounted active/pending jobs toward the authorized four-GPU total; unknown accounting remains blocking.

The exact model is Qwen/Qwen3.5-27B, revision fc05daec18b0a78c049392ed2e771dde82bdf654, non-thinking, deterministic BF16/SDPA. The existing planner release supplies pinned inventory and public source provenance; its approval does not authorize workers. New approval must accept the three contracts, their statement transmission, development use of the pinned mirror with its unchanged provenance limitations, and these GPU ceilings.

## Transfer (local checkout, user performs)

```bash
git add src/bc_phase2/medqa_worker_launch.py tests/test_medqa_worker_launch.py docs/MEDQA_FIRST_WORKER_LAUNCH.md docs/MEDQA_WORKER_ROLE_V2.md
git commit -m "Separate intermediate and terminal MedQA worker instructions"
git push origin main
```

Review any already-staged unrelated files before committing. The commands do not intentionally stage historical outputs or datasets.

## Jupyter: CPU qualification and disabled preparation only

```bash
(
set -euo pipefail
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MEDQA_WORK="$(mktemp -d "$BC_STORAGE/diagnostics/medqa-worker-role-v2.XXXXXX")"
export BC_MEDQA_PARENT="$BC_STORAGE/diagnostics/medqa-planner-overlap.h3AQSA"
printf 'Worker preparation: %s\n' "$BC_MEDQA_WORK"

# Locate the exact approved planner release, without searching private datasets.
export BC_MEDQA_RELEASE="$("$BC_PYTHON" - <<'PY'
import json,os
from pathlib import Path
root=Path(os.environ['BC_MEDQA_PARENT']);matches=[]
for p in sorted(root.glob('*.json')):
    if p.stat().st_size>64*1024*1024: continue
    try: v=json.loads(p.read_text())
    except (ValueError,UnicodeError): continue
    if isinstance(v,dict) and v.get('release_digest') and v.get('manifest',{}).get('scope_digest')=='a8d507df9bd66c0b0223e04787beb37a8d1eaa393f0591c98f0bd6e2bc66fd90': matches.append(p)
if len(matches)!=1: raise SystemExit(f'STOP: expected one approved release, found {len(matches)}')
print(matches[0])
PY
)"

"$BC_PYTHON" -I -B scripts/medqa_worker.py qualify \
  --snapshot "$BC_STORAGE/models/hub/models--Qwen--Qwen3.5-27B/snapshots/fc05daec18b0a78c049392ed2e771dde82bdf654" \
  --output "$BC_MEDQA_WORK/qualification.json"

"$BC_PYTHON" - <<'PY'
import json,os
from pathlib import Path
root=Path(os.environ['BC_MEDQA_WORK'])
r=json.loads(Path(os.environ['BC_MEDQA_RELEASE']).read_text())
c=r['manifest']['scope']['cluster'].copy()
c.update(partition='HPCAIq',time='04:00:00',memory_gb=128,output_root=str(root/'outputs'))
(root/'cluster.json').write_text(json.dumps(c,indent=2)+'\n')
PY

"$BC_PYTHON" -I -B scripts/medqa_worker.py prepare \
  --parent-release "$BC_MEDQA_RELEASE" \
  --cluster "$BC_MEDQA_WORK/cluster.json" \
  --qualification "$BC_MEDQA_WORK/qualification.json" \
  --output "$BC_MEDQA_WORK/bound"
scontrol show partition HPCAIq -o > "$BC_MEDQA_WORK/partition.txt"
squeue --array -u "$USER" -o "%.22i %.12P %.20j %.2t %.10M %R" > "$BC_MEDQA_WORK/queue.txt"
printf 'Saved preparation: %s\n' "$BC_MEDQA_WORK"
)
```

Qualification loads only the pinned local tokenizer, not weights. Preparation measures the three parent-free rendered requests. Generated-parent request fit is enforced at every dispatch, not claimed in advance. A qualification failure blocks approval. Send the preparation summary for exact scope approval; do not rerun planning or expand the composite.

## Executable launch command after exact approval

Set BC_MEDQA_WORK to the directory printed above. After the externally reviewed `approval.json` is recorded with the exact scope digest and all three permission flags true:

```bash
"$BC_PYTHON" -I -B scripts/medqa_worker.py approve \
  --manifest "$BC_MEDQA_WORK/bound/MANIFEST.disabled.json" \
  --approval "$BC_MEDQA_WORK/approval.json" \
  --output "$BC_MEDQA_WORK/approved-release.json"
"$BC_PYTHON" -I -B scripts/medqa_worker.py submit \
  --release "$BC_MEDQA_WORK/approved-release.json" --dry-run \
  --output "$BC_MEDQA_WORK/submission-dry-run.json"
"$BC_PYTHON" -I -B scripts/medqa_worker.py submit \
  --release "$BC_MEDQA_WORK/approved-release.json" \
  --output "$BC_MEDQA_WORK/submission.json"
```

Only one submission for this recipe is allowed. No automatic retry/replacement. Known failed profiles leave the pair explicitly blocked. Unknown usage halts. Wrong completed answers remain measured outcomes; exact option grading occurs after execution with `medqa_worker.py grade --result ... --public ... --protected ... --output ...`. The private evaluator is never loaded by preparation, selection or the GPU runner. Retained/repeated outputs are not independent trials. No clinical reliability claim is made.
