# RepoRecourse clean baseline and proposed contributor-loss diagnostic

Recorded 2026-09-25. Evidence below is user-supplied cluster output, not a local
rerun or independently retrieved cluster record. Historical scores are unchanged.

## Observed engineering results

| Condition | Experiment | Complete success | Logical tokens | CPU seconds |
| --- | --- | --- | --- | --- |
| Original finish behavior | 855edc500f48ec01eb9674e48bb6c2b9d7f59caa11fd218f5a41ab35da72bdcb | 0/1 | 18,302 | approximately 372.72 |
| Assignment-local finish and clarified public contract | b9492f9028928218e190cf0441956d681cecb524b824505d551047f55757a9f9 | 1/1 | 29,745 | 404.791043613 |

Both are Jaffle recorded-payments, independent outline, delegation_jit, clean
development episodes in one source group. Neither is confirmatory.
The corrected episode is a9cfd17e2a30080a28a15d5c2e985502a129f8742a2753730cb440282921beaa.
It reports no uncertain tokens, missing episodes or infrastructure failures.

The original saved queries referenced nonexistent source columns:
customers.customer_id (actual id), orders.customer_id (actual user_id),
orders.order_id (actual id), and payments.payment_id (actual id).
These are static artifact/schema findings, not new SQL executions. Structural
compilation accepted the queries; recorded execution returned semantic_error.
Repair rebound an unchanged invalid artifact, then worker finish closed the
shared episode and a subsequent worker call failed with episode_closed.

In the corrected run, w0 published customer_summary and w1 published
method_summary. Both final obligations passed the available finite evaluator.
w1 incurred one sql_rejected compiler event, read another source and published
successfully within its primary assignment. Both public executions passed.
There was no public alarm, repair stage, explicit rebind, or use of w2/w3.
Both primary versions were retained. Task costs were 12,970 tokens for the
customer assignment and 16,775 for the method assignment. Caps were 100,000
logical tokens and 1,200 CPU seconds under rr-logical-tokens-cpu-v1.

This shows clean engineering feasibility on one repeatedly inspected task.
It does not demonstrate contributor recovery, a policy advantage, general
competence, or causal benefit of the finish fix. The public instructions changed
too, and the corrected GPU run did not exercise finish during repair.
Regression tests, not this GPU observation, exercise the corrected finish path.

## Authorized local implementation (2026-09-26)

The user explicitly authorized a narrow engineering exception, CPU validation,
manifest preparation and submission dry runs. Live jobs, downloads, commits and
pushes were **not** authorized. The earlier proposed seed of 0 is withdrawn as an
unverified assumption: the importer copies the actual historical seed.

The entry point is `rr-manifest --track-f-engineering`. It creates exactly three
unique episodes under `reporecourse_track_f_engineering_v1`:

| Condition / shard | Track | Target | Required result |
| --- | --- | --- | --- |
| fresh_clean / 0 | clean | none | Both Jaffle obligations under the new implementation |
| loss_w0 / 1 | F | w0 | Customer output reconstructed by an eligible identity |
| loss_w1 / 2 | F | w1 | Method output reconstructed, prior customer work retained |

All share the actual historical independent outline, delegation_jit, one copied
seed, frozen 27B BF16 revision, model settings, task/evaluator/source hashes,
24 actions per assignment and 100,000-token / 1,200-CPU-second allowances.
The existing tool/prompt contract and four identities remain shared. No method
name is given to the model or evaluator. CPU qualification binds current source,
control tests, adapter, dependencies and public task. Grammar qualification
remains a separate lock-bound gate. Independent review remains pending.

The raw historical run and snapshot are **not present locally**. Therefore no
real trio ID, copied seed or fresh execution result is claimed in this handoff.
The path-based importer verifies the snapshot file inventory, resolved manifest,
successful result, both bindings and original authors. It resolves the old
implicit action limit from the literal Engine default and verifies that the
historical adapter supplied no override. Any discrepancy stops preparation.
Other tasks, seeds, plans, policies, S/R tracks, enlarged caps and broader
campaigns remain blocked. Historical results are never reused as the new control.

### Resource audit and correction

`rr-logical-tokens-cpu-v1` keeps its units and caps. The source-bound accounting
revision is `rr-admission-reconciliation-v2`. Every condition must be rebuilt.
The 31-second model-host reservation is an **admission estimate**, not an enforced
host CPU timeout. Decoder CPU has its own existing bound and is a subset of
model-host process CPU, not added again. Actual host CPU can exceed the estimate;
full measured usage is charged, estimate overrun and episode overshoot are
recorded, and subsequent dispatch stops. Correctness above the cap is not success.
No clipping or arbitrary reservation increase is used.

Reservations, actual usage, released allowance and uncertain interrupted work
are distinct. Reconciliation consumes an outstanding reservation once. An
interrupted unknown operation debits its reservation conservatively. Token
uncertainty remains charged. Resumed source materialization is additional CPU.
Trusted tool-parent time is charged even if the cap has already been exceeded.
Model token counts are reconciled before a CPU exception can lose those counts.
This is strict admission/scoring, **not a guarantee against all runtime overshoot**.

The episode cap covers source materialization, public plan selection, model-host
CPU (all process threads, including tokenization/decoder), compiler/executor child
CPU plus exclusive parent CPU, public checks and orchestration. Child CPU is not
included in `process_time`; nested parent CPU is subtracted before charging outer
parent time. GPU/wall durations are observations, not added CPU. Model/grammar
static setup is recorded separately by the backend/qualification. Terminal
private grading freezes the bundle and has its separate 240-second CPU ledger;
it cannot generate, repair or select a better candidate. Summed episode caps are
300,000 tokens / 3,600 CPU seconds, excluding this separately declared evaluation
and qualification overhead; these are not GPU-hour estimates.

### Fault, retention and repair semantics

The existing `first_assigned_publication_v1` rule is retained: first outward
publication attempt for the target's assigned output, after envelope/binding
validation but before compilation and public commit/binding. It does not inspect
hidden correctness. The target stays unavailable throughout the branch. Attempts
by the engine to dispatch it are suppressed; stale state restoration that would
resurrect it is rejected. Assignment finish remains local, while final episode
closure and grading are separate.

Only existing committed versions can be executed or read. The blocked action
exists only in the unavailable worker's private journal/history; it is not a
public artifact or scorer candidate. Earlier legitimately published helpers or
outputs remain available. A public announcement contains identity and assignment
only. Unaffected primary work completes before the existing common public check
and ordinary JIT reassignment. Replacements come from the existing eligible
identities, retain original source access and pay ordinary work costs. No fault
reached means no recovery validation; the planned row remains in the report.

## Runbook: review each stop point

### Local review

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
git diff --check
python -I -S scripts/bc.py --help
git diff --stat
git status --short
```

Review changes and pending checks, then manually commit/push only code/docs/tests.
Keep exported reports and private data outside Git. See VALIDATION.md for exact
current tests/skips. No earlier dependency-equipped run qualifies this revision.

### Browser terminal: setup and pinned CPU qualification

Run after pulling the reviewed commit. Use the existing configured account/QoS
and partition. The commands below do not infer GPU capacity from its name.
The checked backend still requires a full 80-GB-class allocation, respects
CUDA_VISIBLE_DEVICES and forbids fallback/offload/quantization.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
git status --short
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_RR_SOURCES="$BC_STORAGE/datasets/reporecourse-v01"
export BC_RR_CLUSTER="$PWD/configs/cluster.qwen27b-na100.local.json"
export BC_RR_BASE_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json"
export BC_RR_BASE_RUN="$BC_STORAGE/outputs/qwen27b-na100/b9492f9028928218e190cf0441956d681cecb524b824505d551047f55757a9f9"
export BC_RR_BASE_SNAPSHOT="$BC_STORAGE/snapshots/23867ec5815e1e45d25eb17ab7e70f6f918bfa636784b61186c8a118a793f02d"
export BC_RR_F="$(mktemp -d "$BC_STORAGE/diagnostics/reporecourse-track-f.XXXXXX")"
export BC_RR_CPU_SOURCE="$BC_RR_F/source"
(
set -euo pipefail
if test -n "$(git status --porcelain)"; then
    git status --short
    exit 1
fi
test -f "$BC_RR_BASE_RUN/manifest.json"
test -f "$BC_RR_BASE_SNAPSHOT/snapshot.json"
mkdir "$BC_RR_CPU_SOURCE"
git archive HEAD | tar -xf - -C "$BC_RR_CPU_SOURCE"
chmod -R a-w "$BC_RR_CPU_SOURCE"
)
```

STOP if paths or the clean checkout check fail. Do not manufacture missing
historical fields. CPU source is a commit archive; the later GPU snapshot also
contains resolved inputs. Their runtime/control fingerprints must match.

**Only after user authorization for a CPU allocation**, submit via the existing
wrapper at its actual archive path, not as a copied Slurm spool script. This
preserves configured partition/account/QoS and requires no GPU:

```bash
"$BC_PYTHON" - <<'PYCPU'
import json, os, subprocess
from pathlib import Path
c = json.loads(Path(os.environ['BC_RR_CLUSTER']).read_text())
a = ['sbatch', '--parsable', '--nodes=1', '--ntasks=1', '--cpus-per-task=4',
     '--mem=32G', '--time=01:00:00', '--partition='+c['partition'],
     '--output='+os.environ['BC_RR_F']+'/cpu.out',
     '--error='+os.environ['BC_RR_F']+'/cpu.err']
for key in ('account', 'qos', 'constraint'):
    if c.get(key): a.append('--'+key+'='+c[key])
a += ['--wrap', 'exec bash "$BC_RR_CPU_SOURCE/experiments/qualify_reporecourse.sh" '
      '--sources "$BC_RR_SOURCES" --output "$BC_RR_F/cpu" '
      '--model-lock "$BC_RR_BASE_LOCK" --track-f-controls']
print(subprocess.check_output(a, text=True).strip())
PYCPU
```

The wrapper refuses missing pins or any relevant skipped/failed test, renews
Jaffle references/mutants, both loss controls, compiler and grammar. No model
weights are executed. It does not qualify Energy or other models/tasks for this
exception. A legacy opt-in OS-sandbox skip is irrelevant to this data path.

After the CPU job finishes, inspect `cpu.out`, `cpu.err`, the Jaffle report and
`grammar.json`. Stop unless controls pass and `cpu/model-lock.json` exists.

### Resolve and inspect the exact trio

```bash
export BC_RR_LOCK="$BC_RR_F/cpu/model-lock.json"
(
set -euo pipefail
"$BC_PYTHON" scripts/bc.py rr-manifest \
  --sources "$BC_RR_SOURCES" --tasks jaffle-recorded-payments \
  --track-f-engineering --baseline-run "$BC_RR_BASE_RUN" \
  --baseline-snapshot "$BC_RR_BASE_SNAPSHOT" \
  --qualification "$BC_RR_F/cpu/jaffle-recorded-payments.json" \
  --model-lock "$BC_RR_LOCK" --output "$BC_RR_F/manifest.json"
"$BC_PYTHON" - <<'PYPLAN'
import json, os
from pathlib import Path
m=json.loads((Path(os.environ['BC_RR_F'])/'manifest.json').read_text())
print(json.dumps({k:m[k] for k in ('experiment_id','source_revision','model_lock_sha256',
    'public_hashes','resource','accounting_version','fault_rule','max_actions','episodes')},indent=2))
PYPLAN
"$BC_PYTHON" scripts/bc.py submit --mode preflight --concurrency 1 \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_F/manifest.json" \
  --model-lock "$BC_RR_LOCK" --dry-run
)
```

A new experiment requires its matching preflight. After reviewing the dry run
and explicitly authorizing a GPU job, run the **same submit command without
`--dry-run`**, saving stdout to `$BC_RR_F/preflight-submission.json`. Do not
resubmit while queued/running. This creates the one immutable GPU snapshot.

After preflight completion:

```bash
export BC_RR_SNAPSHOT="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["snapshot"])' "$BC_RR_F/preflight-submission.json")"
export BC_RR_ID="$("$BC_PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["experiment_id"])' "$BC_RR_F/manifest.json")"
export BC_RR_OUTPUT="$("$BC_PYTHON" -c 'import json,sys; from pathlib import Path; print(Path(json.load(open(sys.argv[1]))["output_root"])/sys.argv[2])' "$BC_RR_CLUSTER" "$BC_RR_ID")"
"$BC_PYTHON" -m json.tool "$BC_RR_OUTPUT-preflight/preflight.json"
```

STOP if preflight failed, allocation facts differ or resource/decoder checks
fail. Long input with early EOS does not prove worst-case fit.

### Sequential runs under that same snapshot

First display the fresh clean dry run:

```bash
"$BC_PYTHON" scripts/bc.py submit --mode run --condition fresh_clean \
  --concurrency 1 --snapshot "$BC_RR_SNAPSHOT" \
  --cluster "$BC_RR_CLUSTER" --manifest "$BC_RR_F/manifest.json" \
  --model-lock "$BC_RR_LOCK" --dry-run
```

After explicit user authorization remove only `--dry-run`. Wait for completion,
then export a new immutable report:

```bash
export BC_RR_REPORT_DIR="$(mktemp -d "$BC_RR_F/results.XXXXXX")"
"$BC_PYTHON" scripts/bc.py rr-export --manifest "$BC_RR_F/manifest.json" \
  --run "$BC_RR_OUTPUT" --output "$BC_RR_REPORT_DIR/engineering.json"
```

If clean fails, **stop**. It cannot be terminal-retried until it passes. The
report includes both deliberately unlaunched loss rows. A real implementation
bug requires a new matched trio, preserving this version.

After user review of a passing clean, repeat the same guarded submit command
with `--condition loss_w0` and `--dry-run`. Review, authorize, remove dry-run,
wait, and export to another new results directory. Then do the same with
`--condition loss_w1`. Do not run a shell loop or submit downstream jobs from
batch code. The gate enforces prior clean success and prior w0 completion;
harness/infrastructure/resource failures stop downstream submission. A semantic
recovery failure remains an observation to review, not a reason to increase caps.
A genuine infrastructure resume uses the existing `resubmit --snapshot ...
--condition <same condition> --concurrency 1 --dry-run`, retaining the journal.
Never use resubmit to repeat a terminal failure.

### Report and decision

`engineering_trace.conditions` always has three rows. It records provenance,
actual node/GPU/runtime facts when available, initial assignments, fault event
and announcement, suppressed dispatch, complete event/CPU ledger, repair
executors, published/bound/retained versions, private finite-check results and
failure history. Queries, source contents, model histories and private fixtures
are not exported. Analysis execution flags are separate from historical model
execution. Raw journals remain available for audit.

Compare total and post-announcement work descriptively. Lower loss cost can mean
skipped work; same seed does not make divergent histories identical. Correct
outputs after a reached fault count as reconstruction evidence only when an
eligible identity published the missing work. A nontrigger is not recovery.
Completed rows containing episode_closed remain harness failures in the trace.

Clean and both genuine reconstructions passing would demonstrate mechanism
operation on one demo task at two loss locations. It would not demonstrate policy
superiority, broad competence or statistical significance. Model repair failure
is retained; harness failure stops expansion. Independent review, Energy license,
API competence, broad task coverage, calibrated B0 and measured selector value
remain unresolved. No authored-plan comparison, 12-task campaign, S/R track,
open planning or alternative model is authorized here.

## Implementation handoff inventory

Changed runtime: `src/reporecourse/resources.py`, `engine.py`, `runtime.py`.
Changed gate/aggregation: `src/reporecourse/experiments.py`; new exact scope/report
in `track_f.py`, new scripted CPU controls in `track_f_controls.py`.
BC adapters: `src/beyond_consensus/reporecourse_cli.py`, `cli.py`,
`experiments/reporecourse.py`, `experiments/cluster.py`; new read-only historical
resolver `experiments/reporecourse_history.py`.
Existing CPU wrapper: `experiments/qualify_reporecourse.sh`.
New regression file: `tests/test_reporecourse_track_f.py`.
Documentation: this runbook, `RESEARCH_PROTOCOL.md`, `STATUS.md`, `VALIDATION.md`
and `REPORECOURSE_IMPLEMENTATION.md`. The pre-existing September 25 progress
report and prior STATUS edits were retained.

Local result: 282 tests, 267 passed / 15 skipped; ten shell checks, compileall,
stdlib-only help and diff hygiene passed. Pinned executor and cluster checks
remain pending as listed in VALIDATION.md. The next user action is review and
manual commit/push, followed by the CPU qualification section above; no GPU
condition is ready to run merely because local unit tests passed.


## September 26 preflight revision: numbered synthetic records

The historical H100 preflight exhausted 2,048 output tokens during repetitive
reasoning over repeated padding. Its failed score is retained. The local
`rr-numbered-records-v2` replacement separates instructions from deterministic
numbered padding, keeping reasoning, output allowance, context target and exact
required action unchanged. A pass would qualify this revised diagnostic only;
neither early EOS nor observed reserved memory establishes worst-case fit.

After reviewing and committing/pushing this revision, repeat the setup and CPU
qualification above in a **new directory**, then rebuild the exact trio manifest.
Use the reviewed PH100q configuration if still appropriate for the allocation;
the example NA100q path above is not a claim that that partition is available.
Never overwrite the failed preflight or submit its old manifest with new code.
Review the new preflight's `short_action_probe`, `long_action_probe`,
`failure_stages` and `long_context_probe` provenance before any fresh_clean run.
No task episode or GPU retry is launched by this local preparation.
