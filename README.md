# Beyond Consensus

Research foundation for **Adversarially Robust Division of Labour in LLM Agent Teams**.

The question is whether recovery-aware delegation improves complete-task success
under contributor compromise at the **same total execution budget**. Preparation
has no built-in success advantage or cost discount.

## Run locally

Python 3.12+; no CUDA, model downloads, APIs, Slurm or Docker required:

```text
python -m unittest discover -s tests -v
python scripts/check_shell.py
python scripts/bc.py --help
python scripts/bc.py demo --output outputs/mock-demo
```

Optionally install the `bc` entrypoint with `python -m pip install -e .`.
The mock demonstration executes bounded numeric workflows with real action parsing,
tools, budgets, attacks, provenance, recovery and final evaluation. Its results
are labelled **mock_demo** and are not coding-benchmark research evidence.

## What works

- Four E1 policies and a clean single-agent E0 baseline.
- Equal-total-budget execution and a separately labelled fixed-repair-allowance
  diagnostic; full accounting, dependency tracking and conservative resume.
- A finite allocation solver, measured calibration, and full planned-grid reporting.
- Lazy Qwen/Transformers inference, explicit staging, and guarded Slurm scripts
  using immutable code snapshots and a shared four-GPU limit across wrapped campaigns.
- A versioned CooperBench loader with hashes, pair IDs and grouped splits.

**Real CooperBench execution is blocked:** an approved sandbox and its coding
worker/evaluator integration are still required. GPU inference and live Slurm
submission have not been tested here. `configs/e1.json` is a **320-episode plan**,
not completed coverage. The four-task GPU pilot uses labelled workflow fixtures.

## Guides

- [Local → GitHub → Slurm runbook](docs/LOCAL_TO_SLURM.md)
- [Research protocols and policy definitions](docs/RESEARCH_PROTOCOL.md)
- [Models, upstream data and sandbox boundary](docs/MODELS_AND_DATA.md)
- [Implemented and deferred features](docs/STATUS.md)
- [Local validation record](docs/VALIDATION.md)

No jobs are submitted by installation or tests. The user stages large artifacts,
commits/pushes changes and authorizes experiments explicitly.
