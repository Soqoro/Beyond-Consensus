# RepoRecourse v0.1 development packs

This directory contains **benchmark-authored metadata and small private-at-runtime
reference/test programs**, not upstream repositories, downloaded databases or
native LiveSQLBench hidden material. Source bytes are staged outside Git by
`bc rr-stage`; `source_registry.json` binds exact upstream and extracted hashes.

There are three repository-grounded draft requests, not twelve: two data-product
requests and one API integration request. There are also two synthetic engineering
fixtures. All are development-only. Independent task/source/license review is
pending. No task is a harvested historical change; no model or recovery-method
success is claimed.

`public/` is loaded by an allowlisting public-view builder. `private/` is an
explicitly separate evaluator package, used for terminal scoring and reference
qualification only. These are authored for this benchmark and may be versioned
for audit; inclusion here does not make them accessible through worker tools.
Publication can expose references to future model training. This mechanism
makes no contamination-free or OS-isolation claim.

The three public outlines expose organization descriptions, not implementation
SQL/schemas, test inputs, expected values or witness costs. Private independent
and shared-helper witnesses establish possible alternatives; they are not model
outputs or a trusted repair service. Grouped execution is a third public outline.

See [implementation/runbook](../../docs/REPORECOURSE_IMPLEMENTATION.md) and
[design](../../docs/reporecourse_benchmark_design.md).
