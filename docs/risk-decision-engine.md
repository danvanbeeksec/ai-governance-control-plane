# Risk Decision Engine Specification

## Purpose

This specification translates the [AI System Risk Methodology](risk-methodology.md) into deterministic, testable governance logic. It defines the contract between intake, risk classification, review routing, and a qualified human decision.

The engine answers one question:

> What overall inherent AI system risk tier follows from the submitted facts and the current version of the public project rules?

It does not approve a system, calculate residual risk, determine legal status, predict loss, or replace security, privacy, legal, compliance, operational-risk, or technical review.

## Decision model

```text
validated assessment facts
  -> autonomy and information-sensitivity matrix lookup
  -> baseline inherent risk tier
  -> deterministic elevation rules
  -> final inherent risk tier
  -> human review route
```

Control recommendations are produced by a separate applicability engine after this inherent-risk decision. Claimed or recommended controls never lower the inherent tier in v0.1.

## Assessment contract

### Required identity and accountability inputs

| Field | Type | Requirement | Governance meaning |
|---|---|---|---|
| `assessment_id` | string | Required, unique | Stable identifier for traceability |
| `system_name` | string | Required | Human-readable name |
| `business_purpose` | string | Required | Intended outcome, users, and boundaries |
| `accountable_owner` | string | Required | Person or role accountable for the use case |

### Required classification inputs

| Field | Allowed values | Meaning |
|---|---|---|
| `autonomy_level` | `human_supervised`, `conditionally_autonomous`, `autonomous` | Highest intended capability and operating authority |
| `information_sensitivity` | `public`, `internal`, `confidential`, `restricted` | Most sensitive information reasonably expected |
| `human_review` | `prior_to_each_meaningful_action`, `checkpoints_or_exceptions`, `no_prior_review` | When meaningful action receives human review |
| `action_authority` | `generate_only`, `recommend`, `modify_nonproduction`, `modify_production`, `execute_material_transaction`, `safety_relevant_action` | Most consequential action available to the system |

### Contextual inputs

| Field | Allowed values | Default | Meaning |
|---|---|---|---|
| `system_access` | `none`, `standard`, `privileged` | Required, no inference | Highest permission level available |
| `agent_capabilities` | list of capabilities | Required; empty list means confirmed absent | Tools, external communication, delegation, or persistent memory |
| `external_reach` | `none`, `bounded`, `broad` | Required, no inference | Potential scale of external effect |
| `reversibility` | `easy`, `recoverable_with_effort`, `difficult` | Required, no inference | Practical ability to undo impact |
| `decision_impact` | `none`, `operational`, `consequential`, `regulated_or_consequential` | Required, no inference | Nature of affected decisions or outcomes |

Production intake should also capture provider, deployment environment, affected populations, jurisdictions, model and component versions, data sources, integrations, limitations, proposed controls, and evidence references. Those fields do not change the v0.1 calculation unless a published rule explicitly uses them.

## Autonomy model

Autonomy is classified by effective capability and authority, not product branding or the presence of an agent label.

| Attribute | Human-supervised | Conditionally autonomous | Autonomous |
|---|---|---|---|
| Generates content or analysis | Yes | Yes | Yes |
| Selects workflow steps | Proposed for approval | Within defined boundaries | Independently |
| Executes meaningful action | Only after prior approval | Within approved limits | Without approval for each action |
| Tool or connector use | Human-triggered or tightly constrained | Controlled and scoped | May select and invoke tools |
| Oversight | Before each meaningful action | Checkpoints, exceptions, or periodic review | Limited, delayed, or outcome-based |
| Adaptation and iteration | Human directs iteration | Bounded iteration | Independent planning and adaptation |

Classification rules:

1. Use the highest capability available in the intended environment.
2. Evaluate actual permissions, tools, memory, communication paths, and operating authority.
3. Record boundary conditions when capability differs by workflow.
4. Treat a claimed approval step as effective only when it occurs before meaningful action and cannot be bypassed in normal operation.
5. Route disputed or unclear classifications to human review without inventing a lower level.

## Information sensitivity model

Use the highest classification of information the system is reasonably expected to access, retrieve, process, generate, retain, or disclose. Indirect access through retrieval, tools, logs, memory, prompts, outputs, or connected systems counts.

| Value | Decision criterion |
|---|---|
| `public` | Approved for public disclosure or already lawfully public |
| `internal` | Routine, non-public organizational information with limited expected harm |
| `confidential` | Sensitive business, customer, employee, contractual, security, or operational information where misuse could cause material harm |
| `restricted` | Information requiring the strongest protection because misuse could cause significant legal, regulatory, financial, operational, security, customer, or individual harm |

The labels are local public-project terms. They do not replace an organization's authoritative classification policy.

## Baseline risk matrix

| Autonomy | Public | Internal | Confidential | Restricted |
|---|---:|---:|---:|---:|
| `autonomous` | Tier 2 | Tier 2 | Tier 1 | Tier 1 |
| `conditionally_autonomous` | Tier 3 | Tier 3 | Tier 2 | Tier 1 |
| `human_supervised` | Tier 3 | Tier 3 | Tier 3 | Tier 1 |

The machine-readable authority is [`data/risk-model.yaml`](../data/risk-model.yaml). Documentation and tests must agree with that file before a ruleset release.

## Elevation model

Rules establish a minimum tier. They never subtract points, offset another risk, or lower the baseline. The most rigorous applicable result wins, using `tier_1 > tier_2 > tier_3`.

| Rule | Trigger | Minimum | Purpose |
|---|---|---:|---|
| `ER-001` | Production modification, material transaction, or safety-relevant action without prior approval | Tier 1 | Captures direct consequence authority |
| `ER-002` | Privileged access plus external tools, external communication, delegation, or persistent memory | Tier 2 | Captures combined privilege and agent reach |
| `ER-003` | Consequential impact that is difficult to reverse | Tier 1 | Captures severity and recoverability |
| `ER-004` | Regulated or consequential decision without prior review | Tier 1 | Captures due-process and oversight exposure |
| `ER-005` | Autonomous external communication with broad reach | Tier 1 | Captures scalable external impact |
| `ER-006` | Restricted information | Tier 1 | Explicit matrix backstop |
| `ER-007` | Autonomous use of Confidential information | Tier 1 | Explicit matrix backstop |

Backstop rules deliberately repeat material matrix constraints. Their appearance in the explanation confirms the governing policy condition and improves auditability.

Some facts require judgment that v0.1 does not encode. Examples include uncertain regulatory scope, vulnerable populations, concentration risk, material supply-chain dependency, novel safety concerns, and unreliable intake. These require specialist review and may justify a human-owned elevation or deployment restriction outside the automated result.

## Calculation logic

```text
1. Validate the model structure and version.
2. Validate all required inputs.
3. If a required fact is missing:
     return insufficient_information
     assign no baseline or final tier
     identify every missing field
4. Validate enumerated values.
5. Look up baseline_matrix[autonomy_level][information_sensitivity].
6. For every elevation rule in the published order:
     evaluate all conditions using AND logic
     when any_of is present, match at least one listed capability
     record the rule even if the tier is already at or above its minimum
     set final_tier to the more rigorous of current tier and minimum tier
7. Return the complete explanation record.
8. Require qualified human review and route according to the final tier.
```

Rule order affects explanation order, not the final result. Implementations must evaluate all rules so a decision record preserves every applicable reason.

## Explainability and decision record

Every evaluated result must contain:

- Assessment identifier
- Assessment schema version
- Model identifier and semantic version
- Submitted facts
- Exact matrix inputs
- Baseline tier
- Every applied rule ID and independently written reason
- Tier before and after each rule
- Final inherent risk tier
- Plain-language explanation sequence
- Missing information, if any
- Unresolved questions
- Executive summary
- Framework-source provenance status
- Statement that qualified human review is required

An explanation must distinguish submitted facts from derived results. It must not say that a system is safe, compliant, approved, prohibited, or legally classified solely because of a tier.

Example:

```json
{
  "status": "evaluated",
  "assessment_id": "SYN-006",
  "assessment_schema_version": "0.1.0",
  "model_id": "ai-governance-inherent-risk",
  "model_version": "0.1.0",
  "baseline_tier": "tier_2",
  "applied_rules": [
    {
      "rule_id": "ER-001",
      "prior_tier": "tier_2",
      "resulting_tier": "tier_1",
      "changed_tier": true
    }
  ],
  "final_tier": "tier_1",
  "framework_source": {
    "repository": "danvanbeeksec/ai-governance-control-framework",
    "status": "not_loaded"
  },
  "human_review_required": true
}
```

## Worked examples

### Supervised public research assistant

- Human-supervised
- Public information
- Generates content only
- Prior review before use

Matrix result: Tier 3. No elevation rule applies. Final result: Tier 3.

### Privileged diagnostic agent

- Conditionally autonomous
- Internal information
- Privileged access
- External diagnostic tool

Matrix result: Tier 3. `ER-002` establishes a Tier 2 minimum. Final result: Tier 2.

### Procurement workflow agent

- Conditionally autonomous
- Confidential information
- Executes material transactions at checkpoints rather than prior review

Matrix result: Tier 2. `ER-001` establishes a Tier 1 minimum. Final result: Tier 1.

### Incomplete intake

- Human-supervised
- Information sensitivity not supplied

No matrix result is calculated. Status is `insufficient_information`, no tier is assigned, and the missing field is reported.

See [`data/example-assessments.yaml`](../data/example-assessments.yaml) for the complete synthetic validation set.

## Versioning and change governance

A ruleset release should include the YAML model, specification, examples, and passing tests as one change set.

- Patch: clarification with no decision change
- Minor: additive input or rule that may change decisions for some assessments
- Major: incompatible schema, tier definition, or calculation change

For any decision-affecting change, record purpose, owner, review evidence, test impact, effective date, and migration or reassessment expectations. Historical decisions must retain the model version used at the time.

## Acceptance criteria

The v0.1 engine is complete when:

1. All 12 baseline combinations pass automated tests.
2. Every elevation rule has a positive test and does not lower risk.
3. Missing required information produces no tier.
4. Invalid enumeration values are rejected.
5. Every example produces its documented expected outcome.
6. Every evaluated result is versioned and traceable.
7. Policy-data changes can alter a decision without editing Python code.
8. A human remains explicitly accountable for review and decision.

## Boundaries

This public specification is independently authored using public standards and synthetic examples. It does not reproduce employer materials, control catalogs, thresholds, forms, mappings, workflows, architecture, or implementation details. It is a portfolio prototype, not a production framework or compliance determination.
