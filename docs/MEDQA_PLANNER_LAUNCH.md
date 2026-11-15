# Frozen MedQA planner-only launch handoff

This adds the missing launch connection for the existing twelve-source cohort. It does not change the MedQA prompt, selected sources, optimiser, worker interface, historical evidence, or accepted request sizes. No data download, benchmark read, model execution, Slurm operation, staging, commit, or push was performed during implementation.

## Frozen evidence and scope

- Cohort: `1f471cbd92f4f957678bc26af84985ffb44699422122367c297f83983e6159a0`.
- Public file SHA-256: `c38c5fd2b9b4d5661810fe4eac0f267490244ccdbe6ac6d1a360fa8ce16edb4b`.
- Jupyter cohort: `/dataset/suaq0001/beyond-consensus/diagnostics/medqa-cohort.xKzwlB/intake/cohort.public.json`.
- Jupyter token-fit report: `/dataset/suaq0001/beyond-consensus/diagnostics/medqa-token-fit.SkqoLe/token-fit.json`.
- User-supplied tokenizer evidence: twelve inputs, 1,306–1,465 tokens; total input plus output reservations 53,646 tokens. This is fit evidence, not generated-plan quality or GPU-memory qualification.
- Qwen/Qwen3.5-27B revision `fc05daec18b0a78c049392ed2e771dde82bdf654`; deterministic non-thinking generation using the unchanged natural-screen transport.
- Maximum twelve calls, one per source, no correction or retry. Output 3,072/input 13,312/context 16,384. Aggregate hard cap 196,608 tokens; one hour; one >=80GB GPU; 4 CPUs; 128GB host RAM; HPCAIq. Observed reservations do not silently change the approved hard ceiling.
- All four original options remain unmarked in every public request. The launcher never opens `evaluator.private.json` or the original full dataset. Provenance metadata stays outside model payloads.

## Implementation

`src/bc_phase2/medqa_planner_launch.py` binds the public file, request measurements, historical exact model inventory, current interface hashes, scheduler configuration and separate source review. It uses the existing CheckedTransport/Qwen loader, atomic ledger/locking, snapshot inventory, environment checks and shared per-user scheduler registry. No general inference or estimator framework was introduced.

`Session` applies the existing one-shot screening semantics to twelve requests. Reservations are durable before generation. Known invalid, unsupported and length-limited outcomes continue; unknown dispatch/usage, integrity failure or resource breach stops. A crash preserves its reservation and cannot reopen the session. Submission is keyed by cohort, so changed output paths or scopes cannot bypass no-retry. Each result includes all twelve source statuses and raw attempted responses for later human review. Worker/profile/recovery stages remain disabled.

`launch_medqa_planner.py` exposes bind, approve, submit and run-allocated. The sbatch wrapper uses the frozen snapshot, offline library flags and the existing scheduler allocation. GPU imports remain lazy; CLI help is standard-library-only. No live approval is created by these commands.

## Remaining source review

The provided receipts explicitly leave authors-archive equivalence and dataset usage rights unresolved. Section 4 of `CODEX_DICE_FIX_MATH_WAVE_MEDQA_V2.md` requires the authors' English four-option dev source or a source-verified equivalent and recorded applicable terms. Structural consistency and the mirror card do not complete that requirement.

Disabled preparation accepts a pending source-review record and reports blockers. Approval refuses unresolved source review even if GPU permission is supplied. Resolving this requires documented evidence tied to the existing source hash and cohort, not another cohort, invented metadata or a claim that the code licence settles dataset rights. A changed source-review receipt changes the launch scope, not the selected IDs or prompts. No review verdict is fabricated here.

## Transfer (user executes; do not include datasets or outputs)

Inspect the staged list first; leave unrelated changes out of this commit.

```bash
cd /home/gnoriq/repos/Beyond-Consensus
git diff --cached --name-only
git add -- src/bc_phase2/medqa_planner_launch.py scripts/launch_medqa_planner.py experiments/run_medqa_planner.sbatch tests/test_medqa_planner_launch.py docs/MEDQA_PLANNER_LAUNCH.md
git diff --cached --stat
git commit -m "Connect frozen MedQA planner cohort to guarded launch and accounting"
git push origin HEAD
```

## Jupyter disabled binding

This uses the existing full-inventory receipt; all weights are rehashed before live loading. It reuses the previous actual cluster configuration, explicitly changes its proposed wall ceiling to one hour, and records current scheduler metadata. It does not submit a job or load a model. If any named historical receipt is missing, stop rather than substituting guessed evidence.

```bash
(
set -euo pipefail
umask 077
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_MEDQA_LAUNCH="$(mktemp -d "$BC_STORAGE/diagnostics/medqa-planner-launch.XXXXXX")"

"$BC_PYTHON" - <<'PY'
import json,os
from pathlib import Path
root=Path(os.environ['BC_MEDQA_LAUNCH'])
storage=Path(os.environ['BC_STORAGE'])
receipt=json.loads((storage/'diagnostics/dice-next-math.HKQUz1/submission.json').read_text())
manifest=json.loads((Path(receipt['output'])/'manifest.json').read_text())
config=dict(manifest['release']['manifest']['scope']['cluster'])
if config['partition']!='HPCAIq' or config['memory_gb']!=128:
    raise SystemExit('STOP: unexpected historical cluster configuration')
config.update(time='01:00:00',output_root=str(root/'outputs'))
review=dict(
    cohort_digest='1f471cbd92f4f957678bc26af84985ffb44699422122367c297f83983e6159a0',
    dataset_sha256='774bbd90103af43badbe8d5294e336443573fc37b918763920b8fc3b3df581d9',
    authors_archive_equivalence='not_independently_verified',
    rights_review='unresolved',evidence_reference=None,reviewer=None,reviewed_at=None)
for name,value in [('cluster.json',config),('source-review.pending.json',review)]:
    with (root/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
PY
scontrol show partition HPCAIq -o > "$BC_MEDQA_LAUNCH/partition.txt"
squeue --array -u "$USER" -o '%.22i %.12P %.20j %.2t %.10M %R' > "$BC_MEDQA_LAUNCH/queue.txt"
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py bind \
  --cohort "$BC_STORAGE/diagnostics/medqa-cohort.xKzwlB/intake/cohort.public.json" \
  --verification "$BC_STORAGE/diagnostics/medqa-token-fit.SkqoLe/token-fit.json" \
  --inventory-report "$BC_STORAGE/diagnostics/d1-local-verify.1pghSs/local-verification.json" \
  --cluster "$BC_MEDQA_LAUNCH/cluster.json" \
  --partition-record "$BC_MEDQA_LAUNCH/partition.txt" \
  --source-review "$BC_MEDQA_LAUNCH/source-review.pending.json" \
  --output "$BC_MEDQA_LAUNCH/bound"
printf 'Preparation directory: %s\n' "$BC_MEDQA_LAUNCH"
)
```

Expected state with the supplied evidence: `blocked_source_review`, with unchanged selected sources. Preserve this packet. Once source evidence is actually resolved, bind into a fresh directory with that separate review record. Do not edit a frozen manifest.

## Conditional launch syntax, not present authorisation

After a blocker-free bound packet exists and the user explicitly approves its exact scope, save the corresponding completed approval template as `approval.json`. Only then:

```bash
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py approve \
  --manifest "$BC_MEDQA_LAUNCH/bound/manifest.disabled.json" \
  --approval "$BC_MEDQA_LAUNCH/approval.json" \
  --output "$BC_MEDQA_LAUNCH/release.json"
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_LAUNCH/release.json" --dry-run \
  --output "$BC_MEDQA_LAUNCH/submission-dry-run.json"
"$BC_PYTHON" -I -B scripts/launch_medqa_planner.py submit \
  --release "$BC_MEDQA_LAUNCH/release.json" \
  --output "$BC_MEDQA_LAUNCH/submission.json"
```

A failed/uncertain submission is not permission to repeat these commands. Other GPU jobs remain subject to the shared guard. Runtime checks verify exact inventory/environment, one visible >=80GB device and registered allocation before model dispatch. This is planner-only: review the resulting decomposition records before any worker release.

## Actual offline validation

Final focused run: **42 tests passed in 14.896 seconds**, using `PYTHONPATH=src:tests python -m unittest test_medqa_planner_launch test_next_results test_math500_screen_launch test_d1_natural_launch -v`. This includes 13 new bridge tests and representative existing transport/intake/launch coverage. The initial new-test run found a test fixture reading the ledger wrapper at the wrong level; the assertion was corrected to inspect its persisted `state`, with no weakening of production integrity behavior.

Coverage includes disabled/exact approval, unresolved source review, changed request/metadata/settings, protected field rejection, all twelve invalid responses with no thirteenth call, valid unsupported response, truncation continuation, unknown usage stopping, crash reservation/no replay, source/time/render/token guards, ambiguous submission across changed output roots, complete unrun reporting, and allocation mismatches.

`python scripts/check_shell.py`: **22 shell files passed**. `python -I -S -B scripts/launch_medqa_planner.py --help`: passed with site packages disabled. Python compilation and `git diff --check` passed. Evidence: `outputs/medqa-planner-launch-review/tests.txt`, `shell.txt`, `cli-help.txt`. No broad unittest discovery/solver campaign was run, following the authoritative handoff's focused-check restriction.

Readiness: **offline planner launch integration tested; source review blocked; live approval absent; worker stages disabled**. The source remains the pinned mirror; neither dataset equivalence nor usage permission has been newly established by this implementation. Historical experiments, the optimiser and existing production modules were not modified.
