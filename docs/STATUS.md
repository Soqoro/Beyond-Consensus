# Implementation status and handoff

## Current checkpoint: restricted SQLite/SILO migration (2026-09-16)

The latest attached implementation request supersedes CooperBench as the required
backend. We remain on Slurm; PBS and external-hosting paths are not active plans.
The required scope is executable data workflows. The prior uncommitted progress
and delegation evidence below is retained as history.

- Implemented: restricted SELECT/view trees and fixed CPU executor; SQLite
  fixture episodes through existing policies/accounting/provenance; pinned nested
  view bindings and common charged replay of surviving query templates.
- Implemented: local native staging/inspection, exact-record review scaffolds,
  reference and negative controls, common-state pair validation, and v2 manifests.
- Implemented: Prefix Sum/Pipeline Hash SILO adaptation with four workers,
  explicit protected/no-copy access, public-input/scorer parity checks and all
  original output obligations. Communication changes are labelled explicitly.
- Preserved: numeric diagnostics, original model/dependency settings, A/B budget
  separation, Slurm registry, one GPU per shard, four-GPU guard and snapshots.
- Locally validated: 113 tests (112 passed, one opt-in legacy sandbox skip), nine
  shell files, bounded CPU fixture/SILO mock CLI execution and missing-material
  failure paths. These are engineering checks, not model/benchmark results.
- User-reported cluster check: SQLite/model preflight job 1076633 passed on an
  A100 40 GB. The first full SQLite fixture smoke completed but failed (0/1).
  Its trace shows database/source-ID confusion and queries submitted without
  reading the assigned contracts. Shared prompt/error feedback is corrected
  locally; a fresh real-model smoke is required before the four-task pilot.
- Blocked externally: native benchmark validation needs actual databases,
  author-supplied nonempty solutions/tests and reviewed restricted translations.
  No actual native tasks or pairs have been validated. The crypto pair remains
  a candidate. Native/paired SQLite and SILO model/Slurm runs remain unexecuted.
- Deferred: new semantic sabotage until clean/withholding gates pass, remaining
  SILO families, E2–E5, adaptive attacks and grouped inferential statistics.

See [MIGRATION_SQLITE_SILO.md](MIGRATION_SQLITE_SILO.md) for M0–M4, precise subset
limitations, source pins, scorer differences and exact next commands. Local
test outcomes are recorded in [VALIDATION.md](VALIDATION.md).

## Historical checkpoint: delegation blocker and prior progress

The user's preceding request was to document the results and delegation problem.
Alternative hosting and migration work is deferred; no PBS, local-PC, Colab,
remote-sandbox or rented-GPU deployment has been validated or selected for execution.

- **Working:** Qwen3.5-4B GPU preflight, corrected single-task fixture smoke (1/1),
  and two 32-episode fixture pilots (32/32 each), all reported by the user.
- **Scientific interpretation:** no advance-preparation work or demonstrated
  recovery-policy advantage in those pilots. Repeated clean controls are not
  independent tasks. These are fixture results, not CooperBench results.
- **Partial containment evidence:** the basic Alpine probe passed on Jupyter and
  node13, but did not qualify the full coding sandbox.
- **Direct delegation blocked:** `sandbox-inspect` found no usable delegated
  cgroup v2 parent on Jupyter or inside Slurm job `1076414` on node13.
- **Inherited limits insufficient in the observed allocation:** job `1076418`
  requested 2 GiB but had `memory.max=max` and `memory.swap.max=max` at every
  readable ancestor. Its job cgroups lacked `pids.max`; higher groups were
  unlimited. CPU confinement to logical CPUs `24,152` was present.
- **Still pending:** a qualified repository sandbox, actual task image/source
  controls, and the first real clean CooperBench E0 episode. Four-policy coding
  execution remains unimplemented.

Writable delegation is required by the legacy repository adapter, not by the research
question itself. An alternative must establish equivalent tested resource and
isolation boundaries; none has been implemented. The existing fail-closed checks
remain in effect. See the [delegation evidence](VALIDATION.md#user-reported-delegation-and-inherited-resource-probes)
and [handoff](../handoff.md) for the exact observations and deferred options.

## Plan and bounded milestones

1. **A — CPU foundation:** schemas, accounting, provenance, bounded model/tool
   execution, terminal evaluation, mock episodes and regression tests.
2. **B — Model/cluster support:** inspected official interfaces, lazy Transformers
   backend, explicit staging, GPU diagnostics, Slurm dry runs and commit snapshots.
3. **C — Research behavior:** four policies, finite robust allocation, selective
   reconstruction, separate A/B protocols, manifests/resume/reporting and a
   versioned CooperBench loader with guarded execution.

## Delivered

- `src/beyond_consensus/`: typed records and strict JSON configuration; `bc` CLI;
  injected model and runtime components; deterministic mock and one real backend.
- Complete numeric workflow episodes and a clean single-agent E0 baseline.
- Ordinary fallback, JIT indexing/planning/reconstruction, independent selective
  replication, recovery allocation with optional preparation and reserves.
- Model/tool/search reservations, full re-prefill and retry charges, bounded attack
  timeouts, independent attacker accounting, public audit and terminal evaluation.
- Artifact/message dependencies, selective invalidation and context snapshots.
- Finite allocation and reconstruction with shared prerequisite accounting,
  comparison to an independent tiny-case oracle, and explicit search-limit status.
- Measured development calibration command and prediction errors; uncalibrated
  status and confirmatory-claim blocking when appropriate.
- Protocol A end-to-end execution; executable CPU Protocol B capture/comparison.
- Full planned manifests, deterministic IDs, grouped splits, task sharding,
  append-only events, atomic results, conservative checkpoint/resume, complete
  coverage reports and small sanitized exports.
- Model/data staging commands; offline, single-device Qwen backend and preflight.
- Slurm helpers with one shared per-user submission guard, immutable commit
  archives, resolved input hashes, environment inventory and no editable imports.
- CPU CI, platform-neutral Python entrypoint, pinned dependency specifications,
  LF enforcement, configuration templates, profiles and the browser-terminal runbook.
- Opt-in Apptainer/cgroup adapter, qualification/review commands and a clean
  integrated coding E0 worker/evaluator. CPU tests inject sandbox responses;
  actual cgroup/container qualification and a real coding episode remain pending.

## Legacy coding boundaries and deferred work

**C is complete for typed fixtures and manifest integration, not for real coding
experiments.** The exact external prerequisite is an approved, tested cluster
sandbox. The site must establish denied network/home/credential access, resource
limits, isolated workers and evaluator, and absent hidden tests/reference patches
including Git history. No such capability was available here. Docker/Apptainer
presence alone is insufficient. The loader fails closed; it does not execute a
stub and mark it successful.

The user subsequently reported a successful basic Apptainer probe on Jupyter
and supplied successful compute-node probe logs from `node13` (kernel
`6.8.0-51-generic`, private Apptainer `1.5.3-3.el8`). The probe checked an explicit
writable work mount, absence of two tested host paths, and a separate network
namespace with no routes. This establishes basic container operation on that
node, not the full sandbox contract above. Credential/socket isolation, resource
enforcement, worker/evaluator separation and hidden-material exclusion remain
unvalidated. See [VALIDATION.md](VALIDATION.md) for the image identity and evidence.

The clean coding E0 adapter and joint evaluator are now implemented behind
explicit image/site qualification, source review and baseline/reference controls.
They remain unvalidated on the cluster and cannot run from the old Alpine probe
alone. Four-policy coding decomposition/cost calibration cannot be inferred from
numeric fixtures and remains unimplemented. See [CODING_SANDBOX.md](CODING_SANDBOX.md)
for exact gates and commands. Real GPU fixed-state capture, restored-context reconstruction
routes, oracle localization, adaptive attacks, dependency-poisoning sweeps,
cross-family/Gemma validation, grouped confidence intervals, and E2–E5 are deferred.

Initial implementation validation used CPU and scheduler mocks only. Subsequent
user-provided cluster logs report a successful Qwen3.5-4B preflight on an A100
40 GB, followed by a completed but unsuccessful single-task fixture episode.
After correcting the invalid JSON examples, the user reported a successful
single-task GPU episode and two successful 32-episode fixture pilots: clean
versus withholding, and clean versus artifact sabotage. No advance preparation
was used; these runs do not establish a recovery-policy advantage. They do not
validate real repository isolation or CooperBench execution. See
[VALIDATION.md](VALIDATION.md) for the reported hardware, revision and limitations.

## Conflicts and scientific choices

- The repository initially contained only a README. No manuscript or AAI PDF was
  found in the repository or available local attachments. The supplied request is
  the scientific specification; its AAI facts are recorded as a documentation
  snapshot, not current scheduler information. No unavailable manuscript constraint
  is claimed to have been checked.
- The initial implementation followed the requested Slurm/browser workflow.
  The user later considered PBS H200 migration, then local/remote alternatives,
  then requested documentation first. The latest attached request now explicitly
  selects restricted SQLite/SILO data workflows on the original Slurm system.
  Historical PBS/hosting discussion is superseded; delegation stays a legacy
  repository-execution issue.
- The model card's mutable development installation example is replaced by an
  inspected release pin, with GPU validation explicitly pending.
- CooperBench's upstream namespace/commit observations differed across cached web
  pages and live metadata. `MODELS_AND_DATA.md` records both observations. Import
  requires explicit version metadata instead of silently equating them.
- Immutable source fixtures can make JIT as effective and cheaper. The default
  allocator is allowed to choose no preparation. Mock demonstrations provide no
  evidence that recovery improves research-task success.

## Validation

See `docs/VALIDATION.md` for the exact commands and outcomes from this workspace.
Regression tests exercise accounting, exposure, provenance, allocation, final-output
coverage, grouped splits, resume, protocol separation, sandbox blocking, sanitization,
and scheduler mocks. The opt-in repository-isolation integration test is skipped
without an explicit cluster sandbox profile; it executes real probes when one is supplied.

Next local commands and the separate online-cluster sequence are in
[LOCAL_TO_SLURM.md](LOCAL_TO_SLURM.md). Stop before experiments until the user has
reviewed the implementation, configured actual site facts and authorized submission.
