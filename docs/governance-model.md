# Governance Model

## Design thesis

Good governance makes accountable decisions easier to reach, explain, and revisit. The prototype organizes governance around a decision record, not a framework checklist.

It separates:

1. Submitted facts
2. Derived classifications
3. Overall inherent AI system risk determination
4. A human-owned review route
5. A human-owned decision

## Accountability

| Role | Accountability |
|---|---|
| Requester | States purpose, facts, expected benefit, and uncertainty accurately |
| Business owner | Owns the use case, benefit, outcome, and ongoing appropriateness |
| Governance reviewer | Challenges classification and confirms the review path |
| Specialist reviewer | Assesses security, privacy, legal, compliance, or model-risk issues |
| Decision owner | Accepts, conditions, defers, or rejects the use |

Software informs the decision but cannot own it.

## v0.1 lifecycle

```text
draft intake
  -> validate required facts
  -> derive classifications
  -> calculate routing tier
  -> prepare decision summary
  -> qualified human reviews and decides
```

Approval workflow, evidence completion, monitoring, reassessment, and retirement are deferred.

## Classification model

- Audience exposure: internal, external, or mixed
- Information Sensitivity: Public, Internal, Confidential, or Restricted
- AI Capability and Autonomy Level: Autonomous, Conditionally Autonomous, or Human-Supervised
- Decision influence: content support, recommendation, or automated action
- Human review: prior review, checkpoints or exceptions, or no review of each meaningful action
- Agent capabilities: tools or APIs, action authority, privilege, external communication, delegation, and persistent memory or state
- Reversibility: easy, recoverable with effort, or difficult
- Reach: pilot, bounded use, or broad use
- Provider dependency: internal or external
- Generative capability: present or absent

These are local project labels with no claimed legal meaning.

## Control library relationship

The external [AI Governance Control Framework](https://github.com/danvanbeeksec/ai-governance-control-framework) separates enterprise AI governance system controls from AI-system-specific controls and is the authoritative source for the machine-readable library.

The current prototype validates and ingests an explicitly pinned framework artifact without copying or modifying its controls. Decision records preserve framework provenance. The approved applicability methodology and recommendation engine separate enterprise dependencies, applicable system controls, and unresolved human determinations without selecting controls by risk tier.

## Executive summary questions

1. What is proposed and why?
2. Who could be affected?
3. What material characteristics were identified?
4. What routing tier was assigned and why?
5. What must happen before or during use?
6. What remains unknown, disputed, or human-owned?

## Public-use safeguards

- Use fictional organizations, people, systems, providers, and events.
- Do not disguise or lightly alter employer scenarios.
- Do not import private controls, mappings, thresholds, forms, states, architecture, or wording.
- Do not reproduce standards text.
- Do not represent the prototype as proof of legal or framework compliance.
