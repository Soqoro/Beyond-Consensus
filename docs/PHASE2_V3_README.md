# Phase II v3: local CPU and mock implementation

Date: 2026-10-26 (Asia/Singapore).

## Scope

The controlling sources are [`CODEX_PROMPT_PHASE2_V3.md`](../CODEX_PROMPT_PHASE2_V3.md),
[`PHASE2_PLAN_V3.md`](../PHASE2_PLAN_V3.md), and
[`PILOT_MANIFEST_V3.yaml`](../PILOT_MANIFEST_V3.yaml).
Only offline CPU validation is implemented. The entry point registers deterministic
and seeded-stochastic **mock workers only**. There is no API, local inference,
model-download, GPU, cluster, training, commit or push command. Editing a model
name, environment variable or approval record cannot register a live backend.
Python/application controls do not constitute an OS security sandbox.

## Components and reuse

- `src/bc_phase2/model.py`: frozen task, workflow, allocation, artifact and usage
  records, exact rational inputs and required-output coverage.
- `allocation.py`: general weighted matching with virtual singleton vertices;
  thresholded lexicographic objectives; optional mathematical incident budgets;
  independent small partition reference; random, direct balancing, greedy and
  unit-weight baselines; synthetic/recorded LLM reply validation.
- `runtime.py`: stable task-level scheduling, declared reads, actual mock
  invocations, fresh affected-output replay, owner-output mutations and sham
  continuations, aborted reconstruction/completion separation, atomic synthetic
  spending reservations and append-only physical attempts.
- `campaign.py`: a deliberately small fixed synthetic demonstration with frozen
  allocations, interleaved logical slots, qualified common-clean sharing and
  explicit identical-partition reuse. Complete checkpoints can resume without
  replanning; an unclosed/unknown physical attempt requires review.
- `analysis.py`: balanced fixed-partition owner matrices, three distinct cost
  statistics, common-complete comparisons, budget/quality unknowns and
  source-weighted missingness bounds, without confidence intervals.
- `data.py`: local synthetic MATH-500/GPQA/GAIA record boundaries and a supplied
  development-estimator interface. Synthetic equality grading is not an official
  benchmark evaluator. No benchmark data is downloaded.
- `planning.py`, `template.py`: disabled versioned template and stage dependency
  diagnostics, explicit slot expansion and pilot scale eligibility. The template
  reader supports only the restricted YAML syntax used by the supplied file.
- `configs/phase2/pilot-v3.disabled.json`: lossless JSON mirror of the supplied
  template; `template-binding.json` binds the original bytes.
- `configs/phase2/mock-records.schema.json`: declarative report schema. Runtime
  checks are implemented in the Python contracts; JSON Schema is not a required
  import for help, validation, scheduling or mock execution.

The implementation reuses Phase I's standard-library `closure` and `Invalid`
utilities and its matching design (general graph, retained isolated vertices,
perfect-cardinality check, exact threshold search). It extends that design in a
separate module because the old workload contract requires exactly two tasks per
owner and its historical cost restrictions must remain unchanged. It reuses the
existing scoped regression runner. Neither historical algorithms nor outputs
are rewritten.

## Local commands

Python 3.12 or later is required. Help and disabled-template inspection need only
its standard library:

```bash
cd /home/gnoriq/repos/Beyond-Consensus
python -S scripts/phase2.py --help
python -S scripts/phase2.py validate-template
python -S scripts/phase2.py validate-template --stage calibration
```

Exact matching uses the separate optional pin in `requirements-phase2.txt`:
**NetworkX 3.4.2**. Phase I's 3.6.1 pin remains unchanged. The default interpreter
in the implementation session did not have NetworkX. Validation used an already
installed pure-Python copy, exposed through `/tmp/phase2-local-deps`; no packages
were downloaded or installed. That temporary path is session-local. On another
machine use an existing compatible local environment or report the dependency
as missing; these instructions do not authorize network installation.

With that local dependency visible:

```bash
PYTHONPATH=/tmp/phase2-local-deps python -m unittest discover \
  -s tests -p test_phase2_v3.py -v

PYTHONPATH=/tmp/phase2-local-deps python scripts/phase2_validate.py \
  --output outputs/phase2-local-verification

PYTHONPATH=/tmp/phase2-local-deps python scripts/phase2.py mock-demo \
  --output outputs/phase2-local-demo --synthetic-cap 50000 --repeats 2

# Same command and same output: returns completed results without new work.
PYTHONPATH=/tmp/phase2-local-deps python scripts/phase2.py mock-demo \
  --output outputs/phase2-local-demo --synthetic-cap 50000 --repeats 2
```

Use a new verification directory; evidence writers reject existing directories.
Resume only the exact frozen demo specification. A changed code digest, cap,
workflow or executor is a new condition. An interrupted started call is never
silently assumed free or retried. Known completed physical checkpoints are
reused with their earlier charge, without mutating artifact provenance.

The bounded review driver records actual commands, logs and exit statuses:

```bash
python scripts/phase2_review.py \
  --output outputs/phase2-local-review \
  --local-dependencies /tmp/phase2-local-deps
```

Limits are 600 seconds for the command sequence, 180 seconds per command, and
120 seconds inside exactness/binding/timing verification. The timing examples
are 28 small synthetic matching solves at n=4–10, with m=n+1 or m=2n. They are
not a larger Phase I graph census or empirical model calibration. The reference
enumerator refuses more than eight tasks. The mock demo permits only one or two
repetitions and a synthetic cap of at most 100,000 units.

Repository regressions use `scripts/phase1_exhaustive_safe_tests.py`: it runs
unittest discovery separately for every allowed test module. Four historical
Phase I modules remain `NOT_RUN_PERMISSION`, since they contain/depend on
larger-domain scoring. This is explicitly not unrestricted `python -m unittest
discover -s tests -v`. `python scripts/check_shell.py` is included unchanged.

## Reading mock results

`report.json` retains the entire frozen registry and all outcomes. Failed,
invalid and not-run slots do not disappear. `full_cost=null` is unknown complete
cost, not zero. A completed wrong answer still has a complete bill.

- Research accounting counts each physical clean and replay invocation once.
- Each logical deployment includes the entire clean bill and one alternative
  owner incident; it does not divide clean cost by the number of methods.
- Reconstruction cost is reported separately from the deployment total.
- Identical partition reuse has an explicit physical ID. It is not an independent
  repetition or evidence of model determinism.
- Synthetic units and CPU/wall measurements are different units; neither is a
  measured LLM token bill, GPU attribution or currency estimate.

The deliberately malformed `llm_worst` synthetic reply demonstrates an invalid
allocation outcome. No actual LLM was consulted. Unit-weight allocator outputs
are separately tested; the disabled template retains their preselected ablation
subset rather than silently adding them to the main eight-output grid.

### Decoded allocation replies (EXT-01)

`llm_reply` requires a decoded object with only `groups`: exactly n lists of
one or two nonempty, exact known task-ID strings, covering every task once.
Strings, mappings and tuples are rejected as external group containers. Trusted
internal ownership tuples remain supported. One invalid reply may receive one
structural correction; a valid first reply ends validation, so any extra reply
invalidates the transcript without being inspected or counted. No matcher or
worker is called as a fallback. This boundary does not parse raw JSON text or
certify duplicate-key handling by a future provider/parser.

## Gates before any later stage

Calibration needs actual immutable model/version and sampling settings,
source-level development/test splits and data rights, task admission and evaluator
versions, positive cost units, task/stage limits, reservation/retry policy, a
collection policy, and separate stage authorization. It does **not** need an
already-fitted estimator or attack policy. No such authorization is conferred
by a successful offline check.

Pilot additionally needs a frozen development estimator, common-clean invariance
qualification, meaningful size/closure/context coverage, and a reviewed budget.
The proposed 12-workflow pilot is four workflows each at n=4,7,10, with six outputs
and two repetitions: 24 clean sessions plus 1,008 owner incidents before reuse,
failures, calibration, attacks or retries. This is arithmetic, not a launch plan.

Main execution also needs the final estimator, sample/repetition manifest,
quality criterion, multiplicity/uncertainty plan, source weights and exclusions,
exact ablation subset and immutable condition bindings. Corruption needs its own
owner-budget, sham/coupling and detection policy. The comparative compiler keeps
predicted mathematical incident budget B null; optional B is a local solver test
only. No live adapter exists in this handoff.
