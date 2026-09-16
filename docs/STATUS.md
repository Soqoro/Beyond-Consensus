# Implementation status and handoff

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

## Boundaries and deferred work

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
- The requested Slurm/browser workflow supersedes any older PBS, node-specific or
  remote-shell workflow. None was present in the initial repository.
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
