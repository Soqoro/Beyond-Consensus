# Local validation record

Environment: Linux, Python **3.12.7**, standard-library acceptance suite.
No torch/CUDA installation was present or needed. Validation performed during
implementation on 2026-09-15.

## Automated checks

| Exact command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **53 tests: 52 passed, 1 skipped**, 11.935 seconds on the final full pass |
| `python scripts/check_shell.py` | All **9** shell/Slurm files passed LF, final newline, usage, dry-run, strict-mode and `bash -n` checks |
| `python -m compileall -q src tests scripts` | Passed |
| `git diff --check` | Passed |
| `python scripts/bc.py --help` | Passed |
| `python -I -S scripts/bc.py --help` | Passed with site packages disabled |
| `python scripts/bc.py doctor --dry-run` | Passed; no model loaded |
| `python scripts/bc.py stage-model --config configs/gpu-smoke.json --root /tmp/bc-staging-dry-run --dry-run` | Passed; no files or weights downloaded |

The skipped test is the genuine repository-isolation integration test. Its
reported reason is: **“Repository isolation integration unavailable: no approved
sandbox adapter or site isolation attestation exists.”** Mock tests separately
verify that detecting a container executable does not enable repository execution.

The tests include independent tiny-case allocation oracles; shared prerequisites;
no-preparation selection; JIT indexing at the alarm; persistent compromise;
independent replicas; messages and rewritten artifacts; full token/tool/search
accounting; incomplete outputs; grouped splits; A/B separation; interruption during
model execution and diagnostic preparation; uncertain in-flight charges; immutable
source snapshots; scheduler argument quoting; overlapping-submission rejection;
manifest coverage; and sanitized exports. The 320-row grid test constructs a
planned manifest only and executes none of those episodes.

## Executed CLI acceptance sequence

These exact commands used `/tmp` so no raw results enter version control:

```text
python scripts/bc.py demo --output /tmp/bc-acceptance-v1/demo
python scripts/bc.py demo --output /tmp/bc-acceptance-v1/demo
python scripts/bc.py freeze-primary --config configs/fixed-primary.json --output /tmp/bc-acceptance-v1/fixed/primary.json
python scripts/bc.py diagnostic-manifest --fixed-state /tmp/bc-acceptance-v1/fixed/primary.json --output /tmp/bc-acceptance-v1/fixed/manifest.json
python scripts/bc.py run --manifest /tmp/bc-acceptance-v1/fixed/manifest.json --output /tmp/bc-acceptance-v1/fixed/results
python scripts/bc.py export --output /tmp/bc-acceptance-v1/demo --bundle /tmp/bc-acceptance-v1/debug.tar.gz --dry-run
python scripts/bc.py export --output /tmp/bc-acceptance-v1/demo --bundle /tmp/bc-acceptance-v1/debug.tar.gz
python scripts/bc.py calibrate --config configs/mock-demo.json --output /tmp/bc-acceptance-v1/calibration.json
```

Outcomes: **8 mock episodes completed**, rerunning left all episode event-file
hashes unchanged, **4 Protocol B mock comparisons completed**, a sanitized bundle
was written, and **12 operation measurements** were recorded as `mock-measured`.
These are engineering checks, not research results or CooperBench coverage.

## User-reported cluster validation and prompt correction

The following evidence was pasted by the user from the cluster terminal; the
local agent did not access the cluster or submit these jobs.

- Preflight job `1076205` returned `smoke_completed_review_output` and generated
  `{"ready":true}` with Qwen3.5-4B revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
- Hardware: NVIDIA A100-SXM4-40GB, bfloat16, driver `570.133.20`,
  torch `2.10.0+cu126`, Transformers `5.3.0`. The short probe generated 8 tokens
  in 5.7467 CUDA-event seconds and peaked at 9,262,348,800 allocated bytes. These
  numbers do not establish full-context memory use or sustained throughput.
- The subsequent single/clean fixture episode completed with **0/1 task success**.
  Experiment ID:
  `ee34d5abf1cb3c4d7c503ac20fa771af1c43bc5864906c2c754150402dd0ad80`.
  Visible worker messages repeated the prompt's unquoted-key pseudocode, omitted
  the action envelope and never read the assigned source in the shown turns.
- The shared prompt now supplies valid JSON action examples and an explicit
  source-read instruction for each assignment. Fixture instructions no longer
  demonstrate invalid JSON. Calibration compatibility includes worker instructions.
  The parser, retry bounds, budget rules and model settings remain unchanged.
- Follow-up local validation: `python -m unittest discover -s tests -v` ran
  **56 tests: 55 passed, 1 skipped**, in 9.808 seconds. All nine shell checks and
  `python -I -S scripts/bc.py --help` passed. Regression coverage checks every
  prompt example against the actual tool parser, the observed malformed output,
  retained-context source assignments, calibration invalidation, and preflight
  `--model-lock` handling.

The prompt correction has not yet been tested with the real model. Keep the
failed experiment intact and create a new manifest after syncing the corrected
commit; completed failures are not eligible for resume. The four-task GPU pilot
and real CooperBench execution remain unvalidated.

## Not run during initial local validation

- Any real GPU/model load, hardware preflight, or model fit/throughput measurement.
- Any live Slurm submission, cluster pilot, or full E1 experiment.
- Any real repository or generated program outside the typed fixture interpreter.
- Sandbox boundary integration on actual cluster isolation.
- Windows execution; a CPU Windows/Linux CI matrix is provided but was not run here.
- Large model/dataset downloads, installation of the GPU stack, root-repository
  commits or pushes. Snapshot tests create disposable Git commits only in test
  directories under `/tmp`.

Small official documentation/schema files were inspected over HTTPS. They were
not installed or executed. See [MODELS_AND_DATA.md](MODELS_AND_DATA.md) for sources
and the distinction between verified interfaces and untested GPU behavior.
