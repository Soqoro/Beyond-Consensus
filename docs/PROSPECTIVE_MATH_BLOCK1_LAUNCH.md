# First prospective MATH block: planner binding

Eight frozen questions; the source-family review is complete within its stated retrieval coverage. The reviewed cohort is `4f50133da314439ccfc15f3bc794c67d49b2e7eb965ac8d4c7aaa4babd53c133`. Candidate membership and the generic procedure have not changed. No decomposition or workflow admission is inferred from the review.

The new protocol is `prospective-math-block1-planner-v1`. It uses the existing shared registry/snapshot/submission and allocation checks from `composite_math_launch`. A small optional transport factory permits the accepted natural-planning `CheckedTransport` to use the same Qwen loader. Historical worker transports and evidence labels retain their defaults. Planner evidence is labelled separately. No new model backend or approval framework.

## Fixed limits

One initial call per question, no retry/correction: eight calls, 3,072 output, 13,312 input, 16,384 context, 131,072 aggregate tokens. One-hour HPCAIq allocation, one >=80GB GPU, four CPUs, 128GB host RAM. Existing accounted user-GPU overlap ceiling remains four. Worker execution stays disabled.

Model: Qwen/Qwen3.5-27B at `fc05daec18b0a78c049392ed2e771dde82bdf654`, non-thinking, deterministic BF16/SDPA. Preparation verifies local metadata/template and measures all eight fully rendered requests. Existing observed weight-inventory hashes are reused as a receipt and fully rechecked at dispatch; they are not independent provenance certification.

Requests use only each public statement and the unchanged compact natural-planning contract. The review narrative, other questions, owners, costs and answers do not enter them. Completed malformed/truncated plans remain recorded outcomes and do not prevent subsequent calls when accounting is reliable. Unknown dispatch/usage, changed bindings and resource exhaustion stop dispatch. Durable reservations and per-source outputs remain; no automatic resumption/retry.

## Actual offline evidence

`outputs/prospective-math-planner-binding/` records 35 initial focused passes, 20 loader/regression passes after the transport evidence-label change, and eight final launcher tests including fake-tokenizer preparation and tampered-request rejection. A newly added preparation fixture initially failed because its invented statements did not match real source hashes; the corrected fixture explicitly substitutes the already-verified upstream packet for this isolated test. The original failure log is retained; production source verification was not relaxed.

All 24 shell scripts pass checks. Isolated CLI help loads no model. No scheduler submission, model invocation, dependency download, commit or push was performed. Source hashes and request fit must still be checked on Jupyter before a scope digest can be approved. No new broad solver tests were run.

## Preparation on Jupyter

The accompanying chat commands use the existing pinned public extraction and original inventory receipt, create a fresh one-hour cluster config, record `scontrol` partition evidence, and write:

- `bound/manifest.disabled.json`
- `bound/approval.pending.json`
- `bound/preparation-resources.json`

Do not edit the manifest. Return its printed summary for exact-scope review. This step loads only the local tokenizer, never model weights.

After separate exact approval is recorded, the implemented launch path is:

```text
python -I -B scripts/launch_prospective_math.py approve --manifest BOUND/manifest.disabled.json --approval APPROVAL.json --output RELEASE.json
python -I -B scripts/launch_prospective_math.py submit --release RELEASE.json --dry-run --output DRY_RUN.json
python -I -B scripts/launch_prospective_math.py submit --release RELEASE.json --output SUBMISSION.json
```

These placeholders describe the implemented interface, not permission to submit. The release schema consumes explicit source-transmission/GPU booleans, reviewer/time and exact scope digest. Shared registry blocks a second block-one attempt even if a new output directory is chosen. Profile/worker approval is not part of this planner-only scope.
