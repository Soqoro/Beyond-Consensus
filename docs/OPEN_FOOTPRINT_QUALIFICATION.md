# Task-free open-planning footprint qualification

## Decision and status

The task-free CPU preparation and GPU preflight runner are implemented. This
is not a runnable task manifest or a completed qualification. Implementation
does not authorize GPU submission. The production open-planning dispatcher
remains blocked. No task, reference solution, evaluator, or source repository
is used by these probes.

The proposed experiment is **bounded representation and observation delivery**.
It does not measure whether the model can invent a useful decomposition. Copying
a supplied synthetic plan cannot establish autonomous planning competence.

## Evidence carried forward

| Record | Result and scope |
| --- | --- |
| CPU directory `rr-open-fix.T7sJw0`, source `f4c25a0c028cbb2e730f791eff9e753b8335b3fa` | User supplied passing fixture and scoped worker/planner grammar summaries. |
| Preflight `c634622159286dcc20ce6424c4f0f5da0cb160d3d40b2dfb29ce861dc11c6d9e` | 16/16 normal actions passed, pool seven, one model, A100-SXM4-80GB; 237560 tokens. No full-budget stress or task execution. |
| `provenance.SLY9HD/audit.json` | Internal snapshot/manifest/lock/runtime bindings verified, errors empty. The full uploaded report was reviewed. |
| Slurm `1087371_0` | Separately supplied accounting shows COMPLETED, exit 0:0, elapsed 00:19:43. The offline audit itself does not query Slurm. |
| Proposal `2b050af79f31234bd9607cdb6244b321145f00069f0ddd72f9300e944cd78388` | Blocked engineering proposal derived from historical stock experiment `853f0646ce1fab388c6da48b4270297eb763009e5041bd4d081c758c6f7cff06`. |

The proposal lives at
`/dataset/suaq0001/beyond-consensus/diagnostics/rr-open-fix.T7sJw0/open-proposal.8_kl771z`.
Its unchanged blocker list is not a claim that the supplied CPU and grammar work
was never performed. That evidence must be linked and reviewed against the
implementation used by this new qualification. Do not edit the old proposal or
audit to clear blockers.

## Frozen settings

- Qwen/Qwen3.5-27B, revision/tokenizer
  `fc05daec18b0a78c049392ed2e771dde82bdf654`, BF16, thinking enabled,
  `do_sample=false`.
- Context 16384; per-call output 2048, **including reasoning**. Each dispatched
  prompt must fit within 14336 rendered input tokens. Do not truncate histories.
- Worker grammar `reporecourse-json-scoped-v1-pool-7`; planner grammar
  `reporecourse-plan-scoped-v1-pool-7`. One model instance, one allocated GPU,
  sequential calls, fresh generation caches.
- No change to task engineering caps (100000 tokens / 1200 CPU seconds).
  Qualification accounting is separate and must not be added to a historical
  task ledger or treated as B0 calibration.
- No automatic retries, cap increases, smaller replacement plans or selection
  of the best response. A revised probe is a new version with new evidence.

## CPU preparation: exact synthetic cases

Before inference, generate and freeze all cases and their expected actions.
Use the existing `v2.validate_work_plan` and scoped runtime; do not introduce a
parallel permissive plan validator or hand-written approximation of observations.

The synthetic public contract has one source named `probe_source`, containing
only the sentence “Synthetic qualification source; no task implementation.” It
has one terminal obligation `probe_result`, format `schema`, and no examples,
database, hidden evaluator, repository source, or reference program. Intermediate
names are `artifact_00` etc.; unit names are `unit_00` etc. This is authored
qualification material, not a benchmark task or a catalog addition.

| Case | Fixed construction | Required model response |
| --- | --- | --- |
| `plan_02` | Two-unit chain; owners cycle through w0..w6. | Complete `submit_plan` envelope matching the supplied plan. |
| `plan_07` | Seven-unit chain; all seven owners represented. | Complete matching `submit_plan` envelope. |
| `plan_24` | Twenty-four-unit chain; owners cycle through w0..w6. | Complete matching `submit_plan` envelope. |
| `scope_empty` | Fresh scoped assignment, no permitted imported artifacts or messages. | `{"tool":"read_source","name":"probe_source"}` |
| `scope_imports16` | Sixteen independent schema producers followed by a consumer with 16 explicit version imports; one additional unrelated producer is present. | Read the exact version bound to consumer alias `input_00`. |

For each chain, a unit produces its own named `schema` artifact. Except for the
first unit it consumes the previous artifact through alias `input`, with exactly
that predecessor in `depends`. Only the last unit lists `probe_result` in
`outputs`, mapping it to its own artifact in `terminal_bindings`. Other terminal
mappings and outputs are empty. Every unit includes source focus
`["probe_source"]`, description “Carry the synthetic interface forward.” and
interface prose “Synthetic schema artifact.” The plan schema is
`rr-work-plan-v2`; plan IDs equal the case IDs. Include all fields required by the
scoped planner grammar. No schema implementation is requested from the planner.

For the import observation, publish inert boolean schemas through the existing
trusted runtime actions without executing them. Record exact versions and let
`AssignmentScopes` and `Environment.observation` construct the observation.
The unrelated version is a negative visibility control: it must not appear in
delivered artifact metadata, bindings or messages. The expected read refers to
the import version produced during this CPU preparation, not a fabricated hash.
Both observation cases use a fresh assignment history. Original public sources
remain accessible. This is a selected scoped-observation test, not coverage of
all restore, message, repair, or long-history states.

## Token and grammar measurements before GPU work

Use the exact frozen tokenizer and chat template offline (`local_files_only`),
without loading model weights. Record serialized UTF-8 bytes and tokenizer counts
for every complete expected action, including the `submit_plan` envelope and one
valid stop token. Record the actual rendered prompts and their token counts.
Use the existing planner/worker message construction, with an explicitly labelled
qualification instruction appended to request the fixed response. Hash that
instruction and the resulting prompts; do not change production task prompts.

Feed each expected action and stop token through its qualified grammar and
check acceptance. Structural validation and grammar acceptance are separate
fields. A structurally valid plan may still exceed the output cap.

If an expected action plus stop exceeds 2048 tokens, mark the case
`output_representation_exceeds_cap` and do not dispatch that case. This is a
measured incompatibility of the tested serialization with the configured cap,
not proof that every equivalent plan is impossible to serialize more compactly.
If the prompt plus reserved output exceeds 16384, mark
`input_reservation_exceeds_context` and do not truncate it. No failing case can
be dropped from the final qualification decision.

CPU results must list unmeasured token counts as null until measured; bytes are
not token estimates. Passing representation checks does not establish room for
reasoning. Small generated outputs in the earlier preflight are not substitutes
for these measurements.

## Bounded GPU phase and pass criteria

GPU submission follows review of the CPU packet and an explicit user decision.
Use the existing shared registry, scheduler inspection and frozen-source snapshot
workflow. Concurrency is one; all calls share the same allocation/model. Do not
dispatch task branches or call the production open-task entry point.

At most **five calls**, one per case, seed 0. Each call reserves its actual input
plus 2048 output tokens. The declared maximum is therefore 81920 logical tokens;
report actual tokens, reasoning tokens, uncertain reservations, model-host CPU,
decoder CPU, setup CPU, device time, wall time and allocated/reserved VRAM
separately. Preserve the existing decoder CPU allowance of 30 seconds per call.
Use a two-hour batch wall limit as an engineering bound, not a runtime prediction.
An interrupted call retains uncertain accounting and cannot pass.

A case passes only if all of the following hold:

1. Its CPU structural, grammar and context/output representation checks passed.
2. Generation ended at an allowed EOS, with a complete constrained action and
   no error, uncertain usage, silent truncation or output-limit stop.
3. JSON parsing rejects duplicate keys. Parsed plan actions match the frozen
   expected plan (object key order/whitespace may differ) and pass the actual
   structural validator. Worker actions match the exact expected action.
4. Observation visibility controls pass, including absence of the unrelated
   artifact. Version binding is exact; no prefix/name substitution is accepted.
5. Resource use and runtime/model/grammar/source bindings are recorded without
   contradictions. Calls beyond the declared count are failures, not retries.

The overall status is `passed_observed_cases` only when **all five** pass.
Otherwise retain the per-case failures and report `failed` or `incomplete`.
Do not replace the 24-unit case with a shorter success. Execution/resource errors
must remain distinguishable from representation and generation failures.

## Evidence packet and interpretation

Prepare a new immutable packet with the proposal ID, input file hashes, model
and tokenizer metadata/weights, both grammar qualification keys, source revision,
protocol version, synthetic public contract, case definitions, expected actions,
prompt hashes, CPU measurements and negative-control outcomes. The GPU report
adds the resolved snapshot, scheduler identity and per-call generation/resource
records. A later offline audit must verify those bindings; an opaque success flag
is insufficient. None of these records are approval tokens for the task runner.

Even a complete pass leaves these fields false:

- `task_execution_allowed`
- `campaign_allowed`
- `task_competence_measured`
- `autonomous_planning_competence_measured`
- `worst_case_fit_established`

These five samples do not cover maximum-length descriptions, every legal graph,
24 artifacts per unit, transitive import closures, accumulated messages or all
eight planner turns. No claim of universal 24-unit capacity is permitted.
The exact generated task plan and subsequent histories still need fail-closed
context/resource admission. Clean scoped task execution requires its own reviewed
implementation and approval; the preselected loss branch additionally requires
clean conformant success review and separate approval. No budget, model,
topology bound or task success criterion is changed by this specification.

## Implemented entry points and next CPU step

- `scripts/prepare_rr_open_footprint.py`: stdlib case preparation by default;
  explicit `--measure` uses the offline tokenizer and decoder on a CPU batch
  allocation. It loads no model weights. Reports are written to fresh paths.
- `bc.py rr-open-footprint-manifest`: freezes a measured CPU packet and its lock
  into `rr-open-footprint-manifest-v1`, separate from existing preflight schemas.
- The existing `submit --mode preflight` route enforces one GPU and the shared
  registry. `run` rejects the new manifest before loading a backend. The manifest
  cannot be used for task episodes, campaign conditions or automatic retries.
- The new report is `rr-open-footprint-report-v1`. Failed CPU cases remain present
  as undispatched failures; partial GPU success cannot produce an overall pass.
- Shared planner/worker message helpers preserve production prompt content;
  only this diagnostic appends the fixed qualification instruction. Both old
  preflight modes reuse the same backend initialization as before.

Freeze the reviewed source into a new directory using the existing browser
terminal workflow. In that CPU allocation, run (paths must identify the frozen
source and the current scoped locks):

```bash
"$BC_PYTHON" -I "$BC_FOOTPRINT/source/scripts/prepare_rr_open_footprint.py" \
  --proposal "$BC_OPEN/open-proposal.8_kl771z/proposal.json" \
  --model-lock "$BC_OPEN/cpu/model-lock-json-pool-7.json" \
  --planner-lock "$BC_OPEN/cpu/model-lock-plan-pool-7.json" \
  --measure \
  --output "$BC_FOOTPRINT/cpu-packet.json"
```

Keep the proposal and prior audit intact. The qualified locks must still pass
current qualification-key verification; do not replace their keys manually.
A source change after measurement requires a new packet. An optional stdlib
preparation without `--measure` leaves token counts null and cannot be used to
build a GPU manifest. Measured CPU failures produce a report and exit code 2;
inspect the individual reasons instead of treating them as missing output.

Review the CPU packet first, especially `plan_24`. No token measurement or GPU
result for this protocol has been obtained locally. The pinned optional stack
is not available in the local test environment. No GPU submission command is
provided at this stage. After the CPU review, a separately authorized preflight
can measure eligible cases; even a complete pass grants no task permissions.


## Measured output-cap failure: offline review

The user-supplied packet `d8b8502e01c6dfccf66f00d3872438e021f409418aa5d355df8eabd95483dfe2`
reports 2125 action-plus-stop tokens for `plan_24`, exceeding 2048 by 77.
All five grammars and context reservations passed; no model inference occurred.
The job's exit 2 is a measured case failure, not evidence that the CPU runner
crashed. Preserve this packet and do not repeat the unchanged measurement.

The new read-only review compares candidate planner output allowances with
recorded token counts. Default scenarios are **not recommended new settings**:

| Candidate planner cap | Headroom after this 2125-token action | Maximum planner input at context 16384 |
| --- | ---: | ---: |
| 2048 | -77 | 14336 |
| 3072 | 947 | 13312 |
| 4096 | 1971 | 12288 |

Headroom must accommodate any reasoning, delimiters and serialization differences.
No such usage has been measured for complete-plan generation. The tool reports
hypothetical combined reserves of 0, 512, 1024 and 2048; they are not quantiles,
calibration or predictions. The 24-unit case fits the 1024-reserve arithmetic
at 4096 but not 3072; it does not fit a 2048 reserve at either candidate. Existing
approximately 14k-input preflight evidence cannot qualify those larger output
reservations within a fixed 16k context. Short observed footprint prompts do fit
those reservation sums; this says nothing about accumulated planning histories.

After pushing/pulling the review script, run on Jupyter without a batch job:

```bash
cd "$HOME/Beyond-Consensus"
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_CAPACITY="$(mktemp -d "$BC_STORAGE/diagnostics/rr-planner-capacity.XXXXXX")"

"$BC_PYTHON" -I -S scripts/review_rr_planner_capacity.py \
  --packet "$BC_STORAGE/diagnostics/rr-open-footprint.kjzVxE/cpu-packet.json" \
  --planner-caps 2048 3072 4096 \
  --non-action-reserves 0 512 1024 2048 \
  --output "$BC_CAPACITY/review.json"
```

This reads the original full packet and emits a fresh report; it runs no tokenizer,
model, SQL, scheduler command or historical runtime code. It cannot independently
authenticate the source files or scheduler history. Worker output stays 2048;
`selected_planner_output_cap` and `measured_reasoning_tokens` remain null.
A candidate's arithmetic fit never changes `task_execution_allowed` or grants
GPU submission. Current decoder qualification keys and the synthetic runner bind
output 2048. A later allowance change needs an explicit versioned contract and
fresh compatible evidence; manually changing old locks/manifests is invalid.
