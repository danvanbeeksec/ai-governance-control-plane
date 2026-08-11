# Control Applicability Methodology

## Purpose

This methodology defines how the recommendation engine connects canonical assessment facts to the external AI Governance Control Framework. It is a policy contract, not a compliance determination or statement that a control is effective.

The machine-readable authority for the methodology is [`data/control-applicability-rules.yaml`](../data/control-applicability-rules.yaml). It covers every control in the currently pinned framework version, not a permanent control catalog. The framework remains the authority for control objectives, requirements, applicability language, evidence examples, and implementation notes.

## Design principles

1. System facts drive applicability. The inherent-risk tier controls review rigor but does not create a control bundle.
2. A matched rule may establish applicability. An unmatched rule does not establish non-applicability.
3. Missing or unsupported context produces `undetermined`, not silent exclusion.
4. Enterprise dependencies are displayed separately from system controls.
5. Inheritance requires confirmation of the provider, scope, configuration, exclusions, evidence, and review period.
6. Control applicability does not establish implementation or operating effectiveness.
7. A qualified human confirms the final applicability decision.

## Output sections

### Enterprise dependencies

Enterprise controls are capabilities the system expects the organization to provide, such as governance authority, policy, competence, and independent challenge. They appear as `inherited_dependency`, not as system-level implementation claims.

For each dependency, a later workflow should capture:

- accountable provider;
- inheritance scope;
- required system configuration;
- exclusions and gaps;
- evidence source and review period;
- failure and escalation path.

Controls with layer `both` may appear under system controls while retaining `enterprise_dependency: true`. This means the individual system has responsibilities and also depends on an enterprise capability.

### System controls

System controls are evaluated against facts about the proposed AI system. They may be universal, conditionally applicable, or require human determination.

The human-facing review presents them in this order:

1. Required system controls, which the system owner must ensure are implemented or validly inherited with accountable ownership and evidence.
2. Controls requiring an applicability decision, which are unresolved rather than optional or not applicable.
3. Enterprise dependencies, for which the system owner must identify the provider and confirm the inheritance conditions even when another function operates the capability.

## Treatment types

| Treatment | Method | Initial outcome |
|---|---|---|
| `universal` | Applies to every governed system or every adopting organization within the stated section. | `applicable` for system controls or `inherited_dependency` for enterprise dependencies |
| `conditional` | One or more factual trigger groups can establish applicability. Groups use OR logic; conditions inside a group use AND logic. | `applicable` when matched, otherwise `undetermined` |
| `human_determination` | Current assessment fields cannot safely resolve applicability. | `undetermined` |

This version never produces an automated `not_applicable` result. A future method may support that outcome only when explicit negative facts, rationale, and appropriate approval are available.

## Condition language

The first version supports two operators:

- `in`: the scalar assessment value is one of the listed values.
- `contains_any`: a list-valued assessment field contains at least one listed value.

Conditions may reference only fields and values defined by the canonical Pydantic `Assessment` contract. This prevents rules from depending on facts the intake does not actually collect.

## Decision procedure

For each framework control:

1. Confirm that the control exists in the pinned, validated framework.
2. Read its assigned section and treatment.
3. For an enterprise dependency, return `inherited_dependency` and request inheritance confirmation.
4. For a universal system control, return `applicable`.
5. For a conditional system control, evaluate every trigger group against submitted facts.
6. If any trigger group matches, return `applicable` with the matched facts and rule rationale.
7. If no trigger matches, return `undetermined` with the rule's unresolved questions.
8. For human determination, return `undetermined` with its unresolved questions.
9. Preserve the framework and applicability-methodology versions with the result.
10. Require qualified human confirmation before recording the final applicability decision.

## Current intake limitations

The canonical assessment does not yet capture several facts needed for confident applicability decisions, including:

- lifecycle stage and production status;
- generative-AI and untrusted-input pathways;
- personal-data processing and affected populations;
- development, integration, and customization model;
- training, evaluation, retrieval, grounding, and other data sources;
- external providers, components, subprocessors, and concentration dependencies;
- deployment environment, jurisdictions, and specific obligations;
- proposed control inheritance and evidence sources.

Controls depending on these facts remain `undetermined` unless an existing field positively establishes applicability. This limitation is intentional and exposes the next intake-design requirements.

## Human review requirements

A reviewer may confirm, add, or remove applicability only with a rationale. A `not_applicable` decision should identify the facts considered, approval authority, date, framework version, and conditions that require reassessment.

The recommendation layer must not:

- claim that a control is implemented or effective;
- reduce the inherent-risk tier;
- infer legal or regulatory status;
- hide unmatched conditional controls;
- alter imported control language;
- treat enterprise inheritance as automatically satisfied.

## Change governance

The applicability methodology has its own version because it is a control-plane decision artifact, not part of the framework. A change to a trigger, treatment, section, or outcome can change recommendations and therefore requires documented purpose and owner, review against every framework control, representative and boundary tests, impact analysis for existing assessments, and an explicit effective date and migration decision.

Framework upgrades and applicability-methodology upgrades are separate decisions. Neither should silently change a historical assessment.

## Framework evolution and compatibility

The methodology does not assume that the current framework control count is permanent. Compatibility is determined by comparing control IDs and versions at adoption time.

When a framework version adds, removes, or renames a control, or when the framework library version changes:

1. The new framework artifact is reviewed and pinned explicitly.
2. The compatibility check compares its control IDs with the methodology treatments.
3. Missing, unknown, or duplicate treatments, or a version mismatch, produce `methodology_update_required`.
4. The recommendation engine must stop rather than ignore the difference.
5. Every new control receives an explicit section, treatment, rationale, triggers where appropriate, unresolved questions, and enterprise-dependency designation.
6. The applicability methodology receives a new version and is reviewed with the framework upgrade.
7. Historical assessments retain the framework and methodology versions originally used.

`methodology_update_required` describes an incompatible policy contract. It is not a control-applicability outcome. `undetermined` applies only after a compatible methodology is loaded and the submitted system facts remain insufficient.

## Completion criteria for this milestone

- Every control in the currently pinned framework version has exactly one treatment.
- Every enterprise-layer control appears under enterprise dependencies.
- Every conditional trigger uses canonical assessment fields and values.
- Conditional and human-determination controls include unresolved questions.
- Automated non-applicability is excluded.
- Existing synthetic assessments can be validated against the rule vocabulary.
- The recommendation engine implements this approved methodology without changing its policy choices.
