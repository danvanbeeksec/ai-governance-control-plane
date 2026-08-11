# AI System Risk Methodology

## Purpose

This methodology assigns an overall inherent AI system risk tier to a proposed use case. It considers security, privacy, operational, legal, regulatory, financial, customer, individual, and other material risks before compensating controls are applied.

The method supports proportionate review and provides an input to the separate control-recommendation engine. It is deterministic and explainable, but it is not a prediction of loss, legal classification, regulatory determination, or enterprise risk-acceptance method. A qualified human owns the final decision.

## Model

```text
Information Sensitivity
        +
AI Capability and Autonomy
        =
Baseline Inherent Risk Tier
        +
Contextual Risk Factors
        =
Final Risk Tier
```

The matrix establishes a baseline. Contextual factors can elevate that result, but do not reduce it in v0.1. The model avoids a numeric score because arithmetic would imply unsupported precision and comparability.

## Principles

- Use observable characteristics and visible rules.
- Separate submitted facts from derived judgments.
- Assess inherent risk before considering control effectiveness.
- Preserve the baseline and every elevation reason in the decision record.
- Treat the result as a decision aid, not a substitute for professional judgment.
- Use independently written project logic informed by, but not copied from, public sources.

## Information Sensitivity

Classify the most sensitive information the AI system is expected or reasonably likely to access, process, generate, retrieve, retain, or disclose.

| Classification | Public-project definition |
|---|---|
| **Public** | Information approved for external disclosure or already externally available. Public does not include non-public information merely because many employees can access it. |
| **Internal** | Non-public organizational information broadly available to employees and intended for routine internal use. |
| **Confidential** | Sensitive business, customer, employee, contractual, security, or operational information requiring access restrictions because unauthorized use or disclosure could cause material harm. |
| **Restricted** | Highly sensitive information requiring the strongest protections because unauthorized use, disclosure, alteration, or loss could cause significant legal, regulatory, financial, operational, security, customer, or individual harm. |

These labels are generic public-project terminology. They do not reproduce an employer classification scheme or determine a legal status.

## AI Capability and Autonomy Level

Classify the highest level at which the AI system can operate in its intended environment. Consider what the system can plan, decide, access, invoke, change, communicate, and delegate, not only whether it produces content.

| Level | Public-project label | Definition |
|---|---|---|
| **Level 1** | **Autonomous** | The system can independently plan or select meaningful actions, execute them, and adapt or iterate without human approval for each action. |
| **Level 2** | **Conditionally Autonomous** | The system can perform defined actions within approved boundaries. Human oversight occurs through checkpoints, exceptions, periodic review, or post-action review rather than approval of every meaningful action. |
| **Level 3** | **Human-Supervised** | The system generates outputs, recommendations, or proposed actions, but a human reviews and approves each meaningful action before execution. |

If capabilities differ by workflow, classify the use case at the highest intended level and record the boundary conditions. Access to tools, permissions, external systems, memory, and other agents informs both this classification and the contextual review.

## Baseline Inherent Risk Tier

| AI Capability and Autonomy Level | Public | Internal | Confidential | Restricted |
|---|---:|---:|---:|---:|
| **Level 1: Autonomous** | Tier 2 | Tier 2 | Tier 1 | Tier 1 |
| **Level 2: Conditionally Autonomous** | Tier 3 | Tier 3 | Tier 2 | Tier 1 |
| **Level 3: Human-Supervised** | Tier 3 | Tier 3 | Tier 3 | Tier 1 |

The Internal column is an independently designed public-project extension that distinguishes broadly available organizational information from externally available Public information.

### Tier interpretation

| Tier | Inherent risk | Default review posture |
|---|---|---|
| **Tier 1** | High | Formal multidisciplinary assessment, enhanced approval, documented control design, and senior accountable ownership before use |
| **Tier 2** | Moderate | Targeted specialist review, explicit operating boundaries, documented testing, and proportionate approval before use |
| **Tier 3** | Lower | Standard governance review, named ownership, permitted-use boundaries, and proportionate testing |

High inherent risk does not mean prohibited, and lower inherent risk does not mean safe. The tier determines attention and expected rigor, not the final decision.

## Contextual Risk Factors

After the matrix lookup, evaluate conditions that may make the baseline insufficient. Each applied elevation must identify the submitted fact, rule, prior tier, and resulting tier. Multiple factors may reinforce the rationale but the final tier cannot exceed Tier 1.

### Agent capability factors

Evaluate whether the system has:

- Access to external tools, connectors, or APIs
- Ability to execute transactions, modify records, or affect physical or digital operations
- Privileged access, credentials, or permissions in enterprise systems
- Ability to communicate externally or publish without prior approval
- Ability to delegate tasks to other AI systems or agents
- Persistent memory or state across interactions
- Ability to operate without human review of each meaningful action

These factors reflect the broader attack surface and consequence pathways of agentic systems, including tool misuse, identity and privilege abuse, memory manipulation, insecure inter-agent communication, and cascading failures identified by OWASP.

### Other contextual factors

Also evaluate:

- Material decisions or actions affecting individuals, customers, finances, legal rights, safety, or essential operations
- Broad external or enterprise reach
- Difficult or slow reversibility after impact
- Regulatory, contractual, or jurisdiction-specific obligations
- Use involving vulnerable populations or consequential access to services or opportunities
- Significant third-party, supply-chain, or concentration dependency
- Missing, disputed, or unreliable intake information

### v0.1 elevation rules

- Any Restricted information results in Tier 1.
- Autonomous operation with Confidential information results in Tier 1.
- Ability to modify production systems, execute material transactions, or take safety-relevant action without prior human approval results in Tier 1.
- Privileged access combined with external tools, external communication, delegation, or persistent memory results in a minimum Tier 2 and may require Tier 1 when material impact is plausible.
- Consequential impact combined with difficult reversibility results in Tier 1.
- A regulated or consequential decision without prior human review results in Tier 1.
- Broad external reach combined with autonomous external communication results in Tier 1.
- Missing information about sensitivity, capability and autonomy, human review, or action authority returns `insufficient_information` rather than a final tier.

Context requiring judgment is routed for human review. The prototype must not silently infer a legal obligation or invent missing facts.

## Determination Process

1. Validate required intake information.
2. Determine Information Sensitivity using the highest applicable classification.
3. Determine the AI Capability and Autonomy Level using the highest intended operating capability.
4. Look up the Baseline Inherent Risk Tier in the matrix.
5. Evaluate contextual risk factors and mandatory elevation rules.
6. Assign the Final Risk Tier and preserve the complete rationale.
7. Assign the human-owned review route. Control selection is a separate, deferred method.

The output records source fields, classifications, baseline tier, applicable contextual factors, elevation rules, final tier, missing information, assumptions, ruleset version, and a human-decision warning.

## Controls and Residual Risk

The Final Risk Tier remains an inherent-risk result. Control applicability is a separate implemented step. Control design, effectiveness, and residual-risk assessment remain deferred, and v0.1 does not reduce the inherent tier based on claimed safeguards.

## Future Runtime Governance

Agentic systems may require governance during operation, not only at intake and approval. Future versions may address:

- Activity and tool-invocation monitoring
- Behavioral baselines and anomaly detection
- Identity, permission, and configuration drift
- Automated incident routing and accountable escalation
- Stop mechanisms, emergency disablement, and rapid containment
- Reassessment triggered by capability, model, data, integration, or operating-context changes

These are roadmap concepts only. Runtime telemetry, automated routing, containment, and production integrations remain outside v0.1.

## Limitations and Validation

- The matrix simplifies organizational and use-case context.
- Information classification and capability boundaries may be misunderstood or change over time.
- Intake is self-reported.
- The methodology is independently designed and has not been empirically calibrated or legally validated.
- The listed factors are not exhaustive and do not replace specialist assessment.
- Public references inform the design but do not endorse this methodology or make it conformant with a standard.

Validate matrix lookups, each elevation rule, missing critical information, monotonicity, reason-code traceability, and representative synthetic cases. Review the design qualitatively with governance, security, privacy, legal, compliance, operational-risk, and technical perspectives before claiming usefulness beyond a demonstration.

## Methodology References

The methodology draws on public concepts concerning lifecycle risk management, system context, trustworthiness, agent capabilities, tool and identity risks, human oversight, and proportionate governance. See [References](references.md) for full citations and scope notes.

The methodology is independently authored. It does not reproduce a standard, claim certification or compliance, or adopt any public source's taxonomy as its scoring method.
