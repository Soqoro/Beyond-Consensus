# Apptainer qualification and clean coding E0

## Status and scope

The basic Alpine probe succeeded in user-supplied logs on Jupyter and `node13`.
The new `apptainer-cgroup-v1` adapter has CPU regression coverage only in this
workspace. It has **not** passed qualification on the cluster. A successful old
Alpine probe is not an approval for this adapter or a benchmark image.

This implementation enables an opt-in **single clean integrated coding E0** once
its sandbox and task environment pass their gates. Four logical identities remain
in the context store; E0 uses `w0` with one frozen model. The fixture policies,
attacks, budgets and saved results are preserved. Four-policy coding experiments,
coding calibration, attacks and Protocol B are still rejected; the numeric
planner is not applied to source code.

## Isolation design

- Every operation invokes the pinned private Apptainer runtime with user, PID,
  IPC and network isolation, no routes, all capabilities dropped, no home or
  automatic host binds, and a small allowlisted host environment. There is no
  GPU bind and no host execution fallback.
- The source, fixed helper and request are readonly mounts. Work takes place in
  private `/tmp`, which qualification must establish is tmpfs. No writable host
  bind exists. Cgroup memory bounds therefore also bound private filesystem use.
- One **delegated cgroup v2** child per invocation limits memory (including swap),
  process count and aggregate CPU bandwidth. The trusted host bootstrap joins
  that child before executing Apptainer. On timeout, excess wire output, errors,
  and normal completion, `cgroup.kill` kills descendants, including detached
  sessions. The adapter verifies the cgroup is empty before removing it.
- Delegation requires a writable parent with `memory`, `pids` and `cpu` enabled
  in `cgroup.subtree_control`, plus `cgroup.kill`. Merely having Slurm memory
  limits, user namespaces or an Apptainer executable does not establish this.
  The program never changes site-wide controller settings or substitutes weaker
  limits. If unavailable, ask the site for delegation within the allocated job.
- Read/write/list/delete/command/submit operations transfer only bounded data.
  Every call reconstructs its workspace. Returned edits reject traversal,
  symlinks, hard links, special files, Git history and excessive file sizes/counts.
  Transfers allow at most 20,000 files, 256 MiB total, 4 MiB per file and 8 MiB of
  changed bytes per call. Unsupported repositories fail explicitly.
- Only the terminal evaluator receives the two selected test patches and reviewed
  test drivers. Reference patches are mounted only for environment positive
  controls, never for model runs. No hidden evaluation response returns to a
  worker, including on retry.

This is containment, not a claim to defend against kernel vulnerabilities. The
image and private runtime are trusted reviewed dependencies. Review must exclude
credentials, scheduler tools/sockets, hidden benchmark material and Git history
from the image itself. Mount flags cannot hide files baked into an image.

Official interfaces: [Apptainer exec](https://apptainer.org/docs/user/1.5/cli/apptainer_exec.html),
[Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).

## 1. Inspect capabilities on the target compute node

After syncing this source to the cluster, use the browser-terminal Slurm workflow
to run this trusted diagnostic in a short CPU allocation. It submits no jobs,
loads no model and executes no repository programs:

```bash
python scripts/bc.py sandbox-inspect \
  --runtime-root "$BC_PRIVATE_APPTAINER" \
  --image "$BC_STORAGE/containers/alpine-3.24.1.sif"
```

The output includes the private runtime fingerprint and the current cgroup's
delegation status. The Alpine image can be used for this read-only inspection.
Actual qualification needs the **intended reviewed coding image**, with a Python
3 interpreter and Git for test-patch application, plus its task dependencies.
The Alpine image used in the basic probe has not established those dependencies.
Do not download/install tools during a measured episode. A dependency image should
contain dependencies only; supply reviewed pristine source separately. Do not
bake a dataset checkout, feature patches, test patches, or Git history into it.

## 2. Create a profile and qualify it

Use new output paths; do not mutate profiles or environments used by jobs.
`BC_CODING_IMAGE` is the actual task image, not an invented benchmark image name.

```bash
python scripts/bc.py sandbox-profile \
  --runtime-root "$BC_PRIVATE_APPTAINER" --image "$BC_CODING_IMAGE" \
  --scratch-root "$BC_STORAGE/sandbox-scratch" \
  --python /usr/local/bin/python3 \
  --output "$BC_STORAGE/sandbox-profile.json"

python scripts/bc.py sandbox-probe \
  --profile "$BC_STORAGE/sandbox-profile.json" \
  --output "$BC_STORAGE/sandbox-node13-report.json"
```

Set `--python` to the interpreter actually installed in the image. `current`
finds the nearest already-enabled delegated ancestor of the current process;
a populated leaf cannot distribute memory to child cgroups. A site-provided
delegated absolute ancestor may instead be set with `--cgroup-parent`. Site
review must ensure delegation stays within the allocation's resource envelope.
The probe executes only fixed project-owned tests,
reports individual checks and returns a nonzero exit status on failure. It never
approves itself. Resource checks verify kernel cgroup limits; they do not run an
unbounded fork bomb or memory exhaustion workload. The cleanup test starts a
detached child and requires the invocation cgroup to become empty after timeout.

After reviewing the image content, site policy and passing reports, the reviewer
may explicitly record approval:

```bash
python scripts/bc.py sandbox-approve \
  --reports "$BC_STORAGE/sandbox-node13-report.json" \
  --reviewer "$USER" --image-reviewed \
  --output "$BC_STORAGE/sandbox-approval.json"
```

Approval binds the node name, kernel, user, profile, image, runtime tree and helper
source hashes. Qualify every eligible node before scheduling across a partition.
At execution an unqualified node fails before model loading. `sandbox-approve`
records the operator's explicit review; it is not an administrator attestation or
a substitute for site permission. Approval files remain outside worker mounts.

## 3. Prepare the actual task environment

Stage/import real upstream data using the existing `stage-data` and `cooper-import`
commands. Source staging is a separate explicit preparation step: obtain the
exact base commit recorded by the imported task and export a reviewed pristine
tree **without Git history, hidden tests or reference patches**. Do not execute
upstream setup/build scripts on the host. The tree is copied as data only. The
operator review asserts its relationship to the upstream commit; this adapter
does not invent a provenance claim from a directory name or run Git hooks.

Create a private JSON `suites` mapping **both actual feature IDs** to reviewed
argv arrays which run their test suites against `/tmp/work`. The evaluator makes
the original `run_tests.sh` and `runner.sh` available under `/bc/evaluator`;
invocation arguments vary by upstream repository and must be inspected from the
staged version. No generic test command is assumed. Both test patches are applied
to one integrated candidate before the suites run. Test-patch or reference-patch
conflicts are environment failures, not silent patch omission or task failure.

```bash
python scripts/bc.py cooper-environment \
  --data-manifest "$BC_STORAGE/cooper-data-manifest.json" \
  --task-id "$BC_TASK_ID" --base-root "$BC_BASE_TREE" \
  --profile "$BC_STORAGE/sandbox-profile.json" \
  --approval "$BC_STORAGE/sandbox-approval.json" \
  --suites "$BC_STORAGE/cooper-suites.json" \
  --reviewer "$USER" --source-reviewed \
  --output "$BC_STORAGE/cooper-environment.json"

python scripts/bc.py cooper-validate-environment \
  --environment "$BC_STORAGE/cooper-environment.json" \
  --data-manifest "$BC_STORAGE/cooper-data-manifest.json" \
  --output "$BC_STORAGE/cooper-environment-validation.json"
```

The second command runs baseline and reference controls inside the approved
sandbox without a model. Both feature suites must fail the unchanged base and
pass with both reference patches applied. Validation preparation work is reported
separately and is not a model outcome. Failure needs repository-specific review;
do not weaken the expected control results to make a task eligible.

## 4. Freeze one clean coding E0

Copy `configs/cooper-e0.template.json` to a gitignored `.local.json`. Set the three
absolute paths (`data_manifest`, `coding_environment`, `coding_validation`) and
the correct preassigned `data_split` for the selected task. The imported selection
must place that task first in its split. `manifest` pins environment and validation
hashes and rejects mismatched tasks or stale controls.

Use the existing `manifest --model-lock ...`, `submit --concurrency 1 --dry-run`,
explicit submission and `aggregate` workflow. GPU submission continues through
the shared per-user registry, immutable source snapshot and scheduler inspection.
Do not use a separate ad hoc GPU launcher. No commands in this document authorize
a large download, a full campaign or bypassing the registry.

`coding-structure-v1` is an explicit E0 monitor label: source and artifact format
checks only, no hidden tests as public feedback. Complete task success requires
both terminal feature suites. Model input/output, malformed calls, tool dispatch,
source materialization and sandbox/evaluator work are charged. CPU quota, memory,
process limits and elapsed wall time are recorded; the token/tool surrogate is
not a FLOP estimate. Contexts are never silently truncated.

Interrupted primary coding work restarts from pristine source and keeps all prior
and uncertain charges. Completed episodes never rerun. After entering terminal
evaluation, retry may re-evaluate the frozen candidate but never call the model
again. This differs explicitly from the fixture engine's operation-level resume.

## Local and cluster validation

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
```

Local tests inject labelled sandbox responses and do not execute downloaded or
model-generated code. They are not evidence of actual containment. To run the
opt-in real qualification test **inside the intended compute allocation**:

```bash
BC_SANDBOX_TEST_PROFILE="$BC_STORAGE/sandbox-profile.json" \
  python -m unittest tests.test_repository.RealSandboxTests -v
```

This test is skipped by default. Cluster qualification, task image preparation,
operator approval, environment controls and a real coding model episode remain
pending until their actual reports are supplied.
