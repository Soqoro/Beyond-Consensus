# Local validation record

## Opt-in 27B implementation checks (2026-09-20)

See [the ordered competence runbook](QWEN27B_COMPETENCE.md). Local checks:

- `python -m unittest discover -s tests -v`: **194 run, 193 passed, one existing
  opt-in legacy skip**, 68.327 seconds on the stable source tree.
- `python scripts/check_shell.py`: nine shell files passed.
- `python scripts/check_docs_shell.py`: 46 shell blocks/four embedded Bash scripts
  passed syntax checks; no documented command was executed.
- `python -m compileall -q src tests scripts`, `git diff --check`, and
  `python -I -S scripts/bc.py --help`: passed.
- Model staging dry-run downloaded nothing; a /tmp manifest planned exactly four
  episodes; comparison without historical raw evidence reported unmatched.

An intermediate full run failed the native-reference source-change guard while
implementation files were being edited. That test passed individually, followed
by the complete stable-source passing run above. No scoring rule was changed to
make it pass. Hardware/loader tests use explicit CPU doubles; they establish
rejection paths, not actual fit or competence. New tests also cover immutable
profile/lock requirements, quota failures without downloads, model-specific
qualification keys, the actual loader refusing 40 GB before weight loading,
synthetic controls, strict CASE scoring, interrupted decoder reservations,
long-context allowance and stale native executor bindings.

Official small metadata resolved post-trained Qwen3.5-27B to
`fc05daec18b0a78c049392ed2e771dde82bdf654`. The reviewed Transformers 5.3.0 source
contains the required loader; installed cluster loading remains unexecuted.
No dependency environment was changed. No weights/database downloads, GPU jobs,
commits or pushes were performed. Fresh CPU qualification, actual 80-GB-class
preflight, all four probe outcomes, renewed solar controls and native 27B
competence remain pending. No 27B result or general research-readiness claim
follows from these software checks.


## Constrained cluster result and audit report (2026-09-20)

The user supplied CPU qualification, aggregate/cost reports and per-probe traces.
Qualification passed six positive and four negative controls on CPU, with no
model or SQL execution. XGrammar 0.1.32, vocabulary 248320 and stops 248044/248046
were reported. Static setup took 281.770546626 CPU seconds; full qualification
307.99545583099996 CPU seconds. This supersedes earlier pending qualification.

Experiment `d701d4b32a8d44d6d4b51a7b0df94a7ab1b7b53a98d996a69248f2f2c1b3ba80`
completed four episodes with **1 success**, **3 public integration passes**, one
missing required artifact and **28649** charged work. All cases were scored;
no missing/retryable shards. Latest actual job/node/GPU identifiers were not
supplied. The remote files were not independently accessed locally.

| Probe | Work | Calls | Rejections | Result |
| --- | ---: | ---: | ---: | --- |
| Aggregate | 5704 | 3 | 0 | Grouping executed; addition used instead of sum/count, incorrect values submitted |
| Join | 12280 | 3 | 3 | Eight duplicate joins/aliases in first action; two retries capped at 2048 before reasoning close |
| View | 5130 | 3 | 0 | Correct artifact and final result |
| CASE | 5535 | 3 | 0 | Correct classifications/order, missing required `sign_label` alias |

Ten generations stopped at EOS; two join retries hit the length cap with unknown
reasoning counts, incomplete constraint status and zero mask calls. No partial
retry action executed. CASE's strict failure is consistent with the documented
column-and-row scorer. Do not recode it as a complete-task pass. Legacy
`integration_failures=3` does not mean three public integration failures.

Manifest hash `99eeae34dfecf7a9bb8b9bdd66d2239303a034b82cd462eae1f131c0b79e2e05`;
cost report `f6ca1d2e0b666e621c97d9d9f0c5bf16bbe6d0d01ccdfc71c991e75bf797c396`;
source `497f7ba08cf17a693480e34619dd4a95d60cfaf3:69759f99984dd2b39b754666fe2dca5d615ac85462d93a65635425deb09cf7e0`.
See [the progress report](PROGRESS_REPORT_2026-09-20.md) for remaining bindings,
historical results, cost/independence limitations and audit questions. Work is
paused at the user's request; no next model or campaign is selected. This update
changes documentation only and makes no new model/runtime/scoring change.

Report checkpoint verification: full unittest discovery ran **183 tests in
65.531 seconds (182 passed, one existing opt-in sandbox skip)**. All nine shell
checks passed. Report links, the latest per-probe work sum and `git diff --check`
passed. No remote model run or independent remote ledger replay was performed.

## Reasoning results and constrained action preparation (2026-09-20)

### User-reported cluster evidence

Experiment `3996c58d44658d42f2d94fd08517884c606e068b798aac077118365d995dda63`
completed four probes: **1 passed (view), 3 failed**, total **30715** work,
mean 7678.75. All 15 generations stopped at EOS with measured reasoning tokens.
No failure was an output-cap hit. One synthetic source group, nonconfirmatory.
Manifest hash `57b915691055499314d8fde8a09fcc47f9e1c21ade3abca0da5cf9738f7ebbc9`;
report ID `f4b4d1261a61df4c0f7781605585871ae7aa165f897cbcb5632725f073fe9ec3`;
source `f16fe76dcaa586807686442572f53a78fbacffb2:7dfab42cbb17e3ddfc4f1fdbca1b9ee54d683c6172cc53192135b0079068398c`.

| Probe | Episode work | Operation work | Calls | Rejections | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| CASE | 8506 | 8465 | 4 | 3 | Invalid JSON and CASE structure, no SQL execution |
| Aggregate | 8175 | 8134 | 4 | 3 | Repeated unsupported function/group_by structure, no SQL execution |
| View | 6910 | Not supplied | 4 | 1 | Passed terminal scoring |
| Join | 7124 | 7083 | 3 | 3 | Repeated invalid JSON at column 435, no SQL execution |

The join also skipped the requested initial contract read. The task/schema was
already supplied in its system message; no successful execution is inferred from
its intended join. Aggregate failure feedback was generic. The earlier 0/4 to
1/4 comparison changed thinking, output allowance and public view validation;
it does not isolate thinking. Charged work increased by approximately 29.1%.

### Prepared implementation, not a GPU result

The new opt-in config retains reasoning and all existing bounds; it adds a public
JSON-schema constraint using pinned XGrammar 0.1.32. Generic recursive expression,
call, CASE, join, grouping, query/view and tool shapes contain no data-dependent
choices. A fresh matcher starts only after the generated reasoning close. EOS
before that boundary and truncated/incomplete actions cannot execute. The parser
and restricted executor still check permissions, bindings and semantics.

Schemas and dependency versions are bound to manifests/calibration and result
conditions. Default runs remain unconstrained; historical serialized model hashes
remain readable. Additional decoder CPU work is reserved and charged even on
failure. Fixed object order/whitespace and measured overhead are disclosed as
interface changes. A CPU-only optional-stack checker loads the existing tokenizer
and tests real token masks and positive/negative syntax controls without weights,
SQL or task/reference material. See [the runbook](SQLITE_CONSTRAINED_DIAGNOSTIC.md).

The local environment has no torch, transformers, tokenizer or xgrammar packages;
therefore native grammar compilation/masks and GPU inference remain unverified.
No dependency/model download, GPU job or push was performed. Local tests use
stdlib structural validation and scripted worker/processor doubles; they must
not be reported as constrained model results.

Local verification: full suite **183 tests in 63.306 seconds: 182 passed, one
existing opt-in sandbox skip**. Six focused constraint tests also passed after
removing a redundant schema check outside decoder accounting. All nine shell
checks passed. Compilation, stdlib-only CLI help/manifest construction, eight
diagnostic runbook shell blocks, two new Python blocks and `git diff --check`
passed. Controls cover observed malformed shapes, reasoning/prompt boundaries,
dependency failure, manifest tampering, historical hashes, charged successful and
failed calls, and truncated actions that cannot execute SQL. No real token-mask
qualification or GPU inference was performed locally.

## Synthetic GPU failure and public view correction (2026-09-19)

### User-reported GPU observations

Experiment `f082c0b74ce198653acac3d9d2ec955870d66e574f5d67bf436442adf60b195b`
completed all four synthetic single/clean probes with **0 successes**, one public
integration pass, three missing required artifacts and **23786** charged work
(mean 5946.5). All 16 model generations stopped at EOS; none reached the output
cap. These share one synthetic source group and establish no benchmark or policy
result. Manifest hash:
`e3feb29c33fa76b055b964672ec82413e19376eccf6c67b1eb2e339298208257`;
observed-cost report:
`86cdc13ab2e1efa8ebb14c5f187f66d657233291a6382f894c013f72153b0b1d`.

| Probe | Episode work | Operation work | Recorded outcome | Trace finding |
| --- | ---: | ---: | --- | --- |
| Aggregate | 5792 | 5751 | malformed | Invalid read offset, then invalid JSON/tree construction |
| Join | 5618 | 5577 | malformed | Invalid read offset, wrong join structure, invented artifact ID |
| CASE | 6050 | 6009 | malformed | Invented artifact ID and invalid CASE construction |
| View | 6326 | 6185 | submitted | View missing FROM and required alias was accepted, then failed final scoring |

The exact view defect was reproduced locally: CREATE VIEW alone succeeds without
resolving its body. This is a harness defect alongside the observed model/interface
failures. It is not evidence that GPU memory, Slurm, or output length caused these
four failures, nor proof of general model incapacity.

### Correction and bounded next configuration

Each view now undergoes a fixed zero-row read under the existing authorizer and
resource limits. SQLite DQS_DDL/DQS_DML are disabled: otherwise an unqualified
missing quoted identifier can silently become a string literal. String literals
remain supported through the restricted literal expression. The executor reports
`view_validation=zero-row-v1` and `double_quoted_strings_disabled=true`; unavailable
controls fail closed. Capability fingerprints therefore change for calibration
and native reference validation. Existing native validations must be regenerated
on CPU before a later native run; old evidence remains preserved.

Only explicitly public structured output names are projected for alias checking;
no reference SQL, evaluator projections, expected rows or correctness feedback are
used. The synthetic view source now repeats its already public names as
`output_columns`. Failed validation remains charged and returns `invalid_view`
without an artifact. Zero-row resolution does not prove value correctness or
exercise every data-dependent runtime path. Native contracts lacking explicit
public output names retain terminal column checks.

The approved new config, `configs/sqlite-tool-compatibility-reasoning.json`, uses
thinking and a shared reasoning/action generation cap of **2048**, retaining the
same pinned model, deterministic decoding, 8192 context, 12 actions, 100000 work
per episode, four probes and one GPU shard. The existing no-thinking config is
unchanged. The comparison includes reasoning, generation allowance, public
validation and structured contract presentation; it cannot attribute a difference
to thinking alone. No new model result is claimed. No jobs, pushes or downloads
were performed during this local implementation.

### Local validation

`python -m unittest discover -s tests -v`: **177 tests in 68.472 seconds,
176 passed and one existing opt-in sandbox test skipped**. All nine shell checks
passed. New regressions cover missing FROM, nonexistent columns, missing public
aliases, valid constant SELECTs, source integrity, charged rejected calls with no
stored artifact, wrong values remaining terminal-only, and configuration bounds /
executor fingerprint invalidation. Existing native reference controls also pass.
These use CPU scripted workers, not model inference.
Compilation, isolated standard-library CLI help and four-episode manifest creation
passed. Documentation checks validated 39 shell blocks and seven Python blocks;
`git diff --check` passed.

## Synthetic tool-compatibility diagnostic (2026-09-19)

### Reported cluster measurements preceding this change

The read-only budget audit reports reference actions of **622 and 375 content
tokens**, or **623 and 376 with one stop**, for `solar_2` and `solar_M_3`.
Both fit 768. Public schema is three pages and columns four; the full public
catalogue is one page, and reading all public documents plus assumed fixed
steps would take 65 actions. No assertion is made that all documents are needed.
Audit input hash: `5c38481e64d4055042691f08c0c2bae4ff64332a8ec43ebaf135458178580003`;
script hash: `602eed04ca8392e9bb662141f32aa1995c06444cea1bc0593a4aa79a8fbe21c7`;
model-lock hash: `beb4dcd0f1605695c54e21963cb6a70087b20a76e5c23b6f26571c15283604db`.
CPU audit time 0.092284807 s, tokenizer subprocess CPU 12.898848828 s, wall
23.08567424863577 s. This supersedes the previous locally unmeasured status;
these analysis costs remain separate from episode ledgers.

The authorized 24-action follow-up, array **1078011**, experiment
`5f4bcf452b24b0b2f267cb9c327e8742042034dd02692ac872c87154c342ff4a`,
still completed 0/2 with both required artifacts missing. Total work **131348**
versus **73320** (+79.1%); mean 65674. Maximum per-episode work remained 100000.
Observed-cost report ID:
`d1dc30ea9d761a60b203a746789e0c4431a93cfae835707525a51b22334d3ea2`;
manifest hash `03fc48c60f6999f1d8e746dfb9994861f29185f9df5805238bb08e92bd172f31`.

| Probe | Calls | Recorded operation outcome | Operation work | Trace |
| --- | ---: | --- | ---: | --- |
| solar_2 | 13 | malformed | 49716 | Ten reads; three identical invalid capped query attempts, first JSON error at column 256 |
| solar_M_3 | 24 | action_limit | 81550 | Twenty-four reads, all EOS; no view creation |

Operation work totals 131266; the remaining 82 charged units belong to the
rest of the episodes and are not attributed to a specific stage by this table.
The query stopped at the malformed retry guard, not the new action limit.
Neither task produced an artifact. These observations support stopping action-
limit increases; they do not prove every compatible model or representation
would fail. No recovery-policy effect was measured.

### Implementation and local controls

The opt-in `tool_compatibility_v1` SQLite fixture suite generates four separate
single/clean episodes: grouped sum/count with aliases, a join, CASE, and a named
view plus explicit final submission. Natural-language requirements, schemas and
the join relationship are supplied directly; source reads still cost work.
The suite has no documents or native material and supplies no solution trees to
workers. Its database setup is fixed trusted code. Generated queries use the
existing restricted tree compiler/executor; the public monitor does not read
terminal expectations. Terminal-only scoring compares all columns/rows against
independent Python calculations; it does not enforce a unique query spelling.

The suite has distinct adaptation/scorer/access labels and one shared synthetic
source group. The default arithmetic fixture data and scorers remain unchanged.
The dedicated config preserves the frozen 4B model, no thinking, 768 output,
8192 context, 12 actions, 100000 work per episode, one shard and four planned
episodes. No automatic data staging, model selection or job submission is added.
This intentionally changes task complexity and information presentation; it is
not a controlled causal test of document discovery alone.

Independent scripted CPU workers construct the four valid trees and consume the
actual returned version ID for final submission. All four positive episodes
passed. Each of three negative conditions failed all four: corrupted values,
wrong column aliases, and creation without final submission (16 total CPU
control episodes). Tests also check group/regime labels, denied broader
conditions, preserved default fixtures, positive charged work, four context
identities and absence of terminal feedback during model calls. These are
harness controls with test doubles, not real-model successes.

Full suite: **173 tests in 62.182 seconds, 172 passed and one existing opt-in skip**.
All nine shell-file checks, compilation, isolated standard-library CLI help,
39 documented shell blocks, six Python snippets and diff hygiene passed. An
isolated stdlib CLI manifest/planned-cost check produced four episodes, 48
primary actions and 400000 maximum work, with zero model executions.
GPU diagnostic results remain pending. Follow the
[bounded browser-terminal runbook](SQLITE_TOOL_DIAGNOSTIC.md); no native rerun or
larger campaign follows automatically.

## Solar post-EOS control and budget audit (2026-09-19)

User-reported preflight **1078003** passed on A100-PCIE-40GB. It generated the
ready JSON in six output tokens, ending at **248046**, effective stops
`[248044,248046]`, pad 248044, under `tokenizer-turn-eos-v1`. SQLite capability
checks also passed. This verifies operational turn stopping, not task competence.

Run array **1078005**, experiment
`cfb6d97fed8222c496b256acffa5880b3ba00a78cab355da0193ba575cd90fd3`,
then completed both native single/clean development tasks with **0 successes and
two missing required artifacts**. Profile, task obligations, 12-action cap,
768-token output cap, 8192 context and 100000 work per episode were unchanged.
Both tasks share one `database:solar` group; this is not a recovery comparison.

| Task | Charged work | Reads | Query attempts | Rejections | Final artifact |
| --- | ---: | ---: | ---: | ---: | --- |
| solar_M_3 | 30641 | 12 | 0 | 0 | Missing |
| solar_2 | 42679 | 10 | 2 | 2 | Missing |

The view worker reread its contract and consumed nine sequential KB documents
without constructing a view. The query worker used the catalogue and four metric
KBs, repeated two KB reads and schema inspection, then attempted the same invalid
query action twice. Local parsing of the supplied strings confirms both are
2872 characters and fail first at **column 256**. They also use an unsupported
`sum` expression key and column names as nonexistent table names. These mistakes
precede the output cutoff. No query executed, so the run does not measure the
semantic accuracy of an executed candidate. No reference content is reproduced here.

Of 24 generations, **22 ended at EOS 248046**, and the two query attempts reached
768 tokens (`length_limit`). The largest prompt was 5390 tokens, leaving room
for the configured output allowance inside 8192. There is no context overflow in
these logged calls. Missing fast-path libraries are reported, but these traces
provide no evidence that installing them fixes the malformed actions or read loop.

Total charged work **73320**, mean **36660**, reconciles with both episode ledgers
and is 1831 above the preceding 71489 control. The reported observed-costs ID is
`8bb8e4b9e4cd5660efc26d2f6f73e9122deec8f99811b32d77eeac6f4853dc6d`;
manifest hash `320336ee7ace48d49889cb7272325f62a325b01b31ed98a071821c5e522b6adf`.
These are user-supplied remote results, not locally executed GPU measurements.

### Representation and action audit

Source inspection confirms that successful creation/query and final submission
are separate charged actions, and document pages are 4000 characters. Under the
explicit scenario of one contract read, schema inspection, one catalogue page,
one creation/query and one final submission, five of 12 actions are used,
leaving seven for document pages and retries. This is **conditional arithmetic**,
not a demonstrated minimal successful route. The worker could choose fewer
reads, and a reference is not guaranteed to be the shortest valid expression.

The former private `/tmp/bc-author-materials.f0n5jtmc/` review and pinned Qwen
tokenizer are unavailable locally in this session. Exact reference token sizes
are therefore **unmeasured**, and no character-to-token heuristic is substituted.
The cluster retains the validated native manifest and model lock. The new
`scripts/audit_sqlite_budget.py` validates that manifest, compiles existing trees
without SQL execution and optionally uses an explicit offline tokenizer subprocess.
It reports compact action sizes, one-stop token allowance, public page counts,
input/script/lock hashes and separate CPU/wall measurements. It never prints or
saves the reference expressions, selects gold-derived worker reads, edits caps,
loads weights or submits jobs. Existing reports cannot be overwritten.

Local verification: full discovery completed 170 tests in 58.569 seconds,
169 passed and one existing opt-in test skipped. The final focused audit suite
passed all four tests, including an additional mocked tokenizer boundary/hash
check added after full discovery started. It checks 767+1 versus 768+1 against
the cap, offline invocation and changed-metadata rejection; these synthetic
counts are test inputs, not measured solar lengths. The other checks cover
creation/submission envelope fields, reference-text exclusion, character rather
than byte paging, standard-library default operation and immutable reports.
All nine shell files, compilation, isolated stdlib CLI/help, 20 shell blocks,
five Python snippets and diff hygiene passed. No real tokenizer, model or SQL
execution was performed by this audit locally.

Next collect that private report using [the browser commands](RESEARCH_GATE.md#solar-budget-audit).
If the canonical reference exceeds the cap, that establishes a representation
constraint, not impossibility for all equivalent solutions. If it fits, there
is still no clean-model competence result. More output alone does not repair
the observed early syntax/grounding errors. No further GPU campaign is prepared.

## Tokenizer turn-stopping correction (2026-09-19)

The user supplied a read-only inspection of the pinned checkpoint/tokenizer
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. The staged model directory has no
`generation_config.json`; its `config.json` text configuration has
`eos_token_id=248044`. Tokenizer metadata resolves:

| ID | Token | Role |
| --- | --- | --- |
| 248044 | `<\|endoftext\|>` | Model text-config EOS; tokenizer padding |
| 248045 | `<\|im_start\|>` | Chat message start |
| 248046 | `<\|im_end\|>` | Tokenizer EOS and template message end |
| 248068 / 248069 | `<think>` / `</think>` | Thinking delimiters, not marked special in this tokenizer metadata |

The template file SHA-256 is
`a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715`.
It emits `<|im_end|>` after assistant messages and an empty thinking block when
`enable_thinking=false`. The backend already uses this template and setting;
the audit does not indicate that reasoning was silently enabled. Its old
generation call supplied no explicit EOS or padding options and classified stop
causes only against `model.generation_config.eos_token_id`.

This establishes a config/tokenizer turn-boundary mismatch. It can allow a
model to continue beyond a valid assistant turn into extra dialogue if its
effective stop set omits the turn delimiter. The old decoded trace discards
special tokens, so it cannot prove which raw delimiter appeared in the malformed
generation. Nor does the mismatch alone explain all repeated document reads.

Correction in `models/transformers_backend.py`:

- Verify that tokenizer EOS resolves consistently, is not unknown, and occurs
  in the staged template. Invalid/missing token metadata fails explicitly.
- Preserve the loaded model's EOS IDs and append tokenizer EOS if missing;
  pass that set explicitly to every generation. Expected for the reported
  metadata: `[248044, 248046]`. Use tokenizer padding when model padding is unset.
- Record configured/effective IDs in runtime and effective IDs plus the final
  generated token in generation diagnostics. Stop classification uses that set.
- Keep complete generated-token accounting, including EOS; do not clip decoded
  text to its first JSON action. Model files and generation defaults on disk
  are not edited. Prompt, model revision, reasoning/sampling, task, scorer and
  budgets remain fixed.
- Bind real calibration compatibility to `tokenizer-turn-eos-v1`; source hashes
  already distinguish new manifests. Old failed controls remain unchanged.

Four focused CPU regressions passed using test doubles, without loading any GPU
library or model: preserving/model-plus-tokenizer stops and padding; rejecting
unverified metadata; actual backend `generate` receiving the explicit stop IDs
and ending a scripted stream before its fake next turn; and real calibration
invalidation while mock compatibility stays unchanged. The scripted generation
charges its two tokens including the final EOS. This is adapter behavior, not a
real-model success claim. Full unittest discovery ran **167 tests in 50.364
seconds: 166 passed, one existing opt-in skip**. All nine shell checks,
compilation, isolated stdlib CLI help, 33 documented shell blocks, one embedded
Bash script, five embedded Python snippets and diff hygiene passed.

At this historical checkpoint, the next step was to deploy reviewed code, make a fresh two-task manifest and inspect preflight
runtime/generation stop metadata before the bounded control. Do not download or
fabricate a `generation_config.json`, modify the locked template, raise caps or
start a broader campaign. GPU effectiveness was then unmeasured; the post-EOS
record above supersedes that status.

## Solar document-discovery follow-up (2026-09-18)

User-supplied aggregate, cost report and worker messages from array **1077718**:

- Experiment: `754c06ed06a51174619455ced15d592db875cbbdca1c39f15f157808801643c4`.
- Condition: `qwen35-4b-control`, single/clean, full, protocol A, native SQLite,
  one `database:solar` group, unchanged 12 actions / 768 output tokens / 8192 context.
- Manifest hash: `06d6bf890a3098ac56b9de74d73b61ca17764b0da1742a903436a3a2a97557de`.
- Cost report: `solar-interface.s6cxt7/observed-costs.json`, ID
  `3b8cde348c9bf1e248d7c8ba7f833a17d231153b707761fa7db0f303f366b99a`.
- Analysis source: `0db2f608d3a67c9540c9e9b30df9e311ef25a0ba:8ed2ca6d9986ddc5a680aef7e19131c64d97a66cef70278ebb8e655f2bdf5038`.
- Result: 2/2 completed, 0/2 successful; both artifacts missing and all public
  coverage/shape/integration checks failed. No missing/retryable shards.

| Task | Charged work | Actions | Rejections | Observed behavior |
| --- | ---: | ---: | ---: | --- |
| `solar_2` | 40824 | 12 | 1 | Contract, schema, catalogue, four document reads, one malformed generation, then the four reads again |
| `solar_M_3` | 30665 | 12 | 0 | Contract, schema, contract again, then nine sequential document reads |

The query worker selected MROI, urgency, revenue-loss and maintenance-cost
definitions from public titles. Its eighth generation began with a document-read
action, then emitted simulated user/assistant turns and `<think>` text within
the same response. It reached 768 tokens (`length_limit`). The parser rejected
the response with `Extra data`; neither the leading action nor the simulated
tool results were executed. It then reread the same four definitions. There was
no SQL/view action or required-artifact submission in either task.

The view worker did not call `list_documents`; after one repeated source read
it read `kb-0` through `kb-8` in order. Some definitions were relevant, others
were not. All its generations ended with EOS. Across both episodes, 23 of 24
generations ended with EOS, one with `length_limit`; the maximum logged input
was 4377 tokens, below the context cap even with the output allowance reserved.
Both workers used all 12 actions with substantial work allowance remaining.

Total charged work 71489 (mean 35744.5) is 14622 / 25.7% above the previous
56867. This is surrogate charged work, not a GPU-time comparison. The catalogue
enabled useful discovery in one trace, but there is no complete-task improvement
and no evidence about the correctness of an attempted SQL solution. The single
length-limited generation was a simulated conversation, not a nearly complete
SQL artifact; simply enlarging its output cap is not an evidence-backed fix.

Pause identical/prompt-only reruns and broad policy/model sweeps. Inspect the
existing staged chat template, EOS configuration and tokenizer metadata next,
without loading weights or submitting a job. The backend uses the staged
template and model generation configuration; decoded transcript text alone
does not prove whether generated role markers were ordinary text or special
tokens, nor establish a stopping/template bug. Do not switch reasoning, enlarge
budgets, clip the response to its first JSON object or fabricate tool results.
Any future condition must preserve these failures and have a fresh manifest.
This update changes documentation only; the prior 163-test code validation
remains the latest full suite result. All nine shell checks, 32 documented shell
blocks, one embedded Bash script, four embedded Python snippets and diff hygiene
passed. No model inference, submission or runtime change occurred locally.

## Solar native model control read loop (2026-09-18)

User-supplied preflight, aggregate and worker trace; the cluster checkpoints are
not present locally. Preflight job **1077667** passed on an A100-PCIE-40GB with
the frozen Qwen3.5-4B, BF16/no-thinking settings and an `ok` SQLite executor.
The 8-token readiness response ended with EOS. Run-array stderr filenames identify
**1077671**, with no traceback in the supplied log tails.

- Experiment: `39194c9de0eafc3e98c9cf02393afd7483f39476e36b61addf6afc2c6556b9f4`.
- Manifest: `/dataset/suaq0001/beyond-consensus/private/livesqlbench/solar-control.YYPkSx/manifest.json`.
- Mode: `gpu_sqlite_native_development`; single/clean, full, protocol A,
  `qwen35-4b-control`, `bc_livesql_native_v1`, one database source group.
- Result: 2/2 completed, 0/2 successful, two missing required artifacts; public
  coverage/shape/integration failed for both. No missing/retryable shards.

| Task | Charged work | Actions | Tool rejections | Largest input / output (tokens) |
| --- | ---: | ---: | ---: | ---: |
| `solar_2` | 27882 | 12 | 0 | 3098 / 16 |
| `solar_M_3` | 28985 | 12 | 0 | 3280 / 17 |

Both traces have exactly the same tool sequence: their own `read_source`, one
`inspect_schema`, then ten more reads of the same contract. No public document,
query/view construction or artifact submission was attempted. All 24 generation
records report `finish_reason=eos`. Each run remained far below the 100000 work
cap and the 8192 context limit; outputs were below the 768-token allowance.
The loop reached the configured 12-action limit. A `source_read` event for the
schema explains the 12 source events; these are not 12 distinct task documents.
Total work is 56867. These observations establish lack of progress to artifact
construction, not the semantic accuracy of an attempted SQL solution.

The schema response included `assigned_contract_action` even after the correct
contract had been read. The initial public document list exposed IDs such as
`kb-17` without titles, and neither worker attempted to discover the definitions
needed by the named metrics. The repeated cue is a plausible contributor to the
loop; the trace alone does not prove it caused the model's behavior.

Shared interface correction in `runtime/data_domain.py`:

- Schema observations retain the current assignment without another read cue;
  reading a different source still returns the existing assignment reminder.
- `list_documents(offset)` returns up to 64 public IDs/titles in stable ID order,
  using only the public KB `knowledge` field or the ID as a fallback. Long titles
  have explicit 80-character previews; document bodies require separate reads.
- The catalogue is not filtered by the question, method, reference, private
  knowledge IDs or hidden tests. It has normal tool/model-prefill charges and
  provenance. Common instructions explain document discovery and completion.
- No automatic correction/query generation, free read, loop bypass, new SQL
  capability or model/budget/decoding/scorer change. Repeated reads still consume
  actions and can fail. New manifests and calibration compatibility hashes bind
  the changed interface; old results remain intact.

Focused tests exercise charged discovery through primary, repair, replication
and preparation; pagination/title previews; hidden-data exclusion; unchanged
wrong-source guidance; and a repeated-read worker still failing at action 12.
They use labelled scripted fixtures, not real-model inference. Full unittest
discovery ran **163 tests in 55.734 seconds: 162 passed, one existing opt-in
skip**. All nine repository shell checks, compilation, isolated stdlib CLI help,
31 documented shell blocks, one embedded Bash script, three embedded Python
snippets and diff hygiene passed.

A CPU-only catalogue check on the already-staged public solar documents listed
all 55 IDs/titles in one 4997-character observation, below the existing 12000
character bound, with the normal 10-unit tool charge. No document body, model
inference or SQL execution occurred in that check. GPU effectiveness remains
unknown; the two-task native competence gate and broader pair/policy gates remain
unmet. No job submission, model download, commit or push occurred in this update.

## Solar cluster CPU result reported by the user (2026-09-18)

The user supplied the summary from
`/dataset/suaq0001/beyond-consensus/private/livesqlbench/solar-check.NatDlH/native-validated.private.json`.
It reports `command_failed=false`, `validated_tasks=2`, and both `solar_2` and
`solar_M_3` as `validated`. For each, `positive_joint`,
`reset_repeat_identical`, `source_integrity_after_controls`, its missing-obligation
control and its corrupted-obligation control are all true; reasons are null.
These are individual reference controls, not the two-task joint pair validation.

Earlier, the user verified and canonicalized the uploaded private review to
its exact recorded hash, registered it, and froze the clean source into the
same check directory. The scheduler dry run accepted two CPUs on node02 in
PA100q and printed identifier 1077655. **That is not the actual submission ID**;
the executed job ID and its node were not supplied with the result summary.
Raw cluster manifests and ledgers were not copied into this local workspace.

This clears the cluster CPU prerequisite for two development tasks from one
database group under the existing reviewed result-comparison adaptation. It
does not establish model competence, full upstream evaluator parity, two
independent source groups or the requested two-pair gate. Next prepare a
two-episode single/clean control at the unchanged Qwen3.5-4B revision/settings,
with fresh GPU preflight and the shared registry guard. No job is submitted by
this documentation update.

## Solar reference review and local CPU controls (2026-09-18)

Cluster evidence supplied by the user: the merged material SHA-256 matched;
the four solar files downloaded; public/material registration and the unapproved
two-task review template succeeded in `staging.L7bFVF`. Both tasks were blocked
only on review. The assistant then fetched the same four pinned public files
(2261806 bytes total) into its private temporary workspace for local review.

Manual inspection covered the two author SQL references and their test functions
as text. All eight source-table inventories/column names came from the public
schema document. The resulting typed trees compile under `bc-select-tree-v1`:

- `solar_2`: all eight output fields, LEFT JOIN, grouped aggregates, priority CASE
  and ordered MROI result. The private check consumes the full submitted report.
- `solar_M_3`: the required named view, both joins and all five output columns;
  arithmetic and final rounding follow the pinned author SQL. The private check
  reads every required column from the submitted view and compares all rows.

**Scorer scope:** the existing `bc-sqlite-joint-v1` exact comparison is unchanged.
For the report it checks ordered values; for the view it checks an unordered
multiset retaining duplicate counts. Upstream `solar_2` invokes `ex_base`, while
the view's Python test checks existence/columns and at most five samples with
0.05 tolerance; its TAPR calculation uses rounded intermediate values unlike the
author SQL. The review records these differences explicitly. This is a reviewed
reference-result adaptation, not a claim that arbitrary author Python tests were
translated with identical semantics. No gold input or hidden check is added to
worker views, and no output rows are truncated to fit executor limits.

Local CLI controls on the actual pinned solar database:

| Subject | Positive / repeat / source integrity | Missing / corrupted obligations | Charged work |
| --- | --- | --- | ---: |
| `solar_2` | Passed | Both rejected | 255 |
| `solar_M_3` | Passed | Both rejected | 345 |
| Joint pair `pair-7c327cdcf197f2ac` | Passed | Each of both obligations rejected when removed or corrupted | 575 |

`sqlite-validate --task-ids solar_2 solar_M_3 --count 2` admitted both tasks with
`command_failed=false`. `sqlite-pairs --count 2` on the single explicit candidate
validated that one pair but returned `command_failed=true`,
`status=blocked_or_rejected` and `missing_candidate_slots=1`, as required. The
second pair is still missing. There is one independent development database
group and no model/GPU competence observation.

Executor: Python 3.12.7 / SQLite 3.45.3, existing default resource/row/step limits.
All controls used the fixed trusted executor and charged ledgers. No downloaded
SQL strings, upstream test functions or repository code were executed. Source:
`06a0b0d4b34ad0d883736a378b28ab11d1bf68d0:4506cd2f5b98ce6b65014e70a2c58f099403db86295f39a810695a8fc5d5db00`.

Private outputs are in `/tmp/bc-author-materials.f0n5jtmc/solar-review-v1/`:
`solar-review.private.json`, `solar-pairs.private.json`, reviewed staging and
native/pair validation manifests. `validation-summary.json` records sanitized
control outcomes and report bindings. They are local results; do not copy their
machine-specific staging manifests as cluster validation evidence.

SHA-256 bindings for transferable review inputs and public data:

- Completed private review: `78c2ccc691573f73aae9b38b26416fdced1b3d05f54a36e23a673607624ed31a`.
- One private pair candidate: `6efb09cf9be1623a329e3d40b83619169d1d30d4fbf599ec6f3ccfcd33640506`.
- Solar database: `d143744388100c33eaf7330af84dc71321fc7c317332961e4129196fd66cbc27`.
- Schema: `40ca184d021761f4612341ce689d898256e004d5ecb7a02ca8a364b37a5390b1`.
- Column meanings: `02ac182f79550cc0047165a080fe35bde0e9bf32264ac49a98d8ebe419d96fbf`.
- Public KB: `fc9205112fcd1ea67cd16f51d9377d6c7e0fb250bb2bde03236f8efda5fef72e`.

No runtime/scoring source changed. Cluster CPU replay, a second compatible pair
and later model competence are pending; no cluster submission or push occurred.

Repository verification: full unittest discovery ran 160 tests in 54.989 seconds
(159 passed, one existing opt-in skip); nine shell files, 22 documented shell
blocks and two embedded Bash scripts passed. The new documented Python block
parsed, and `git diff --check` passed. These checks did not submit the prepared
CPU job or execute its browser commands.

## Author supplement inspection (2026-09-18)

The user uploaded `livesqlbench_sqlite_gt_kg_testcases_20260601.jsonl`, described
in the authors' response as solutions, oracle knowledge and test functions.
It is a 359514-byte JSONL supplement with exactly four keys per record:
`instance_id`, `sol_sql`, `external_knowledge`, `test_cases`. It is not a full
record file suitable for direct `sqlite-stage --materials` registration.

The small public metadata file was fetched at the existing pinned revision and
its expected hash verified. Its ID set matches all 270 unique supplement IDs.
The offline merge replaced only the three private fields and verified every
other public field was unchanged. The merged file passes the existing `records`
parser. No missing tests or solution entries were synthesized.

| Check | Observed count |
| --- | ---: |
| Exact matching unique task IDs | 270 |
| Records with nonempty solution lists (shallow check) | 270 |
| Records passing existing recursive solution-presence check | 268 |
| Records with nonempty tests | 92 |
| Records passing both solution and test presence checks | 90 |
| Query records with / without tests | 2 / 178 |
| Management records with tests | 90 |

`mental_M_4` has one nonempty and one blank solution entry; `news_M_2` has a
blank solution entry. Both fail the current completeness check. The known pair
candidate `crypto_M_2 + crypto_8` still fails the material gate: `crypto_8` has
no tests. Presence is not restricted-tool support, reviewed evaluator approval,
reference success or benchmark readiness. Empty tests remain unavailable under
the current protocol; the receipt of this file does not relax that rule.

Exact SHA-256 bindings:

- Public: `2b964165a6cda878a4e4d4de9ccef1c6ad623b96e5215b522d81be284c9fcebc`.
- Author supplement: `55f9f98f4cec88890aa5c2baca5bf2db0402679f948ba4ea309a04e0357dcdda`.
- Merged: `b28bbcf4d1b0f63a6994d6ea1914e187ebc9ba185cb1a69476742b3c4cb3f698`.

Private working files are outside Git in `/tmp/bc-author-materials.f0n5jtmc/`:
`author-supplement.private.jsonl`, `materials.private.jsonl` and a sanitized
`merge-report.json`. Private JSONLs have mode 0600. The original uploaded file
was preserved and excluded via `.gitignore`; it was not committed. Matching IDs
establish a valid join, not semantic compatibility of author answers/tests with
the pinned database version. That still requires reviewed CPU controls.

No SQL, test functions, downloaded code or model was executed. No database
archive was downloaded and no job was submitted. The existing native parser and
presence gates were used unchanged; the only non-documentation repository edit
is the ignore pattern for the uploaded private supplement.

Verification: full unittest discovery ran 160 tests in 59.911 seconds, with
159 passed and one existing opt-in skip. All nine shell files, 20 documented
shell blocks and one embedded Bash script passed their checks. `git diff --check`
passed, and `git check-ignore` confirms the uploaded supplement is excluded.

## Cluster follow-up reported by the user (2026-09-18)

Evidence: browser-terminal aggregates, compact per-episode `silo-analyze` output,
`diagnostic-costs` reports and a matched `allocation-audit` excerpt supplied by
the user. The compact SILO totals were recomputed locally from those excerpts.
Raw cluster output directories were not available locally; no cluster execution
or independent replay of the original result files is claimed.

### Historical SQLite fixture ledger attribution

Pilot `d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd`:
all eight matched recovery/JIT pairs (four clean, four withholding) report
`reconciled` and `entire_gap_matches_search=true`. Each total-work difference is
256, finite-search difference 256, and non-search residual zero. Mean planning
work is 257 for recovery and 1 for JIT. This supersedes the earlier claim that
historical attribution was unconfirmed. It establishes a recorded surrogate-work
charge difference, not GPU seconds, token counts or a recovery success advantage.
Historical candidate counts/calibration origins are not inferred from this alone.

### SILO original versus explicit actual-carry interface

Both are eight-source full single/clean development runs under protocol A,
`qwen35-4b-control`: Qwen3.5-4B, BF16, no thinking, deterministic decoding,
8192 context and 768 output-token cap. The comparison reuses the same frozen
source groups and changes only the interface to `submitted_final_value_v1`.
The carry field copies the actual predecessor submission, including wrong values;
it does not provide a gold carry or a calculator.

| Observation | Original | Explicit actual carry |
| --- | ---: | ---: |
| Completed / planned episodes | 8 / 8 | 8 / 8 |
| Complete-task successes | 0 / 8 | 0 / 8 |
| Correct values | 101 / 480 | 101 / 480 |
| Public coverage / shape / integration passes (each) | 8 / 8 | 8 / 8 |
| Fully correct first segments | 6 / 8 | 6 / 8 |
| Incoming-state consistency, later segments | 1 / 24 | 6 / 24 |
| Within-segment increment errors | 21 / 448 checks | 7 / 448 checks |
| Later segments with inherited-only error | 0 / 24 | 5 / 24 |
| Charged work | 173439 | 185156 |
| Mean charged work per episode | 21679.875 | 23144.5 |

In both conditions every u1 boundary is inconsistent, all 24 later segments
have zero globally correct values, and all 101 correct values occur in u0.
The original trace records 96 EOS stops and no limit events. The supplied compact
carry trace omits stopping metadata, so that observation is not transferred to it.
All required artifacts are present and evaluators available; the summary's legacy
`integration_failures=8` means unsuccessful completed episodes, not failed public
integration. No repair, alarm or reserve violation was reported.

Carry used 11717 additional charged units (+6.7557%). Local consistency improved,
but neither complete-task nor per-value correctness improved on these eight
development sources. This is a descriptive comparison with no confirmatory
inference and no recovery-policy comparison. **Pause additional GPU runs of this
4B/no-thinking SILO setting.** The next gate is native SQLite material/reference
readiness, not a larger SILO battery or model sweep.

Provenance supplied in the reports:

- Original experiment: `7cd048f8209c217b2763cc711ed8ee91dc5cdca9c2ecaef8123e215da6252d79`;
  manifest hash `07c3420e585c596f1be7ab30dc791da98bcd8fc366df93a19bbd4e241469166a`.
- Carry experiment: `455cb07b9f493a40abc7473d493266690339e32c7d0dd750d65e8dacb52b79ad`;
  manifest hash `1decc3d43fd1bc7d8675223d77d18d9b7a07471d3fbb07b88e2926e6429ecce8`.
- Cost report IDs: original `384949b05eda970a57e3c03b3974ce8e6a0927114023074ef31e9a9d7d5b5a65`;
  carry `10d7df40638b1aa634a7e0a87ba91d51bd205c5ddad7fee1992d26c12daf6945`.
- Both cost reports identify source
  `06a0b0d4b34ad0d883736a378b28ab11d1bf68d0:4506cd2f5b98ce6b65014e70a2c58f099403db86295f39a810695a8fc5d5db00`.
- Model/tokenizer revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
  SILO upstream commit: `e74127782ed1c42fff474249961f022c063d76f2`;
  adaptation `bc_silo_recoverable_v1`, scorer `silo-segments-v1`.
- Preflight jobs **1077600** and **1077609** reported NVIDIA A100-PCIE-40GB,
  BF16 supported, driver 570.133.20, torch 2.10.0+cu126 / transformers 5.3.0,
  and successful ready-JSON generation. These are preflight observations;
  actual eight-task campaign job IDs/device reports were not supplied here.

The original frozen plan remains under the user's
`/dataset/suaq0001/beyond-consensus/research-gate.iK0VlI/silo/` and the comparison
under `research-gate.iK0VlI/carry-interface.j4zddx/`. Outputs are in the storage
`outputs/<experiment_id>` directories. Preserve those files and derived reports.

### Local continuation: native prerequisite check

The actual `sqlite-readiness` CLI, without a staged manifest, returned
`scoring_unavailable`, reason `staging_manifest_not_supplied`; SQL and model
execution were both false. Runtime checks report Python 3.12.7, SQLite 3.45.3,
authorizer/defensive mode, disabled extension loading, trusted-schema-off,
table inventory and process limits available. This establishes local executor
capabilities only; native ready counts and current cluster files remain unknown.
The report is outside Git at `/tmp/bc-native-continuation.rfit7o_s/readiness.json`.

No scientific code, scoring behavior, defaults or budgets changed. Current
instructions now inspect existing native staging/material availability and retain
the CPU reference/pair gates. No jobs, downloads, pushes or author messages were
performed during this continuation.

Continuation verification: `python -m unittest discover -s tests -v` ran 160
tests in 55.904 seconds: **159 passed, one existing opt-in skip**.
`python scripts/check_shell.py` passed all nine shell files;
`python scripts/check_docs_shell.py` passed 20 documented shell blocks and one
embedded Bash script. The new inventory example's embedded Python parsed and its
missing-manifest branch ran successfully against a temporary directory. No real
native staging manifest was available to exercise its inspection branch here.
`git diff --check` passed.

## Prior recoverability research gate implementation (2026-09-18)

The user has not run the previous cycle's browser-terminal commands. The starting
local checkout was clean. This incremental cycle preserves earlier observations;
no remote audit, GPU experiment or real native reference validation was performed.
See [RESEARCH_GATE.md](RESEARCH_GATE.md) for evidence, inference, blockers and the
ordered next decisions.

| Actual local command | Outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **160 tests: 159 passed, one existing opt-in legacy integration skip**, 53.409 seconds |
| `python -m unittest tests.test_research_gate -v` | **9 passed**, 3.435 seconds |
| `python scripts/check_shell.py` | **9 shell files passed**, including `bash -n` |
| `python scripts/check_docs_shell.py` | **19 documented shell blocks and one embedded Bash script passed**; no commands executed |
| `python -m compileall -q src tests scripts` | Passed |
| `git diff --check` | Passed |
| `python -I -S scripts/bc.py --help` | Passed; GPU imports remain lazy |

Focused behavior evidence:

- Catalogue counting distinguishes 32 labelled/masked candidates from one actual
  independent SQLite workflow, or two linked numeric dependency workflows.
  Outputs, owners, serial order, reserve and newly introduced intermediate units
  are counted separately. Unknown checking/integration costs remain null.
- Prescribed linked/isolated numeric workflows and selected existing boundaries
  retain all obligations under the same JIT repair and reserve rule. Actual linked
  artifact reads are charged/versioned; invalidating the upstream version also
  invalidates descendants. New organization conditions get new experiment IDs.
  Hidden-material sentinels cannot affect candidate inventory or generation.
- Tiny exact additive fixtures exercise deferral over compromise scenarios with
  both cheap and expensive preparation. JIT retains identical after-alarm tools.
  These are scripted fixtures, not real-model planning or preparation benefits.
- A saved **mock** run's paired ledgers reconcile the 256-unit search difference;
  inconsistent/duplicated entries prevent confirmation. Missing raw ledger data
  remains unavailable, never measured zero. Source result files remain unchanged.
  This does not confirm the historical cluster attribution.
- The initial SILO preparation contains only eight full single/clean episodes.
  Reuse preserves frozen contents and rejects excluded/duplicate sources. A fake
  scheduler dry run checks one GPU per shard and `--array=0-3%1`, with no submission.
  The embedded-script test catches syntax errors inside a quoted here-document,
  which outer-block `bash -n` alone would miss.

Actual CLI preparation/audit artifacts are outside Git at
`/tmp/bc-research-gate.jpqKf9`: numeric and SQLite `planning-audit` reports,
`sqlite-readiness`, and `silo-battery --full-only` / `validation-config` outputs.
Readiness is `scoring_unavailable`; the historical 270 metadata records were not
re-inspected. The generated seeds are 1001, 1002, 1003, 1007, 1008, 1011, 1013,
1014, with eight distinct development source groups. Only full/plan data files
were frozen; no local/boundary/confirmation/measurement campaign was created.

`build_manifest` was also called locally on the pinned control config to check
the eight-episode plan, followed by the actual `diagnostic-costs --manifest` CLI.
No staged model lock is available locally, so this is **an unstaged local plan**,
not a cluster-ready submission. Regenerate with the actual `--model-lock` after
pulling the reviewed source. Cost report: eight executions, 800000 total cap
units, 384 primary actions, 8192 context, 768 generated-token cap per call;
measured work/mean costs remain null. No hardware result is inferred.

Native decomposition selection is still blocked: no validated public task
structure/legal alternative plans or compatible measured operation costs are
available. The implemented opt-in layer exposes only existing numeric dependency
choices; it is not a native intermediate-view generator or a research-ready
optimizer. The native reference/scorer boundary and all historical failures below
remain intact. No commit, push, job submission, author contact or large download
was performed.

## Bounded native/allocation/SILO validation cycle (2026-09-17)

Implemented the incremental cycle described in
[VALIDATION_CYCLE.md](VALIDATION_CYCLE.md), preserving the previously uncommitted
documentation and all historical observations below. No GPU or native benchmark
result was generated during this work.

Final local checks on Python 3.12.7:

| Command | Actual outcome |
| --- | --- |
| `python -m unittest discover -s tests -v` | **151 tests: 150 passed, one skipped**, 54.044 seconds |
| `python -m unittest tests.test_validation_cycle -v` | **28 passed**, 9.111 seconds |
| `python scripts/check_shell.py` | **9 shell files passed** LF/usage/dry-run/strict handling and `bash -n` |
| `python -m compileall -q src tests scripts` | Passed |
| `git diff --check` | Passed |
| `python -I -S scripts/bc.py --help` | Passed with isolated Python and site packages disabled |

The skip is the existing opt-in legacy sandbox integration test, not a missing
SQLite/SILO test. The suite exercises the fixed stdlib SQLite executor; it does
not validate a GPU, native author materials, or site/container capabilities.

New focused regressions establish:

- Native missing/empty material and integrity failures stay unscored; reports do
  not expose gold, hidden tests or private paths. Synthetic positive/negative
  controls, common-bundle pair tests, reset/source integrity and native-subset
  comparison parity pass. Missing second and reversed duplicate pairs stay blocked.
- Optional allocation tracing leaves decisions unchanged, exposes actual
  candidates/scenarios/limits, and reproduces 256 recovery versus zero JIT primary
  search states for four independent fixture units with equal route estimates.
  Charge IDs, stage/total reconciliation and the model-token formula expose
  duplicate/mismatched accounting without discarding legitimate equal charges.
- Constructed preparation executes and is source-grounded; eligible restoration
  charges reads and re-prefill; compromised dependencies are rejected. Replication
  is selected under its existing objective, and JIT retains identical after-alarm
  preparation operations. The unchanged additive catalogue cannot produce a
  strict advance-preparation optimum; see the explicit scientific conflict in the
  cycle document. No selected favorable empirical plan was manufactured.
- The labelled third-smoke excerpt reproduces 15/60 correct values. Offline
  analysis separates incoming and local increment errors from inherited state.
  Shape-valid all-wrong answers pass public integration and fail final scoring
  without oracle feedback. Boundary replay preserves wrong actual values,
  rejects altered content under an existing version, and retains missing slots.
- Fresh deterministic development selection, local-task labelling, confirmation
  separation, default settings, template capability rejection, stopping/limit
  observations, condition grouping, immutable snapshots and mocked Slurm dry runs
  behave as specified. Operation measurements use the actual worker/ledger path;
  interrupted operation work and disjoint holdout validation are exercised.
  Sanitized bundles preserve allowlisted runtime facts and exclude private paths.

The final CLI preparation checks wrote reports/data/manifests outside Git under
`/tmp/bc-validation-final.CiLfBU`:

- `sqlite-readiness` returned `scoring_unavailable`: no staged native manifest was
  supplied locally. The historical 270 public records were not re-inspected.
- `allocation-reproduce` used explicit **constructed** cold/prepare/prepared
  predictions of 2000 each and reproduced the 256-state planner charge. These
  are not measured model costs or a reconstruction of the remote pilot ledger.
- `silo-battery`, `validation-config`, `manifest` and `diagnostic-costs` prepared
  eight full and 32 local executions, plus a 24-boundary ceiling and two held-out
  confirmation sources. No model executed. Boundary data require real baseline
  submissions and were not fabricated.
- `measurement-plan` excluded those diagnostic/confirmation sources and prepared
  four fresh sources split two/two for training and holdout: 96 operations across
  four executions. The training config/manifest froze successfully; no empirical
  measurement or automatic calibration activation occurred.

Remaining gates: actual native databases/documents and nonempty author
solutions/tests with bound manual review; a second compatible pair candidate;
historical remote ledgers/checkpoints for exact attribution of the 256-unit gap;
and user-triggered GPU preflight/clean diagnostic measurements. Staged template
reasoning support and any 9B revision/hardware fit are unverified. No job,
download, push, external message or broad four-policy campaign was launched.

Exact local and browser-terminal commands are in the
[ordered runbook](VALIDATION_CYCLE.md#ordered-commands).

## Third SILO smoke still failed complete-task scoring (2026-09-17)

The user reported the completed recurrence-guidance smoke, experiment
`9a7b999f0fdae4ed106080940417c0ee6002fd691658ca8b7044623bd15a583e`, from
`silo-smoke-v3-manifest.json`. Its reviewed dry run requested one GPU in `PA100q`;
actual job ID, snapshot and hardware inventory have not been supplied.

The single/clean episode again had full coverage and 0/1 successes. All four
artifacts were retained, with no public alarm, repair work, reserve violations or
missing/retryable shards. Protocol A, the source group, protected-original-shard
access, adaptation, scorer and upstream pin match the preceding two smokes.
The provided stderr excerpt contains only the optional fast-path fallback notice.

The subsequent trace identifies episode
`f5215f0f62c9ca58609549707de361b298aa6d3bc7326ae235684a527a7fdf58` with
21581 work units, zero tool rejections and public integration true. Its final
scorer reports one correct segment and `native_S=native_P_level_II=0.25`.
Independent accumulation of the posted inputs confirms **15/60 correct outputs**,
all in u0. Local scorer replay reproduces the reported metrics and source hash;
all original inputs match the second smoke.

| Segment | Correct outputs | First submitted value | Correct first value from original inputs | Visible predecessor's last value |
| --- | ---: | ---: | ---: | ---: |
| u0 | 15/15 | 9 | 9 | None |
| u1 | 0/15 | 11 | 388 | 386 |
| u2 | 0/15 | 13 | 802 | 458 |
| u3 | 0/15 | 46 | 1171 | 436 |

The explicit recurrence guidance coincided with u0 becoming fully correct,
raising value accuracy from 3/60 to 15/60 and complete segments from zero to
one. Total work increased by 2763, from 18818 to 21581. Task success remained
zero. This is a descriptive development comparison, not a general causal or
competence claim.

Boundary-state errors persist even with a correct predecessor: u1 sees u0's
final value 386 but starts at 11, consistent with using its first value 9 plus
the new input 2. Its entire submitted answer list is identical to the previous
run. The second u1 increment is 60 instead of 25. u2 starts at 13 rather than
the 460 implied by its visible predecessor's final value 458; its second
increment is 85 instead of 2. These are additional errors, not just propagation
of an earlier wrong total. u3's first value implies incoming state 17, not its
visible predecessor's final value 436; subsequent increments match its shard.
The trace does not establish why the model chose 17. No hidden computed carry
or correction was supplied, and the public structural checks behaved as designed.

Next: pause prompt-only reruns and the larger SILO policy pilot. The current
frozen model setup has not established clean competence on this task. Any next
model/reasoning condition should be an explicit, separately labelled competence
diagnostic with fresh provenance and appropriate charged generation/context
budgets, keeping source access and scoring fixed. The prior instruction to retain
the validated model/thinking configuration remains in force; no configuration
or runtime change was made in this review. All three failed outputs are preserved.
These are repeated development observations on one source group, not independent
test instances or a recovery-policy comparison. A completed scientific failure
remains terminal, not a retryable infrastructure error.

## Second SILO smoke retained all segments but failed scoring (2026-09-17)

The user supplied the aggregate for experiment
`055d8a4bc4a459072438d845d6c142763227045f8ad457ac36c27898e072d4bf`, generated
from `silo-smoke-v2-manifest.json` after the operation-guidance change below.
The dry run requested one GPU in `PA100q`; actual job ID, snapshot and hardware
inventory remain unsupplied. The task source group, protected-original-shard
access regime, adaptation, scorer and upstream pin match the first SILO smoke.

The one single/clean episode completed with full coverage but 0/1 successes.
All four artifacts were retained; false alarms, detected-but-unfinished cases,
repair work and reserve violations were zero. No shards were missing/retryable.
This is progress from the first smoke's zero retained artifacts but not a clean
competence pass. The subsequent trace for episode
`aec03aa8d202cc426139bcf7073a44375725dc84970453d3317d588e2c08c936` confirms
18818 total work, zero tool rejections and successful public integration. All
four original shards were read and all four answer lists were submitted.

In the current runtime, the SILO public audit accepts segment coverage/shape;
terminal scoring checks the actual cumulative outputs. The aggregate's
`integration_failures=1` counts a completed unsuccessful episode and does not by
itself establish a public integration failure. Here `joint_public_integration`
is true, while final evaluation reports 0/4 correct segments and
`native_P_level_II=0.05`. Independent accumulation of the user-visible inputs
finds exactly 3/60 matching outputs. The visible inputs match generator seed 1
and the reported source hash; local scorer replay reproduces the reported counts.

| Segment | First incorrect position (1-based) | Submitted value | Correct value from original inputs | Correct outputs |
| --- | ---: | ---: | ---: | ---: |
| u0 | 4 | 144 | 100 | 3/15 |
| u1 | 1 | 11 | 388 | 0/15 |
| u2 | 1 | 13 | 802 | 0/15 |
| u3 | 1 | 42 | 1171 | 0/15 |

For u0, the first three outputs are correct; the fourth adds 49 instead of the
fourth input 5, then the remaining totals stay 44 too high. Later segments also
fail to use the preceding segment's final cumulative output. For example u1
begins at 11, consistent with the predecessor's first value 9 plus the new input
2, even though the visible predecessor's last value was 430. Using that untrusted
carry would produce 432, still wrong globally but distinct from the submitted
11. u3 similarly starts at 13+29 rather than the visible predecessor's 490+29;
its later increments match its original shard. u2 contains further incorrect
increments. These are arithmetic/indexing and boundary-state failures beyond
simple propagation of u0's error. There is no evidence of a scorer or tool error.

The shared SILO prompt now restates the public Prefix Sum recurrence explicitly:
one scalar carry, zero only for the first original segment, predecessor's final
answer element when using that artifact, then each original input in order.
It asks the model to check successive differences against the original inputs.
This is common task-definition guidance, with no task-specific numbers, computed
carry, calculator tool, new source access or numerical feedback. Public auditing,
terminal scoring, model/thinking settings, sample sizes and budgets are unchanged.
The model still performs all arithmetic; the longer prompt/re-prefill is charged.

A regression test injects wrong scalar arithmetic and first-element carry use
through a scripted worker, verifying that complete shape-valid answers still
pass public integration, fail terminal scoring and receive no corrective hidden
feedback or automatic repair. It is not evidence that the real model improves.
The prompt change invalidates prior calibration compatibility and requires a
new source-pinned manifest.

The next step at that checkpoint was a fresh single/clean diagnostic using
`silo-smoke-v3-manifest.json` and the same staged inputs/model to test the public
recurrence clarification. Its failed aggregate is recorded above. Reusing this development
instance does not establish generalization; a pass must precede broader clean
coverage. This remains a non-confirmatory adaptation check, not a recovery-policy
comparison or evidence of a recovery advantage. No GPU run or push was performed
from this workspace.

Validation after the recurrence clarification:

- `python -m unittest discover -s tests -v`: 123 tests, 122 passed and one
  existing opt-in legacy sandbox integration skip.
- `python scripts/check_shell.py`: all nine shell files passed.
- `git diff --check`: passed.

## First SILO Prefix Sum GPU smoke failed (2026-09-17)

The user generated and validated eight II-11 tasks with protected original
shards, then supplied the aggregate for experiment
`9d2b2a4a46319fce4c3907ed67a0abf65607209d04f1699e24bc8a30d98fe125`.
Its reviewed dry run requested one GPU in `PA100q`; the actual job ID, snapshot
and hardware inventory have not been supplied.

The single/clean episode completed with full coverage but failed joint scoring:
0/1 successes, zero retained artifacts, one integration failure, one false alarm
and one detected-but-unfinished case. Repair work was 40; preparation and
historical work were zero. No missing/retryable shards or reserve violations
were reported. This is Protocol A, `gpu_silo_development`, adaptation
`bc_silo_recoverable_v1`, access `protected_original_shards`, scorer
`silo-segments-v1`, tool policy `bc-p2p-sequential-artifact-v1`, upstream
`e74127782ed1c42fff474249961f022c063d76f2`. It remains non-confirmatory.

The stderr excerpt shows completed weight loading, the optional fast-path
fallback and pad-token notices, with no traceback in the supplied excerpt.
The subsequent worker trace identifies the mechanism. Episode
`1703e4e54209bec1d177b024d7e9203595a9051febaf0113b807055aa7b32dc3` spent 8693
work units, recorded 12 tool rejections and failed public integration. For each
assignment u0 through u3, w0 emitted three valid-JSON `submit` preparation outlines
describing a future source read, despite `operation=implement`. All were rejected
without creating artifacts. There were no source/shard reads or arithmetic
answers in the supplied conversation. This does not establish arithmetic
incompetence or a recovery-policy failure: it was a single/clean action-selection
failure. The only concrete submission example in the old SILO instructions was
for preparation; the model repeatedly used that shape. This association motivates
clearer instructions but does not isolate the cause of model behavior.

The local correction documents JSON envelopes for the implementation tools,
explicitly separates `prepare` from `implement`/`replicate`, and tells the model
to execute its existing first_action rather than describe it in an outline.
Rejected SILO preparation submissions during implementation/replication now
return `preparation_only_action`, the public operation/assignment, the source-read
action and the required completion tool/fields. No source data, hidden answers,
correctness feedback or automatic reads are added. Every attempted action and
subsequent correction remains charged within the existing retry limit. Valid
preparation submissions remain available during preparation.

Regression tests reproduce all 12 bounded rejections, exercise a scripted
correction through charged source/shard reads and a real segment submission in
primary/repair/replication stages, and preserve preparation-only submission rules.
These establish runtime behavior, not real-model success. The prompt revision
changes calibration compatibility and requires a new source-pinned manifest.

The next step at this checkpoint was to create
`silo-smoke-v2-manifest.json` with the same SILO data and model lock, inspect its
one-GPU dry run and run the clean smoke after syncing the change. That run is
recorded above. Preserve the failed result. Larger SILO
pilots remain pending clean model competence; no GPU execution or push was
performed from this workspace.

Validation after the operation-guidance change:

- `python -m unittest discover -s tests -v`: 122 tests, 121 passed and one
  existing opt-in legacy sandbox integration skip.
- `python scripts/check_shell.py`: all nine shell files passed.
- `git diff --check`: passed.

## Second SQLite fixture pilot passed (2026-09-17)

The user reported that the revised pilot ran with four GPUs in `PA100q`, after
cancelling the pending `NA10040q` submission. Experiment
`d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd`, using
`sqlite-pilot-v2-manifest.json`, completed with **32/32 task successes**. The
successful submission's job ID, snapshot and actual GPU hardware inventory have
not been supplied. This is user-reported cluster evidence, not an independently
inspected remote run.

| Policy | Clean successes | Withholding successes | Withholding ASR_cc | Total withholding repair work |
| --- | ---: | ---: | ---: | ---: |
| Ordinary | 4/4 | 4/4 | 0/4 | 26445 |
| JIT | 4/4 | 4/4 | 0/4 | 26429 |
| Recovery | 4/4 | 4/4 | 0/4 | 26429 |
| Replication | 4/4 | 4/4 | 0/4 | 400 |

The aggregate reports complete coverage, no missing/retryable shards, no budget
exhaustion, integration failures, false alarms, detected-but-unfinished cases or
reserve violations. Preparation and historical work are zero in every group.
Clean groups each retained 16 artifacts over four episodes; withholding groups
retained 12 for ordinary/JIT/recovery and 16 for replication.

Compared with the preceding pilot, clean success rose from 2/4 to 4/4 for every
policy; ordinary/JIT/recovery withholding success rose from 1/4 to 4/4, while
replication remained at 4/4. The revised shared instructions/observations and
the deployment partition both changed. This is a successful engineering rerun,
not an isolated causal estimate of the prompt change. It covers four synthetic
source groups under Protocol A and remains explicitly non-confirmatory.

The user subsequently supplied the eight grouped cost rows from saved episode
results. All work below uses `token_tool_surrogate_v1`, not seconds or FLOPs.
Each row contains four episodes; planned preparation counts are zero throughout.

| Policy | Condition | Mean total work | Mean replication work | Planned replicas (total) | Tool rejections (total) |
| --- | --- | ---: | ---: | ---: | ---: |
| Ordinary | Clean | 22111 | 0 | 0 | 1 |
| Ordinary | Withholding | 21715.5 | 0 | 0 | 0 |
| JIT | Clean | 22111 | 0 | 0 | 1 |
| JIT | Withholding | 21711.5 | 0 | 0 | 0 |
| Recovery | Clean | 22367 | 0 | 0 | 1 |
| Recovery | Withholding | 21967.5 | 0 | 0 | 0 |
| Replication | Clean | 37470.75 | 15151.75 | 16 | 1 |
| Replication | Withholding | 26682 | 11299.75 | 16 | 0 |

Replication used 69.47% more total work than ordinary on clean tasks and 22.87%
more under withholding, with the same success rate. Its smaller repair bill
therefore did not yield lower total work in this pilot. Recovery used 256 more
work units than JIT in each condition; no preparation was selected. JIT's
withholding mean was only four work units below ordinary. These descriptive
differences establish no general policy ranking or preparation benefit.

There were four recorded tool rejections, one in each clean policy group, and
none under withholding. Every episode still succeeded. These counts do not
identify the rejected action or demonstrate four independent error mechanisms;
that would require event traces. The original aggregate attachment contained no
stderr log contents. Withholding can skip primary/duplicate execution, so its
lower total work does not by itself show that repair was free or easier.

The grouped cost/rejection audit is complete. Preserve the prior failed pilot. The
bounded SQLite clean/withholding fixture check is now satisfied; it neither
validates native LiveSQLBench tasks nor enables the still-gated data sabotage
condition. Native data/material review and a separate SILO clean smoke remain
the next task-family prerequisites. No further fixture patch is indicated by
this successful aggregate, and no runtime behavior was changed during its review.

Local review checks: `python -m unittest discover -s tests -v` ran 119 tests
(118 passed, one opt-in legacy sandbox integration skip);
`python scripts/check_shell.py` passed all nine shell files;
`git diff --check` passed.

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

The next step at this checkpoint was to build a new manifest for the
existing 32-episode SQLite fixture pilot, such as `sqlite-pilot-v2-manifest.json`,
and inspect its guarded dry run after committing/pushing/pulling the change.
The resulting successful pilot is recorded above. The one-worker smoke does
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

## Native 16K condition and read-history audit (2026-09-21)

CPU-only implementation validation: `python -m unittest discover -s tests -v`
ran 196 tests in 73.815 seconds, passed with one existing opt-in skip.
`python scripts/check_shell.py` validated nine shell files;
`python scripts/check_docs_shell.py` validated the existing 46 blocks/four
embedded scripts; explicit checking of `docs/NATIVE_CONTEXT16K.md` validated
five additional blocks and one embedded Bash script. Compileall, stdlib-only
CLI help and `git diff --check` passed. New tests reject cross-context
qualification reuse, restrict 16K to the two-task native condition, check
synthetic long-history sizing and verify sanitized read-loop/context reporting.
No model, SQL benchmark, download or Slurm job was executed for this change.
Remote read-history evidence and 16K GPU fit remain pending. Historical native
context failures are documented in [NATIVE_CONTEXT16K.md](NATIVE_CONTEXT16K.md).

## Native 24-action profile and diagnostic archives (2026-09-21)

The final full CPU suite ran 198 tests in 64.990 seconds: 197 passed, one existing
opt-in skip. Focused 27B tests passed (15 tests). The initial suite exposed an
old string-substring privacy assertion: it matched the word `contexts` in the
new scope description. The assertion now checks for raw `contexts`/`messages`
JSON fields; explicit private-body/literal sanitization tests also pass. No
runtime privacy failure or score change was observed. Full suite rerun passed.
Nine shell files, existing 46 documentation blocks/four embedded scripts and
six new NATIVE_ACTIONS24 blocks passed syntax validation. Compileall, stdlib CLI
help and diff whitespace checks passed. No GPU model/benchmark or Slurm job was
run locally. The 24-action native condition is unexecuted.

Tests enforce the old profiles' limits, the new exact 24-action condition and
unchanged budget/model/retry settings. They exercise reset/restore archival,
export/restore round trips, legacy checkpoints, deep-copy independence, private
text omission and the exclusion of diagnostic archives from recovery candidates.

## Offline native failure replay (2026-09-22)

Full CPU regression: 203 tests in 72.056 seconds, 202 passed and one existing
opt-in skip. Five new focused tests passed, including a real restricted synthetic
SQLite child replay reporting an unresolved column without its identifier,
source integrity preservation, no raw comparison rows in reports, missing-history
handling, failed-call accounting and replay-call bounds. Nine shell files,
46 existing documentation blocks/four embedded scripts and the new audit's three
blocks/one embedded script passed checks. Compileall, stdlib-only CLI/help and
diff whitespace checks passed. No actual native/private solar replay, model run,
cluster submission, download, commit or push occurred locally. The new audit
requires explicit manual CPU Slurm execution; its results remain pending.

## Public SQLite interface audit (2026-09-22)

Added three synthetic restricted-executor controls for unbound aliases versus
bound/constant SELECTs, SUM arity, and division versus executable multiplication.
No native inputs, model calls, task-specific answer repairs or runtime behavior
changes were used. See [SQLITE_INTERFACE_AUDIT.md](SQLITE_INTERFACE_AUDIT.md).

Validation: `python -m unittest discover -s tests -v` ran **206 tests in
72.776 seconds: 205 passed, one existing opt-in skip**. The three focused tests
passed. `python scripts/check_shell.py` validated all nine shell files.
Isolated stdlib CLI help, test-file compilation and `git diff --check` passed.
No cluster jobs, downloads, commits or pushes were performed.

## Opt-in SQLite execution feedback (2026-09-22)

Added five focused tests for fixed-category privacy/fallback, explicit opt-in and
manifest/calibration identity, worker correction versus retry exhaustion in both
legacy and new modes, normal model/tool/SQL charges, terminal-path isolation,
four positive synthetic episodes, and rejection of mixed feedback provenance.
All five passed using scripted CPU workers; no actual model competence is claimed.

Full `python -m unittest discover -s tests -v`: **211 tests in 68.819 seconds,
210 passed and one existing opt-in skip**. `python scripts/check_shell.py` passed
all nine shell files. Isolated stdlib CLI help, new config loading and
`git diff --check` passed. No GPU execution, download, commit or push occurred.

## Matched supplied-draft correction diagnostic (2026-09-22)

Three focused tests passed: matched frozen tasks/config bounds; real restricted
CPU execution with scripted correction, seed/tool/model accounting, equal initial
histories, paired report, and completed-resume non-reexecution; and repeated bad
model actions exhausting the unchanged retry count with terminal failed scores.
These are synthetic engineering controls, not new model results.

Full suite: `python -m unittest discover -s tests -v` ran **214 tests in
80.808 seconds: 213 passed, one existing opt-in skip**. All nine shell files,
46 existing documentation blocks/four embedded scripts, and the new runbook's
two shell blocks passed syntax checks. Compileall, isolated stdlib correction-audit
CLI help and diff whitespace checks passed. No GPU job, download, commit or push.

## Consolidated progress review (2026-09-22)

Created PROGRESS_REPORT_2026-09-22.md and recorded the user's review pause in
STATUS.md. Cross-checked recent 27B experiment IDs, statuses and costs against
uploaded reports; verified report links and work-total arithmetic. Documentation
only; no runtime, scoring, historical output or task changes.

Regression suite: **214 tests in 81.991 seconds, 213 passed and one existing
opt-in skip**. All nine shell checks and diff whitespace checks passed. No
cluster job, download, commit or push occurred. The paired correction experiment
remains prepared with no reported cluster submission/result.

## 2026-09-22 SQL front end / finite graph implementation

- Full suite with the optional pinned SQLGlot installed in `/tmp/bc-sql-phase-env`:
  **222 tests, 221 passed, one existing opt-in legacy skip** (final full run: 106.701 seconds).
  A subsequent focused matched-config test also passed after tightening nested
  model/budget field-presence checks.
- The separate compiler qualification passed all four test methods with zero
  skips: 25 supported synthetic query cases, rejection/resource cases, protected
  runtime integration, charged construction failures, and valid-but-wrong scoring.
  It executes only trusted synthetic SQL; it is not a native reference approval.
- The existing nine shell files passed validation. `compileall`, isolated
  stdlib-only CLI help and `git diff --check` passed.
- Constructed finite graphs execute through the existing engine in clean and
  withholding conditions and preserve completed-run resume. Cost selection tests
  use explicitly constructed estimates, including an independent-plan win.
- The optional parser was a 524-kB wheel, SQLGlot 27.28.1 (MIT), installed only in
  a temporary local environment. No GPU packages, model weights or data archives
  were downloaded. The stdlib-only environment skips optional-parser tests.
- No actual 27B tokenizer/XGrammar, Slurm/GPU, renewed private native reference,
  native paired-interface, real planner-generation or calibration run was executed.
  See the phase runbook for remaining implementation and external prerequisites.

### 2026-09-23 follow-up review

Reference front-end qualification now blocks missing or extra reference obligations
before parsing, including a partially populated evaluation map. A mocked coverage
regression checks this gate without private data. Corrected the parser resource
limit description: a file-size limit does not prohibit creating files.

Full optional-parser suite: **223 tests in 100.660 seconds, 222 passed and one
existing opt-in skip**. Nine shell checks, compileall, isolated stdlib-only CLI
help and diff whitespace checks passed. No cluster jobs or new research results.

### SQL-text masked-token diagnostic

Added failure details only to the offline synthetic decoder checker after the
user-reported cluster failure. Standard-library environment regression run:
223 tests in 87.683 seconds, 219 passed and four skips (optional parser and legacy
integration). Nine shell checks and diff whitespace checks passed. Actual
Qwen tokenizer/XGrammar reproduction remains pending on the cluster.

### SQL-string escape projection fix

Full optional-parser suite: **224 tests in 110.543 seconds, 223 passed and one
existing opt-in skip**. Seven focused action-constraint tests passed, including
runtime oversize rejection and separate decoder projection provenance. Shell
checks, compilation, stdlib-only checker help and whitespace checks passed.
Actual XGrammar/Qwen controls remain cluster qualification work.

### Historical native feedback compatibility

Four focused plan/coverage tests passed. Full optional-parser suite: **226 tests
in 98.834 seconds, 225 passed and one existing opt-in skip**. Regression checks
cover input immutability, explicit-setting preservation and rejection of altered
experiment/source/config provenance. Historical source digest reconstructed from
Git matches the user-reported baseline. Nine shell checks passed; no inference or
SQL execution was used to resolve the missing feedback field.

### Synthetic preflight failure evidence

Three focused mocked probe tests cover invalid JSON/action envelopes, compiler
rejection without database access, executor failure, wrong rows and successful
rows. Full optional-parser suite: **229 tests in 95.897 seconds, 228 passed and
one existing opt-in skip**. Nine shell checks and whitespace checks passed.
The historical failed synthetic generation was not recoverable from the supplied
report; no new GPU result is claimed.

### Explicit synthetic probe envelope

Four focused preflight-report tests passed, including generation-limit and
incomplete-action rejection without compiler access. Full stdlib environment
suite: **230 tests in 74.124 seconds, 226 passed and four skips** (optional parser
and opt-in legacy integration). Nine shell checks, compileall and whitespace
checks passed. No real tokenizer/model generation was run locally. The temporary
optional-parser environment from earlier turns is no longer present.

### SQL-text naming instructions

Two focused regression tests verify the actual DataDomain text prompt has
SQL-string query examples accepted by the public envelope schema, retains exact
version binding instructions, removes the tree column-object hint, and leaves
tree/SILO prompts unchanged. Full stdlib suite: **232 tests in 80.466 seconds,
228 passed and four skips** (optional parser and legacy integration). Nine shell
checks, compileall, isolated CLI help and diff whitespace checks passed. No new
GPU/model or native SQL evaluation was run.
