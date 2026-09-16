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
- Four persistent worker identities share one frozen model on one allocated GPU.
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
