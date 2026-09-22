# SQL interface and finite decomposition phase — 2026-09-22

## Status and change plan

Preserve the September 22 review and all historical results. Add a separate
SQL-string grammar and bounded lowering child, test against the existing tree
executor, prepare fresh matched configs from the actual native manifest, and
exercise genuinely different synthetic graphs through the existing episode
engine. Keep native policy comparisons and supplied-draft correction paused.

**This is implementation evidence, not a completed experiment.** No GPU inference,
Slurm submission, model/data download, commit or push was performed in this phase.
A 524-kB pinned parser wheel was downloaded for isolated local CPU tests.

## Preserved evidence

See [the September 22 report](PROGRESS_REPORT_2026-09-22.md) for history. In brief:
27B synthetic compatibility and feedback screens each passed 4/4 at 21,327 work;
zero rejections in both means no demonstrated feedback benefit. Latest native
16K/24-action condition `13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981`
was 0/2 at 171,715 work, in one repeatedly inspected database group. Solar query
construction failed; the view executed but failed its required semantics.
The historical recovery/JIT gap of 256 was planner-search work, not a measured
recovery advantage. No new scientific outcomes replace these observations.

The checkout contains 270 private author-material records, including one
solution entry for each solar task. Contents were not exported or put in worker
prompts. The corresponding **approved translated review, staged database, actual
native manifest and model lock are not in this checkout**. Their cluster existence
is already reported. This is a local execution prerequisite, not a claim that
the author materials have never been obtained. Renewed reference representability
and controls remain necessary on those actual assets.

## Existing language and new front end

The old executor remains the authority: `sqlite_executor.Compiler` validates
objects, depth <=12 and <=400 nodes; SQLite resolves columns/aliases under its
authorizer. SELECT supports 1–32 output expressions, table/subquery sources,
inner/left/cross joins (up to 8), where/group/having/order, DISTINCT and LIMIT
0–1000. Expressions support columns, bounded numeric/string/NULL literals,
arithmetic/comparison/AND/OR/IS/LIKE, calls, searched CASE, and scalar subqueries.
Names remain ASCII identifiers of at most 63 characters, excluding `sqlite_`.

Functions remain abs, coalesce, ifnull, nullif, round, length, lower, upper,
substr, trim, replace, min, max, sum, avg, count, total, json_extract,
json_array_length and json_type. At most eight function arguments; exact arity
is still checked by SQLite. Bad arities are **not repaired** by the compiler.
SQLite COUNT(*) lowers to the existing zero-argument COUNT() representation.
No joins, aliases, metric formulas or missing tables are inferred.

`model.action_constraint=sqlite-sql-text-v1` is the explicit opt-in. It changes
`select_sql` to a JSON string in the same tool envelopes. View names and exact
version bindings remain separate fields. The old `sqlite-json-schema-v1` schema
and default behavior remain available. No worker CREATE VIEW wrapper is accepted.

SQL text -> bounded parser child -> exhaustive supported AST lowering -> existing
IR validation -> existing version-bound closure -> existing protected executor
-> unchanged final evaluator. No original worker SQL is sent to a connection.

The parser is **SQLGlot 27.28.1, MIT**, pinned with the wheel SHA-256 in
`requirements-sql-text.txt`. Its official [documentation](https://sqlglot.com/sqlglot.html)
warns that parsing is intentionally lenient. The installed wheel's SQLite dialect
and parser source were inspected. The adapter disables function normalization and
implicit `ON TRUE`, rejects unsupported argument fields/nodes, and rejects TOP/FETCH
normalization. It never uses the optimizer, transpiler or SQLGlot executor.

Accepted strings are a documented subset of SQLite, not arbitrary SQLite:

- Quoted identifiers retain the original allowed identifier alphabet.
- Computed output expressions require explicit aliases; otherwise lowering could
  change implicit output-column labels. Plain column outputs need no alias.
- No wildcard projection, CTE, window/filter aggregate, set operation, CAST,
  simple CASE, IN/BETWEEN, COLLATE, nondefault NULL ordering, OFFSET, DDL/DML,
  PRAGMA, attachments, file functions, extensions or virtual tables.
- One statement with an optional trailing semicolon/comments. Quoted semicolons
  and comment markers are data, not extra statements.
- SQL strings <=16,384 UTF-8 bytes, <=4096 tokens, <=400 AST nodes and depth <=32;
  the tighter existing IR limits then apply.
- Separate child: 3 CPU seconds, 256 MiB address-space cap, 8-second wall timeout,
  a zero file-size limit (which does not prohibit file creation). These are bounded parsing controls, **not
  an OS sandbox** or a native-engine vulnerability guarantee.

Only fixed construction categories leave failed parsing/lowering. No corrected
query, private exception text, hidden schema or evaluator feedback is returned.
There is no database call on construction failure. Successful lowering still
permits semantically wrong queries, which retain wrong final scores.

### Accounting, context and qualification

Parser invocations cost the existing allowance convention: 3 × tool_charge,
including rejected attempts. Measured child CPU and parent wall time are recorded
separately. The tree arm keeps its existing IR compilation charge inside the SQL
executor. Extra parsing work in the text arm is part of the treatment, not free.
Model/prefill/reasoning/decoder/retry charges remain unchanged. Static grammar
setup remains outside task ledgers and reported separately.

The worker still reserves the entire output allowance against context. It stores
capped/incomplete replies verbatim, rejects incomplete constrained actions, and
re-feeds history without silent truncation or automatic repair. This phase did
not change that shared policy. Three malformed attempts exhaust two retries.

Text grammar and CPU compiler approvals are distinct and embedded separately in
its new model lock. Compiler approval checks current implementation/test hashes;
model/grammar qualification keys include the action mode. Both native arms need
new decoder locks after the shared decoder code change. Backend/scorer reference
controls are a separate approval: compiler tests cannot stand in for them.

The opt-in preflight uses nonbenchmark synthetic input through the new grammar,
lowering and protected executor, in addition to the existing long-context probe.
It retains single full A100/H100 80-GB-class placement checks, BF16, visible-device
checks and no offload/quantization. Early EOS still does not establish full-cap fit.

## Matched native comparison

`sql-interface-configs` requires the **actual latest resolved native manifest**,
checks its config hash and required settings, and compares renewed public contracts,
harness and evaluator inputs. It refuses missing budget/seed/feedback fields.
It writes two fresh configs, each with the existing two tasks and one seed.
Four total episodes, two manifests, submitted sequentially with concurrency one.

Frozen: model/tokenizer revision, reasoning, sampling, context/output/action caps,
work budget, retries, feedback mode, documents, tasks, evaluator, reserve, identities,
monitor and access regime. Changed: name, action mode/grammar, necessary syntax
instructions, actual tokenization and parser charge. Both use the same renewed data
approval path and shared new source. The historical run is never used as the fresh
paired control. The generation/source limits are not copied from synthetic probes.

`sql-interface-audit` verifies matching recorded inputs and exports existing
competence/coverage/cost diagnostics plus compiler outcomes and work. It does not
infer wrong formulas from a summary; those require a separate private offline audit.
Scores remain the reviewed `bc_livesql_native_v1` adaptation, not upstream parity.

## Finite decomposition: implemented scope and remaining work

Legacy planning fixes original obligations, unit outputs, owners and primary
order. It varies two exposure-boundary labels and backup/preparation masks, with
policy-specific reserve/preparation rules. Identical dependency graphs can occur
under both labels. This is not general decomposition.

The new bounded public schema admits 2–4 candidates, <=6 units, unchanged terminal
contracts, intermediate view contracts, owners from w0..w3 and a complete
topological schedule. Structural validation does not certify semantic correctness.
Owner renaming does not count as effective graph variation. Fewer than two distinct
admissible graphs yields `insufficient_decomposition_variation`.

Constructed CPU example: two required department reports, either independently
computed or consuming one shared aggregate view. Both retain the same original
terminal outputs. The selected frozen candidate actually replaces execution units,
source contracts, prerequisites, owners and schedule **inside EpisodeEngine**.
Intermediate outputs are excluded from the terminal denominator. Existing artifact
versions, transitive reads, messages, invalidation, worker identities, JIT routes,
unchanged-query replay and ledger are reused. Clean/withholding tests execute SQL
and repair, and completed-run resume preserves results. They are scripted tests.

Fixed, nominal and recovery selectors share the same finite catalog and eligibility.
The engine-connected selector enumerates per-identity dependency closures and counts shared
repair once. Unknown phase/unit costs block selection. Constructed estimates are
explicitly engineering-only; cases where independent organization wins are tested.
The selection objective is conditional recovery under declared scenarios, not
end-to-end robustness under imperfect detection. Initial reserve is fixed and
advance preparation absent. All plans retain the same common JIT capabilities.

**Remaining qualification blockers:**

- Graph execution accepts a frozen candidate or a finite catalog with a selector
  in synthetic/mock task metadata. The selector is connected to the existing
  engine and its search work is charged. No native policy manifest is enabled.
- `generate_candidates` implements one separately authorized call through the
  same backend. Its fixed message envelope carries a JSON catalog in `text`
  (maximum 4096 characters); no message is delivered. Public terminal-contract
  references expand to exact public contracts, never reference answers. Input,
  output, decoder and validation work use the supplied ledger. Invalid catalogs
  consume the charge and yield no valid alternative. CPU tests use a scripted
  backend. Real 27B generation and a full generated-catalog campaign remain
  unqualified; generating candidates does not open the native policy gate.
- No compatible 27B unit/repair/quality estimates exist locally. No measured
  optimized-policy manifest is enabled. Constructed fixture costs cannot enable it.
- The native solar pair has no verified alternative decomposition in this phase.
  Do not force a shared view or claim its suitability from the synthetic example.
- The local synthetic attack chooses the identity with largest declared affected
  closure before execution; it is not a learned or cost-optimal adversary. Actual
  provenance, including messages, remains authoritative for invalidation.
- Native reference renewal, exact reference representability, CPU tokenizer/XGrammar
  qualification, GPU preflight and all four native executions remain unrun locally.

Deferring optional preparation remains rational under additive work, identical
post-alarm access/capabilities and no binding latency constraint. Larger source
files alone do not defeat those assumptions. Different decompositions use equal
original budgets (A); do not pool them as common-state equal-remainder (B).

## Local review commands

```bash
python -m unittest discover -s tests -v
python scripts/check_shell.py
python -m compileall -q src tests scripts
python -I -S scripts/bc.py --help
git diff --check
# Optional isolated parser tests; no models or benchmark data:
python -m venv /tmp/bc-sql-review
/tmp/bc-sql-review/bin/python -m pip install --require-hashes -r requirements-sql-text.txt
/tmp/bc-sql-review/bin/python scripts/check_sql_frontend.py --output /tmp/bc-sql-qualification.json
python -m unittest tests.test_finite_decomposition -v
# Inspect user-supplied public task and candidate JSON files:
python scripts/bc.py decomposition-inspect --task-manifest /path/to/public-task.json --candidates /path/to/candidates.json
git diff --stat
git diff -- AGENTS.md src scripts tests requirements-sql-text.txt
```

Review/stage only intended files. These commands are user-controlled:

```bash
git add -p AGENTS.md src scripts docs/STATUS.md docs/VALIDATION.md
git add requirements-sql-text.txt scripts/check_sql_frontend.py \
  src/beyond_consensus/runtime/sql_text.py src/beyond_consensus/planning/decomposition.py \
  src/beyond_consensus/diagnostics/sql_interface.py tests/test_sql_text.py \
  tests/test_sql_interface_plan.py tests/test_finite_decomposition.py \
  docs/SQL_INTERFACE_AND_DECOMPOSITION_PHASE.md
# Include the previously drafted progress report only after reviewing it:
git add docs/PROGRESS_REPORT_2026-09-22.md
git diff --cached --stat
git diff --cached --check
git commit -m "Add restricted SQL input and finite graph development tools"
git push
```

Do not use `git add .` with private material in this checkout.

## Cluster browser workflow — user-triggered steps

Pull reviewed code into a clean checkout. Keep private inputs outside Git. Set
`BC_BASELINE` to the **actual** old output manifest and `BC_REVIEW` to the existing
approved review JSON; do not regenerate approval from a blank template.

```bash
cd "$HOME/Beyond-Consensus"
git pull --ff-only
export BC_STORAGE=/dataset/suaq0001/beyond-consensus
export BC_PYTHON="$BC_STORAGE/envs/bc-gpu-py312/bin/python"
export BC_CLUSTER="$PWD/configs/cluster.qwen27b-na100.local.json"
export BC_LOCK="$BC_STORAGE/models/Qwen--Qwen3.5-27B/model-lock.json"
export BC_PHASE="$(mktemp -d "$BC_STORAGE/diagnostics/sql-interface.XXXXXX")"
export BC_BASELINE="$BC_STORAGE/outputs/qwen27b-na100/13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981/manifest.json"
# Set this to your existing approved review file:
: "${BC_REVIEW:?Set the existing approved solar review path}"
test -f "$BC_BASELINE"
test -f "$BC_REVIEW"
# Explicit small optional dependency; no model downloads:
"$BC_PYTHON" -m pip install --require-hashes -r requirements-sql-text.txt
export BC_PARTITION="$("$BC_PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1]))["partition"])' "$BC_CLUSTER")"
```

If the historical output root differs, locate its existing manifest; do not create
one from an aggregate. A missing file stops the matched-setting claim.

Create a frozen CPU work copy and batch script (no heavy login-node qualification):

```bash
(
set -euo pipefail
test -z "$(git status --porcelain)"
mkdir "$BC_PHASE/source"
git archive HEAD | tar -xf - -C "$BC_PHASE/source"
cat > "$BC_PHASE/qualify.sh" <<'SH'
#!/bin/bash
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?CPU batch allocation required}"
cd "$BC_PHASE/source"
"$BC_PYTHON" scripts/check_sql_frontend.py --output "$BC_PHASE/compiler.json"
"$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$BC_LOCK" --context-limit 16384 \
  --output "$BC_PHASE/tree-grammar.json" --qualified-lock "$BC_PHASE/tree-lock.json"
"$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$BC_LOCK" --context-limit 16384 \
  --action-constraint sqlite-sql-text-v1 --frontend-report "$BC_PHASE/compiler.json" \
  --output "$BC_PHASE/text-grammar.json" --qualified-lock "$BC_PHASE/text-lock.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-stage \
  --root "$BC_STORAGE/datasets/livesqlbench-0664a2f" \
  --materials "$BC_STORAGE/private/livesqlbench/materials.private.jsonl" \
  --review "$BC_REVIEW" --output "$BC_PHASE/reviewed-stage.json" > "$BC_PHASE/inspection.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-validate --staged "$BC_PHASE/reviewed-stage.json" \
  --task-ids solar_2 solar_M_3 --count 2 --output "$BC_PHASE/native-validated.private.json"
printf '%s\n' '[{"source_ids":["solar_2","solar_M_3"],"rationale":"Renew original joint obligations"}]' > "$BC_PHASE/pair-candidate.json"
"$BC_PYTHON" -I scripts/bc.py sqlite-pairs --staged "$BC_PHASE/reviewed-stage.json" \
  --candidates "$BC_PHASE/pair-candidate.json" --count 1 --output "$BC_PHASE/pair-validated.private.json"
"$BC_PYTHON" -I scripts/bc.py sql-interface-reference --data-manifest "$BC_PHASE/native-validated.private.json" \
  --report "$BC_PHASE/reference-frontend.json"
"$BC_PYTHON" -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["status"] == "passed", "Reference expressivity blocked"' "$BC_PHASE/reference-frontend.json"
"$BC_PYTHON" -I scripts/bc.py sql-interface-configs --baseline-manifest "$BC_BASELINE" \
  --renewed-data "$BC_PHASE/native-validated.private.json" --output-root "$BC_PHASE/matched"
SH
bash -n "$BC_PHASE/qualify.sh"
)
# Submit only this CPU qualification job when ready:
sbatch --partition="$BC_PARTITION" --nodes=1 --ntasks=1 --cpus-per-task=4 \
  --mem=32G --time=01:00:00 --output="$BC_PHASE/cpu.out" --error="$BC_PHASE/cpu.err" "$BC_PHASE/qualify.sh"
```

Wait for completion and review compiler/grammar/native/pair reports. If any gate
fails, stop; no retry overwrites immutable reports. Run the evaluator-only representability check in the CPU allocation before
native execution. It never exports reference SQL and cannot alter the scorer.

Build both manifests only after those checks:

```bash
for BC_ARM in tree text; do
  "$BC_PYTHON" scripts/bc.py manifest --config "$BC_PHASE/matched/$BC_ARM.json" \
    --model-lock "$BC_PHASE/$BC_ARM-lock.json" --output "$BC_PHASE/matched/$BC_ARM-manifest.json" || break
done
bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_PHASE/matched/text-manifest.json" --model-lock "$BC_PHASE/text-lock.json" --dry-run
# Separately, after reviewing the dry run:
bash experiments/submit_gpu_preflight.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_PHASE/matched/text-manifest.json" --model-lock "$BC_PHASE/text-lock.json"
```

Review preflight `command_failed`, synthetic compiler/executor probe, lengths,
placement and memory. Early EOS is not full-cap qualification.

Run the two arms **sequentially**, reviewing completion before switching `BC_ARM`:

```bash
export BC_ARM=tree
bash experiments/submit_pilot.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_PHASE/matched/$BC_ARM-manifest.json" --model-lock "$BC_PHASE/$BC_ARM-lock.json" \
  --concurrency 1 --dry-run
# Separately, user-authorized execution:
bash experiments/submit_pilot.sh --cluster "$BC_CLUSTER" \
  --manifest "$BC_PHASE/matched/$BC_ARM-manifest.json" --model-lock "$BC_PHASE/$BC_ARM-lock.json" --concurrency 1
# After tree finishes, repeat those two commands with BC_ARM=text.
```

Existing submit wrappers retain the shared registry/scheduler guard, one active
campaign and maximum four GPUs. This does not control unrelated manual jobs.
Finally derive both output paths from the cluster JSON and manifest IDs:

```bash
export BC_TREE_RUN="$("$BC_PYTHON" -c 'import json,sys;from pathlib import Path;print(Path(json.load(open(sys.argv[1]))["output_root"])/json.load(open(sys.argv[2]))["experiment_id"])' "$BC_CLUSTER" "$BC_PHASE/matched/tree-manifest.json")"
export BC_TEXT_RUN="$("$BC_PYTHON" -c 'import json,sys;from pathlib import Path;print(Path(json.load(open(sys.argv[1]))["output_root"])/json.load(open(sys.argv[2]))["experiment_id"])' "$BC_CLUSTER" "$BC_PHASE/matched/text-manifest.json")"
"$BC_PYTHON" scripts/bc.py sql-interface-audit --tree-run "$BC_TREE_RUN" --text-run "$BC_TEXT_RUN" \
  --report "$BC_PHASE/interface-results.private.json"
```

Review these four development outcomes before authorizing anything else. Neither
synthetic plan tests nor compiler qualification opens the native recovery gate.

### SQL-string escape qualification correction (2026-09-23)

The first cluster text qualifier rejected escaped identifier quotes. XGrammar
0.1.32's bounded-string production excludes JSON escapes (see
[the pinned GenerateString implementation](https://github.com/mlc-ai/xgrammar/blob/v0.1.32/cpp/json_schema_converter.cc#L1286)).
For SQL-text payload fields only, a distinct decoder schema uses normal JSON
strings. Runtime action validation still limits decoded strings to 16384
characters; the compiler additionally enforces 16384 UTF-8 bytes. Output-token
and CPU caps are unchanged. This is an explicit decoder/runtime schema split,
not a claim that the decoder enforces length. Both schema hashes and the length
policy are bound into the text contract. Tree decoder schema remains unchanged.
Renew both qualifications from a fresh source snapshot before matched runs;
new synthetic escaped-string controls must pass on the actual pinned tokenizer.
