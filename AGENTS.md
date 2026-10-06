# Beyond Consensus project constraints

Read `docs/RESEARCH_PROTOCOL.md` and `docs/STATUS.md` before changing scientific
behavior. Preserve existing work and record scientific conflicts explicitly.

- CPU functionality and CLI help use Python 3.12+ standard library only.
- Run `python -m unittest discover -s tests -v` and
  `python scripts/check_shell.py`. GPU imports must remain lazy.
- Never fabricate results, task metadata, calibration, or cluster capabilities.
- Charge all task-specific computation; keep equal-total (A) and equal-remainder
  diagnostics (B) separate. Method names must not affect the model or evaluator.
- Keep attacker truth, public monitoring, and hidden evaluation separate.
- Legacy runs use four persistent worker identities. Opt-in RepoRecourse v0.2
  uses 2–8 logical identities (including 7) on one frozen model/allocated GPU;
  pool-specific grammar and memory qualification is required. Physical campaign
  concurrency remains at most four GPUs, one during qualification.
- Required evaluation uses restricted SQLite artifacts and the labelled SILO
  recoverable-contributor adaptation. Numeric fixtures remain diagnostics.
- No generated code or downloaded repository code on the host. Workers use
  validated data tools; the fixed trusted SQLite CPU executor is allowed.
  CooperBench is optional legacy and requires its tested, approved sandbox.
  Never bypass that gate or call restricted data tools an OS sandbox.
- Keep gold/test material out of worker views. Empty references/tests mean
  scoring unavailable. Preserve exact version bindings and complete obligations.
- Separate native/pair/fixture/SILO scores, access regimes and upstream revisions.
- Do not submit jobs, download large artifacts, push, or launch full experiments
  without explicit authorization. Use the browser-terminal Slurm workflow.
- No PBS, SSH/SCP/tunnels, external hosting, cloud APIs, Docker, Apptainer,
  cgroup delegation, Redis or services are required for the new data path.
- All GPU submissions use the shared per-user registry and scheduler inspection;
  one active campaign, at most four GPUs. No batch self-submission.
- Do not commit models, datasets, outputs, credentials, private PDFs, hidden tests,
  environments, or snapshots. Do not put authentication in Git URLs.

Milestones and limitations are tracked in `docs/STATUS.md`.

## SQL interface / finite decomposition phase

- Preserve JSON-tree defaults. Optional SQLGlot is used only by the explicit
  SQL-text compiler child; core imports and CLI help stay stdlib-only.
- SQL text must lower to the existing approved IR. Never execute worker SQL
  directly, normalize unsupported operations away, or repair task semantics.
- Keep compiler, grammar and native reference approvals separate and hash-bound.
- Native interface arms must be rebuilt from actual resolved historical settings;
  no summary-derived budget/seed/feedback assumptions or historical control reuse.
- Finite graph execution is currently synthetic/mock/JIT-only. Model-generated
  planning campaigns and native policy runs remain blocked pending the separate competence,
  legal-variation and compatible-calibration gates. Do not call scripted plans
  measured research results. See docs/SQL_INTERFACE_AND_DECOMPOSITION_PHASE.md.

## RepoRecourse v0.2

- Read `docs/REPORECOURSE_V0_2.md` for the versioned migration and remaining gates.
- Compare pre-execution planners with the same frozen workers and common public
  JIT; fixed-plan recovery references remain a separate lane. No controller training.
- Freeze planning before target selection; charge its actual ledger logically
  in each end-to-end branch and report physical reuse separately. Track R is
  equal-remaining only. Never rescore or migrate historical v1 experiments.
- Author outlines/reference drivers are labelled; no hidden tests/witnesses in
  planner inputs. Missing qualified tasks, calibration and memory tests stay blocked.
- CPU reference matrix results do not authorize new variable-pool GPU campaigns
  or expand the legacy Jaffle clean/F(w0)/F(w1) exception.

## Open planning and plan scoped execution

- The intended new main condition is `planning_lane=open_generated` with
  `execution_contract=plan_scoped_v1`. It is opt-in; historical manifests retain
  adaptive behavior. Authored outlines are diagnostics, not the generator's menu.
- Read `docs/OPEN_PLANNING_RUNBOOK.md`. Keep planning pre-execution and common
  workers, public monitoring and JIT across planners. No controller training.
- Declared imports are permissions, not required reads or proof of independence.
  Keep correctness, budget, conformance and execution status separate; retain
  protocol-violation rows. Denied attempts are charged, not delivered edges.
- Mediate observations, tools, registries, messages and restored assignment
  histories through `AssignmentScopes`. All task-authorized original sources
  remain available. New units start fresh contexts without resetting identity loss.
- Recovery changes only explicitly admitted assignment scopes through recorded
  common-JIT overlays. Ordinary denied reads do not authorize an overlay.
- New grammars, observation contracts and runtime hashes require renewed controls.
  CPU doubles/reference tests are not generated-plan or GPU competence evidence.
  Existing stock/Jaffle exceptions do not authorize open-generated task execution.
