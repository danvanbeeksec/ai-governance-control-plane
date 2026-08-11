# Control Recommendation Engine

## Purpose

The recommendation engine applies the approved control-applicability methodology to a canonical assessment and a completed inherent-risk decision. It produces a deterministic, versioned recommendation set using the pinned external framework.

The engine recommends controls for human confirmation. It does not approve a system, determine legal obligations, assess control implementation, measure operating effectiveness, calculate residual risk, or change the inherent-risk tier.

## Required inputs

- a canonical validated `Assessment`;
- its completed `DecisionRecord`;
- a validated `LoadedFramework`;
- an approved, compatible `ApplicabilityMethodology`.

The assessment facts must exactly match the facts retained in the risk decision. The decision's framework provenance must exactly match the loaded framework. Any mismatch stops processing.

## Processing

1. Require methodology status `approved`.
2. verify framework and methodology compatibility.
3. Verify assessment identity, submitted facts, risk completion, and framework provenance.
4. Return every enterprise-section control as `inherited_dependency`.
5. Return every universal system control as `applicable`.
6. Evaluate conditional trigger groups with OR logic between groups and AND logic within a group.
7. Preserve every matching fact, operator, expected value, and trigger-group number.
8. Return an unmatched conditional control as `undetermined` with unresolved questions.
9. Return a human-determination control as `undetermined` with unresolved questions.
10. Preserve the complete imported control record without modifying its language.

## Output contract

The `ControlRecommendationSet` contains:

- assessment ID and schema version;
- risk-model ID, version, and unchanged inherent-risk tier;
- framework repository, version, schema, commit, and digest;
- applicability-methodology ID, schema version, and version;
- separate enterprise-dependency, applicable-system, and undetermined-system lists;
- matched facts and unresolved questions;
- control totals and human-confirmation requirements.

Each recommendation embeds the exact validated framework control record. This makes the rationale and authoritative control content available together without transferring control authority to the control plane.

## Failure behavior

The engine fails closed when:

- the methodology is not approved;
- framework and methodology versions or control coverage do not match;
- the risk decision is incomplete;
- assessment identifiers or facts differ;
- framework provenance differs;
- an unsupported applicability operator is encountered.

Framework-methodology incompatibility reports `methodology_update_required`. Missing system context under a compatible methodology produces `undetermined` recommendations.

## Human decision boundary

Every recommendation requires qualified human confirmation. Reviewers may confirm or override applicability only with documented rationale and the versions used. Enterprise dependencies require confirmation of provider, inheritance scope, configuration, exclusions, evidence, and review period.

The output does not contain an automated `not_applicable` state.

## Completion criteria

- Every control in the compatible framework is returned exactly once.
- Enterprise dependencies remain separate from system controls.
- Every applicable conditional control identifies its matching facts.
- Unresolved controls retain review questions.
- Identical facts and versions produce identical output.
- Submitted facts and imported controls remain unchanged.
- The inherent-risk tier is preserved exactly.
