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
- No generated code or downloaded repository code on the host. The typed fixture
  interpreter is the only currently supported execution mode; real repositories
  require a tested, approved sandbox adapter and must fail closed without one.
- Do not submit jobs, download large artifacts, push, or launch full experiments
  without explicit authorization. Use the browser-terminal Slurm workflow.
- All GPU submissions use the shared per-user registry and scheduler inspection;
  one active campaign, at most four GPUs. No batch self-submission.
- Do not commit models, datasets, outputs, credentials, private PDFs, hidden tests,
  environments, or snapshots. Do not put authentication in Git URLs.

Milestones and limitations are tracked in `docs/STATUS.md`.
