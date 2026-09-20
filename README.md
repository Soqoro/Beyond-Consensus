# Beyond Consensus

**Current status: opt-in 27B competence path prepared; not executed.**
The user selected Qwen3.5-27B after reviewing the
[2026-09-20 progress report](docs/PROGRESS_REPORT_2026-09-20.md).
Follow the [ordered manual runbook](docs/QWEN27B_COMPETENCE.md) for staging,
qualification and bounded tests. Existing 4B controls remain unchanged; the latest
4B result is 1/4 complete tasks and 3/4 public integration. No 27B memory-fit,
native-competence or recovery-method result is established.

Research foundation for **Adversarially Robust Division of Labour in LLM Agent Teams**.

The question is whether recovery-aware delegation improves complete-task success
under contributor compromise at the **same total execution budget**. Preparation
has no built-in success advantage or cost discount.

The required evaluation path is now **restricted SQLite data artifacts** adapted
from LiveSQLBench-Base-Lite-SQLite and an explicitly labelled **SILO recoverable
contributor adaptation**. Numeric workflows remain controlled diagnostics.
CooperBench is an optional legacy adapter. This is data-workflow research,
not repository-level coding evidence.

## Run locally

Python 3.12+; no CUDA, model downloads, APIs, Slurm or Docker required:

```text
python -m unittest discover -s tests -v
python scripts/check_shell.py
python scripts/bc.py --help
python scripts/bc.py demo --output outputs/mock-demo
python scripts/bc.py data-capabilities
python scripts/bc.py demo --config configs/sqlite-demo.json --output outputs/sqlite-demo
```

Optionally install the `bc` entrypoint with `python -m pip install -e .`.
The mock demonstration executes bounded numeric workflows with real action parsing,
tools, budgets, attacks, provenance, recovery and final evaluation. Its results
are labelled **mock_demo** and are not coding-benchmark research evidence.
The SQLite demo is labelled **mock_sqlite_fixture_development**. Its fixed CPU
executor requires supported Python/SQLite defensive settings and stdlib process
limits (tested locally on Linux); missing capabilities produce an explicit block.
Neither data adapter requires containers, cgroup delegation, root, or services.

## What works

- Four E1 policies and a clean single-agent E0 baseline.
- Equal-total-budget execution and a separately labelled fixed-repair-allowance
  diagnostic; full accounting, dependency tracking and conservative resume.
- A finite allocation solver, measured calibration, and full planned-grid reporting.
- Lazy Qwen/Transformers inference, explicit staging, and guarded Slurm scripts
  using immutable code snapshots and a shared four-GPU limit across wrapped campaigns.
- A bounded JSON SELECT/view API, version-pinned provenance, and charged replay.
- Native SQLite staging/prerequisite inspection and reviewed reference/pair
  validation commands. Public empty gold/test fields block scored readiness.
- Prefix Sum and Pipeline Hash data/scorer adapters, four-worker generation,
  explicit protected-shard/no-copy regimes, and complete-segment scoring.

**Real SQLite benchmark validation remains pending:** databases, author-provided
solutions/tests, and reviewed translations to the restricted evaluator are
required. `crypto_M_2` + `crypto_8` is an unvalidated candidate. The user-reported
SQLite GPU preflight and corrected third fixture smoke passed. Pilot job 1076661
completed 32/32 episodes, but every policy passed only 2/4 clean tasks. Two clean
submissions used wrong multipliers after reading another assignment's contract.
After public assignment reminders and column-alias guidance were added, the
revised fixture pilot passed **32/32 episodes** on user-reported PA100q allocations.
Replication used more total work at equal success; preparation work stayed zero.
The grouped cost audit is complete. The first SILO Prefix Sum GPU smoke completed
but failed (0/1): the worker repeatedly submitted preparation outlines during
implementation. After action guidance was added, the second smoke retained all
four segments with no public alarm but still failed scoring: arithmetic and
predecessor-carry errors left only 3/60 numerical outputs correct. Shared
instructions now state the public recurrence explicitly, but the third smoke
also failed complete-task scoring. Its trace shows improvement to 15/60 correct
values (one segment), with persistent carry/arithmetic errors. Further prompt-only
reruns and larger SILO pilots are paused pending a model-competence decision.
Native/paired SQLite GPU
runs remain pending. Cluster observations and prior numeric
results are recorded in VALIDATION. `configs/e1.json` plans 320 episodes only
after 20 approved development
pairs exist; it never manufactures missing pairs. The default GPU smoke/pilot
configs now select labelled SQLite fixtures; `numeric-*.json` preserve prior configs.

Legacy CooperBench still fails closed without its approved sandbox. The observed
Slurm delegation limitation is preserved in the historical documentation and
does not block the new restricted data-tool path.

## Guides

- [Local → GitHub → Slurm runbook](docs/LOCAL_TO_SLURM.md)
- [Research protocols and policy definitions](docs/RESEARCH_PROTOCOL.md)
- [Models, upstream data and sandbox boundary](docs/MODELS_AND_DATA.md)
- [Implemented and deferred features](docs/STATUS.md)
- [Local validation record](docs/VALIDATION.md)
- [SQLite/SILO migration, interfaces, limits and prerequisites](docs/MIGRATION_SQLITE_SILO.md)

No jobs are submitted by installation or tests. The user stages large artifacts,
commits/pushes changes and authorizes experiments explicitly.
