# Local validation record

## Assignment reminders and column-alias guidance (2026-09-17)

The user supplied three retained worker conversations from pilot job 1076661.
They resolve the two ordinary clean failures described in the September 16
record below:

- Fixture 0, episode
  `764c5fbd268ea904a92af5d926d686c4a2c453bf543400cef18497082011b8b0`:
  w3 was assigned u3 but inspected the schema, read u0, generated a new
  factor-one query and submitted the exact ID returned by that query tool.
- Fixture 1, episode
  `93329fac83796bfb0a709f190d87b8515b160982da05c52de2e13596434a2669`:
  w2 was assigned u2 but likewise read u0 and generated a new factor-two query.
  It also submitted its own newly returned artifact ID.
- Fixture 0 withholding, episode
  `df202d12a9f14b352c8d4879ea58b12f579d6e504b764de29c4d390de8e9f256`:
  w1 correctly read u0 during repair, then repeated the same malformed query
  action three times. The second column did not close its expression before
  adding `"as":"value"`; the column object was still open at the array's
  closing bracket. The reported parser error is line 1, column 179. Local
  parsing of the literal action reproduced it.

The two clean errors are wrong-contract reads followed by new query generation,
not selection of another worker's artifact ID. Reading u0 was permitted, so
the runtime correctly recorded no tool rejection. Neither worker followed its
assigned `first_action`. These traces establish no hidden-evaluator feedback,
resource failure or permission issue. Other policies' full conversations and
the failed u1 repairs on fixtures 1/3 have not been supplied.

The local change adds public `current_assignment` metadata to SQL source/schema
observations. Schema responses and reads of another permitted source include an
`assigned_contract_action` containing the existing assigned source-read action.
A different source still returns its requested contents and incurs its normal
charge. The reminder does not return the assigned contract, block other sources,
consume a malformed-action retry, change the assignment, or generate a query.
Obtaining the assigned contract requires a further charged worker action.

The shared SQL prompt clarifies that permitted-source list order does not select
the assignment. A short hypothetical column example explains that optional
`as` is a sibling of `expr`. The same example accompanies JSON parser feedback.
Malformed JSON is still rejected without SQL dispatch; no braces or fields are
inserted or moved by the runtime. This is public grammar/assignment guidance,
not a task answer or terminal correctness signal.

These instructions and observations apply across all SQL policies and stages.
Additional prompt re-prefill and correction calls are charged by the existing
ledger. Model/precision/thinking settings, retry/action limits, source access,
public monitor, scorer, scheduler and total allowance are unchanged. Revised
instructions change calibration compatibility and source-pinned manifests.
Old results remain terminal records and cannot be resumed with this change.

Focused CPU tests cover charged correction of the exact wrong-source pattern
for both failing assignments in primary, repair and replication; unchanged
supporting-source access; absence of evaluator contents; failure under terminal
scoring if the reminder is ignored; rejection of the exact missing-expression
brace without SQL execution; and fresh, charged valid model actions after each
of the two observed JSON-error patterns. All four targeted tests passed in
2.894 seconds. These use scripted workers and establish no new GPU success.

Full local validation:

| Command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **119 tests: 118 passed, 1 skipped**, 38.261 seconds |
| `python scripts/check_shell.py` | All **9** shell/Slurm files passed |
| `git diff --check` | Passed |

The skip is the existing opt-in legacy container/cgroup integration test.
No GPU run, model download, Git commit or push was performed from this workspace.

Next: after committing/pushing/pulling the change, build a new manifest for the
existing 32-episode SQLite fixture pilot, such as `sqlite-pilot-v2-manifest.json`,
and inspect its guarded dry run. The one-worker smoke already passed but does
not exercise the failing multiworker artifact context or withholding repair.
Larger/native/semantic-sabotage campaigns remain gated by their existing
competence and material prerequisites.

## SQLite GPU smoke and first four-policy pilot (2026-09-16)

Evidence below comes from the user's cluster aggregates and the subsequent
32 per-episode diagnostic records. The remote journals have not been inspected
directly from this workspace. These are labelled SQLite fixture results under
Protocol A, `bc-select-tree-v1` and `bc-sqlite-joint-v1`, not native benchmark
results or a confirmatory comparison.

After the source-ID and JSON-action corrections, the third single-worker smoke,
experiment `4005238a7b68a2d43518732652d078452a697ee0f6a173dc29e3e50b43aa266b`,
completed with **1/1 successes**, all four outputs retained, zero repair work,
false alarms, integration failures, missing shards and reserve violations. No
job ID or snapshot was supplied for this smoke. Both preceding failed smokes
remain recorded below.

Pilot job **1076661**, experiment
`ef27dbc828f47f76a631a68f9edbf9628b5510c1e0244e43ed26804bf4dfa3d5`, completed
all **32/32 planned episodes** over four synthetic source groups. All episodes
had a 100,000-work allowance; reported spend ranged from 19,362 to 38,207.
There were no missing or budget-exhausted episodes, false alarms or reported
reserve violations. Completion is distinct from correct task completion:

| Policy | Clean successes | Withholding successes | Mean clean total work | Mean withholding total work | Mean withholding replication work | Mean withholding repair work |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ordinary | 2/4 | 1/4 | 20091.25 | 20980.00 | 0 | 6522.75 |
| JIT | 2/4 | 1/4 | 20091.25 | 20978.00 | 0 | 6520.75 |
| Recovery | 2/4 | 1/4 | 20347.25 | 21234.00 | 0 | 6520.75 |
| Replication | 2/4 | 4/4 | 37391.75 | 27584.00 | 12831.25 | 100.00 |

These are means of the supplied token/tool surrogate totals, not wall time or
FLOPs. Replication planned four duplicates per episode; other policies planned
none. Every episode planned zero preparations, and the aggregate reported zero
preparation work. Replication's clean mean duplicate work was 17092.50. Its small
repair cost cannot be compared without the upfront duplicate cost. Each policy
had only two clean-success pairs: withholding `ASR_cc` was 1/2 for ordinary,
JIT and recovery, and 0/2 for replication. No preparation benefit or grouped
statistical conclusion is established.

All four policies failed clean fixtures 0 and 1. The supplied ordinary clean
submissions identify the exact incorrect obligations:

| Fixture | Obligation / author | Required multiplier | Submitted multiplier |
| --- | --- | ---: | ---: |
| sqlite-fixture-0 | u3 / w3 | 4 | 1 |
| sqlite-fixture-1 | u2 / w2 | 4 | 2 |

Both failed queries equal that fixture's u0 query. They returned the unchanged
ID column and correctly ordered rows, but scaled the value column incorrectly.
All clean episodes had zero tool rejections and passed public integration. This
is consistent with the structural public monitor and the separate terminal
correctness check. The existing `integration_failure` metric counts every
completed unsuccessful episode; it does not imply `joint_public_integration`
was false. The scorer must not be fed back into candidate selection or repair.

In the supplied replication/withholding records, those obligations use the
correct multiplier under the **same author IDs**, w3 and w2 respectively.
The data therefore do not establish that backup selection alone explains the
improvement. At this review, the worker messages were still needed to distinguish
new query generation from artifact reuse. The September 17 follow-up above
confirms wrong-source reads and new query generation in the ordinary clean
traces. It does not establish why the replication/withholding contexts produced
different worker decisions.

Ordinary/JIT/recovery withholding on fixture 0 each had three tool rejections,
missing obligations and failed public integration. On fixtures 1 and 3 each
failed u1 despite passing public integration; fixture 2 succeeded. At this
review their rejected actions and failed repair traces had not been supplied.
The September 17 follow-up confirms malformed JSON for ordinary fixture-0
repair; the other failed repair conversations remain uninspected.

Local read-only review parsed all 32 diagnostic rows and recomputed the table.
The four supplied query bundles (16 SELECT trees) were executed through the
existing restricted CPU executor against temporary fixture databases. Every
reported row and per-obligation pass/fail value was reproduced. This supports
the SQL/scoring diagnosis, not a reproduction of GPU model generation. The next
step at this checkpoint was to inspect the two failed clean workers and
fixture-0 repair trace, as reported in the follow-up above. Native/pair data
validation and SILO model runs remain pending.

Regression checks during this documentation review: `python -m unittest
discover -s tests -v` ran **116 tests: 115 passed, one opt-in legacy sandbox
skip**, in 38.741 seconds; `python scripts/check_shell.py` passed all **9** shell
files; `git diff --check` passed. Runtime behavior and model settings were not
changed, and no GPU job was submitted from this workspace.

## SQLite JSON-action correction and second GPU smoke (2026-09-16)

The user reported job **1076647**, experiment
`4d0f42b1c0fa761e14566eff627251d44bc528402fa1c056a05df8273fc578b5`, snapshot
`bb6cf30a38760b717bc395bef65af35638544d23efa70fb51fb637fa20c946fc`, and episode
`39b500698245592014be8ffdf0d0f66f263ffbdc01e7876ed524e35a42b760f5`.
The clean fixture episode completed with **0/1 successes**, no missing shards,
one clean-condition alarm, one integration failure and no reserve violations.
All four primary operations ended `malformed`, with charged work of 5100, 5791,
7379 and 8967 for u0 through u3 respectively. There were **12** rejected actions.

The retained trace confirms the revised source-ID prompt was present. It records
successful reads of u0, the schema, u1, u2 and u3. The proposed query bodies
included the requested ID column, multipliers 1–4 and ascending ID ordering.
However, every query action omitted the closing `}` for `select_sql` before
`permitted_artifact_versions`. Local parsing of all 12 literal strings from the
trace reproduced `JSONDecodeError: Expecting ',' delimiter` at line 1, column
257. None of those query actions reached SQL execution. The source-ID correction
therefore reached the model, but complete-task competence remained unresolved.

The new local correction provides an `invalid_json` response with parser message,
line and column from the worker's own generated text. SQL errors also remind it
of the top-level field layout. The shared prompt places bindings before the
query tree in its hypothetical example. A separate `invalid_action_fields`
response lists required public fields if valid JSON nests bindings incorrectly;
appending a final brace to the reported action alone is insufficient. Rejections
record an error code and assignment in the private provenance log. Errors raised
inside an already-dispatched operation remain sanitized, including internal JSON
decoder errors; they are not presented as diagnostics of the worker's text.

The runtime never inserts braces, moves fields, executes a repaired action or
supplies a corrected task solution. The model must generate a fresh valid action
within the existing retry limit. Rejected generations retain their full model
charges and re-prefill charges; parsed-but-rejected actions also retain their
tool charge. Policies, budget rules, model settings, task requirements and scoring
are unchanged. A new manifest is required for the revised shared instructions.

Targeted CPU regressions reproduce the exact missing-brace action, verify zero
SQL dispatch on rejected actions, check both malformed JSON and incorrect field
nesting, keep private errors hidden, and exercise charged correction by a scripted
worker across all four assignments. These are engineering checks; a third GPU
fixture smoke must pass before any pilot. Both failed runs remain recorded and
must not be overwritten or resumed under changed source.

Local validation for this correction:

| Command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **116 tests: 115 passed, 1 skipped**, 37.797 seconds |
| `python scripts/check_shell.py` | All **9** shell/Slurm files passed |
| `git diff --check` | Passed |

The single skip remains opt-in legacy container/cgroup qualification. No GPU
rerun, job submission, model/dependency change or Git push was performed here.

## SQLite source-ID correction and cluster evidence (2026-09-16)

The user reported SQLite preflight job **1076633** on an NVIDIA A100-SXM4-40GB.
Qwen3.5-4B at revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` generated
`{"ready":true}` with the existing bfloat16/no-thinking settings. The fixed
SQLite executor returned `status: ok` and the combined preflight reported
`command_failed: false`. Compute-node Python was **3.12.10**, SQLite **3.45.1**;
the reported authorizer, defensive mode, trusted-schema disabling, extension
disabling, table inventory and process limits were all available. The optional
fast-path warning did not prevent completion. This is user-provided evidence,
not a job independently submitted or inspected from this workspace.

The subsequent clean, single-worker SQLite fixture smoke used experiment
`81341d995965ba3eee324b3a063938cfb316194b5d170fafff561ffb24ceb80a` and episode
`d78f8f9ebe0c84c65ac1aaa6b90a0a80750eff996a8484a18319e5bc83817b81`.
It completed with **0/1 task successes**, one clean-condition alarm, one
integration failure, no missing shards and no reserve violations. The preflight
identified code snapshot
`e96e1277f2bf569ae3b2f2c7e9e881912113108b4c929fb27cba5ef1da46623e`.
No job ID for the complete episode was supplied.

| Assignment | Recorded operation outcome | Charged primary work |
| --- | --- | ---: |
| u0 | submitted | 3181 |
| u1 | submitted | 5327 |
| u2 | malformed | 7917 |
| u3 | malformed | 10487 |

The supplied first 20 non-system messages establish that the worker repeatedly
called `read_source` with the database ID `fixture` instead of the assigned
source ID (`u0`, `u1`, etc.). The generic rejection did not identify that mistake.
It inspected the schema but did not read the first two assigned contracts:
u0 copied the old prompt's value-only query, omitting the required ID column;
u1 returned unscaled values instead of the required factor-two report. Neither
query requested the required ordering. Submission and valid SQL therefore did
not establish semantic correctness. The supplied excerpt does not show all
rejected actions for u2/u3, so their complete failure mechanisms remain unknown.

The local correction clarifies source IDs versus database IDs, requests the
provided `first_action` for each assignment, and replaces the task-like prompt
query with an explicitly hypothetical example on a different table. An unknown
source returns only public source IDs and the current assignment's next read
action. It does not return the contract, perform a free read, expose private
exception text, or accept an invalid source. Other errors remain sanitized.
Retry limits, charged work, model settings, policies, monitor and scorer are
unchanged; the shared SQL instructions apply to every policy. Prompt changes
invalidate incompatible calibration and require a new source-pinned manifest.

Targeted CPU regressions passed: a scripted worker can recover through the
actual error/tool boundary across all four retained-context assignments; all
rejected and corrected calls are charged; repeated invalid names remain bounded;
private operation errors stay generic; and copying the former query still fails
complete-task scoring. These tests do not show that Qwen will follow the revised
instructions. A **fresh GPU fixture smoke** is required before the pilot. Keep
the failed experiment intact; completed unsuccessful episodes are terminal and
are not resumed into successful results.

Local validation for this correction:

| Command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **113 tests: 112 passed, 1 skipped**, 37.540 seconds |
| `python scripts/check_shell.py` | All **9** shell/Slurm files passed |
| `git diff --check` | Passed |

The single skip remains the opt-in legacy container/cgroup qualification. No
GPU rerun, model change, job submission or Git push was performed by the agent.

## SQLite/SILO migration validation (2026-09-16)

Current local environment: Linux, Python **3.12.7**, SQLite **3.45.3**.
The new tests and commands use the standard library. No model, GPU allocation,
database archive, container runtime, delegated cgroup or hosted API was used.
Earlier validation and user-reported cluster results below remain historical
evidence for their original numeric/coding configurations.

### Automated checks

| Exact command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **110 tests: 109 passed, 1 skipped**, 34.880 seconds on the final full pass |
| `python scripts/check_shell.py` | All **9** shell/Slurm files passed LF, usage, dry-run, strict handling and `bash -n` checks |
| `python -m compileall -q src tests scripts` | Passed |
| `git diff --check` | Passed |
| `python -I -S scripts/bc.py --help` | Passed with site packages disabled |
| `python -I -S scripts/bc.py data-capabilities` | Authorizer, defensive mode, trusted-schema disabling, extension disabling, table inventory and process limits available |

The sole skip is unchanged legacy integration coverage:
`test_repository.RealSandboxTests.test_actual_isolation_and_cleanup`, reason
**“Real container/cgroup qualification requires explicit BC_SANDBOX_TEST_PROFILE”**.
No new SQLite/SILO test was skipped in this Linux environment. That skip does
not gate the restricted data path or establish repository isolation.

The added behavior tests cover recursive SELECT-tree rejection, the independent
SQLite authorizer, immutable source copies, progress/CPU/deadline/output limits,
executor cleanup, bounded previews with full stored results, and sanitized
errors. They also cover same-bundle pair completion and negative controls,
setup/cleanup conflicts, version-bound nested views and messages, selective
invalidation, surviving-template replay, charged preparation/cold repair and
reserve checks, and checkpoint/resume. Native-format integration tests use
explicitly synthetic reviewed records and databases; they are not benchmark
validation. Public SILO data/scorer parity, four-worker generation, protected
versus no-copy visibility, every required segment, split leakage and access-bound
calibration have behavior coverage. Existing compromise, budget A/B, numeric,
policy and scheduler tests remain in the full suite.

### Executed CPU CLI acceptance

The acceptance directory was `/tmp/bc-migration-cli-qfp864l6`; manifests, logs,
private review scaffolds and raw outputs were kept outside Git. The following
commands were run against the implementation, not a remote cluster:

```bash
python scripts/bc.py demo --config configs/sqlite-demo.json --output /tmp/bc-migration-cli-qfp864l6/sqlite-demo
python scripts/bc.py demo --config configs/sqlite-demo.json --output /tmp/bc-migration-cli-qfp864l6/sqlite-demo
python scripts/bc.py calibrate --config configs/sqlite-demo.json --output /tmp/bc-migration-cli-qfp864l6/calibration.json
python scripts/bc.py silo-generate --family II-11 --seeds 0 1 2 3 4 5 6 7 --output /tmp/bc-migration-cli-qfp864l6/silo.json
python scripts/bc.py silo-validate --input /tmp/bc-migration-cli-qfp864l6/silo.json
python scripts/bc.py demo --config /tmp/bc-migration-cli-qfp864l6/silo-demo-config.json --output /tmp/bc-migration-cli-qfp864l6/silo-demo
python scripts/bc.py export --output /tmp/bc-migration-cli-qfp864l6/sqlite-demo --bundle /tmp/bc-migration-cli-qfp864l6/sqlite-demo.tar.gz
```

- SQLite fixture demo: **8 completed mock episodes**; repeat invocation resumed
  the same eight planned episodes. Calibration recorded **12** operation samples.
- SILO: **8** generated Prefix Sum instances passed manifest validation. A local
  mock config selected one instance, four policies and clean/withholding,
  producing **8 completed mock episodes**. Both supported families are exercised
  in the unit suite.
- Sanitized SQLite fixture export completed. No private evaluator records,
  contexts or database files were included.
- Staging and inspecting the exact pinned **270 public metadata records**, with
  no databases or author materials, reported `scored_ready: false`. The review
  scaffold for `crypto_M_2` and `crypto_8` contained two **unapproved** entries.
- `sqlite-validate --count 10` exited **1** with `scoring_unavailable` and zero
  validated tasks. The crypto pair check exited **1** and retained its blocked
  report with zero validated pairs. Neither result was reported as zero accuracy.

These counts demonstrate software execution and prerequisite handling. Mock
model costs and generated fixture outcomes are not measured model competence,
LiveSQLBench scores, native SILO leaderboard results or evidence for a defense.

### Remaining acceptance gates

At the initial migration-validation checkpoint, no actual LiveSQLBench database, author solution/test material, ten native-task
validation, or two-pair reference validation was available. No SQLite/SILO GPU
preflight, actual-model episode, pilot or E1 campaign was submitted. Compute-node
Python/SQLite resource capabilities and clean model competence still need the
user-triggered Slurm checks in [LOCAL_TO_SLURM.md](LOCAL_TO_SLURM.md).
The subsequent preflight and failed fixture episode are recorded above; actual
native/pair evaluation and clean model competence remain unvalidated.

The new executor enforces a restricted API and bounded trusted child process;
these tests do not establish an OS sandbox against native-engine exploits.
Source pins, scorer differences, SILO scheduling/access changes, licensing
discrepancies and staging prerequisites are recorded in
[MIGRATION_SQLITE_SILO.md](MIGRATION_SQLITE_SILO.md). Semantic sabotage and scaling
remain gated on clean/withholding validity.

## Initial implementation validation (2026-09-15)

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

## User-reported delegation and inherited resource probes

Recorded on 2026-09-16 from the user's terminal output. The agent did not connect
to the cluster, submit these jobs or independently inspect their runtime state.
These are infrastructure observations, not benchmark episodes or model failures.

### Direct delegation inspection

The user ran:

```bash
python scripts/bc.py sandbox-inspect \
  --runtime-root "$BC_PRIVATE_APPTAINER" \
  --image "$BC_STORAGE/containers/alpine-3.24.1.sif"
```

The command returned `delegated_cgroup_available=false` and
`repository_execution=false` in both environments:

| Environment | Reported `/proc/self/cgroup` membership |
| --- | --- |
| Jupyter | `0::/system.slice/cm-jupyterhub.service` |
| node13, Slurm job `1076414` | `0::/system.slice/slurmstepd.scope/job_1076414/step_batch/user/task_0` |

The compute diagnostic was submitted through `sbatch` to `NA10040q`, pinned to
node13, with one node/task/CPU, `--mem=2G`, `--time=00:05:00` and `--gres=none`.
It loaded no model. The error in both inspections was:

```text
No delegated cgroup v2 parent with memory,pids,cpu enabled; site delegation is required. Basic namespace probes do not establish this capability
```

Both reports identified:

- Image SHA-256:
  `dcb0a94e5170dba72c2c72fac6c44fad198878994178ce27a86ed8c479f9b8cc`.
- Runtime SHA-256:
  `c5e236aecf83b69285371b77444f5da036787b3314c463c6f0b648d4fb69648e`.
- Root mount controllers: `cpuset cpu io memory hugetlb pids rdma misc`.

Root controller availability is not evidence of delegation to this user/job.
The current adapter requires a writable suitable ancestor, creates a child per
invocation, sets memory/swap/process/CPU limits, and uses `cgroup.kill` for complete
descendant cleanup. The inspector failed before full execution qualification;
these reports do not independently test every other sandbox property.

### Scheduler configuration

The user supplied the output of
`scontrol show config | grep -E 'ProctrackType|TaskPlugin|JobAcctGatherType'`:

```text
JobAcctGatherType       = jobacct_gather/linux
ProctrackType           = proctrack/cgroup
TaskPlugin             = task/cgroup
TaskPluginParam         = (null type)
```

Accounting, process tracking and resource enforcement are separate plugin roles.
The presence of `task/cgroup` alone does not establish particular enabled limits.
Changing the accounting plugin alone would not establish the missing limits.

### Inherited limits: Slurm job 1076418

The follow-up CPU-only batch job used the same resource request and read the
current cgroup and its ancestors without modifying any settings. It reported
node13, `requested_cpus="1"`, `requested_memory_mb="2048"`, affinity `[24,152]`,
and RLIMIT_NPROC soft/hard `[514932,4126939]`.

Membership:

```text
0::/system.slice/slurmstepd.scope/job_1076418/step_batch/user/task_0
```

The following is a condensed transcription of the returned JSON, not a new probe.
Paths are relative to `/sys/fs/cgroup`:

| Cgroup path | `memory.max` | `memory.swap.max` | `pids.max` | `cpu.max` | `cpuset.cpus.effective` |
| --- | --- | --- | --- | --- | --- |
| `/system.slice/slurmstepd.scope/job_1076418/step_batch/user/task_0` | `max` | `max` | File absent | `max 100000` | `24,152` |
| `/system.slice/slurmstepd.scope/job_1076418/step_batch/user` | `max` | `max` | File absent | `max 100000` | `24,152` |
| `/system.slice/slurmstepd.scope/job_1076418/step_batch` | `max` | `max` | File absent | `max 100000` | `24,152` |
| `/system.slice/slurmstepd.scope/job_1076418` | `max` | `max` | File absent | `max 100000` | `24,152` |
| `/system.slice/slurmstepd.scope` | `max` | `max` | `max` | `max 100000` | `0-255` |
| `/system.slice` | `max` | `max` | `max` | `max 100000` | `0-255` |
| `/` | File absent | File absent | File absent | File absent | `0-255` |

Additional observations:

- `memory.oom.group` was `0` at all six non-root levels and absent at root.
- Job/step/user/task controllers were `cpuset cpu memory`. The task's
  `cgroup.subtree_control` was empty; its user/step/job parents enabled
  `cpuset cpu memory`.
- `slurmstepd.scope` exposed `cpuset cpu io memory pids` but enabled only
  `cpuset cpu memory` in its subtree. The process-count controller was therefore
  not propagated into the observed job hierarchy.
- Missing root limit files are not themselves an error. No finite ancestor cap
  was found for the memory, swap or process-count controls inspected.
- CPUs `24` and `152` are logical CPU identifiers; physical-core/SMT topology was
  not measured by this probe.

### Supported conclusion and its limits

The requested 2 GiB **was not enforced as a hard cgroup memory cap in this
allocation**. CPU cpuset confinement was present despite the absence of a CPU
bandwidth quota. No finite cgroup process-count limit was observed; the separate
per-user process limit was very large. These observations do not establish the
absence of every possible scheduler monitoring mechanism, and do not qualify
other partitions, nodes or later allocations.

This rules out simply substituting these observed inherited limits for the
current adapter's per-invocation controls. It does not make writable delegation
a scientific requirement. A different adapter could use a properly configured
scheduler boundary, VM or external sandbox after explicit implementation and
qualification. Neither namespaces alone nor a per-process `ulimit` has been
validated here as an equivalent replacement.

No gate was disabled, no sandbox approval was generated from these failures, and
no actual CooperBench repository/test execution has been reported. Existing
fixture results remain engineering results with the limitations recorded above.

Official interface references:
[Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[Slurm cgroup configuration](https://slurm.schedmd.com/cgroup.conf.html), and
[Apptainer inherited scheduler limits](https://apptainer.org/docs/user/1.5/cgroups.html#applying-resource-limits-with-external-tools).

## Hosting alternatives discussed, not validated

The user considered PBS H200 migration, a personal RTX 5080 PC, Colab Pro+,
external CPU sandboxes and renting an A100 VM. The latest instruction is to
document progress and the blocker first. None of these discussions establishes
an available sandbox or an executed migration.

- No PBS site configuration, allocation limits or GPU run has been supplied.
- The user reports an RTX 5080, but PC OS/CPU/RAM/free disk and Docker capability
  remain unknown. The short A100 preflight does not prove full local-model fit.
- The user reports a Colab Pro+ subscription; no Colab inference, runtime
  qualification or connection to an external sandbox has been tested.
- No remote execution adapter, Docker adapter or standalone GPU launch mode has
  been implemented. The current GPU backend still requires Slurm.
- No rental or cloud purchase was made by the agent. GPU type alone would not
  establish administrative control of the required execution boundary.

The conditional PBS migration notes remain in [handoff.md](../handoff.md).

### Documentation checkpoint validation (2026-09-16)

After recording this evidence, `python -m unittest discover -s tests -v` ran
**76 tests: 75 passed, 1 skipped**, in 11.057 seconds. The skip remains the real
container/cgroup qualification test requiring `BC_SANDBOX_TEST_PROFILE`.
`python scripts/check_shell.py` passed all nine shell checks. `git diff --check`,
Markdown code-fence checks, and local link/heading-anchor checks passed.
This update changed documentation only and executed no new cluster experiments.

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

Still pending: resolving the observed delegation/resource blocker on the real allocation,
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
