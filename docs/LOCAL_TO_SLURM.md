# Local → GitHub → Slurm online terminal

All submissions and large staging commands below are **manual next steps**.
Implementation did not submit jobs, download weights/datasets, or run the E1 grid.
Local development needs Python 3.12+, no CUDA or container runtime.

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

### One-GPU preflight and one-task E0 smoke

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

### Four-task engineering pilot

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
run. Export contains bounded sanitized JSON summaries, manifests, configuration,
errors and tracebacks. It excludes contexts, hidden contents, credentials,
environment dumps, model caches, repositories and tensors. Inspect the small
bundle, then download it using the cluster browser's file-download interface.
Completed jobs depend on neither the browser session nor a local machine, and
offline batch inference needs no external network after staging.

### CooperBench staging and the 320-episode plan

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

Copy `configs/e1.json` to a gitignored local JSON file and set `data_manifest` to
that absolute validated path. Stage/resolve Qwen3.5-9B separately. The E1 config
describes 320 planned episodes. **Execution is currently blocked pending an
approved, tested repository sandbox and a coding worker/evaluator adapter.**
Loader validation alone does not authorize upstream setup scripts on the host.
The four-task GPU fixture pilot is not CooperBench evidence. See
[models, data and the execution blocker](MODELS_AND_DATA.md).
