# Beyond Consensus: SQLite/SILO migration and progress handoff

## Latest continuation: post-EOS control and CPU budget audit (2026-09-19)

Preflight 1078003 verified EOS 248046 with both stop IDs. Array 1078005 still
completed 0/2 native solar tasks, 73320 work, both artifacts missing. The view
worker spent 12 actions reading; the query worker made two identical malformed
query attempts, both capped at 768 tokens with their first JSON error at column
256. No SQL executed. Twenty-two other generations stopped correctly.

Do not repeat the EOS preflight/control sequence below. Next use the
[read-only budget audit](docs/RESEARCH_GATE.md#solar-budget-audit). The script
checks recorded validation provenance and compiles reference trees without
executing them. Optional offline tokenization uses the cluster's existing
environment; no weights load. Reference contents stay private, outside worker
views. Counts are unmeasured locally because the prior temporary reference
files and pinned tokenizer are no longer available. Preserve the historical
failures and current settings; a larger model/budget is not yet selected.

## Prior continuation: verified stopping metadata mismatch (2026-09-19)

The user reports text-config EOS 248044 (`<|endoftext|>`), tokenizer EOS 248046
(`<|im_end|>`), and a template using the latter to close messages. There is no
staged `generation_config.json`. The previous backend did not explicitly add
tokenizer EOS to the model's effective stop set. Generated fake dialogue is
consistent with crossing a turn boundary, but raw historical token IDs were not
saved and this does not explain all failed tool choices.

Local correction: pass the union of model and verified tokenizer stop IDs on
every generation, use tokenizer padding if needed, and record effective/final
token IDs. All tokens remain charged. Real calibration now binds the generation
policy; new manifests are required. Locked metadata, prompts, budgets, model
settings and strict action parsing stay unchanged. Review/deploy then use
[the bounded fresh-manifest/preflight sequence](docs/RESEARCH_GATE.md#solar-turn-stopping-correction).
No GPU was run locally; both prior solar controls still scored 0/2. See
[the metadata record](docs/VALIDATION.md#tokenizer-turn-stopping-correction-2026-09-19).

## Prior continuation: document discovery worked partly; native control still fails (2026-09-18)

Array 1077718, experiment `754c06ed06a51174619455ced15d592db875cbbdca1c39f15f157808801643c4`,
completed 0/2 with missing artifacts and 71489 charged work (+25.7%). The query
worker used the catalogue and read relevant documents, then generated one
simulated conversation to the 768-token cap and reread the documents. The view
worker read `kb-0` through `kb-8` sequentially without the catalogue. Neither
attempted SQL. Both reached the unchanged 12-action cap.

Pause further identical/prompt-only runs. Next use the [read-only metadata audit](docs/RESEARCH_GATE.md#solar-metadata-audit)
on the existing model lock; no model loading or job submission is needed.
A tokenizer/stopping defect is not established by the decoded transcript.
No code/config/scoring change was made in this follow-up. Preserve both failures;
clean-model competence, a second pair and broader policy gates remain unmet.
See [the evidence](docs/VALIDATION.md#solar-document-discovery-follow-up-2026-09-18).

## Prior continuation: solar model read-loop diagnosis (2026-09-18)

Preflight 1077667 passed; user-reported run array 1077671 completed both native
tasks but failed 0/2 with missing artifacts. Each worker spent all 12 actions on
one schema read and eleven identical contract reads, with zero rejections and
no document reads/SQL/submission. All generations ended with EOS; work was
27882 (`solar_2`) and 28985 (`solar_M_3`). Historical experiment
`39194c9de0eafc3e98c9cf02393afd7483f39476e36b61addf6afc2c6556b9f4`
is a completed failure, not retryable infrastructure work.

The local shared-interface correction removes the schema reread cue and adds
charged, paged public document titles (`list_documents`). It never selects by
gold or generates SQL. Source reads, limits, model settings and scorer remain
unchanged; whether it fixes the real model is unmeasured. Next review/commit/push
then prepare a fresh two-task manifest with the same inputs/settings. Use
[the bounded preparation commands](docs/RESEARCH_GATE.md#solar-read-loop-correction)
and stop at preflight dry run. No broader campaign, model sweep or SILO rerun.
The assistant has not submitted a job or pushed code. See
[the evidence](docs/VALIDATION.md#solar-native-model-control-read-loop-2026-09-18).

## Prior continuation: solar cluster CPU references passed (2026-09-18)

The user reports both `solar_2` and `solar_M_3` validated with all positive,
reset, integrity, missing and corrupted controls passing. Use the actual cluster
manifest at `$BC_STORAGE/private/livesqlbench/solar-check.NatDlH/native-validated.private.json`.
The next step is a two-task single/clean competence control with
`qwen35-4b-control`, the existing model lock, fresh preflight and one concurrent
GPU shard. Keep the unchanged decoding/budget settings. The two tasks are one
source group; no GPU competence or cluster joint-pair result is available yet.
The prior dry-run identifier 1077655 is not the actual job ID. See
[VALIDATION.md](docs/VALIDATION.md#solar-cluster-cpu-result-reported-by-the-user-2026-09-18).

## Prior continuation: solar CPU references pass locally (2026-09-18)

The user staged the solar database/documents and private merged materials on the
cluster. The assistant completed a private typed-tree review and validated both
`solar_2` and `solar_M_3` locally, including negative/reset/integrity controls.
Their one joint pair also passed; the requested second pair remains missing.
No GPU competence is established. All checks use the existing strict reference
result-comparison adaptation, with its differences from upstream sample/tolerance
tests documented in [VALIDATION.md](docs/VALIDATION.md#solar-reference-review-and-local-cpu-controls-2026-09-18).

Transfer `/tmp/bc-author-materials.f0n5jtmc/solar-review-v1/solar-review.private.json`
through the browser, hash-check and register it outside Git using
[the current commands](docs/RESEARCH_GATE.md#solar-review-transfer-and-registration).
Then prepare CPU batch replay from a frozen source copy. No scientific code or
scorer changes need deployment; the review is private data and must not be pushed.
The earlier unapproved template and all historical outputs remain intact.

## Prior continuation: private author material joined (2026-09-18)

The uploaded supplement joins all 270 pinned public task IDs. The merged private
JSONL is outside Git at `/tmp/bc-author-materials.f0n5jtmc/materials.private.jsonl`;
its SHA-256 is `b28bbcf4d1b0f63a6994d6ea1914e187ebc9ba185cb1a69476742b3c4cb3f698`.
Transfer it through the cluster's browser upload to private storage outside the
checkout, then verify that hash. The original attachment is preserved and ignored.
Do not push either input or the merged file.

268 records pass the solution-presence check, 92 have tests and 90 pass both;
these are not counts of supported or validated tasks. Empty tests and blank
solution entries remain unchanged. `crypto_8` has no tests, so the previously
proposed pair remains blocked. Databases and reviewed evaluator translations
are still needed before reference validation. No author code/SQL was executed.
See [the inspection details](docs/VALIDATION.md#author-supplement-inspection-2026-09-18).

## Prior continuation: native SQLite prerequisites (2026-09-18)

Start with [the current research gate](docs/RESEARCH_GATE.md#ordered-next-commands).
The user has now completed the historical ledger audit and both eight-source
SILO conditions. Original and explicit actual-carry interfaces each scored
0/8 tasks and 101/480 values; carry used 185156 versus 173439 work (+6.8%). Local
arithmetic improved, but all eight u1 boundaries still failed. Pause further
4B/no-thinking SILO GPU runs. No broader diagnostic or policy campaign follows.

All eight matched historical recovery/JIT ledger pairs reconcile their 256-unit
gap entirely to finite-search charges. Keep surrogate work distinct from GPU
time. See [the reported evidence](docs/VALIDATION.md#cluster-follow-up-reported-by-the-user-2026-09-18)
for full experiment IDs and limitations; raw cluster results are not local.

Next inspect existing native staging, author solution/test materials and private
review availability. Local readiness has no staging manifest; remote availability
must be checked. Then use existing CPU reference/pair gates on supported tasks,
followed by clean-model competence only when ready. No dataset downloads, jobs,
author messages or pushes were performed by this continuation.

## Prior continuation: research gate implementation (2026-09-18)

Start with [RESEARCH_GATE.md](docs/RESEARCH_GATE.md), which supersedes the earlier
battery-first sequence. The user has not run the previous browser commands.
Local changes add an exact catalogue inventory, matched saved-ledger audit,
opt-in existing numeric boundary choices with common JIT/reserve, and eight-only
SILO preparation. The full local suite passed 159 tests with one existing skip.
Native materials, native workflow alternatives/costs, historical remote ledger
attribution and actual clean-model competence remain blocked/unconfirmed. No
remote execution or empirical recovery advantage is claimed. Review and push
manually, then pull/audit before any separately authorized small GPU control.

## Prior continuation: bounded validation cycle

The incremental native/allocation/SILO diagnostic tooling is now implemented.
Start with [VALIDATION_CYCLE.md](docs/VALIDATION_CYCLE.md) and its ordered commands;
the migration narrative below preserves earlier progress. Native materials,
real GPU/template checks, and full historical pilot ledgers remain unavailable
locally. No jobs or downloads were launched.

The allocator reproduces 256 primary finite-search charges under equal route
estimates, consistent with the reported gap but not proven for the old run.
Its present objective lets JIT buy the same preparation after an alarm: cheaper
prepared repair alone cannot justify advance preparation. This scientific
conflict is documented rather than resolved by forcing a plan. Preparation
execution, dependency rejection and charged restoration are covered by behavioral
tests; empirical cost comparisons remain future measurements.

The next SILO path freezes eight fresh development sources: full baselines first,
then 32 separate local tasks and up to 24 continuations from **actual** baseline
artifacts. Original serialization and pinned 4B/no-thinking remain the control.
No gold carry or arithmetic tool is exposed. Native reference checks can proceed
independently once actual materials are staged and reviewed.

See [the validation record](docs/VALIDATION.md) for current test counts.

## Preserved migration handoff

Updated: 2026-09-17. The **latest attached migration request supersedes the
historical deployment discussion below**. Continue on the current Slurm cluster
with restricted SQLite/SILO data workflows. No PBS, cloud, rental or remote
sandbox is an active option in this task. CooperBench is optional legacy.

Start with [MIGRATION_SQLITE_SILO.md](docs/MIGRATION_SQLITE_SILO.md),
[STATUS.md](docs/STATUS.md) and [LOCAL_TO_SLURM.md](docs/LOCAL_TO_SLURM.md).
The new path reuses the model, workers, budgets, provenance and scheduler, and
does not require cgroup delegation. Real database/material validation remains
pending. After two failed fixture smokes, the third passed following source-ID
and JSON-action feedback corrections. Pilot job 1076661 completed 32/32 episodes
but every policy passed only 2/4 clean tasks. Two clean submissions used the
wrong multipliers; local restricted execution reproduced their incorrect rows.
The ordinary worker traces confirm wrong-source reads followed by new query
generation, plus malformed column-alias JSON during fixture-0 repair. Public
assignment reminders and grammar guidance were added. The revised pilot
`d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd` then passed
32/32 episodes using four GPUs in `PA100q`, as reported by the user. The grouped
cost audit is complete: replication cost more at equal success; preparation
remained zero. Four tool rejections occurred across the clean groups, none under
withholding, and all episodes succeeded.
The subsequent SILO Prefix Sum single/clean smoke `9d2b2a4a...` completed but
failed (0/1 success, no retained artifacts). Its trace confirms 12 rejected
preparation outlines during implementation, with no source/shard reads.
After SILO action examples and operation-specific guidance were added, the second
smoke `055d8a4b...` retained all four segments with no public alarm but still
failed scoring. Its trace confirms zero tool rejections, public integration
true and 3/60 correct values: arithmetic/indexing and predecessor-carry errors.
Shared instructions now state the public scalar recurrence and a self-check;
the fixed tools do not compute corrections. The third smoke `9a7b999f...` also
failed complete-task scoring while retaining all four artifacts. Its trace
confirms 15/60 values correct (u0 fully correct), zero tool rejections, public
integration true and 21581 work. Wrong carries and local arithmetic errors
persist in later segments. Pause further prompt-only reruns and larger SILO pilots.
Prior results and delegation probes are preserved below as history, not current
execution instructions.

## Current implementation and next step

- M0 works locally: bounded SQLite fixture tools, joint scoring, provenance,
  common charged replay and four-policy clean/withholding behavior.
- M1/M2 code paths exist: native staging/review/reference checks and compatible
  same-state pairs. Actual validation is blocked by missing databases and
  author-supplied evaluation materials. No real pair has been approved.
- M3 works locally: explicitly adapted four-worker Prefix Sum and Pipeline Hash,
  original-shard access rules, all-output scoring and public-data parity tests.
- M4 configs and guarded submission paths exist. The single-worker smoke and
  revised four-policy pilot passed; the earlier failed pilot is retained. Each
  policy now passed 4/4 clean and 4/4 withholding fixtures. Replication used
  69.47% more total work than ordinary on clean tasks and 22.87% more under
  withholding. Approved development instances and measured calibration remain pending;
  zero preparation and equal success establish no recovery/preparation advantage.
- Validation: **123 tests, 122 passed, one legacy sandbox integration skip**;
  **9 shell files passed**. CPU fixture/SILO mock CLI checks passed. See
  [the current validation record](docs/VALIDATION.md)
  for exact commands and the limits of this evidence.

First run the local commands in [MIGRATION_SQLITE_SILO.md](docs/MIGRATION_SQLITE_SILO.md#exact-staging-and-next-commands).
After the user reviews, commits and pushes the changes, use the existing browser
terminal to pull and follow [LOCAL_TO_SLURM.md](docs/LOCAL_TO_SLURM.md). The reported
preflight job 1076633 and third smoke already passed. Preserve pilot output
`ef27dbc828f47f76a631a68f9edbf9628b5510c1e0244e43ed26804bf4dfa3d5` and its failure
traces. The revised pilot and grouped cost/rejection audit have completed.
See VALIDATION for the eight cost rows and their interpretation.
Use `configs/cluster.pa100.local.json` for the last
user-verified submission profile; live scheduler availability can change.
Next task-family work is native data/material review and an explicit decision
about a separate SILO model/reasoning competence condition. The frozen settings
remain unchanged; do not silently change thinking mode, weights or generation
limits. Any authorized change needs fresh provenance and charged budgets.
These are development diagnostics on reused inputs, not generalization evidence.
Larger runs remain gated by clean competence.
Keep the same model
lock and campaign guard. Data sabotage is still disabled in code. No remote jobs,
downloads, messages or pushes were performed from this workspace during this
result review.

## Historical decision and immediate objective (superseded)

The user previously proposed a **PBS system with an H200 GPU**, then considered
the current Slurm system with an external sandbox, a personal RTX 5080 PC, Colab
Pro+ and an external GPU rental. The instruction at that checkpoint was:
**document the delegation problem and progress first**. No alternative was
selected for execution or validated. CooperBench was then the intended benchmark;
numeric workflow checks did not fulfil that requirement. The current migration
supersedes that required backend while retaining these observations.

Trying the new system is reasonable. The deciding prerequisite is its execution
environment: container isolation, enforced resource limits and reliable process
cleanup. The GPU model and scheduler name alone establish none of those properties.
No PBS queue, account, resource syntax, driver, storage path or sandbox capability
has been supplied or validated yet.

**Milestone at that checkpoint:** record the completed fixture results, the failed direct
delegation checks, and the insufficient inherited limits. The detailed evidence
is now in [VALIDATION.md](docs/VALIDATION.md#user-reported-delegation-and-inherited-resource-probes).

**If PBS migration is resumed:** inspect a small PBS compute allocation and establish whether
the existing sandbox can be qualified. Then port the scheduler integration and
run one GPU preflight, one fixture smoke, and one clean CooperBench E0 task.
Do not jump directly to the four-policy study.

### Historical follow-up instructions (superseded)

1. Read this file, [AGENTS.md](AGENTS.md), [RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md),
   [STATUS.md](docs/STATUS.md), and [CODING_SANDBOX.md](docs/CODING_SANDBOX.md).
2. Continue from the latest user direction; do not assume a migration or rental
   was carried out. If PBS is chosen, obtain its version, a working submission
   script, accessible queues, account requirements, storage and container policy.
3. Test resource/isolation capabilities in the selected execution environment
   before moving large artifacts or implementing a speculative workaround.
4. Preserve prior experiments and their interpretation. Report missing capabilities
   explicitly; do not turn a failed qualification into an approval.

## Historical user workflow and authorization

- The user runs commands in the cluster's browser terminal and pastes the output.
  The local coding agent has no established remote cluster access.
- The user explicitly preferred `sbatch` over `srun` on Slurm. If a PBS migration
  resumes, use that site's supported batch workflow.
- The request at that checkpoint was documentation work. It did not request migration,
  submission, large downloads, a cloud purchase or a Git push.
- The earlier PBS direction would supersede Slurm-specific workflow wording if
  that migration resumes. Preserve allocation, accounting, isolation and submission
  safeguards for any future backend. No alternative backend has been implemented.
- Retain one active campaign, at most four GPUs, one allocated GPU per shard,
  and no batch self-submission. Start with concurrency one. Reconcile any old-site
  jobs before starting a new campaign; do not infer global inactivity from old logs.

## Historical implementation and executions before migration

| Component | Current state |
| --- | --- |
| Numeric workflow fixtures | Implemented; CPU checks and user-reported real-model GPU pilots completed |
| Ordinary, JIT, replication and recovery policies | Implemented for fixtures, with budget/provenance accounting |
| CooperBench data integration | Read-only import/manifests implemented; exact staged task/image on the user's cluster is unknown |
| Clean coding E0 | Opt-in worker/evaluator and Apptainer adapter implemented; no successful real coding episode reported |
| Four-policy CooperBench execution | Not implemented; numeric decomposition/planning cannot simply be applied to source code |
| Coding attacks, coding calibration and coding Protocol B | Unsupported/deferred |
| Scheduler integration | Slurm only; PBS support must be implemented and tested |
| Sandbox qualification | Basic Alpine isolation passed on the old site; full adapter qualification remains blocked |

E0 uses one clean persistent identity (`w0`) to implement both features in an
integrated repository. Four identities remain in the context store. Full success
requires both feature suites. This is not yet the full recovery experiment.

### Existing evidence (user-reported, not independently executed by the agent)

- GPU preflight job `1076205`: Qwen3.5-4B generated `{"ready":true}` on an
  NVIDIA A100-SXM4-40GB, bfloat16, driver `570.133.20`. Peak allocated memory was
  9,262,348,800 bytes for this short probe, not a full-context capacity measurement.
- Original fixture smoke: 0/1 success. The model copied invalid unquoted JSON
  examples. The shared prompt was fixed; the parser was not relaxed.
- Corrected fixture smoke job `1076319`: 1/1 success, all four outputs retained,
  no false alarms or integration failures.
- Withholding pilot: 32/32 successful episodes across four policies, two conditions,
  four tasks and one seed. Sabotage pilot: another 32/32.
- No advance preparation was selected. These fixtures showed **no recovery-policy
  advantage**. Repeated clean controls are not independent new tasks. Results are
  non-confirmatory engineering evidence, not CooperBench scores.

Experiment IDs:

```text
Original failed smoke:
ee34d5abf1cb3c4d7c503ac20fa771af1c43bc5864906c2c754150402dd0ad80
Corrected successful smoke:
d07eaf6b64fe4ec6393fb332f077fcb1bd2c7ee63f743c6d44ba8b08f8609e56
Withholding pilot:
e05c084a88b15e9f6675e9dfa18da40dee13ac1624cf324d5f807ed37830aeff
Sabotage pilot:
ddbf0217caa8fd82a3a4eea8dc7d6d5ddffe1194d4a6795f2b7227d56f492ab8
```

See [VALIDATION.md](docs/VALIDATION.md) for costs, limitations and earlier checks.

## Why repository execution is blocked on the observed Slurm allocation

Old compute target: `NA10040q`, `node13`, kernel `6.8.0-51-generic`.

The private Apptainer installation worked. A basic Alpine probe established a
separate network namespace with only loopback/no routes, absence of two tested
host paths, and container reads/writes through the explicitly bound work directory.
That probe did not establish all sandbox properties or approve a coding image.

The implemented `apptainer-cgroup-v1` adapter needs a **delegated cgroup v2** parent
with `memory`, `pids` and `cpu` enabled, writable child creation/process migration,
and `cgroup.kill`. It creates a bounded child for each tool invocation and verifies
all descendants are gone before cleanup. Its private tmpfs work area is also
bounded by the cgroup's memory limit.

Evidence now recorded in [VALIDATION.md](docs/VALIDATION.md#user-reported-delegation-and-inherited-resource-probes):

| Probe | Observation |
| --- | --- |
| Jupyter `sandbox-inspect` | Membership in `cm-jupyterhub.service`; no suitable delegation |
| Slurm job `1076414` on node13 | Membership in `job_1076414/step_batch/user/task_0`; no suitable delegation |
| Slurm configuration | `ProctrackType=proctrack/cgroup`, `TaskPlugin=task/cgroup`, `JobAcctGatherType=jobacct_gather/linux` |
| Slurm job `1076418`, requested 1 CPU and 2 GiB RAM | CPU affinity and job cpuset `24,152`; `memory.max=max` and `memory.swap.max=max` at every readable ancestor |
| Same job, process limits | No job-level `pids.max` file; higher ancestors had `pids.max=max`; RLIMIT_NPROC soft/hard were 514932/4126939 |
| Same job, CPU quota | `cpu.max=max 100000`; cpuset confinement was present despite no CPU bandwidth quota |

Thus the requested 2 GiB was **not enforced as a hard cgroup memory cap in this
observed allocation**. The evidence does not establish the absence of every other
possible site monitoring mechanism or the behavior of other nodes/partitions.
Simply inheriting the observed Slurm limits did not satisfy this adapter's needs.

Direct user-managed cgroups are an implementation choice, not a scientific
requirement. An alternative with equivalent tested boundaries is possible, but
none has been implemented or qualified. `timeout`, per-process `ulimit` settings,
or deleting the cgroup gate are not established substitutes for aggregate limits,
private filesystem bounds and descendant cleanup.

## Old environment and artifacts to preserve

These paths are historical; do not assume they exist on PBS:

```text
Remote user: suaq0001
Remote checkout: /export/home2/suaq0001/Beyond-Consensus
BC_STORAGE: /dataset/suaq0001/beyond-consensus
GPU Python: $BC_STORAGE/envs/bc-gpu-py312/bin/python
Model lock: $BC_STORAGE/models/Qwen--Qwen3.5-4B/model-lock.json
Model snapshot: $BC_STORAGE/models/hub/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a
Private runtime: $BC_STORAGE/tools/apptainer-1.5.3.SgKY67
Probe image: $BC_STORAGE/containers/alpine-3.24.1.sif
Outputs: $BC_STORAGE/outputs/<experiment-id>
Snapshots: $BC_STORAGE/snapshots/<snapshot-id>
Shared registry: $HOME/.local/state/beyond-consensus/registry.json
```

- Model: `Qwen/Qwen3.5-4B`, checkpoint/tokenizer revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
- Working reported stack: Python 3.12 environment, torch `2.10.0+cu126`,
  transformers `5.3.0`, huggingface-hub `1.5.0`, tokenizers `0.22.2`,
  safetensors `0.7.0`. The optional fast attention/convolution libraries were
  absent; the torch fallback completed the reported runs.
- Private Apptainer version: `1.5.3-3.el8`. Runtime tree fingerprint:
  `c5e236aecf83b69285371b77444f5da036787b3314c463c6f0b648d4fb69648e`.
- Alpine SIF SHA-256:
  `dcb0a94e5170dba72c2c72fac6c44fad198878994178ce27a86ed8c479f9b8cc`.
  This is a probe image, not a validated CooperBench dependency image.
- The old site module advertised `apptainer/1.24` but ran a 1.4.2 development
  build with missing `libsubid.so.4`. A main-process LD_LIBRARY_PATH workaround
  did not fix runtime helpers. The successful private 1.5.3 installation used
  the official unprivileged installer and a local RPM extraction bootstrap.
  Do not repeat this bootstrap on PBS unless its native runtime needs it.
- A pip install previously exhausted temporary storage. Select adequate scratch,
  cache and environment locations after inspecting new-site quotas.

Preserve manifests, locks, raw logs, outputs and source snapshots outside Git.
Do not copy a Python virtual environment and assume it remains portable. Inspect
the new driver/OS and recreate a pinned environment as needed. Model locks and
configs contain absolute paths; relocate/re-stage through the supported workflow,
verify content, and create new manifests rather than altering old run provenance.
Never reuse old node approvals as authorization for the new site.

Local source at handoff preparation: `5aa6e537e7e642782d0a9baffad666df3be9f215`
(before adding this file). Verify the destination checkout's commit; do not assume
the user has pushed or pulled the handoff or any later changes.

## Deferred PBS migration sequence

This is a conditional plan. The latest documentation request does not activate
these steps or establish that the codebase has moved to PBS.

### A. Discover the site before writing resource requests

Collect, using the browser terminal and the site's documented commands:

- PBS implementation/version (OpenPBS, PBS Professional or another compatible
  system), available `qsub`, `qstat`, `pbsnodes`, modules and Python 3.12+.
- An example **working site submission script**: queue, project/account,
  CPU/memory/walltime syntax, GPU resource name/type, environment setup and logs.
- Storage availability, quota, scratch retention, login-node setup/download rules,
  and whether compute nodes can see the checkout, runtime, images and model files.
- Container runtime/version and site rules for user/network/PID namespaces.
- GPU binding rules, including how the site communicates assigned devices. Do not
  hard-code GPU 0 or assume CUDA_VISIBLE_DEVICES is populated identically to Slurm.

Read-only starting commands, where available:

```bash
hostname
python3 --version
command -v qsub qstat pbsnodes apptainer singularity
module avail 2>&1
qstat -Qf
qstat -u "$USER"
```

Record unavailable commands or denied queries; do not assume this command list
works on every PBS variant. No queue names or `qsub -l` resource strings are
prescribed here because the target site's interface is unknown.

### B. Use a small CPU batch job to inspect containment

Use a site-correct CPU-only PBS script, with explicit bounded RAM and walltime,
to collect hostname/kernel, `/proc/self/cgroup`, `/proc/self/mountinfo`, CPU
affinity, RLIMIT_NPROC and the current cgroup plus all relevant ancestor limits.
For cgroup v2 record `memory.max`, `memory.swap.max`, `pids.max`, `cpu.max`,
`cpuset.cpus.effective`, `cgroup.controllers` and `cgroup.subtree_control`.
The parent limits matter even when a task's own files contain `max`.

Check capabilities inside the compute allocation, not just the login service.
If a suitable runtime and probe image are already available, the existing
read-only command can run before porting the GPU scheduler code:

```bash
python scripts/bc.py sandbox-inspect \
  --runtime-root "$BC_PRIVATE_APPTAINER" \
  --image "$BC_PROBE_IMAGE"
```

Set these paths to actual new-site assets first. This command checks delegation
and fingerprints; it does not load a model, execute the image or approve execution.
The existing adapter requires unified **cgroup v2**. PBS may expose another layout
or cgroup version; report that explicitly. Do not interpret a cgroup v1 hierarchy
as successful validation by the v2 adapter.

Decision after inspection:

- Suitable delegated v2 subtree: proceed to actual image/runtime qualification.
- Enforced scheduler limits but no delegation: assess and implement a separate
  adapter with explicit tests for all missing guarantees; do not silently fall back.
- Neither: request a supported sandbox environment or retain fixture-only execution.

### C. Port scheduler support without bypassing allocation guards

This is more than renaming `sbatch` to `qsub`. Relevant code:

| File | Required review/change |
| --- | --- |
| `src/beyond_consensus/experiments/cluster.py` | Cluster config, discovery, resource validation, active GPU accounting, terminal state inspection, submission, job ID parsing, dependencies, retry and array shard selection |
| `src/beyond_consensus/models/transformers_backend.py` | `require_allocation()` currently requires SLURM_JOB_ID; preflight records a Slurm-only job field |
| `src/beyond_consensus/cli.py` | Scheduler help, status commands, submit/resubmit dispatch |
| `experiments/run_shard.sbatch` and other experiment wrappers | Add a PBS launch path preserving exit codes, signals, immutable snapshots and module/activation setup |
| `src/beyond_consensus/experiments/snapshot.py` | Preserve source/input/environment integrity; assess scheduler config representation |
| `src/beyond_consensus/runtime/container_guest.py` | Qualification currently checks Slurm tool names/environment prefixes; extend checks to PBS tools, PBS environment and relevant credentials/sockets |
| `tests/test_cluster.py`, backend tests, `scripts/check_shell.py` | Add PBS cases and coverage of any new shell file extension while retaining Slurm regression coverage |

Use a scheduler abstraction and explicit scheduler/site identity. Validate the
target's job IDs (including server suffixes and arrays), array index mapping,
state/accounting output and GPU resource counts. Test queued/running/held jobs,
array children, ambiguous submissions and missing terminal history. A disappeared
job is not proof of successful completion. Preserve uncertain-submission blocking.

Retain the shared per-user registry across checkouts/configs; distinguish site
and scheduler IDs so old Slurm records cannot be interpreted as PBS jobs. Preserve
prior registry data. Do not create one independent guard per checkout, fabricate
SLURM_JOB_ID under PBS, bypass model allocation checks or allow batch self-submission.
Use site-supported array throttling or an equivalent guarded bounded submission
strategy, keeping the four-GPU ceiling and no overlapping campaign.

Extend container checks to exclude PBS submission/control tools such as `qsub`,
`qdel`, `qalter` and `pbs_attach`. Keep scheduler access and credentials out of
worker/evaluator environments. Record PBS job identity without breaking old results.

### D. Qualify the task environment and run the smallest useful tests

1. Implement and test PBS dry runs, registry guards and allocation recognition.
2. Recreate/verify the pinned model environment and lock at actual new-site paths.
3. Through the guarded PBS workflow, run one GPU preflight and one numeric fixture
   smoke. Measure the actual H200 identity, driver, visible device and model output.
   Preserve old results and use new source/environment manifests.
4. Identify the actual CooperBench dataset revision, task pair, pristine base tree
   and dependency image. Their availability has not been confirmed by the user.
5. Follow [CODING_SANDBOX.md](docs/CODING_SANDBOX.md): `sandbox-profile`,
   `sandbox-probe`, explicit review with `sandbox-approve`, `cooper-environment`,
   then `cooper-validate-environment`. The actual image needs Python/Git and reviewed
   task dependencies; the old Alpine marker probe is insufficient.
6. Require both feature tests to fail the unchanged base and pass the combined
   reference implementation. Keep reference patches and hidden tests out of workers.
7. Freeze one clean `single`/`clean` Protocol A E0 manifest using
   `configs/cooper-e0.template.json`; submit at concurrency one, inspect traces,
   and aggregate. A completed job alone does not establish task success.
8. Only after real coding E0 works, design/implement coding decomposition,
   calibration, policies and attacks before considering the larger research pilot.

## Scientific and implementation constraints to retain

- Python 3.12+ standard library for CPU functionality and CLI help; lazy GPU imports.
- Four persistent logical identities share one frozen model on one allocated GPU.
- Charge all task-specific work, including retries and discarded/uncertain work.
  Keep equal-total Protocol A separate from equal-remainder diagnostic Protocol B.
- Keep attacker truth, public monitoring and hidden evaluation separate. Method
  labels must not influence model/evaluator behavior.
- No downloaded/generated repository code on the host. Real code executes only
  through a tested, reviewed sandbox. No image/runtime detection shortcut to approval.
- Do not fabricate task metadata, calibration, capabilities or experimental outcomes.
- Keep models, datasets, environments, raw outputs, snapshots, private test material
  and credentials out of Git. No authentication in Git URLs.

## Validation and primary references

Run the required checks after changes:

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
git diff --check
```

Checks rerun while preparing this handoff: **76 tests: 75 passed, 1 skipped**
(10.201 seconds), all nine shell checks passed, and `git diff --check` passed.
Local Markdown links were checked. The skipped test requires a real explicitly
configured Apptainer sandbox. Local tests do not establish PBS or container
capabilities. This handoff changes documentation only; no PBS job was submitted.

- [Apptainer: limits inherited from an external scheduler](https://apptainer.org/docs/user/1.5/cgroups.html#applying-resource-limits-with-external-tools)
- [Linux cgroup v2: limits, delegation and cleanup](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Slurm cgroup configuration](https://slurm.schedmd.com/cgroup.conf.html)
- [OpenPBS cgroup hook source](https://github.com/openpbs/openpbs/blob/master/src/hooks/cgroups/pbs_cgroups.PY)
- [OpenPBS qstat manual source](https://github.com/openpbs/openpbs/blob/master/doc/man1/qstat.1B)

The OpenPBS references establish interfaces to investigate, not the installation,
configuration or cgroup version of the user's new site. Prefer its actual version's
documentation and observed allocation behavior when implementing support.
