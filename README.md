# AI Governance Control Plane

**[Open the public Streamlit demonstration](https://ai-governance-control-plane.streamlit.app/)**

The included Streamlit application, **AI System Risk & Control Assessor**, is an independent,
synthetic prototype for recording proposed AI use cases, applying transparent classification and
risk rules, and producing an executive-readable decision summary. It validates and consumes an
explicitly pinned artifact from a separately maintained AI control framework.

This is a governance product demonstration. It shows how governance intent can become a usable and auditable decision process. It is not a production GRC platform or a substitute for qualified legal, compliance, privacy, security, or risk review.

## Phase 2 demonstration

1. Capture a canonical, typed AI use-case assessment and its intended purpose.
2. Validate material characteristics and apply deterministic rules.
3. Assign an explainable overall inherent AI system risk tier.
4. Produce a typed, versioned decision record and concise executive summary.
5. Generate deterministic control recommendations for human confirmation.
6. Run the complete workflow through a synthetic-data Streamlit demonstration.
7. Maintain an AI System inventory with versioned assessment and decision history.
8. Separate session-only public demo data from local SQLite developer persistence.

The [AI Governance Control Framework](https://github.com/danvanbeeksec/ai-governance-control-framework) remains the external, authoritative governance asset. The control plane validates the pinned framework artifact and recommends controls through approved fact-based applicability rules. It does not copy or modify control authority, infer implementation, or create tier-based control bundles.

Every conclusion must trace to submitted facts and visible rules. No model makes or obscures the governance decision.

## Intended users

- Governance leaders who need a concise view of exposure and decisions.
- Risk, security, privacy, legal, and compliance reviewers who need traceability.
- Business requesters who need clear intake and next steps.
- Technical teams who need practical governance requirements.

## Scope boundaries

In scope: synthetic intake, deterministic classification, explainable inherent-risk tiering, decision summary, pinned framework ingestion, fact-based control recommendations, AI System inventory, assessment history, local developer persistence, session-only demo records, and synthetic examples.

Out of scope: approval routing, exceptions, evidence management, monitoring, automated reassessment, dashboards, authentication, integrations, enterprise persistence, automated final approval, legal determinations, and production authorization.

No employer-derived controls, identifiers, mappings, workflows, thresholds, architecture, wording, system names, owners, risks, or data may enter this repository.

## Conceptual stack

- Python for decision logic
- Pydantic for typed models
- Streamlit for the demonstration interface
- JSON or YAML for synthetic fixtures and rules
- SQLite for explicitly configured local developer/testing persistence only

The stack demonstrates implementation fluency and product thinking. Code volume is not a success measure.

## Structure

```text
ai-governance-control-plane/
├── README.md
├── SECURITY.md
├── app.py
├── LICENSE
├── requirements.txt
├── requirements-dev.txt
├── data/
│   ├── README.md
│   ├── control-applicability-rules.yaml
│   ├── example-assessments.yaml
│   ├── framework-source.yaml
│   ├── inventory-seed.json
│   ├── risk-model.yaml
│   └── synthetic-use-cases.json
├── docs/
│   ├── architecture.md
│   ├── inventory-and-persistence.md
│   ├── control-applicability-methodology.md
│   ├── control-recommendation-engine.md
│   ├── control-model.md
│   ├── deployment-guide.md
│   ├── governance-model.md
│   ├── product-definition.md
│   ├── references.md
│   ├── risk-decision-engine.md
│   └── risk-methodology.md
├── src/ai_governance_control_plane/
│   ├── applicability_contract.py
│   ├── applicability.py
│   ├── framework_loader.py
│   ├── inventory.py
│   ├── models.py
│   ├── risk_engine.py
│   ├── summarize.py
│   └── workflow.py
└── tests/
    ├── test_applicability_methodology.py
    ├── test_framework_loader.py
    ├── test_recommendations.py
    ├── test_risk_engine.py
    └── test_workflow.py
```

## Run the demonstration interface

Install the dependencies. This installs the framework package from the exact GitHub commit
recorded in `requirements.txt`. Then run:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The interface automatically validates the installed framework package. For local framework
development, a sibling framework checkout or `AI_CONTROL_FRAMEWORK_PATH` takes precedence. The
digest, schema, version, control count, control IDs, and references must match the source pin
before an assessment can run. The framework dependency is an operator configuration, not an
end-user upload.

The public interface defaults to Demo Mode. It loads fictional inventory examples and keeps new
systems and assessments only in Streamlit session memory. It does not create persistent public user
data. It displays the inherent-risk tier with qualitative guidance in the sidebar, framework provenance, required
system controls, controls requiring an applicability decision, enterprise dependencies,
human-confirmation questions, and a downloadable JSON record.

The interface separates the AI inventory from new assessments through sidebar navigation. Inventory
records expose a complete detail view and current risk tier. Running an assessment produces a draft
that can be revised or downloaded without changing inventory. Only **Submit to inventory** creates
or updates an inventory record and appends assessment history; submission then clears the form and
advances the assessment ID.

Synthetic inventory examples are evaluated through the same deterministic risk and control
workflow as user submissions. Their full records include synthetic assessment history, framework
provenance, required controls, and controls requiring a human applicability decision.

For local developer/testing persistence only, set `CONTROL_PLANE_DATA_MODE=local`. This enables a
local SQLite database at `.local/control-plane.db` or the path in `CONTROL_PLANE_DATABASE`. Never
enable local mode on the anonymous public demo. See [Inventory and persistence](docs/inventory-and-persistence.md).

See the [deployment guide](docs/deployment-guide.md) for public-readiness checks, hosted
verification, publication boundaries, updates, and rollback.

## Run the decision-engine tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Validate the pinned framework

The normal installation supplies `data/controls.yaml` through the framework package pinned in
`requirements.txt`. To validate a separate local artifact instead, run:

```bash
PYTHONPATH=src python -m ai_governance_control_plane.framework_loader \
  --source /path/to/ai-governance-control-framework/data/controls.yaml
```

The loader verifies the SHA-256 digest, schema version, library version, control count,
record structure, unique control IDs, and reference keys. It fails closed on any mismatch.
Updating the pin requires explicit review of the new framework version and digest.

## Public-source foundation

The risk methodology is informed by public OWASP, NIST, ISO, and IEC material while remaining independently authored. See [Public References](docs/references.md). The separate [AI Governance Control Framework](https://github.com/danvanbeeksec/ai-governance-control-framework) owns control requirements, evidence guidance, and public-source mappings.

The project does not reproduce standards text. Its questions, classifications, rules, requirements, examples, and architecture are independently written.

## Independence and publication boundary

This clean-room implementation uses public sources, general professional knowledge, and fictional data. It must be developed on personal equipment and accounts. No employer or client artifact may be copied, closely paraphrased, transformed, uploaded, or used as test data.

Before any public release or demonstration, review factual support, attribution, confidentiality, intellectual property, work-product restrictions, shared authorship, trade secrets, material non-public information, security sensitivity, outside-activity rules, conflicts, licensing, and inferability after redaction.

## v0.1 completion criteria

A reviewer can submit each synthetic case and see validated intake, triggered classifications, factor-level tier rationale, a concise summary, limitations, and open questions. Representative and boundary tests pass. Documentation identifies the external control source without duplicating it.

## Status

**Phase 2 Control Plane foundation implemented.** The interface runs the existing risk and recommendation engines without duplicating their governance logic. It adds the AI System parent model, session-only public demo inventory, local SQLite persistence, immutable assessment history, framework provenance, lifecycle states, synthetic inventory, and duplicate awareness. Public persistent storage, production workflow, authentication, approvals, evidence management, and integrations remain deferred.

Licensed under the MIT License. See [LICENSE](LICENSE).
