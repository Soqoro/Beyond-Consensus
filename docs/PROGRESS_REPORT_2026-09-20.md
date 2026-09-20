# Beyond Consensus — progress report for audit

**Report date:** 2026-09-20  
**Status:** experiments paused for user audit; no next model or campaign selected.  
**Purpose:** consolidate work completed, observed results and limitations before deciding what to do next.

## 1. Executive summary

The research objective is to test whether recovery-aware division of labour
improves complete-task success under contributor compromise at equal total work.
**The current evidence does not establish that advantage.**

Implemented infrastructure supports frozen model/data manifests, guarded Slurm
submission, resumable episode journals, charged work, four worker identities,
restricted SQLite artifacts, a labelled SILO adaptation and separate terminal
scoring. Numeric and arithmetic SQLite fixture campaigns have passed engineering
checks. Recovery selected no preparations in the reported fixture pilots; a
historical recovery/JIT cost gap was traced to planning charges.

Moving beyond fixtures exposed clean-task competence and interface problems:

- SILO original and actual-carry controls both achieved **0/8 complete tasks**.
- Four recorded two-task native solar controls each achieved **0/2**.
- Synthetic SQL tool probes progressed from **0/4** to **1/4** with reasoning,
  then remained **1/4** with constrained actions. The last run improved public
  integration from 1/4 to 3/4, but did not improve complete-task correctness.
- The final CASE output had correct row values but lacked the required column
  alias. Aggregate used the wrong operations; join repeated aliases and then
  exhausted reasoning tokens; view passed.

These observations do not justify a broad policy campaign, a general assertion
that the model cannot do SQL, or a claim that another model will solve the problem.
A stronger-model comparison was discussed, **not selected or executed**. The
current user instruction is to audit first. No further run is authorized by this
report or by the historical command sequences it links.

## 2. Evidence boundaries

| Evidence category | What is available | Limitation |
| --- | --- | --- |
| User-reported cluster evidence | Pasted preflights, aggregates, cost reports, traces and CPU qualification output | The agent has not independently accessed or replayed the full remote output directories |
| Local implementation verification | Repository code, scripted CPU regressions, CLI/shell checks and previously recorded local reference controls | Scripted workers and decoder doubles are not model results |
| Interpretation | Error attribution from explicit actions, returned rows and scorer code | Distinguish observed behavior from inferred causes; no causal or statistical claim follows from these small comparisons |

This report consolidates the conversation and [validation history](VALIDATION.md).
It adds no model results. Raw private author SQL/test material is deliberately
excluded. Hashes below are **reported bindings**, not a claim that the remote files
were downloaded and rehashed during this audit preparation.

## 3. Research and execution setup

- Main checkpoint: **Qwen/Qwen3.5-4B**, model/tokenizer revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
- Reported GPU stack: Python 3.12.10, torch 2.10.0+cu126, Transformers 5.3.0,
  BF16; reported preflights used A100 40 GB devices. PA100q was used for later
  submissions. Do not infer the exact GPU/node for every campaign from preflights.
- Main cluster storage: `/dataset/suaq0001/beyond-consensus`.
- Four persistent identities share one frozen model per allocated GPU. The
  single-policy tool probes use w0; they are not a four-worker collaboration test.
- Protocol A compares equal total work allowances. Protocol B is a separate
  equal-remainder diagnostic and must not be pooled with A.
- Reported work is `token_tool_surrogate_v1`, not wall time, GPU-hours or FLOPs.
  Completion status means the episode finished; success requires terminal scoring.
- All reported research results remain development/nonconfirmatory. Source groups
  and repeated tasks, rather than raw episode counts alone, determine independence.

## 4. Work completed

### Infrastructure and initial coding path

The cluster environment, storage paths, pinned model staging and GPU preflight
were established. The submission workflow freezes a clean checkout, logs source
and model bindings, uses a shared per-user registry and checks scheduler state.
The campaign guard permits at most four GPUs and one active campaign.

CooperBench repository execution was investigated but **not qualified or run**.
The site Apptainer initially lacked `libsubid.so.4`; a private installation later
passed basic namespace/file-visibility/network probes, including on node13.
Those probes did not establish the full required execution boundary.

Job 1076414 found no delegated cgroup parent. Job 1076418 showed CPU affinity
confinement, but no finite inspected ancestor memory/swap/process caps for its
requested 2 GiB allocation. This is evidence about that allocation, not every
node or all possible scheduler mechanisms. The legacy sandbox gate was retained.
PBS, personal GPU, Colab and rental alternatives were discussed but not validated
as migrations. The current restricted data path requires none of those services
or container/delegation facilities.

### Restricted SQLite and SILO path

Implemented fixed trusted SQLite execution of validated JSON query trees,
version-bound query/view artifacts, source integrity checks, public monitoring,
private terminal evaluation and explicit native/pair/fixture provenance.
Generated SQL strings, arbitrary worker programs and upstream test functions are
not executed on the host. Restricted data tools are not an OS sandbox.

The SILO recoverable-contributor adaptation preserves original shard obligations
and labels its changed access/scheduling semantics. Numeric fixtures remain
engineering diagnostics; they are not renamed as native benchmark evidence.

### Corrections and diagnostic additions

| Change | Trigger and purpose | Important limit |
| --- | --- | --- |
| Valid JSON examples and source/assignment guidance | Workers copied pseudocode, used wrong source IDs or repeated another assignment's answer | Prompt changes confound before/after comparisons |
| Public document catalogue | Native workers reread requirements without finding public definitions | Titles are not gold-selected hints; discovery did not yield task success |
| Tokenizer turn-ending correction | Model EOS 248044 differed from chat turn EOS 248046 | Stopping improved; later failures persisted |
| Public view resolution and DQS disabling | CREATE VIEW accepted an unresolved definition | Zero-row resolution is not value correctness or full runtime validation |
| Explicit public view output names | Detect missing required aliases where publicly declared | No hidden evaluator projections are used; not every query contract has this public check |
| Four synthetic tool probes | Separate basic action construction from document discovery | Simplified, repeatedly inspected development tasks; no native competence claim |
| Reasoning/2048 condition | Bounded change after the 0/4 tool run | Thinking, output cap and harness/public presentation changed together |
| Optional XGrammar action mode | Enforce syntactic structure after the reasoning close | Syntax cannot choose the correct operation, alias, join or artifact ID |

## 5. Results by task family

### 5.1 Numeric workflow fixtures

After an initial 0/1 smoke caused by malformed actions, the revised smoke passed
1/1. Two four-policy campaigns subsequently reported:

| Campaign | Successes | Source grouping / interpretation |
| --- | ---: | --- |
| Clean / withholding | 32/32 | Four tasks, two base pools; engineering fixtures |
| Clean / artifact sabotage | 32/32 | Same scale, repeated clean controls; engineering fixtures |

Reported preparation work/counts were zero. Replication reduced later repair work
while paying upfront duplication. No recovery advantage was observed. These
64 episodes are not 64 independent tasks, and numeric sabotage does not validate
native SQLite sabotage or CooperBench execution.

### 5.2 Arithmetic SQLite fixtures and policy-cost audit

A corrected smoke passed 1/1. The first 32-episode pilot completed all episodes
but had mixed success: clean 2/4 per policy, withholding 1/4 for ordinary/JIT/
recovery and 4/4 for replication. A later shared-instruction/assignment revision
ran on PA100q and passed **32/32** across four synthetic source groups.

Reported second-pilot mean work (four episodes per cell):

| Policy | Clean success | Withholding success | Mean clean work | Mean withholding work |
| --- | ---: | ---: | ---: | ---: |
| Ordinary | 4/4 | 4/4 | 22111 | 21715.5 |
| JIT | 4/4 | 4/4 | 22111 | 21711.5 |
| Recovery | 4/4 | 4/4 | 22367 | 21967.5 |
| Replication | 4/4 | 4/4 | 37470.75 | 26682 |

No preparations were selected. Replication planned 16 replicas per condition over
four episodes. Its smaller repair bill did not mean lower total work.
The saved-ledger audit reconciled all eight recovery/JIT pairs: the **256-unit**
gap was entirely finite-search charges, with zero non-search residual. This
establishes a charge attribution, not a general policy ranking.

The legacy planner enumerates a limited boundary/backup catalogue; it is not a
general task-partition optimizer. Independent fixture tasks can collapse boundary
alternatives to the same effective dependency graph. These design limitations
are recorded in [the research protocol](RESEARCH_PROTOCOL.md).

### 5.3 SILO clean controls

Early smokes exposed preparation-action misuse and cumulative-state errors.
The later eight-source comparison used the same frozen tasks and a carry field
that copied the actual predecessor submission, including errors—not a gold carry.

| Measure | Original interface | Explicit actual carry |
| --- | ---: | ---: |
| Complete-task success | 0/8 | 0/8 |
| Correct values | 101/480 | 101/480 |
| Public integration passes | 8/8 | 8/8 |
| Fully correct first segments | 6/8 | 6/8 |
| Later-segment incoming-state consistency | 1/24 | 6/24 |
| Within-segment increment errors | 21/448 | 7/448 |
| Charged work | 173439 | 185156 |

Local consistency improved, but complete-task/value correctness did not; all
101 correct values were in first segments. Carry cost about 6.8% more. Additional
runs of this setting were paused. These were clean single controls, not recovery
policy experiments or an unmodified upstream SILO evaluation.

### 5.4 Native LiveSQLBench solar materials and controls

Public metadata at revision `0664a2f28555faa0dd2947c8c23288df79bcc06b`
contained 270 records but no solution SQLs/test cases. Author-supplied private
materials were obtained and reviewed separately. Two tasks (`solar_2`,
`solar_M_3`) and the solar database/schema/knowledge documents were staged.

Both individual references passed reported cluster CPU positive/reset/source-
integrity and missing/corrupt-obligation controls. Earlier local controls also
validated one joint pair; the requested second pair was absent and remained
blocked. There is only one independent database group.

**Scorer qualification:** this is the reviewed `bc_livesql_native_v1`
reference-result adaptation, not full upstream evaluator parity. The review
records differences in ordering, duplicate handling, sampling, tolerance and
rounding relative to author test functions. Existing reference validations also
predate the changed executor fingerprint and need renewal before later native use.

| Native condition | Success | Required artifacts missing | Charged work | Main finding |
| --- | ---: | ---: | ---: | --- |
| Initial two-task control | 0/2 | 2 | 56867 | Repeated contract reads; no query/view submission |
| Public catalogue correction | 0/2 | 2 | 71489 | Some document discovery, still no final artifacts |
| Tokenizer EOS correction | 0/2 | 2 | 73320 | Stopping corrected; malformed query attempts and read loops remained |
| 24-action comparison | 0/2 | 2 | 131348 | Query hit malformed retry guard; view used all actions reading |

These reuse the same two development tasks. No aggregate “eight independent
native tasks” interpretation is valid. The reference-size audit measured complete
reference actions at **623 / 376 tokens including a stop**, below the 768 cap.
That proves those serializations fit, not that the model can produce them, or
that every prompt/document route fits. More actions did not improve success.

### 5.5 Synthetic SQL tool compatibility: three conditions

All four probes share one synthetic source group, use supplied schemas and
requirements, and require a submitted artifact. Exact result/column checks remain
terminal. Each condition has a 100000-work episode cap, 12 actions and 8192 context.

| Condition | Thinking | Output cap including reasoning | Correct tasks | Public integration passes | Missing required artifacts | Charged work |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Original free-form actions | Off | 768 | 0/4 | 1/4 | 3 | 23786 |
| Reasoning + corrected view validation | On | 2048 | 1/4 | 1/4 | 3 | 30715 |
| Schema-constrained actions | On | 2048 | 1/4 | 3/4 | 1 | 28649 |

The first transition is confounded by reasoning, output allowance, view validation
and public contract presentation. The second is a changed decoding/interface
condition, including fixed property order, whitespace bounds and CPU overhead.
Neither is a confirmatory causal estimate. The last condition spent about 6.7%
less surrogate work than reasoning-only; no end-to-end speedup is established.

## 6. Latest constrained run: detailed findings

Experiment: `d701d4b32a8d44d6d4b51a7b0df94a7ab1b7b53a98d996a69248f2f2c1b3ba80`.
All four episodes completed; no missing/retryable shards. Mean work 7162.25.

| Probe | Success | Work | Calls | Rejections | Detailed result |
| --- | --- | ---: | ---: | ---: | --- |
| Aggregate | No | 5704 | 3 | 0 | Grouped rows, but used amount + 0 and id + 0 instead of sum/count; submitted incorrect values |
| Join | No | 12280 | 3 | 3 | First action repeated the same join/alias eight times; two subsequent generations exhausted 2048 tokens before closing reasoning |
| View | Yes | 5130 | 3 | 0 | Complete valid artifact and correct final result |
| CASE | No | 5535 | 3 | 0 | Correct classifications and row order; required `sign_label` alias omitted |

For CASE, terminal failure is consistent with the documented requirement and
scorer, which compares columns and rows. This is **correct row values but an
incomplete output contract**, not incorrect classification logic. Keep the
complete-task score at 1/4; do not retroactively award an extra success.

Aggregate returned `[[1,4,1],[2,-2,3],[3,0,5]]`, confirming it did not compute the
requested sum/count. This was valid, executable query syntax with wrong meaning.

Join's first action was structurally complete. Repeated aliases are consistent
with its execution rejection; the generic worker error alone does not expose the
exact SQLite exception. The two retries had `reasoning_tokens=null`,
`constraint_complete=false`, `mask_calls=0` and `length_limit`. Null is unknown,
not zero: no closing reasoning delimiter was observed. The system correctly
blocked their execution. The pasted assistant text contains unfinished reasoning
and repeated query fragments; it is not a successful constrained final action.

Across the run, ten generations ended at EOS and two at the length cap. Public
integration passed three probes, terminal correctness one. Legacy
`integration_failures=3` means unsuccessful completed episodes, not three public
integration failures. `missing_artifact_observations=4` is not a count of four
missing required artifacts; the explicit missing-required count is one.

## 7. Decoder qualification and cost accounting

The user-reported CPU qualification passed **six positive and four negative
controls** using the staged tokenizer and XGrammar **0.1.32**, without model
weights, SQL execution or task inputs. Reported vocabulary size: 248320; stop
IDs: 248044 and 248046. It exercised token masks and the reasoning/action boundary.

Static grammar/tokenizer setup used **281.7705 CPU seconds**; total qualification
analysis used **307.9955 CPU seconds**. These are CPU time measurements, not wall
time or episode work. They supersede earlier “CPU qualification pending” notes.
The subsequent GPU run establishes observed operation of this constrained path
on the cluster; it does not qualify other models/tokenizers or all valid queries.

Within episodes, each constrained call reserves 30 CPU seconds at the tool rate
(300 work with current rules), then charges rounded-up measured decoder CPU.
Failed/unknown work retains the allowance. Generated reasoning and action tokens
remain charged within one cap. The latest reported 28649 total includes the
implemented episode accounting, but **per-call decoder CPU/charge rows have not
been supplied in the latest trace excerpt**; independent reconciliation remains
an audit item. Static setup is reported separately from task-specific work.
Therefore compare ledger work, measured setup and wall/device timing separately.

## 8. Audit questions and remaining evidence gaps

1. **Scientific scope:** Are native scorer adaptations and SILO scheduling/access
   differences appropriate for the intended claim? Explicitly review solar test
   parity, the absent second pair and limited independent source groups.
2. **Policy mechanism:** With no preparations selected in fixture pilots, which
   recovery mechanism has actually been exercised? Reconcile catalogue choices,
   calibration origin, reserve rules and the observed 256-unit planning charge.
3. **Model versus interface:** How much do bespoke JSON trees, fixed key order and
   generic error feedback affect behavior? A constrained wrong answer does not
   isolate intrinsic model capability. Do not select a new model based on a claim
   that these traces already prove another model will succeed.
4. **Output contract:** Preserve required aliases and all obligations. Decide
   prospectively whether separately labelled value/column diagnostics are useful;
   do not relax scores after seeing CASE's failure.
5. **Reasoning termination/history:** Audit capped reasoning handling and what is
   re-fed on retries. The trace shows incomplete reasoning stored as assistant
   text; its contribution to later repetition has not been causally measured.
6. **Cost fairness:** Reconcile decoder reservations, actual charges, interrupted
   calls, static setup and model tokens from raw ledgers. Surrogate-work changes
   do not prove throughput or deployment-cost changes.
7. **Public versus hidden information:** Verify the schema, feedback and public
   view checks contain no hidden evaluator information. Review CPU reference
   controls separately from worker competence.
8. **Metrics:** Distinguish execution completion, public shape/coverage/integration,
   semantic correctness, unknown observations and true missing obligations. Review
   whether legacy alarm/failure labels are easy to misinterpret on clean tasks.
9. **Development reuse:** Many prompt/interface choices followed inspection of
   the same small task sets. A later generalization claim needs a prospectively
   frozen evaluation design; these runs are not held-out confirmation.
10. **Provenance completeness:** Retrieve raw cluster manifests, snapshots, runtime
    metadata, checkpoints and full ledgers for independent audit. Latest actual
    batch job/node/GPU details were not supplied. No facts are inferred from a
    dry-run request alone.

No audit conclusion or next experiment is predetermined. Possible decisions—such
as revising the interface, testing another model, changing task scope or stopping
this direction—remain for the user after reviewing the evidence.

## 9. Provenance index and files to preserve

Remote output directories follow `/dataset/suaq0001/beyond-consensus/outputs/<ID>`.
These IDs identify conditions, not independent observations to pool.

| Condition | Experiment ID |
| --- | --- |
| Numeric corrected smoke | `d07eaf6b64fe4ec6393fb332f077fcb1bd2c7ee63f743c6d44ba8b08f8609e56` |
| Numeric withholding pilot | `e05c084a88b15e9f6675e9dfa18da40dee13ac1624cf324d5f807ed37830aeff` |
| Numeric sabotage pilot | `ddbf0217caa8fd82a3a4eea8dc7d6d5ddffe1194d4a6795f2b7227d56f492ab8` |
| SQLite first pilot | `ef27dbc828f47f76a631a68f9edbf9628b5510c1e0244e43ed26804bf4dfa3d5` |
| SQLite second pilot | `d9813ae52441c57c670dac7b564b1a81e6ea3cef01881a0a7455e301ef33d2fd` |
| SILO original eight | `7cd048f8209c217b2763cc711ed8ee91dc5cdca9c2ecaef8123e215da6252d79` |
| SILO actual carry eight | `455cb07b9f493a40abc7473d493266690339e32c7d0dd750d65e8dacb52b79ad` |
| Solar initial control | `39194c9de0eafc3e98c9cf02393afd7483f39476e36b61addf6afc2c6556b9f4` |
| Solar catalogue correction | `754c06ed06a51174619455ced15d592db875cbbdca1c39f15f157808801643c4` |
| Solar EOS correction | `cfb6d97fed8222c496b256acffa5880b3ba00a78cab355da0193ba575cd90fd3` |
| Solar 24 actions | `5f4bcf452b24b0b2f267cb9c327e8742042034dd02692ac872c87154c342ff4a` |
| Tools no thinking | `f082c0b74ce198653acac3d9d2ec955870d66e574f5d67bf436442adf60b195b` |
| Tools reasoning | `3996c58d44658d42f2d94fd08517884c606e068b798aac077118365d995dda63` |
| Tools constrained | `d701d4b32a8d44d6d4b51a7b0df94a7ab1b7b53a98d996a69248f2f2c1b3ba80` |

Latest condition bindings:

- Plan/qualification/cost directory:
  `/dataset/suaq0001/beyond-consensus/diagnostics/sqlite-constrained.fkQai1/`.
- Manifest hash: `99eeae34dfecf7a9bb8b9bdd66d2239303a034b82cd462eae1f131c0b79e2e05`.
- Observed-cost report ID: `f6ca1d2e0b666e621c97d9d9f0c5bf16bbe6d0d01ccdfc71c991e75bf797c396`.
- Source: `497f7ba08cf17a693480e34619dd4a95d60cfaf3:69759f99984dd2b39b754666fe2dca5d615ac85462d93a65635425deb09cf7e0`.
- Model-lock SHA-256: `beb4dcd0f1605695c54e21963cb6a70087b20a76e5c23b6f26571c15283604db`.
- Constraint schema SHA-256: `cc4e9b287e8027b11371a234503496974df0382ffc29d52ab1324ee33297a51d`.
- CPU qualification script SHA-256: `400f67e6df6a41630d46c4d9cc8aabb4ddbede93e71658c75d223373acdbcdb7`.
- Qualification control hash: `388ff4426b84c9bde1b3e9807253b3af0762237d9a02d9fc3e982259cd0d7bb3`.

Preserve each manifest/config, source snapshot and revision, model lock,
qualification report, installed dependency records, scheduler logs, per-episode
`result.json`, `checkpoint.json`, `events.jsonl`, and derived cost/aggregate reports.
Keep native author materials, private reviews and validated manifests in private
storage; do not commit them or include their contents in a public audit bundle.
Do not regenerate immutable reports over existing paths.

## 10. Local verification and audit handoff

The constrained-action implementation checkpoint recorded **183 tests: 182 passed,
one opt-in legacy sandbox test skipped**, plus nine shell checks. Those are CPU
software controls, not 183 successful model episodes. The remote CPU qualification
and GPU evidence described above are separate, user-reported results.

This report update changes documentation only. Current verification is recorded
in [VALIDATION.md](VALIDATION.md). No runtime/scorer/model/budget changes, new jobs,
model downloads, commits or pushes are made as part of preparing this report.
The audit is now the next activity; historical runbooks are reference material.
