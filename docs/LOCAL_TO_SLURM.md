# Local → GitHub → Slurm online terminal

## Active bounded validation cycle (2026-09-17)

Follow [VALIDATION_CYCLE.md](VALIDATION_CYCLE.md#ordered-commands) for the current
ordered local checks, historical ledger audit, native material/review/CPU
controls, and fresh SILO control/local/boundary dry runs. That runbook uses the
existing registry and submission wrappers. It stops before job submission and
the broad four-policy campaign. Earlier setup and E1 instructions below are
reference material, not authorization to repeat staging or launch a grid.

Native scoring still needs real databases and approved author evaluators.
SILO diagnostics can proceed independently, starting with eight full clean
control executions and freezing actual predecessor submissions afterward.
The operation-cost measurement path is optional and uses separate manifests.
None of these jobs was submitted during local implementation.

All submissions and large staging commands below are **manual next steps**.
Implementation did not submit jobs, download weights/datasets, or run the E1 grid.
Local development needs Python 3.12+, no CUDA or container runtime.

**Current required path:** SQLite/SILO restricted data tools on this existing
Slurm cluster. Use the already validated GPU environment and Qwen model lock.
Do not repeat environment/model setup when those assets already exist.
CooperBench commands below are optional legacy; delegation is not required by
the new path. See [migration notes](MIGRATION_SQLITE_SILO.md) for prerequisites.

## 1. LOCAL: edits, tests and the user's GitHub push

From the existing repository:

```text
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell, or
`source .venv/bin/activate` in Bash. All subsequent Python commands are portable:

```text
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_shell.py
python scripts/bc.py --help
python scripts/bc.py demo --output outputs/mock-demo
python scripts/bc.py aggregate --output outputs/mock-demo
python scripts/bc.py demo --output outputs/mock-demo
git diff
git status --short
```

The new SQLite CPU check is:

```bash
python scripts/bc.py data-capabilities
python scripts/bc.py demo --config configs/sqlite-demo.json --output outputs/sqlite-demo
```

Linux CPU resource controls and defensive SQLite settings are required by its
fixed executor. Unsupported platforms report a capability block. Numeric and
SILO CPU checks remain independent of that SQL capability.

The second demo command checks completed-episode resume. Reuse the output only
while code/config/data provenance is unchanged; after edits, select a new output
directory. `bc` is also installed as a console entry point. Bash helpers may use
WSL/Git Bash on Windows. If Bash is missing, the portable shell checker still
checks LF/usage/strict handling and reports why `bash -n` was skipped.

Optional developer tools are pinned in `requirements-dev.txt`; the acceptance
suite above does not require them. No GPU package is a CPU dependency.

For the separate CPU fixed-state diagnostic:

```text
python scripts/bc.py freeze-primary --config configs/fixed-primary.json --output outputs/fixed/primary.json
python scripts/bc.py diagnostic-manifest --fixed-state outputs/fixed/primary.json --output outputs/fixed/manifest.json
python scripts/bc.py run --manifest outputs/fixed/manifest.json --output outputs/fixed/comparison
```

After reviewing changes, **the user** commits and pushes to their existing HTTPS
GitHub remote. Do not create a guessed remote or put a token in its URL.

```text
git remote -v
git add README.md AGENTS.md pyproject.toml requirements-dev.txt requirements-gpu.txt .gitignore .gitattributes .github src configs experiments scripts tests docs
git commit -m "Implement E0/E1 research foundation"
git push
```

Keep local cluster configuration, credentials, private PDFs, hidden tests,
downloaded repositories, caches, models, environments, snapshots and raw outputs
outside version control. The repository provides ignore rules for the default paths.

## 2. CLUSTER ONLINE TERMINAL: setup, staging and guarded jobs

Open the cluster's browser terminal. Clone once using the actual HTTPS remote:

```bash
git clone https://github.com/YOUR-ACCOUNT/Beyond-Consensus.git
cd Beyond-Consensus
```

On subsequent visits:

```bash
cd Beyond-Consensus
git pull --ff-only
python3 scripts/bc.py --help
bash experiments/doctor_login.sh
sinfo -o '%P %a %G %m %l'
module avail
```

`module` may be a shell function. Its absence from `doctor`'s executable search
does not establish that environment modules are unavailable. Inspect the online
terminal's supported initialization method. No model loads in the login doctor.

### Configure local facts

```bash
cp configs/cluster.template.json configs/cluster.local.json
```

Edit this gitignored JSON file in the browser editor. All null required fields
must be replaced with facts from this site:

| Field | Meaning |
| --- | --- |
| `partition` | An accessible partition confirmed by Slurm/site documentation |
| `account`, `qos`, `constraint` | Optional account, QoS and node feature constraint; null unless needed |
| `time` | Explicit `[D-]HH:MM:SS` allocation limit |
| `memory_gb` | Requested **host RAM**; distinct from GPU VRAM |
| `python` | Absolute Python path in the fixed GPU environment |
| `modules` | Discovered module names, loaded once on batch startup |
| `activation_script` | Optional absolute trusted environment activation script |
| `storage_root`, `cache_root`, `snapshot_root`, `output_root` | Absolute user-writable persistent storage paths |

Profiles under `configs/profiles/` record the supplied resource-sheet snapshot:
NH100q / node07 / H100 80 GB SXM5, and PH100q / node06 / H100 80 GB PCIe.
These are examples, not promises of permission or current availability. The A100
rows mix 40 GB and 80 GB machines; in particular, PA100q does not uniformly mean
80 GB. RTXA6Kq lists A6000/A40 48 GB hardware. HPCAIq has A100 80 GB but prioritizes
CPU-intensive work. No H200 partition is documented. None of these profiles pins
a node or assumes a GPU-type GRES string.

The wrapper compares requested time with `scontrol`'s partition maximum and host
RAM with `sinfo` node memory, then uses `sbatch --test-only` before an actual
submission to check scheduler access/account/QoS constraints. Unknown facts fail
with instructions to inspect site information; there are no invented time/RAM defaults.

### One-time environment setup

Choose storage and an environment directory approved for your user. Set
`BC_STORAGE` to that actual absolute path; it is not a system variable. Then:

```bash
python3 -m venv "$BC_STORAGE/envs/bc-gpu-v1"
source "$BC_STORAGE/envs/bc-gpu-v1/bin/activate"
python -m pip install --upgrade pip
```

Install torch 2.10.0 and torchvision 0.25.0 from the **site-compatible official
PyTorch wheel index**, then install the pinned stack:

```bash
python -m pip install -r requirements-gpu.txt
python -m pip check
```

The appropriate wheel index depends on the driver's supported CUDA runtime; see
[the official matrix](https://pytorch.org/get-started/previous-versions/). Discover
modules rather than copying the old CUDA 11.1 examples. Do not install mutable
development branches. Do not install the project editable in the cluster GPU
environment: batch jobs import the frozen source archive. Submission inventories
all installed package versions, rejects editable installs and checks that inventory
at batch startup. Build a new environment for upgrades while jobs are active.

Set the configuration's `python` to
`$BC_STORAGE/envs/bc-gpu-v1/bin/python` **as a literal resolved absolute path**.
JSON does not expand shell variables. Use the same rule for every configured path.

### Explicit model staging

Inspect the planned destination first. The next non-dry-run command downloads
the selected model and requires sufficient storage and any necessary access.

```bash
python scripts/bc.py stage-model --config configs/gpu-smoke.json --root "$BC_STORAGE/models" --dry-run
python scripts/bc.py stage-model --config configs/gpu-smoke.json --root "$BC_STORAGE/models"
```

The lock is at
`$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json`. Reuse it for the pilot.
If staging fails for gated access, accept the model's license on its official
page and configure Hugging Face authentication using the provider's normal
credential mechanism. Never place credentials in repository files, URLs or logs.
Downloads/installations happen here, never in each array element.

### One-GPU preflight and one-task SQLite-fixture E0 smoke

The default `gpu-smoke.json` and `pilot.json` now use labelled SQLite fixtures.
The prior numeric configs are preserved as `numeric-gpu-smoke.json` and
`numeric-pilot.json`. Use new manifest/output filenames for the migration to
avoid confusion with the completed numeric runs. SQL preflight also probes the
fixed CPU executor inside the same allocated compute job.

```bash
python scripts/bc.py manifest --config configs/gpu-smoke.json --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json" --output "$BC_STORAGE/smoke-manifest.json"
bash experiments/submit_gpu_preflight.sh --cluster configs/cluster.local.json --manifest "$BC_STORAGE/smoke-manifest.json" --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json" --dry-run
```

After reviewing the arguments, the user submits by removing `--dry-run`:

```bash
bash experiments/submit_gpu_preflight.sh --cluster configs/cluster.local.json --manifest "$BC_STORAGE/smoke-manifest.json" --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json"
```

The returned JSON identifies the project job, immutable snapshot and output
directory. Review `preflight.json` and `%A_%a` logs after the job finishes. For the
one-task **complete episode** smoke, submit the same manifest using
`submit_pilot.sh --concurrency 1` after preflight completes. This separates model
loading/chat-template compatibility from actual worker/task competence.

### Four-task SQLite-fixture engineering pilot

```bash
python scripts/bc.py manifest --config configs/pilot.json --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json" --output "$BC_STORAGE/pilot-manifest.json"
bash experiments/submit_pilot.sh --cluster configs/cluster.local.json --manifest "$BC_STORAGE/pilot-manifest.json" --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json" --concurrency 4 --dry-run
```

Review, then remove `--dry-run` when authorized. Each shard uses one GPU, one
task and four CPU cores. Four logical workers execute sequential model calls on
that GPU. There is no DDP, multi-node execution or tensor parallelism.

The actual resource arguments include:

```text
--partition=CONFIGURED --nodes=1 --ntasks=1 --cpus-per-task=4 --gres=gpu:1
--array=0-3%4 --time=CONFIGURED --mem=CONFIGURED
```

Log directories exist before submission. All code imports come from a verified
commit archive under `snapshot_root`; later `git pull` cannot change that source.
Manifests, local configuration, model lock and environment inventory are included
and hashed in the snapshot. A dirty checkout cannot be submitted. No editable
install or `PYTHONPATH` overrides the archive. CUDA visibility remains assigned by
Slurm, and inference uses process-local `cuda:0`.

### Global GPU guard

`%4` caps only one array. All project wrappers share
`~/.local/state/beyond-consensus/registry.json` and one atomic submission lock,
independent of this checkout and its profile. They inspect all active/pending GPU
jobs for the user. Unknown GPU accounting and overlapping campaigns are rejected.
Preflight uses the same guard. To request serialization explicitly,
`submit_pilot.sh ... --serialize` adds completion dependencies on known campaigns.
An uncertain submission remains locked for manual scheduler reconciliation.

These wrappers cannot constrain unrelated manual job submissions. Only an
administrator's Slurm account/QoS GPU limit can enforce a hard account-wide cap
against bypasses. Do not launch concurrent manual GPU jobs alongside a campaign.
Batch code never submits jobs, and wrappers never requeue indefinitely.

### Status, failures, resume and browser downloads

Use the exact output, snapshot and job IDs returned by the wrapper:

```bash
bash experiments/status.sh --output "$BC_RUN_OUTPUT" --jobs "$BC_JOB_ID"
squeue --jobs "$BC_JOB_ID"
sacct --jobs "$BC_JOB_ID" --format=JobID,State,ExitCode,Elapsed,AllocTRES
```

`squeue` shows queued/running work. `sacct` supplies accounting and terminal
states, including OOM/timeouts. To stop this campaign, use
`scancel "$BC_JOB_ID"` for its specified project ID. TERM is handled at a safe
model/tool boundary; nonzero exits are preserved. A forced kill may leave an
uncertain reservation and stale lock. Verify the owning job is terminal before
manually removing that specific lock. Do not cancel every job belonging to the user.

When the campaign is terminal:

```bash
bash experiments/resubmit_failed.sh --snapshot "$BC_SNAPSHOT" --concurrency 4 --dry-run
bash experiments/resubmit_failed.sh --snapshot "$BC_SNAPSHOT" --concurrency 4
python scripts/bc.py aggregate --output "$BC_RUN_OUTPUT"
bash scripts/export_bundle.sh --output "$BC_RUN_OUTPUT" --bundle "$BC_STORAGE/pilot-debug.tar.gz" --dry-run
bash scripts/export_bundle.sh --output "$BC_RUN_OUTPUT" --bundle "$BC_STORAGE/pilot-debug.tar.gz"
```

Resume includes only missing/interrupted/infrastructure-failed episodes; completed
episodes in a partly failed shard are skipped. Provenance changes require a new
run. Export contains bounded sanitized JSON summaries, manifests, configuration
and errors. New v2 data-workflow exports exclude raw tracebacks and private input
paths as well as contexts, hidden contents, credentials,
environment dumps, model caches, repositories and tensors. Inspect the small
bundle, then download it using the cluster browser's file-download interface.
Completed jobs depend on neither the browser session nor a local machine, and
offline batch inference needs no external network after staging.

### Native SQLite, paired tasks and SILO

Use [the exact staging/review commands](MIGRATION_SQLITE_SILO.md#exact-staging-and-next-commands)
to obtain a private `bc-data-v2` manifest. No database or author test download is
part of a shard. `sqlite-validate --count 10` checks ten explicitly reviewed
native tasks. `sqlite-pairs` freezes reviewed candidates and retains block/reject
reasons. The provided crypto candidate is not yet validated, and no second pair
has been invented. Register data outside Git. The source databases remain
immutable; the executor owns disposable state for every invocation.

After native/pair validation and the fixture smoke pass, these commands plan
the real model path without submitting it:

```bash
python scripts/bc.py manifest --config configs/sqlite-native-smoke.json \
  --data-manifest "$BC_STORAGE/sqlite-native-validated.json" \
  --model-lock "$BC_MODEL_LOCK" --output "$BC_STORAGE/sqlite-native-smoke-manifest.json"
python scripts/bc.py manifest --config configs/sqlite-pair-validation-pilot.json \
  --data-manifest "$BC_STORAGE/sqlite-pairs-validated.json" \
  --model-lock "$BC_MODEL_LOCK" --output "$BC_STORAGE/sqlite-pair-validation-manifest.json"
bash experiments/submit_pilot.sh --cluster configs/cluster.local.json \
  --manifest "$BC_STORAGE/sqlite-pair-validation-manifest.json" \
  --model-lock "$BC_MODEL_LOCK" --concurrency 1 --dry-run
```

The two-pair config requires two approved **development** pairs; a smaller
validated set stays blocked. For four approved tasks use the corresponding
`sqlite-native-pilot.json` or `sqlite-pair-pilot.json` config. A user removes
`--dry-run` only when ready to submit and previous campaigns are reconciled.

SILO staging creates small deterministic data; no upstream batch runner, API or
Redis server is used:

```bash
python scripts/bc.py silo-generate --family II-11 --seeds 0 1 2 3 4 5 6 7 \
  --access protected_original_shards --output "$BC_STORAGE/silo-prefix.json"
python scripts/bc.py silo-validate --input "$BC_STORAGE/silo-prefix.json"
python scripts/bc.py manifest --config configs/silo-smoke.json \
  --data-manifest "$BC_STORAGE/silo-prefix.json" --model-lock "$BC_MODEL_LOCK" \
  --output "$BC_STORAGE/silo-smoke-manifest.json"
```

`silo-pilot.json` requests four eligible development inputs; manifest creation
reports the actual available count. Generate Pipeline Hash with `--family II-20
--seeds 0` in a separate file. Repeated seeds do not create different Pipeline
Hash data. `--access no_recovery_copy` creates a separately reported boundary
diagnostic. Keep access regimes in separate manifests and campaigns.

For the planned main study:

```bash
python scripts/bc.py manifest --config configs/e1.json \
  --data-manifest "$BC_STORAGE/sqlite-pairs-validated.json" \
  --model-lock "$BC_STORAGE/models/Qwen--Qwen3.5-9B/model-lock.json" \
  --output "$BC_STORAGE/sqlite-e1-manifest.json"
```

This requires 20 approved development pairs and the separately staged, pinned
9B checkpoint; no download happens here. The grid is 20 × 4 × 2 × 2 = 320 final
episodes, still a plan. `silo-e1.json` applies the same count gate to the distinct
SILO environment. Missing data is never substituted with fixtures or repeated
inputs. Stop at smoke/pilot if clean competence, execution limits or runtime
validity are unresolved. New-environment semantic sabotage is intentionally
gated; numeric sabotage diagnostics do not satisfy that gate.

### Optional legacy CooperBench staging and coding plan

For the new bounded clean coding E0 path, first follow
[CODING_SANDBOX.md](CODING_SANDBOX.md). Its qualification and evaluator controls
are mandatory. The 320-episode four-policy coding campaign below remains planned
and unsupported by the clean E0 adapter.

Only stage the real dataset when authorized:

```bash
python scripts/bc.py stage-data --root "$BC_STORAGE/cooperbench" --dry-run
python scripts/bc.py stage-data --root "$BC_STORAGE/cooperbench"
```

Read `dataset-lock.json` for the exact staged directory and revision. Run
`cooper-import --root STAGED_DIRECTORY --subset STAGED_DIRECTORY/subsets/flash.json
--upstream-commit VERIFIED_HARNESS_COMMIT --dataset-revision STAGED_COMMIT
--output DATA_MANIFEST.json`. These uppercase arguments are values to fill from
the inspected upstream/staging metadata, not guessed task IDs.

Copy `configs/cooper-e1.legacy.json` to a gitignored local JSON file and set `data_manifest` to
that absolute validated path. Stage/resolve Qwen3.5-9B separately. The E1 config
describes 320 planned episodes. **Execution is currently blocked pending an
approved, tested repository sandbox and a coding worker/evaluator adapter.**
Loader validation alone does not authorize upstream setup scripts on the host.
The four-task GPU fixture pilot is not CooperBench evidence. See
[models, data and the execution blocker](MODELS_AND_DATA.md).
