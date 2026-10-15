# Beyond Consensus / RepoRecourse — Audit Report

**As of 14 October 2026, while the unique-key GPU preflight is pending**

## 1. Executive summary

We have built and exercised a restricted artifact execution system with generated planning, assignment-scoped worker access, exact artifact bindings, public monitoring, and recovery from persistent worker loss. Clean execution and recovery have succeeded on the demonstrated synthetic-stock cases, and an earlier Jaffle smoke also succeeded.

The subsequent four-task development cohorts exposed a substantial competence gap. Complete success remained low even after interface improvements. The latest completed assignment-interface cohort achieved **2/16 scheduled branch successes**, with all branches reporting conformance. Valid artifacts can still be semantically wrong.

Recent work isolated a second problem: **the native grammar could accept duplicate keys inside arbitrary JSON objects even though the strict parser correctly rejected them**. We implemented an opt-in decoder guard to prevent those keys before token selection. After correcting a tokenizer-normalized synthetic test, the cluster reported **151 CPU controls and all 44 native unique-key controls passed**.

**Current state:** the user reports the bounded unique-key GPU preflight is underway. Its result has not been received. There is no measured task-competence improvement from the new decoder yet.

## 2. Evidence basis and scope

This report consolidates repository audit/status records and cluster results supplied in the conversation. It is not a fresh independent inspection of the remote filesystem or a rerun of the experiments. No model, task SQL, or evaluator was executed to write it.

Sources include:

- [Implementation status](STATUS.md), including the latest response/decoder findings.
- [12 October audit](AUDIT_REPORT_2026-10-12.md), for historical milestones.
- [Four-task trace audit](RICH_COHORT_TRACE_AUDIT_2026-10-12.md).
- [8 October progress report](PROGRESS_REPORT_2026-10-08.md).
- [Research protocol](RESEARCH_PROTOCOL.md) and [current development runbook](UNREVIEWED_COHORT_RUNBOOK.md).

Older entries saying that the four-task experiment was unrun or that a unique-key lock did not exist describe earlier stopping points. The later results below supersede those statements for current status; the historical records remain intact.

Tests, scripted references, grammar qualification, task-free GPU probes, and model task outcomes are distinct evidence classes. Their counts must not be pooled.

## 3. What has been implemented

| Area | Capability and boundary |
| --- | --- |
| Restricted execution | Validated SQL text lowers into the approved query representation; workers do not execute arbitrary code or raw SQL directly. |
| Planning | Plans are validated and frozen before execution and target selection. Authored references remain distinct from generated plans. |
| Worker pool | Opt-in 2–8 logical identities; current pool-seven work shares one frozen model on one GPU. |
| Assignment scopes | Mediate tools, artifact visibility, observations, messages, and restored histories; original authorized sources remain available. |
| Artifact provenance | Exact versions and bindings, publication obligations, and retained execution evidence. |
| Recovery | Common public monitoring and JIT reassignment; worker loss persists across later assignments. |
| Accounting | Logical input/output tokens and separate CPU debits, including denied/failed operations and uncertain interrupted usage. Planning is charged logically per branch; physical reuse is reported separately. |
| Audit | Correctness, completion, budget, conformance, missingness, and intervention triggering are separate fields. |
| Submission | Frozen source, model/grammar locks, shared registry, scheduler inspection, and bounded concurrency. |
| Recent decoder change | Worker-only unique-key prefix mask intersected with the native grammar, with strict parsing retained. |

This is a restricted data/artifact workflow, not an operating-system sandbox or general repository-code agent. No controller training has been performed.

## 4. Earlier experimental milestones

These experiments used different tasks, configurations, and resource profiles. They are a development history, not a single comparable score series.

| Stage | Reported result | What it established |
| --- | --- | --- |
| 4B synthetic tool probes | 0/4 initially; 1/4 with reasoning; constrained condition also 1/4 | Formatting improvements did not establish reliable tool competence. |
| 27B synthetic tool probes | 4/4 in the earlier reviewed runs | Success on small compatibility probes, not native-task competence. |
| Matched native Solar JSON-tree arm | 0/2 | Both native tasks failed under that interface. |
| Matched native Solar SQL-text arm | 1/2 | A local improvement on two repeatedly inspected tasks. |
| Synthetic aggregation diagnostic | 1/2 | Independent-detail joins multiplied rows and inflated aggregates. |
| Initial Jaffle smoke | 0/1 | Published artifacts failed execution and repair did not finish successfully. |
| Corrected Jaffle smoke | 1/1 | Both obligations passed, using 29,745 tokens and 404.79 CPU seconds. |
| v0.2 scripted reference matrix | 188/188 branches; 56 conditions | Harness/reference behavior across pools 2–8 and four authored organizations, not model competence. |

Offline Solar inspection also found unresolved columns, missing obligations, incorrect executable candidates, and context-limit failures. A later unsubmitted candidate executed successfully but failed both exact and native comparison. Offline replay did not promote it or change its historical score.

## 5. Stock planning and recovery results

| Experiment / condition | Success and conformance | Logical tokens | CPU debit (s) |
| --- | --- | ---: | ---: |
| Open clean `151721…` | Passed | 7,476 | 208.01 |
| Conditional F(w0), `f6066e…` | Passed | 9,949 | 232.30 |
| Conditional F(w1), `f6066e…` | Passed | 10,802 | 245.37 |
| Prospective stock clean, `e10d7f…` | Passed | 9,120 | 169.30 |
| Prospective stock F(w0), same run | Passed | 11,849 | 196.63 |
| Prospective stock F(w1), same run | Passed | 12,723 | 211.66 |

Both conditional losses triggered and both obligations passed. Trace inspection distinguished reconstruction followed by exact-version consumption after w0 loss from source-based repair after w1 loss. A recorded artifact read alone did not establish executable reuse.

The conditional branches followed an observed clean success and therefore carry selection bias. The separate prospective stock run demonstrated the protocol on one synthetic request. Its 3,005 planning tokens were already included in each branch total; adding them again would double-count.

These results demonstrate engineering feasibility, not planner superiority or general robustness.

## 6. Four-task development cohorts

The cohort covers Jaffle payment release, Energy single-indicator release, GitHub topics client package, and GitHub multioperation integration. There are **four tasks across three source groups**; the two GitHub tasks are not independent repositories.

Runs used the explicitly labelled unreviewed-development lane. Independent task and rights reviews were not silently converted into approvals.

### Complete-success counts

Denominators below are the four scheduled tasks per planner/track cell. Invalid planning and unexecuted branches remain visible; a scheduled-condition denominator is not an executed-only success rate.

| Version / experiment | Requirement clean | Requirement F | Prompted-open clean | Prompted-open F | Total scheduled successes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial richer cohort `b9f84b…` | 1/4 | 0/4 | 0/4 | 0/4 | 1/16 |
| Interface reliability `5b2323…` | 0/4 | 2/4 | 1/4 | 0/4 | 3/16 |
| Assignment interface `dd7f95…` | 1/4 | 1/4 | 0/4 | 0/4 | 2/16 |

Additional observations:

- Initial cohort: three invalid prompted planning configurations; ten branches executed and reported conformance; five fault interventions triggered.
- Interface reliability: all four generated plans accepted on the first attempt; six scheduled faults triggered. Three CPU-exhausted branches retained checkpoint traces without final evaluation/conformance fields.
- Assignment interface: all sixteen branches reported conformance; all eight F interventions triggered. Two Jaffle/open branches exhausted token admission.
- Denied publication attempts fell from **84 to 7** between the latter two cohorts, while complete success fell from **3/16 to 2/16**. Fewer interface violations did not translate into higher observed task success.

The assignment cohort reported **816,353 logical tokens** and **9,386.019483016 charged CPU seconds**, including physical planning reused but logically charged in each branch. These are not GPU wall-time totals.

The cohorts were repeatedly inspected and changed prospectively. They are not independent replications or a controlled causal estimate of any one interface change.

### Concrete semantic defects found

Read-only inspection against public contracts found:

| Example | Defect | Reported component checks |
| --- | --- | --- |
| Jaffle requirement clean | Counting orders after joining payments multiplies orders with multiple payments. | Customer checks 1/4 |
| Energy requirement clean | Exclusion labels differed from the exact public labels. | Exclusion checks 0/3 |
| Topics requirement F | Consumer emitted an extra field although the public contract required exactly `topics`. | Consumer checks 0/2 |
| Multioperation requirement clean | Update output used `name` instead of `names`, also in its schema. | Update checks 0/4 |

These explain specific mismatches. They do not establish every cause of every failed branch. No audit candidate was repaired and fed back to workers or used to rescore history.

## 7. Qualification and planner-capacity work

The planner cap changed after measured representation and generation failures:

1. A representative 24-unit action required 2,125 tokens including stop, exceeding the original 2,048 cap before reasoning.
2. Initial 4,096-cap calls failed runtime admission; role admission was corrected.
3. With admission corrected, the 24-unit generation still exhausted 4,096 tokens.
4. At 6,144, all five observed footprint cases passed. The large response used 4,377 output tokens, including 2,252 reasoning tokens.

Current task configuration uses Qwen/Qwen3.5-27B at revision `fc05daec18b0a78c049392ed2e771dde82bdf654`, BF16, thinking enabled, deterministic decoding, 16,384 context, 2,048 worker output, and 6,144 planner output.

Task-free footprint probes passed on reported A100 80GB and H100 hardware in the documented runs. Later interface probes passed helper/terminal planning and schema/mapping/SQL publication cases. These are observed-case results, not worst-case fit or task competence.

Engineering branch caps of 100,000 tokens and 1,200 CPU seconds remain uncalibrated; they are not measured B0 budgets.

## 8. Response failure diagnosis

The assignment cohort recorded thirteen malformed-JSON failures: two length-limit endings and eleven normal EOS endings. Original exports could not distinguish duplicate keys from other parse errors and did not retain rejected response text.

Prospective diagnostics now retain bounded parse categories, hashes/lengths, syntax location, and generation metadata without exposing rejected text or duplicate-key text to workers.

A separate three-call reconstructed-input diagnostic (`8ede5e…`) produced:

| Call | Result |
| --- | --- |
| Requirement F | Parsed; 675 output tokens |
| Prompted clean | Parsed; 916 output tokens |
| Prompted F | Rejected for `duplicate_object_key`; 772 output tokens, including 577 reasoning; EOS |

Totals: **11,534 logical tokens**, **186.200644588 charged call CPU seconds**, **410.931751202 wall seconds**, zero uncertain usage. No returned action, SQL, or evaluator ran.

Reconstructed inputs differed by a few tokens from historical inputs. This is **not exact replay**, and the duplicate's location in the historical response remains unknown.

`constraint_complete` was found to be a post-generation strict-validation result, not a direct native matcher completion flag. EOS with that flag false did not establish a premature-EOS or reasoning-gate bug.

## 9. Native duplicate-key finding and correction

### Confirmed grammar/parser gap

CPU boundary audit `rr-decoder-boundary.A87RdN` compared native matcher acceptance, logits masking, stop acceptance, and strict parsing across both stop IDs and both reasoning routes:

| Synthetic case | Observation |
| --- | --- |
| Valid mapping | Accepted |
| Duplicate envelope property | Blocked |
| Nested duplicate property | Grammar accepted; strict parser rejected |
| Escaped-equivalent duplicate property | Grammar accepted; strict parser rejected |
| Incomplete JSON | EOS blocked |

This confirms a synthetic grammar/parser mismatch, not the exact provenance of every historical malformed response.

### Opt-in prevention

Implemented `reporecourse-json-unique-v1-pool-7`, a worker-only mode. An object-local byte-prefix state machine intersects the native token mask before selection. JSON escape decoding defines key equality. It handles nested objects, sibling objects, arrays, split UTF-8, and surrogate pairs.

It does not normalize Unicode, remove keys, repair responses, use last-key-wins parsing, force reasoning termination, or alter old decoder modes. Guard CPU is included within the existing measured decoder interval and 30-second allowance.

### NFC qualification failure and resolution

The first native qualification failed token-byte round-trip checks after 148 CPU controls passed. No qualified lock was issued.

A short tokenizer probe isolated positive case 4: input NFC normalization collapsed a literal decomposed key into its precomposed counterpart. Native vocabulary bytes and HF decoding agreed. This was a synthetic-control encoding problem, not evidence that the native byte decoder was wrong.

Only the test's serialized spelling changed: the combining mark is now a JSON escape, preserving distinct parsed keys while keeping the serialized control NFC-stable. Runtime key semantics and strict round-trip checks remain unchanged.

### Latest completed cluster qualification

Directory: `/dataset/suaq0001/beyond-consensus/diagnostics/rr-unique-nfc.lOjYvr`

Source: `14d56d497ece7f9f16769e6fb95d90404b8a7949`

| Check | Reported result |
| --- | --- |
| CPU controls | 151 passed; zero skips, failures, errors |
| Worker grammar | Passed; 16,384 context / 2,048 output |
| Native unique-key matrix | 44/44 passed; no mismatches |
| Maximum per-case decoder CPU | 0.35181015999998166 seconds |
| Qualified worker lock | Present |
| Model generation | Not performed |

Qualification key: `57ee87220bbe1a520e233d95297fedcedd7e405ad3520fcc7e5f65a2c0200960`.

## 10. Current pending job

The prepared `rr-unique-preflight-manifest-v1` runs three fixed synthetic calls:

1. Nested mapping keys.
2. Escaped Unicode keys.
3. Mapping after a 14,080–14,336-token input.

Bounds: one model/GPU, three calls maximum, 2,048 output tokens per call, no task inputs, no action execution, no evaluator, no automatic retry. Reports retain generation diagnostics, memory observations, token/CPU accounting, and uncertain usage on interruption. Started attempts cannot be silently repeated.

The existing native worker lock is reused only after compatibility checks; fresh adapter controls are required. The user has reported waiting for the job. **No job ID, current run directory, completion status, or GPU result for this new preflight has yet been supplied in this report's evidence.**

Latest local implementation validation: **509 tests ran, 478 passed and 31 optional-dependency tests skipped**; shell checks passed for ten files. CLI-help, compilation, and whitespace checks also passed. These local checks do not substitute for the pending native GPU observations.

## 11. Audit conclusions

### Supported

- Generated scoped execution and worker-loss recovery can succeed in the documented stock engineering cases.
- Four richer tasks are executable through the qualification harness, but model complete success remains low.
- Assignment-specific interface guidance reduced observed publication denials.
- Semantic defects remain after interface conformance.
- Native grammar acceptance and strict JSON acceptance differed for nested duplicate keys.
- The new unique-key guard passed the reported 44-case native CPU matrix after a justified synthetic-control correction.

### Not established

- General planner superiority, reliable repository-wide recovery, or population success rates.
- Independent task/evaluator and rights-review completion for the unreviewed cohort.
- Calibrated B0 budgets or confirmatory results.
- Worst-case memory/context/output feasibility.
- GPU performance or task-success gains from the new unique-key mode.
- Exact reproduction or causal explanation of every historical malformed response.

Historical successes and failures remain unchanged. CPU controls are implementation evidence; the pending GPU preflight is decoder feasibility evidence; only a separately specified prospective task experiment could measure task outcomes under the new mode.

## 12. Decisions after reviewing the pending result

No additional experiment is launched by this report.

- If any preflight call fails, inspect its generation, decoder CPU, memory, and accounting evidence before changing caps or repeating it.
- If all three pass, record observed-case qualification and its limits. Decide separately whether to prepare a prospective task comparison with the new worker mode.
- For any comparison, freeze task/source/scorer/planner/JIT/budget settings, state the changed worker contract explicitly, and retain failed, invalid, and unrun conditions in reporting.
- Continue reporting semantic correctness separately from parse validity and scope conformance. A duplicate-free response can still be wrong.
- Treat the already inspected tasks as development material; broader claims require a separately designed evaluation across appropriate source groups.

The immediate audit question is whether the new decoder completes the bounded native GPU cases within its existing allowance. The later scientific question is whether that change improves task outcomes under a controlled prospective design.


## Addendum — 15 October 2026: unique-key GPU result received

The pending preflight has now failed (job 1096744_0; experiment `a3aadd6913fb1f2968de6c735183c65f48dfd2cf36c0c9c7c2ed724c6d959a32`). This supersedes the pending status in sections 1 and 10 without changing their original evidence cutoff.

- **Nested mapping passed:** 91 input tokens, 601 output tokens (556 reasoning), EOS, complete validation, and 1.344673142 seconds decoder CPU.
- **Escaped Unicode keys failed:** AcceleratorError during the dispatched call; no returned generation record. Its 2143-token reservation is uncertain, not zero measured usage.
- **Long-context mapping was not attempted.**
- Known total: 692 tokens; uncertain total: 2143 tokens; wall time: 184.949315332 seconds; one model instance on NVIDIA A100-SXM4-80GB.
- No task execution, SQL, or evaluator ran. Overall qualification failed.

The supplied stderr log is empty. The adapter retained only the exception class, so the root cause cannot be established from this evidence. In particular, out-of-memory, GPU kernel, and guard failures cannot yet be distinguished. Bounded message/stack/stage capture has been implemented prospectively in the synthetic preflight; it is not a demonstrated decoder fix. The original attempt remains immutable, and no replacement result is claimed.
