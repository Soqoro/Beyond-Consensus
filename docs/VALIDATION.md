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

## Subsequent user-reported GPU fixture pilots

The corrected single-task smoke (job `1076319`, experiment
`d07eaf6b64fe4ec6393fb332f077fcb1bd2c7ee63f743c6d44ba8b08f8609e56`)
succeeded with all four outputs retained and no alarms or integration failures.
The original failed experiment remains a separate record.

The user then supplied complete aggregate reports for two four-task pilots:

| Pilot | Experiment ID | Completed and successful |
| --- | --- | --- |
| Clean / withholding | `e05c084a88b15e9f6675e9dfa18da40dee13ac1624cf324d5f807ed37830aeff` | 32/32 |
| Clean / artifact sabotage | `ddbf0217caa8fd82a3a4eea8dc7d6d5ddffe1194d4a6795f2b7227d56f492ab8` | 32/32 |

Each pilot used four policies, two conditions, four tasks, one seed and two
base-feature pools. Both reports have complete coverage, zero integration
failures, zero clean-condition false alarms and zero reserve violations. Every
policy's attack success rate conditional on clean success was 0/4 in each pilot.
The 64 episodes include repeated clean controls; they are not 64 independent
tasks or confirmatory research evidence.

User-reported mean charged work in the withholding pilot:

| Policy | Clean | Withholding | Planned replicas per episode |
| --- | ---: | ---: | ---: |
| Ordinary | 5280.0 | 5372.0 | 0 |
| JIT | 5280.0 | 5372.0 | 0 |
| Recovery | 5560.0 | 5652.0 | 0 |
| Replication | 10595.0 | 8023.8 | 4 |

All planned preparation counts in that pilot were zero. Both pilot aggregates
also report zero advance-preparation work. Ordinary, JIT and recovery each
incurred 5426 total repair work units across the four attacked episodes in each
pilot, retaining 12 outputs in total. Replication retained 16 outputs and incurred
0 total repair work under withholding and 640 under sabotage. These are charged
work units, not seconds; the sabotage aggregate alone does not separate audit
costs from repair model calls or provide total execution costs.

The observed fixtures show no recovery advantage. Real repository isolation,
the coding worker/evaluator adapter and CooperBench execution remain unvalidated.

## User-reported basic container validation

The user reported success for the basic Jupyter containment probe and supplied
stdout and shell-trace stderr from a CPU-only Slurm probe on `node13`. The agent
did not submit or observe this job directly; its job ID was not supplied.

- Compute host: `node13`, kernel `6.8.0-51-generic`.
- Private runtime: Apptainer `1.5.3-3.el8`, installed under
  `/dataset/suaq0001/beyond-consensus/tools/apptainer-1.5.3.SgKY67`.
- Image: `alpine-3.24.1.sif`, reporting Alpine `3.24.1`, SHA-256
  `dcb0a94e5170dba72c2c72fac6c44fad198878994178ce27a86ed8c479f9b8cc`.
- Flags: `--userns --containall --cleanenv --no-eval --no-home
  --no-mount hostfs,bind-paths,cwd --net --network none`, with an explicit writable
  `/work` bind and `/work` working directory.
- The inside marker was readable and a container write was visible to the host.
  The host checkout's `README.md` and a marker outside the work bind were absent
  at their tested absolute paths.
- The container network namespace differed from the host's. The route query
  returned empty output; the interface listing showed only loopback.
- The script reached `COMPUTE NODE BASIC PROBE PASSED`. The supplied stderr
  contains the expected shell trace and no reported failure.

These checks do not validate alternate paths to host data, credentials,
privileged sockets, scheduler access, process escape/cleanup, resource limits,
worker/evaluator separation, or removal of hidden tests/reference patches and
Git history. They do not qualify other compute nodes or a future benchmark image.
This basic probe did not approve a repository adapter. The opt-in coding E0
implementation described below still requires its own full qualification.

## Opt-in coding E0 implementation (local checks only)

The Apptainer/cgroup adapter, bounded repository transfer, clean coding worker,
joint evaluator, qualification/review CLI and environment control commands now
have standard-library regression tests. No new cluster job or container was
executed by the agent and no coding task success is claimed.

- Full suite: **76 tests, 75 passed, 1 skipped**. The real Apptainer/cgroup test
  requires explicit `BC_SANDBOX_TEST_PROFILE` on the intended cluster node.
  It replaces the old always-skipped placeholder integration test.
- All **9** shell checks passed. Compilation, `git diff --check` and CLI help
  with `python -I -S` passed.
- Tests use labelled fabricated source files, mocked model generations and
  injected sandbox responses. They check strict path/data bounds, history and
  renamed reference-patch rejection, immutable runtime/image fingerprints,
  incomplete/stale approval rejection and failure without cgroup delegation.
- Coding integration tests require both suites, keep private evaluator files
  outside worker mounts, charge container/evaluation work, preserve terminal
  results and ensure evaluator retries never return to model generation.
- Baseline/reference controls reject a vacuous always-passing test command.
  Earlier serialized fixture manifests remain readable after optional coding
  configuration fields were added.

Still pending: delegated cgroup capability on the real compute allocation,
qualification of the actual coding image, explicit site/image/source review,
real upstream task environment controls, and the first clean GPU coding episode.
Four-policy coding execution/calibration and Protocol B remain unsupported.
See [CODING_SANDBOX.md](CODING_SANDBOX.md) for the exact sequence and limitations.

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
