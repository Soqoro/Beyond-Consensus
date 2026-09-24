# Source inspection and attribution

Inspected for this implementation on 2026-09-24. Full immutable revisions,
allowlisted paths, sizes, upstream SHA-256 values and deterministic extracted
SHA-256 values are in `source_registry.json`. No full upstream snapshots or data
rows from these repositories are committed. Source stage downloads are bounded
at each recorded file size and verify both original and extracted bytes.

| Pack | Immutable commit | Material / license | Review state |
|---|---|---|---|
| dbt-labs/jaffle_shop_duckdb | `36bde6cba69d962b83be1d52fc65a0dce1cb4ebb` | Apache-2.0 LICENSE; fictional CSV seeds; source payment amounts explicitly cents | License file inspected; independent review pending |
| owid/energy-data | `7e387a16f70a510e433f8aac7efeac6faa1e5059` | OWID CC BY 4.0, **original third-party terms also apply** | Underlying-provider and independent review pending; GPU task execution blocked |
| github/rest-api-description | `4377b4f4845badf28d13464dfb3042c6cf0e3a1f` | MIT LICENSE.md; OpenAPI 3.0.3 topics update/body/response slice | License file inspected; independent review pending |

## Pack-specific decisions

- [Jaffle Shop](https://github.com/dbt-labs/jaffle_shop_duckdb/tree/36bde6cba69d962b83be1d52fc65a0dce1cb4ebb):
  upstream is a demo. No order price exists in this seed schema, so the design's
  illustrative unpaid/partial-order request is **not implemented**. The concrete
  request is recorded-payment reconciliation by customer and payment method.
  Amounts include all recorded statuses and equal-value distinct records. No
  refund, outstanding balance or revenue-recognition formula is invented.
- [OWID](https://github.com/owid/energy-data/tree/7e387a16f70a510e433f8aac7efeac6faa1e5059):
  retain only iso_code, year, electricity_generation for DNK/FIN/OWID_WRL,
  2018–2023. The request covers DNK/FIN, 2019–2022; boundary/aggregate rows test
  declared exclusions. Codebook unit is TWh. Its provenance names Ember 2026 and
  Energy Institute 2025; row-level provider attribution is not established by
  that column-level list. Credit OWID authors Pablo Rosado, Hannah Ritchie,
  Edouard Mathieu and Max Roser and the original providers. Do not treat OWID's
  blanket license as clearance for every underlying value. Provider review is a
  real open gate, not auto-approved by a successful CPU test.
- [GitHub API description](https://github.com/github/rest-api-description/tree/4377b4f4845badf28d13464dfb3042c6cf0e3a1f):
  PUT topics request and topic response require a names array of strings. Empty
  arrays are permitted. An authored consumer mapping renames names to topics,
  preserving case/order/duplicates. It does not emulate the server's lowercase
  persistence or claim to solve a historical issue. Both schemas have no
  readOnly/writeOnly/nullable fields in this slice; absence of nullable forbids
  null; additionalProperties defaults to allowed. This explicitly reviewed
  subset is not a general OpenAPI-to-JSON-Schema translator.

## Validator/tool sources

- [OpenAPI 3.0.3 schema semantics](https://spec.openapis.org/oas/v3.0.3.html#schema-object)
- [python-jsonschema explicit reference registries](https://python-jsonschema.readthedocs.io/en/stable/referencing/)
- [jsonschema 4.25.1 source](https://github.com/python-jsonschema/jsonschema/tree/v4.25.1)
- [referencing 0.36.2 source](https://github.com/python-jsonschema/referencing/tree/v0.36.2)

The implementation pins jsonschema 4.25.1 and referencing 0.36.2; only the trusted
child imports them. It expands a bounded acyclic `rr:` artifact registry and also
passes a registry whose retrieval callback always refuses. No remote/file refs,
regex/format loaders, plugins or candidate Python are enabled. SQLGlot stays
27.28.1 and lowers to the existing approved restricted SQLite IR. Source/license
pins are independent of these tool pins.
