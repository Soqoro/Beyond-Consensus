# Models, data and execution boundary

## Verified upstream interfaces, untested GPU stack

The official Qwen3.5-4B configuration identifies
`Qwen3_5ForConditionalGeneration`, not a generic causal-LM checkpoint. The adapter
uses that explicit class, the staged official tokenizer/chat template, and text
inputs only. It loads the full checkpoint, including its vision parameters, so
no parameter-count estimate is used as evidence that it fits.
[Official configuration](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/config.json),
[official chat template](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/chat_template.jinja).

The reviewed Transformers **5.3.0 release** includes this model class. Its declared
dependencies permit the pinned Hub and tokenizer versions in `requirements-gpu.txt`.
This avoids the model card's mutable development-install example.
[Release model implementation](https://github.com/huggingface/transformers/blob/v5.3.0/src/transformers/models/qwen3_5/modeling_qwen3_5.py),
[release dependency declarations](https://github.com/huggingface/transformers/blob/v5.3.0/setup.py).

PyTorch documents torch **2.10.0** with torchvision **0.25.0** and separate CUDA
wheel indexes. Select an index compatible with the site's driver during setup.
The resource sheet's CUDA 11.1 commands are historical examples, not this project's
dependency prescription. [Official PyTorch installation matrix](https://pytorch.org/get-started/previous-versions/).

**Status:** interfaces and release constraints were inspected; no GPU model was
loaded locally. The entire candidate GPU stack remains untested on the cluster.
Record a full environment lock after installation and do not mutate an environment
used by running jobs. Pins are top-level requirements; the environment inventory
records resolved transitive versions. CPU acceptance tests use only the standard
library. No development branch is installed by an experiment job.

Defaults: engineering `Qwen/Qwen3.5-4B`, planned study `Qwen/Qwen3.5-9B`, later
validation `google/gemma-3-12b-it`. Gemma's configuration name is reserved but its
execution loader is explicitly blocked pending separate validation. JSON config
records dtype, context/output caps, thinking, sampling, temperature, top-p and
top-k. The backend uses Slurm's process-local `cuda:0`, verifies exactly one visible
GPU, freezes weights and uses one model for all contexts. It never changes
`CUDA_VISIBLE_DEVICES`, silently switches precision, truncates history, quantizes,
or falls back to CPU after OOM.

`stage-model` resolves model/tokenizer commits once and writes `model-lock.json`
under an explicitly chosen root. A lock prevents concurrent staging collisions;
reuse preserves the resolved revision. A revision change needs a new root.
`manifest --model-lock ...` writes immutable revisions into the configuration.
Inference uses staged paths with offline/local-files-only flags. Missing license
acceptance or authentication is diagnosed without logging credential values.

Preflight runs inside a one-GPU allocation. It reports actual hardware, available
and peak VRAM, driver/CUDA/PyTorch versions, bfloat16 support, generation usage,
dtype and context settings. Review the generated response and peak memory before
the pilot; successful loading alone does not demonstrate task competence.

## CooperBench adapter v1

Inspected sources include the official harness's directory layout and dataset
preparation interface, plus actual `subsets/flash.json` and a task's `setup.sh`
and `Dockerfile`. The official subset schema contains `tasks` records with
`repo`, integer `task_id`, and pairs of integer feature IDs. The adapter derives
paths from these actual records and verifies each file before using it.
[Official harness](https://github.com/cooperbench/CooperBench),
[dataset preparation code](https://github.com/cooperbench/CooperBench/blob/main/src/cooperbench/dataset.py),
[official subset](https://huggingface.co/datasets/CooperBench/cooperbench-dataset/blob/main/subsets/flash.json).

The web-inspected harness commit is
`4913c4ebb84d2606cdb5628936b88529f3e181df`. A live metadata lookup also returned
`63b9d44d9f39a02fccf5bf0052db48a917a011fd` during implementation. These are recorded
as different snapshots, not silently assumed identical. Import requires an explicit
upstream commit and the dataset revision obtained during staging. The harness's
older `CodeConflict/cooperbench-dataset` identifier and the current
`CooperBench/cooperbench-dataset` organization differ; this adapter explicitly stages
the latter. Revalidate if the staged schema differs.
[Official dataset](https://huggingface.co/datasets/CooperBench/cooperbench-dataset).

Each imported pair records the harness commit, dataset revision, HTTPS repository,
base commit, feature pool hash, both feature IDs, pair ID, source hashes, and
environment-script hashes. Only `feature.md` descriptions become permitted task
sources. `feature.patch` and `tests.patch` are evaluator-only files; setup scripts,
runners and Dockerfiles are hashed, never executed by this adapter. Ambiguous base
commit or repository extraction fails with an adapter-review diagnostic. The adapter
does not invent image names, test APIs or missing IDs.

All pairs sharing a repository/base commit belong to one split group. A stable
group hash assigns development/validation/test; `data_split` filters before taking
the first configured number of pairs. The selection does not inspect comparative
results. A pair's intended final evaluation is **both feature suites against one
integrated candidate**. Applying independent feature patches and reporting either
feature alone as complete success would change the research question.

## Current execution blocker

The AAI snapshot does not establish a usable isolation facility. This repository
therefore supports **only the bounded typed workflow interpreter** for execution.
Its four arithmetic operations have numeric/step limits; there is no `eval`,
model-generated Python execution, shell tool, filesystem tool, or network tool.

CooperBench loading/manifest validation work, but execution fails before any
repository script or generated program can run. Detecting `docker`, `apptainer`,
or `bwrap` does not enable execution. There is no host fallback.

A future site-approved adapter must demonstrate all of:

- Denied network, host home, credentials, Slurm commands and privileged sockets.
- Restricted mounts, CPU, memory, process and wall-time use.
- Separate worker contexts/workspaces and a private evaluator mount.
- Hidden tests and reference patches absent from all worker-readable paths,
  including Git history, images, shared workspaces and other-worker artifacts.
- Adversarial integration tests for these boundaries. Read-only mounts do not
  make hidden files secret.

The isolation integration test is explicitly skipped with this actual blocker.
No Docker/root privilege, container build, or node execution capability is claimed.
