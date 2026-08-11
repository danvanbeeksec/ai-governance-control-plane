"""Streamlit demonstration interface for the AI Governance Control Plane."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ai_governance_control_plane.framework_loader import (  # noqa: E402
    FrameworkIngestionError,
    LoadedFramework,
    load_framework,
    load_framework_bytes,
)
from ai_governance_control_plane.models import Assessment  # noqa: E402
from ai_governance_control_plane.workflow import run_assessment_workflow  # noqa: E402

try:  # The pinned dependency is installed in deployed and clean-install environments.
    from ai_governance_control_framework import controls_bytes as packaged_controls_bytes
except ImportError:  # A sibling checkout remains supported for local development.
    packaged_controls_bytes = None


RISK_MODEL = ROOT / "data" / "risk-model.yaml"
METHODOLOGY = ROOT / "data" / "control-applicability-rules.yaml"
MANIFEST = ROOT / "data" / "framework-source.yaml"
EXAMPLES = ROOT / "data" / "example-assessments.yaml"

LABELS = {
    "autonomous": "Autonomous",
    "conditionally_autonomous": "Conditionally autonomous",
    "human_supervised": "Human supervised",
    "public": "Public",
    "internal": "Internal",
    "confidential": "Confidential",
    "restricted": "Restricted",
    "prior_to_each_meaningful_action": "Before each meaningful action",
    "checkpoints_or_exceptions": "At checkpoints or exceptions",
    "no_prior_review": "No prior review",
    "generate_only": "Generate content only",
    "recommend": "Recommend",
    "modify_nonproduction": "Modify nonproduction",
    "modify_production": "Modify production",
    "execute_material_transaction": "Execute a material transaction",
    "safety_relevant_action": "Take a safety-relevant action",
    "none": "None",
    "standard": "Standard",
    "privileged": "Privileged",
    "bounded": "Bounded",
    "broad": "Broad",
    "easy": "Easy",
    "recoverable_with_effort": "Recoverable with effort",
    "difficult": "Difficult",
    "operational": "Operational",
    "consequential": "Consequential",
    "regulated_or_consequential": "Regulated or consequential",
    "external_tools": "External tools",
    "external_communication": "External communication",
    "delegation": "Delegation",
    "persistent_memory": "Persistent memory",
}

FIELD_HELP = {
    "autonomy_level": "How independently the system can decide or act after it has been initiated.",
    "information_sensitivity": "The highest sensitivity of information the system receives, creates, retrieves, or exposes.",
    "human_review": "When a qualified person reviews the system's output or intended action before consequences occur.",
    "action_authority": "The most consequential action the system is permitted to perform, not merely what it usually performs.",
    "system_access": "The highest level of access the system has to applications, infrastructure, data, or administrative functions.",
    "external_reach": "How far the system can communicate, publish, transact, or otherwise affect parties outside its immediate operating boundary.",
    "reversibility": "How difficult it would be to identify, contain, and correct the consequences of an incorrect action or decision.",
    "decision_impact": "The highest plausible effect the system's output or action can have on operations, people, rights, eligibility, safety, or regulated outcomes.",
    "agent_capabilities": "Capabilities that expand the system beyond generating a response for an immediate user.",
}

CHOICE_DEFINITIONS = {
    "human_supervised": "The system operates under direct human direction and does not independently initiate meaningful actions.",
    "conditionally_autonomous": "The system may act within defined limits, with human review at checkpoints, exceptions, or escalation points.",
    "autonomous": "The system may take meaningful actions without routine prior human authorization.",
    "public": "Information approved for unrestricted public disclosure.",
    "internal": "Nonpublic information intended for routine use within the organization.",
    "confidential": "Sensitive business, personal, contractual, or security information requiring enhanced protection.",
    "restricted": "The most sensitive information category, where exposure or misuse could cause severe harm or violate strict obligations.",
    "prior_to_each_meaningful_action": "A qualified person reviews each material output or action before it can take effect.",
    "checkpoints_or_exceptions": "Human review occurs at defined stages, thresholds, exceptions, or escalation points rather than before every action.",
    "no_prior_review": "A system output or action can take effect before a person reviews it.",
    "generate_only": "The system creates content or analysis but cannot independently cause another action.",
    "recommend": "The system proposes a decision or action for another person or process to consider.",
    "modify_nonproduction": "The system can change a test, development, or other nonproduction environment.",
    "modify_production": "The system can change a live service, production environment, or operational record.",
    "execute_material_transaction": "The system can initiate or complete a transaction with meaningful financial, contractual, or operational effect.",
    "safety_relevant_action": "The system can initiate an action that could materially affect physical safety or critical operations.",
    "none": "The system has no access or reach in this category.",
    "standard": "The system uses ordinary authorized user or service access without administrative privileges.",
    "privileged": "The system has elevated, administrative, security-sensitive, or otherwise powerful access.",
    "bounded": "Effects are limited to identified recipients, systems, transactions, or approved operating boundaries.",
    "broad": "Effects may reach an open-ended, public, large, or difficult-to-enumerate population or environment.",
    "easy": "An incorrect result can be detected and corrected promptly with limited lasting effect.",
    "recoverable_with_effort": "Correction is possible but requires material investigation, coordination, cost, or remediation.",
    "difficult": "Consequences may be lasting, widely propagated, legally significant, or impractical to fully reverse.",
    "operational": "The result can affect routine work, service delivery, resources, or business processes.",
    "consequential": "The result can materially affect a person, organization, significant transaction, or important business outcome.",
    "regulated_or_consequential": "The result can affect rights, eligibility, access, safety, employment, credit, regulated decisions, or similarly significant outcomes.",
    "external_tools": "The system can call software, services, APIs, or other tools beyond the model itself.",
    "external_communication": "The system can send, publish, or transmit information to another party or audience.",
    "delegation": "The system can assign work or decisions to another automated component or agent.",
    "persistent_memory": "The system can retain information or state for use beyond the immediate interaction.",
}

FIELD_CHOICE_DEFINITIONS = {
    ("system_access", "none"): "The system has no authenticated access to organizational applications, infrastructure, or protected data services.",
    ("external_reach", "none"): "The system cannot communicate, publish, transact, or otherwise act outside its immediate user interaction.",
    ("decision_impact", "none"): "The result does not materially affect operations, people, rights, eligibility, safety, or regulated outcomes.",
}


def label(value: str) -> str:
    return LABELS.get(value, value.replace("_", " ").title())


def definition_for(field: str, value: str) -> str:
    return FIELD_CHOICE_DEFINITIONS.get((field, value), CHOICE_DEFINITIONS[value])


@st.cache_data
def load_examples() -> list[dict[str, Any]]:
    with EXAMPLES.open(encoding="utf-8") as stream:
        examples = yaml.safe_load(stream)["assessments"]
    return [{key: value for key, value in item.items() if key != "expected"} for item in examples]


def local_framework_path() -> Path | None:
    configured = os.environ.get("AI_CONTROL_FRAMEWORK_PATH")
    candidates = [
        Path(configured).expanduser() if configured else None,
        ROOT.parent / "ai-governance-control-framework" / "data" / "controls.yaml",
    ]
    return next((path for path in candidates if path and path.is_file()), None)


def load_verified_framework() -> LoadedFramework | None:
    try:
        path = local_framework_path()
        if path:
            return load_framework(path, MANIFEST)
        if packaged_controls_bytes:
            return load_framework_bytes(packaged_controls_bytes(), MANIFEST)
        return None
    except FrameworkIngestionError as exc:
        st.error(f"Framework validation failed. {exc}")
        return None


def select_value(
    prompt: str,
    field: str,
    values: list[str],
    example: dict[str, Any],
    example_key: str,
):
    default = example.get(field, values[0])
    index = values.index(default) if default in values else 0
    display_values = [label(value) for value in values]
    selected = st.selectbox(
        prompt,
        display_values,
        index=index,
        key=f"{example_key}:{field}",
    )
    return values[display_values.index(selected)]


def render_characteristic_reference() -> None:
    definitions = {
        "Autonomy": ["human_supervised", "conditionally_autonomous", "autonomous"],
        "Information sensitivity": ["public", "internal", "confidential", "restricted"],
        "Human review": ["prior_to_each_meaningful_action", "checkpoints_or_exceptions", "no_prior_review"],
        "Action authority": ["generate_only", "recommend", "modify_nonproduction", "modify_production", "execute_material_transaction", "safety_relevant_action"],
        "System access": ["none", "standard", "privileged"],
        "External reach": ["none", "bounded", "broad"],
        "Reversibility": ["easy", "recoverable_with_effort", "difficult"],
        "Decision impact": ["none", "operational", "consequential", "regulated_or_consequential"],
        "Agent capabilities": ["external_tools", "external_communication", "delegation", "persistent_memory"],
    }
    field_keys = {
        "Autonomy": "autonomy_level",
        "Information sensitivity": "information_sensitivity",
        "Human review": "human_review",
        "Action authority": "action_authority",
        "System access": "system_access",
        "External reach": "external_reach",
        "Reversibility": "reversibility",
        "Decision impact": "decision_impact",
        "Agent capabilities": "agent_capabilities",
    }
    st.subheader("Material characteristic definitions")
    st.caption("Open a characteristic when a definition or choice needs clarification.")
    for heading, values in definitions.items():
        with st.expander(heading):
            field = field_keys[heading]
            st.write(FIELD_HELP[field])
            for value in values:
                st.write(f"• **{label(value)}:** {definition_for(field, value)}")


def display_fact_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(label(item) for item in value) if value else "None selected"
    return label(value) if isinstance(value, str) else str(value)


def render_control_group(title: str, guidance: str, controls, empty_message: str) -> None:
    st.subheader(f"{title} ({len(controls)})")
    st.write(guidance)
    if not controls:
        st.info(empty_message)
        return
    for item in controls:
        control = item.control
        with st.expander(f"{control.control_id} | {control.title}"):
            st.write(item.rationale)
            st.markdown(f"**Framework requirement:** {control.requirement}")
            if item.matched_facts:
                st.markdown("**Matched assessment facts**")
                for fact in item.matched_facts:
                    st.write(f"• {label(fact.field)}: {display_fact_value(fact.submitted_value)}")
            if item.unresolved_questions:
                st.markdown("**Human confirmation needed**")
                for question in item.unresolved_questions:
                    st.write(f"• {question}")


st.set_page_config(page_title="AI Governance Control Plane", page_icon="🧭", layout="wide")
st.title("AI Governance Control Plane")
st.caption("A transparent, deterministic demonstration using synthetic information only.")

with st.sidebar:
    st.header("Demonstration setup")
    examples = load_examples()
    complete_examples = [item for item in examples if item.get("information_sensitivity")]
    selected_name = st.selectbox("Start with a synthetic example", [item["system_name"] for item in complete_examples])
    example = next(item for item in complete_examples if item["system_name"] == selected_name)
    framework = load_verified_framework()
    if framework:
        st.success(f"Verified framework {framework.source.library_version} with {len(framework.controls)} controls")
        st.caption(f"Pinned commit: {framework.source.commit[:12]}")
    else:
        st.warning(
            "The verified framework dependency is unavailable. Place the framework repository "
            "beside this repository or configure AI_CONTROL_FRAMEWORK_PATH."
        )
    with st.expander("Understanding risk tiers"):
        st.markdown("**Tier 1: High.** Enhanced multidisciplinary review and approval.")
        st.markdown("**Tier 2: Moderate.** Targeted specialist review and proportionate approval.")
        st.markdown("**Tier 3: Lower.** Standard governance review and proportionate testing.")
        st.caption(
            "The tier describes inherent risk before controls. It is not an approval, "
            "compliance determination, or residual-risk rating."
        )
    render_characteristic_reference()
    with st.expander("About this demonstration"):
        st.write(
            "This is a synthetic governance prototype. It demonstrates transparent risk "
            "classification and control applicability, not production authorization or compliance."
        )
        st.markdown(
            "[Control plane repository](https://github.com/danvanbeeksec/ai-governance-control-plane)"
        )
        st.markdown(
            "[Authoritative control framework](https://github.com/danvanbeeksec/ai-governance-control-framework)"
        )

st.warning(
    "Public demonstration: use fictional or synthetic information only. Do not enter personal, "
    "confidential, employer, client, regulated, or other nonpublic information."
)

st.info(
    "This demonstration assigns inherent risk and recommends controls for human confirmation. "
    "It does not approve a system, determine compliance, or calculate residual risk."
)

with st.form("assessment"):
    st.header("1. Describe the proposed AI use")
    left, right = st.columns(2)
    with left:
        assessment_id = st.text_input("Assessment ID", value=example["assessment_id"], max_chars=100, key=f"{selected_name}:assessment_id")
        system_name = st.text_input("System name", value=example["system_name"], max_chars=200, key=f"{selected_name}:system_name")
    with right:
        accountable_owner = st.text_input("Accountable owner", value=example["accountable_owner"], max_chars=200, key=f"{selected_name}:accountable_owner")
    business_purpose = st.text_area("Business purpose", value=example["business_purpose"], max_chars=2000, key=f"{selected_name}:business_purpose")

    st.header("2. Record material characteristics")
    first, second, third = st.columns(3)
    with first:
        autonomy_level = select_value("Autonomy", "autonomy_level", ["human_supervised", "conditionally_autonomous", "autonomous"], example, selected_name)
        information_sensitivity = select_value("Information sensitivity", "information_sensitivity", ["public", "internal", "confidential", "restricted"], example, selected_name)
        human_review = select_value("Human review", "human_review", ["prior_to_each_meaningful_action", "checkpoints_or_exceptions", "no_prior_review"], example, selected_name)
    with second:
        action_authority = select_value("Action authority", "action_authority", ["generate_only", "recommend", "modify_nonproduction", "modify_production", "execute_material_transaction", "safety_relevant_action"], example, selected_name)
        system_access = select_value("System access", "system_access", ["none", "standard", "privileged"], example, selected_name)
        external_reach = select_value("External reach", "external_reach", ["none", "bounded", "broad"], example, selected_name)
    with third:
        reversibility = select_value("Reversibility", "reversibility", ["easy", "recoverable_with_effort", "difficult"], example, selected_name)
        decision_impact = select_value("Decision impact", "decision_impact", ["none", "operational", "consequential", "regulated_or_consequential"], example, selected_name)
        capability_values = ["external_tools", "external_communication", "delegation", "persistent_memory"]
        capability_labels = [label(value) for value in capability_values]
        selected_capabilities = st.multiselect(
            "Agent capabilities",
            capability_labels,
            default=[label(value) for value in example["agent_capabilities"]],
            key=f"{selected_name}:agent_capabilities",
        )
        agent_capabilities = [
            capability_values[capability_labels.index(value)] for value in selected_capabilities
        ]
    submitted = st.form_submit_button("Run assessment", type="primary", disabled=framework is None)

if submitted and framework:
    try:
        assessment = Assessment(
            assessment_id=assessment_id,
            system_name=system_name,
            business_purpose=business_purpose,
            accountable_owner=accountable_owner,
            autonomy_level=autonomy_level,
            information_sensitivity=information_sensitivity,
            human_review=human_review,
            action_authority=action_authority,
            system_access=system_access,
            external_reach=external_reach,
            reversibility=reversibility,
            decision_impact=decision_impact,
            agent_capabilities=agent_capabilities,
        )
        result = run_assessment_workflow(assessment, framework, RISK_MODEL, METHODOLOGY)
    except Exception:
        st.error(
            "Assessment could not be completed. Confirm the synthetic inputs and try again. "
            "No assessment result was produced."
        )
    else:
        st.header("3. Review the decision")
        tier, baseline, rules, controls = st.columns(4)
        tier.metric("Inherent risk", label(result.decision.final_tier))
        baseline.metric("Baseline", label(result.decision.baseline_tier))
        rules.metric("Risk elevation rules", len(result.decision.applied_rules))
        controls.metric(
            "Required controls",
            result.recommendations.summary.applicable_system_controls,
        )
        st.subheader("Executive summary")
        st.write(result.decision.executive_summary)
        with st.expander("Why this tier was assigned"):
            st.caption(
                "This trace shows the starting classification and any risk elevation rules. "
                "It provides decision evidence beyond the shorter executive summary."
            )
            for explanation in result.decision.explanation:
                st.write(f"• {explanation}")

        st.header("4. Review control applicability")
        st.write(
            "Use these results to assign control ownership, confirm implementation or inheritance, "
            "collect evidence, and resolve open applicability questions. Recommendations require "
            "human confirmation and do not constitute system approval."
        )
        render_control_group(
            "Required system controls",
            "The AI system owner must ensure each control is implemented or validly inherited "
            "and retain evidence appropriate to the system. Implementation and evidence activities "
            "may be delegated, but the owner remains accountable for confirming completion.",
            result.recommendations.applicable_system_controls,
            "No system controls were established as applicable from the submitted facts.",
        )
        render_control_group(
            "Controls requiring an applicability decision",
            "These controls are not optional and have not been classified as not applicable. "
            "The current intake lacks enough information. The system owner and qualified reviewer "
            "must answer the listed questions and then confirm the control as required or document "
            "a supported not-applicable decision.",
            result.recommendations.undetermined_system_controls,
            "No controls require further applicability information.",
        )
        render_control_group(
            "Enterprise dependencies",
            "These organization-wide governance capabilities are expected for every assessed system. "
            "The system owner does not necessarily implement them, but must identify the enterprise "
            "function supplying the capability and confirm the inheritance scope, configuration, "
            "exclusions, and evidence.",
            result.recommendations.enterprise_dependencies,
            "No enterprise dependencies were returned.",
        )

        export = result.model_dump(mode="json")
        st.download_button(
            "Download assessment record",
            data=json.dumps(export, indent=2),
            file_name=f"{assessment.assessment_id}-assessment.json",
            mime="application/json",
        )
        st.caption(
            f"Framework {framework.source.library_version}, commit {framework.source.commit}; "
            f"risk model {result.decision.model_version}; methodology {result.recommendations.methodology_version}."
        )
