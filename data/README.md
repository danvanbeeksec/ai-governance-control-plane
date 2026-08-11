# Data contracts

## Canonical executable inputs

`example-assessments.yaml` contains the canonical synthetic assessment records exercised by the decision engine and its tests. Its file-level `schema_version` identifies the assessment contract used by every record in the file.

`risk-model.yaml` is the machine-readable authority for the inherent-risk model.

`framework-source.yaml` pins the external framework repository, commit, artifact path,
digest, schema version, library version, and expected control count. It is a dependency
manifest, not a copy of the framework or a local control authority.

`control-applicability-rules.yaml` is the machine-readable authority for how the control
plane treats every control in the currently pinned framework version as universal,
conditional, or requiring human determination. It does not redefine the controls or claim
that they are implemented. A changed framework requires an explicit compatibility review
and methodology version update.

## Product-discovery examples

`synthetic-use-cases.json` predates the executable assessment contract and contains richer product-discovery examples. It is retained as non-executable product-discovery material and must not be treated as a second assessment schema. A later milestone should add an explicit transformation into the canonical assessment contract.
