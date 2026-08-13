# Architecture

## Reusable service boundary

`GovernanceDecisionService` loads a provenance-validated framework and composes the existing risk and applicability engines. Streamlit remains a presentation consumer. External interfaces must call this service rather than importing UI code or reimplementing governance rules.

The installable package includes the risk model, applicability methodology, and framework source manifest as read-only resources. `GovernanceDecisionService.from_packaged_resources()` combines those resources with the separately installed authoritative Framework artifact. Path-based construction remains available for reviewed local overrides.

Guided intake is a validation boundary, not a reasoning engine. It derives field requirements from the canonical assessment model, reports missing and invalid facts, and accepts client-proposed inferences only after explicit confirmation. Risk and control evaluation begin only after a complete canonical assessment exists.

```text
Framework authority -> validated loader -> GovernanceDecisionService -> Streamlit / MCP / API
                                               |
                                               +-> risk engine
                                               +-> applicability engine
```

## Objective

Keep decision logic small, inspectable, and independent from the user interface. A reviewer should trace a result from submitted YAML through validation, classification, tiering, and summary generation without a machine-learning model or hidden service.

## Flow

```text
Synthetic inventory or Streamlit form
  -> required-field and enum validation
  -> deterministic classifier
  -> risk-tier calculation
  -> decision-summary assembler
  -> control applicability
  -> append-only assessment history
  -> inventory, executive, and detailed views
```

## Components

| Component | Responsibility | v0.1 technology |
|---|---|---|
| Intake model | Fields, enums, constraints, explanations | Pydantic model and YAML fixtures |
| Classifier | Facts to reason-coded labels | Pure Python, implemented |
| Tier engine | Matrix, elevation rules, explanation record | Pure Python and YAML, implemented |
| Summary assembler | Typed decision record and concise narrative | Pydantic model and Python templates, implemented |
| Framework loader | Pinned external control validation and provenance | Pydantic, YAML, and SHA-256, implemented |
| Applicability contract | Complete, valid treatment of each external control | Pydantic and YAML, implemented |
| Recommendation engine | Facts and treatments to versioned control recommendations | Pure Python and Pydantic, implemented |
| Workflow coordinator | Run the risk and recommendation engines in the required order | Pure Python and Pydantic, implemented |
| Demo UI | Load or collect a synthetic case and display results | Streamlit, implemented |
| Fixtures | Fictional examples and expected results | YAML and JSON |
| Tests | Models, rules, boundaries, and examples | pytest |
| Inventory repository | AI System parents and assessment history | Session memory by default; local SQLite by explicit configuration |

## Current and proposed code structure

```text
data/
├── control-applicability-rules.yaml
├── example-assessments.yaml
├── framework-source.yaml
├── inventory-seed.json
└── risk-model.yaml
src/ai_governance_control_plane/
├── applicability.py
├── applicability_contract.py
├── framework_loader.py
├── inventory.py
├── models.py
├── risk_engine.py
├── summarize.py
└── workflow.py
tests/
├── test_applicability_methodology.py
├── test_framework_loader.py
├── test_recommendations.py
├── test_risk_engine.py
└── test_workflow.py

app.py

```

The risk engine remains independent from external control data. The framework is installed from the exact GitHub commit in `requirements.txt`, while `data/framework-source.yaml` independently pins the reviewed source and digest. The framework loader validates the packaged bytes and returns external controls plus provenance. A configured local path or sibling checkout may override the package for development but must pass the same validation. End users cannot replace the framework through the assessment interface. The workflow coordinator runs the risk decision first and then passes the unchanged decision to the recommendation engine. The recommendation engine cannot modify the inherent-risk result. The Streamlit interface collects and presents information but owns no risk or applicability rules.

## Data contracts

The canonical executable intake includes schema version, ID, system name, purpose, accountable owner, autonomy, information sensitivity, human review, action authority, system access, agent capabilities, external reach, reversibility, and decision impact. The richer JSON use-case examples are product-discovery material, not an executable schema.

Decision output includes validation status, assessment and model versions, submitted facts, baseline tier, qualitative tier labels, rule trace, final tier, missing facts, unresolved questions, an executive summary, a human-decision warning, and framework provenance. An immutable history event stores that decision with the submitted assessment and control-applicability output beneath its AI System parent. Numeric scoring is intentionally excluded because the methodology rejects unsupported precision.

## Design decisions

- No model in the decision path.
- Pure core functions testable without Streamlit.
- Validated input remains immutable during evaluation.
- Every schema and ruleset is versioned.
- No persistent public submissions. Demo mode is session-only.
- SQLite is opt-in and local-only for developer and testing use.
- No live integrations or credentials.

## Security and privacy

- Accept synthetic data only.
- Add no telemetry or network calls in v0.1.
- Do not log free text by default.
- Constrain types, lengths, and enums.
- Escape rendered content and never evaluate submitted code or markup.
- Pin dependencies and add dependency and secret scanning before public release.
- Define retention, deletion, access control, encryption, and migration before adding persistence.

## Deferred architecture

Authentication, APIs, workflow orchestration, evidence storage, automated reassessment, monitoring, integrations, and multi-user persistence remain deferred. Future runtime governance may include behavioral baselines, activity and tool-invocation monitoring, incident routing, stop mechanisms, and containment.
