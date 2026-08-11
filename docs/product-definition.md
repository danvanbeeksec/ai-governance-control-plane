# Product Definition

## Product statement

The AI Governance Control Plane is an independent, synthetic prototype that makes early AI-governance decisions visible, consistent, and explainable. It records intended use, identifies decision-relevant characteristics, applies deterministic rules to overall inherent AI system risk, and summarizes the result for decision-makers. The separate [AI Governance Control Framework](https://github.com/danvanbeeksec/ai-governance-control-framework) remains the authoritative control source and is consumed through a pinned, validated artifact.

It demonstrates governance architecture and selective automation. It does not automate accountability away.

## Problem

AI intake often gathers information without producing a clear decision. Requesters may not understand what reviewers need, specialists may repeat triage work, and executives may receive activity data instead of exposure, rationale, and required action.

The v0.1 question is narrow: can a transparent prototype consistently classify a proposed use case, assign a review tier, and explain why?

## Users and needs

| User | Need | v0.1 response |
|---|---|---|
| Business requester | Understand required information and next steps | Plain-language intake and summary |
| Governance lead | Understand exposure, rationale, and unknowns | Tier, reason codes, route, questions |
| Specialist reviewer | See which facts triggered attention | Factor-level traceability |
| Technical implementer | Understand and verify the control source | Pinned framework artifact and provenance |

## Value hypothesis

Explicit intake facts, decision rules, and outputs can improve triage consistency and direct specialist attention to the use cases that warrant it. The value is explainability and workflow clarity, not predictive accuracy or code complexity.

## Functional scope

### Intake

Capture a synthetic ID, purpose, expected benefit, users, affected population, capability type, exposure, decision role, human review point, generic data categories, external-provider involvement, materiality, reach, reversibility, and known uncertainties.

### Classification

Derive visible labels for Information Sensitivity, AI Capability and Autonomy Level, external impact, consequential decisions, agent capabilities, third-party dependency, and generative-AI use. Each label cites its source field and rule.

### Tiering

Determine the Baseline Inherent Risk Tier from Information Sensitivity and AI Capability and Autonomy, evaluate Contextual Risk Factors, and assign one of three Final Risk Tiers using `risk-methodology.md`. Tier names are review-routing labels, not legal categories.

### Control applicability

Validate a complete treatment for every control in the currently pinned framework version. Separate enterprise dependencies from system controls, use submitted facts only to establish positive applicability, and return unresolved questions when current intake facts are insufficient. Framework changes require a compatible methodology version before recommendations may proceed. The deterministic recommendation engine implements this approved method.

### Decision summary

Present intended purpose, key classifications, tier and rationale, proposed route, missing information, assumptions, and a warning that a qualified human retains the decision.

## Non-functional requirements

- Explainability: every result traces to input and rule.
- Determinism: identical validated input produces identical output for a fixed ruleset.
- Accessibility: executive summary avoids unnecessary jargon.
- Testability: rules support unit and boundary tests.
- Privacy: synthetic fixtures only.
- Change visibility: results identify schema and ruleset versions.
- Portability: core logic remains separate from UI and storage.

## Delivery stages

1. Approve definition, data model, rules, fixtures, public boundary, and license.
2. Implement typed models, pure decision functions, and a versioned decision record. **Implemented.**
3. Implement pinned framework ingestion and decision-record provenance. **Implemented.**
4. Define and approve a complete, machine-readable control-applicability methodology. **Implemented.**
5. Implement the control-recommendation engine. **Implemented.**
6. Add a small Streamlit flow. **Implemented.**
7. Add deployment configuration, security notes, setup instructions, hosted verification, and rollback guidance. **Implemented.**
8. Add reviewed hosted screenshots after the initial Community Cloud verification.
9. Perform point-of-use confidentiality, IP, licensing, employer-policy, and factual review before publication.

## Future roadmap candidates

Later versions may add control implementation and evidence assessment, residual-risk decisions, lifecycle reassessment, and runtime governance, including activity and tool-invocation monitoring, behavioral baselines, identity or permission drift, incident routing, stop mechanisms, and rapid containment. These capabilities require production telemetry, integrations, operating ownership, security design, and validated escalation processes. They remain outside v0.1 and are not represented as implemented.

The next intake and applicability iteration should evaluate three related enhancements:

1. Add a direct question establishing whether people outside the organization can interact with the AI system or receive its outputs. Keep this distinct from autonomous external communication and broader external reach so controls such as AI-AGT-003 receive explicit facts.
2. Analyze the business purpose and system description to propose answers to unresolved applicability questions. Any proposed answer must show its supporting text, uncertainty, and affected controls, and must require user confirmation before it changes a control outcome.
3. Add a review workflow for recording answers to the current Human confirmation needed questions, recalculating applicability, and preserving who confirmed the answer, when, and against which framework and methodology versions.

AI-GOV-003 remains a system control with an enterprise dependency until an inventory integration exists. The organization must provide the inventory capability, while the system owner must ensure this specific system is entered with the required information. A future integration may create or update that entry and return evidence, but the current assessment record does not claim to do so.

## Open choices

- Keep private until a working demonstration or publish the definition earlier.
- Store rules in Python initially or versioned YAML.
- Confirm final disposition terminology.
- Confirm the MIT License before public release.
