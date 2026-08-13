"""AI System Risk & Control Assessor demonstration interface."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

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
from ai_governance_control_plane.inventory import (  # noqa: E402
    add_seed_history,
    find_potential_duplicates,
    load_seed_systems,
    repository_for_mode,
)
from ai_governance_control_plane.models import (  # noqa: E402
    AISystem,
    Assessment,
    AssessmentHistoryRecord,
    OwnerRoles,
)
from ai_governance_control_plane.workflow import run_assessment_workflow  # noqa: E402

try:  # The pinned dependency is installed in deployed and clean-install environments.
    from ai_governance_control_framework import controls_bytes as packaged_controls_bytes
except ImportError:  # A sibling checkout remains supported for local development.
    packaged_controls_bytes = None


RISK_MODEL = ROOT / "data" / "risk-model.yaml"
METHODOLOGY = ROOT / "data" / "control-applicability-rules.yaml"
MANIFEST = ROOT / "data" / "framework-source.yaml"
EXAMPLES = ROOT / "data" / "example-assessments.yaml"
INVENTORY_SEED = ROOT / "data" / "inventory-seed.json"

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


def inventory_repository():
    mode = os.environ.get("CONTROL_PLANE_DATA_MODE", "demo").lower()
    state_key = f"inventory_repository:{mode}"
    if state_key not in st.session_state:
        st.session_state[state_key] = repository_for_mode(mode, load_seed_systems(INVENTORY_SEED))
    return mode, st.session_state[state_key]


def seed_assessment_history(inventory, framework: LoadedFramework | None) -> None:
    """Evaluate synthetic inventory through the same workflow as user submissions."""
    if framework is None:
        return
    examples = {item["assessment_id"]: item for item in load_examples()}
    assessment_by_system = {
        "SYS-SYN-001": "SYN-001",
        "SYS-SYN-002": "SYN-003",
        "SYS-SYN-003": "SYN-006",
        "SYS-SYN-004": "SYN-007",
        "SYS-SYN-005": "SYN-004",
        "SYS-SYN-006": "SYN-009",
    }
    records = []
    for system_id, assessment_id in assessment_by_system.items():
        system = inventory.get_system(system_id)
        if system is None:
            continue
        result = run_assessment_workflow(
            Assessment.model_validate(examples[assessment_id]),
            framework,
            RISK_MODEL,
            METHODOLOGY,
        )
        if system.current_risk_tier != result.decision.final_tier:
            inventory.save_system(system.model_copy(update={"current_risk_tier": result.decision.final_tier}))
        records.append(
            AssessmentHistoryRecord(
                history_id=f"HIST-{system_id}-001",
                system_id=system_id,
                assessment=result.assessment,
                decision=result.decision,
                control_applicability=result.recommendations.model_dump(mode="json"),
                created_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
            )
        )
    add_seed_history(inventory, records)


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


def render_assessment_result(result) -> None:
    st.header("3. Review the draft decision")
    tier, baseline, rules, controls = st.columns(4)
    tier.metric("Inherent risk", label(result.decision.final_tier))
    baseline.metric("Baseline", label(result.decision.baseline_tier))
    rules.metric("Risk elevation rules", len(result.decision.applied_rules))
    controls.metric("Required controls", result.recommendations.summary.applicable_system_controls)
    st.subheader("Executive summary")
    st.write(result.decision.executive_summary)
    with st.expander("Why this tier was assigned"):
        for explanation in result.decision.explanation:
            st.write(f"• {explanation}")
    st.header("4. Review control applicability")
    render_control_group(
        "Required system controls",
        "Controls established as applicable from the submitted facts.",
        result.recommendations.applicable_system_controls,
        "No system controls were established as applicable.",
    )
    render_control_group(
        "Controls requiring an applicability decision",
        "These controls require additional facts and human confirmation.",
        result.recommendations.undetermined_system_controls,
        "No controls require further applicability information.",
    )
    render_control_group(
        "Enterprise dependencies",
        "Organization-wide capabilities expected for the assessed system.",
        result.recommendations.enterprise_dependencies,
        "No enterprise dependencies were returned.",
    )


def render_record_detail(system: AISystem, inventory) -> None:
    if st.button("← Back to inventory"):
        st.session_state.pop("detail_system_id", None)
        st.rerun()
    st.title(system.name)
    st.caption(f"Complete inventory record · {system.system_id}")
    risk, lifecycle, record = st.columns(3)
    risk.metric("Current risk tier", label(system.current_risk_tier) if system.current_risk_tier else "Not assessed")
    lifecycle.metric("Lifecycle", label(system.lifecycle_state))
    record.metric("Record type", label(system.record_type))
    st.subheader("Purpose and deployment")
    st.write(system.purpose)
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Provider:** {system.provider}")
        st.markdown(f"**Model:** {system.model or 'Not specified'}")
        st.markdown(f"**Business unit:** {system.business_unit or 'Not specified'}")
        st.markdown(f"**Deployment context:** {system.deployment_context or 'Not specified'}")
    with right:
        st.markdown(f"**Autonomy:** {label(system.autonomy_level)}")
        st.markdown(f"**Information sensitivity:** {label(system.information_sensitivity)}")
        st.markdown(f"**Delivery model:** {label(system.vendor_status)}")
        st.markdown(f"**Visibility:** {label(system.visibility)}")
    st.subheader("Ownership")
    st.table([
        {"Role": "Business owner", "Assigned owner": system.owners.business_owner},
        {"Role": "Technical owner", "Assigned owner": system.owners.technical_owner or "Not assigned"},
        {"Role": "Governance reviewer", "Assigned owner": system.owners.governance_reviewer or "Not assigned"},
        {"Role": "Vendor owner", "Assigned owner": system.owners.vendor_owner or "Not assigned"},
    ])
    st.subheader("Governance metadata")
    metadata_left, metadata_right = st.columns(2)
    with metadata_left:
        st.markdown(f"**Schema version:** {system.schema_version}")
        st.markdown(f"**Created:** {system.created_at:%Y-%m-%d %H:%M UTC}")
        st.markdown(f"**Last updated:** {system.updated_at:%Y-%m-%d %H:%M UTC}")
    with metadata_right:
        st.markdown("**Reassessment triggers:**")
        if system.change_triggers:
            for trigger in system.change_triggers:
                st.write(f"• {trigger}")
        else:
            st.write("None recorded")
    if system.metadata:
        st.markdown("**Additional metadata:**")
        for key, value in system.metadata.items():
            st.write(f"• {label(key)}: {display_fact_value(value)}")
    history = inventory.list_history(system.system_id)
    st.subheader(f"Assessment history ({len(history)})")
    if not history:
        st.info("This synthetic record has a current tier but no session assessment history.")
    for item in reversed(history):
        with st.expander(f"{item.assessment.assessment_id} · {label(item.decision.final_tier)} · {item.created_at:%Y-%m-%d %H:%M UTC}"):
            st.markdown(f"**Rationale:** {item.decision.executive_summary}")
            st.markdown(f"**Framework version:** {item.decision.framework_source.library_version}")
            st.markdown(f"**Framework digest:** `{item.decision.framework_source.digest}`")
            st.markdown(f"**Required system controls:** {item.control_applicability['summary']['applicable_system_controls']}")
            st.markdown(f"**Controls requiring a decision:** {item.control_applicability['summary']['undetermined_system_controls']}")
            required_tab, unresolved_tab = st.tabs(
                ["Required controls", "Controls requiring a decision"]
            )
            with required_tab:
                required_controls = item.control_applicability["applicable_system_controls"]
                if not required_controls:
                    st.info("No system controls were established as applicable from the recorded facts.")
                for recommendation in required_controls:
                    control = recommendation["control"]
                    st.markdown(f"**{control['control_id']} · {control['title']}**")
                    st.write(recommendation["rationale"])
                    st.caption(control["requirement"])
                    st.divider()
            with unresolved_tab:
                unresolved_controls = item.control_applicability["undetermined_system_controls"]
                if not unresolved_controls:
                    st.info("No controls require additional applicability information.")
                for recommendation in unresolved_controls:
                    control = recommendation["control"]
                    st.markdown(f"**{control['control_id']} · {control['title']}**")
                    st.write(recommendation["rationale"])
                    for question in recommendation["unresolved_questions"]:
                        st.write(f"• {question}")
                    st.divider()
    complete_record = {
        "system": system.model_dump(mode="json"),
        "assessment_history": [item.model_dump(mode="json") for item in history],
    }
    st.download_button(
        "Download full JSON record",
        data=json.dumps(complete_record, indent=2),
        file_name=f"{system.system_id}-inventory-record.json",
        mime="application/json",
    )


st.set_page_config(page_title="AI Governance Control Plane", page_icon="🧭", layout="wide")
data_mode, inventory = inventory_repository()
with st.sidebar:
    st.title("Control Plane")
    page_choice = st.selectbox("Go to", ["📋  AI inventory", "➕  New assessment"])
    page = "AI inventory" if page_choice == "📋  AI inventory" else "New assessment"
    st.divider()
    framework = load_verified_framework()
    if framework:
        st.success(f"Framework {framework.source.library_version} verified")
    else:
        st.warning("The verified framework dependency is unavailable.")
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
            "This synthetic prototype demonstrates transparent risk classification and control "
            "applicability. It does not authorize production use or determine compliance."
        )
        st.markdown("[Control plane repository](https://github.com/danvanbeeksec/ai-governance-control-plane)")
        st.markdown("[Authoritative control framework](https://github.com/danvanbeeksec/ai-governance-control-framework)")

seed_assessment_history(inventory, framework)

if data_mode == "demo":
    st.info("Demo Mode: new inventory records exist only in this browser session and are not retained.")
else:
    st.warning("Local developer mode: records are retained in the configured SQLite database.")

if page == "AI inventory":
    detail_id = st.session_state.get("detail_system_id")
    detail_system = inventory.get_system(detail_id) if detail_id else None
    if detail_system:
        render_record_detail(detail_system, inventory)
    else:
        st.title("AI inventory")
        st.caption("Review governed systems, current risk tiers, lifecycle states, and ownership.")
        systems = inventory.list_systems()
        st.dataframe(
            [{
                "System ID": item.system_id,
                "System": item.name,
                "Risk tier": label(item.current_risk_tier) if item.current_risk_tier else "Not assessed",
                "Lifecycle": label(item.lifecycle_state),
                "Autonomy": label(item.autonomy_level),
                "Sensitivity": label(item.information_sensitivity),
                "Provider": item.provider,
            } for item in systems],
            use_container_width=True,
            hide_index=True,
        )
        selected_system_name = st.selectbox("Select an inventory record", [item.name for item in systems])
        selected_system = next(item for item in systems if item.name == selected_system_name)
        risk, lifecycle, assessments = st.columns(3)
        risk.metric("Risk tier", label(selected_system.current_risk_tier) if selected_system.current_risk_tier else "Not assessed")
        lifecycle.metric("Lifecycle", label(selected_system.lifecycle_state))
        assessments.metric("Session assessments", len(inventory.list_history(selected_system.system_id)))
        st.write(selected_system.purpose)
        if st.button("View full record", type="primary"):
            st.session_state["detail_system_id"] = selected_system.system_id
            st.rerun()
else:
    st.title("New assessment")
    st.caption("Run and revise an assessment before deciding whether to submit it to inventory.")
    st.warning("Use fictional or synthetic information only.")
    examples = [item for item in load_examples() if item.get("information_sensitivity")]
    st.subheader("Choose how to begin")
    st.write(
        "Describe your own fictional AI use case in the form below, or load a synthetic example "
        "to explore how the assessment and control recommendations work."
    )
    selected_name = st.selectbox(
        "Synthetic example",
        [item["system_name"] for item in examples],
        help="Selecting an example prepopulates the form. You can change any field before running the assessment.",
    )
    example = next(item for item in examples if item["system_name"] == selected_name)
    if st.session_state.get("last_selected_example") != selected_name:
        st.session_state["blank_assessment_form"] = False
        st.session_state["last_selected_example"] = selected_name
    blank_form = st.session_state.get("blank_assessment_form", False)
    sequence = st.session_state.setdefault("assessment_sequence", 1)
    form_generation = st.session_state.setdefault("form_generation", 1)
    form_key = f"assessment:{selected_name}:{form_generation}"
    with st.form(form_key):
        st.header("1. Describe the proposed AI use")
        left, right = st.columns(2)
        with left:
            assessment_id = st.text_input("Assessment ID", value=f"DEMO-{sequence:03d}", max_chars=100)
            system_name = st.text_input("System name", value="" if blank_form else example["system_name"], max_chars=200)
        with right:
            accountable_owner = st.text_input("Accountable owner", value="" if blank_form else example["accountable_owner"], max_chars=200)
            provider = st.text_input("Provider", value="" if blank_form else "Synthetic provider", max_chars=200)
            provider_model = st.text_input("Model", value="" if blank_form else "Synthetic model", max_chars=200)
        business_purpose = st.text_area("Business purpose", value="" if blank_form else example["business_purpose"], max_chars=2000)
        st.header("2. Record material characteristics")
        first, second, third = st.columns(3)
        with first:
            autonomy_level = select_value("Autonomy", "autonomy_level", ["human_supervised", "conditionally_autonomous", "autonomous"], example, form_key)
            information_sensitivity = select_value("Information sensitivity", "information_sensitivity", ["public", "internal", "confidential", "restricted"], example, form_key)
            human_review = select_value("Human review", "human_review", ["prior_to_each_meaningful_action", "checkpoints_or_exceptions", "no_prior_review"], example, form_key)
        with second:
            action_authority = select_value("Action authority", "action_authority", ["generate_only", "recommend", "modify_nonproduction", "modify_production", "execute_material_transaction", "safety_relevant_action"], example, form_key)
            system_access = select_value("System access", "system_access", ["none", "standard", "privileged"], example, form_key)
            external_reach = select_value("External reach", "external_reach", ["none", "bounded", "broad"], example, form_key)
        with third:
            reversibility = select_value("Reversibility", "reversibility", ["easy", "recoverable_with_effort", "difficult"], example, form_key)
            decision_impact = select_value("Decision impact", "decision_impact", ["none", "operational", "consequential", "regulated_or_consequential"], example, form_key)
            capabilities = ["external_tools", "external_communication", "delegation", "persistent_memory"]
            selected_capabilities = st.multiselect("Agent capabilities", [label(value) for value in capabilities], default=[label(value) for value in example["agent_capabilities"]])
            agent_capabilities = [value for value in capabilities if label(value) in selected_capabilities]
        run_draft = st.form_submit_button("Run assessment", type="primary", disabled=framework is None)
    if run_draft and framework:
        try:
            assessment = Assessment(
                assessment_id=assessment_id, system_name=system_name, business_purpose=business_purpose,
                accountable_owner=accountable_owner, autonomy_level=autonomy_level,
                information_sensitivity=information_sensitivity, human_review=human_review,
                action_authority=action_authority, system_access=system_access,
                external_reach=external_reach, reversibility=reversibility,
                decision_impact=decision_impact, agent_capabilities=agent_capabilities,
            )
            result = run_assessment_workflow(assessment, framework, RISK_MODEL, METHODOLOGY)
            st.session_state["draft_assessment"] = {
                "result": result, "provider": provider, "model": provider_model,
            }
        except Exception:
            st.error("Assessment could not be completed. Confirm the inputs and try again.")
    draft = st.session_state.get("draft_assessment")
    if draft:
        result = draft["result"]
        render_assessment_result(result)
        st.info("This is a draft. Nothing has been added to inventory yet. Change the form and run it again as needed.")
        submit, discard, download = st.columns(3)
        if submit.button("Submit to inventory", type="primary"):
            assessment = result.assessment
            system = next((item for item in inventory.list_systems() if item.name.casefold() == assessment.system_name.casefold()), None)
            if system is None:
                system = AISystem(
                    system_id=f"TEMP-{uuid4().hex[:12].upper()}", name=assessment.system_name,
                    purpose=assessment.business_purpose, provider=draft["provider"], model=draft["model"] or None,
                    owners=OwnerRoles(business_owner=assessment.accountable_owner), lifecycle_state="assessing",
                    record_type="temporary_submission" if data_mode == "demo" else "managed_inventory",
                    visibility="demo" if data_mode == "demo" else "private",
                    autonomy_level=assessment.autonomy_level, information_sensitivity=assessment.information_sensitivity,
                    current_risk_tier=result.decision.final_tier, vendor_status="vendor",
                    metadata={"created_from": "assessment_interface"},
                )
                duplicates = find_potential_duplicates(system, inventory.list_systems())
                if duplicates:
                    st.warning("Potential duplicate detected: " + ", ".join(item.name for item in duplicates))
            else:
                system = system.model_copy(update={"current_risk_tier": result.decision.final_tier})
            inventory.save_system(system)
            inventory.add_history(AssessmentHistoryRecord(
                history_id=f"HIST-{uuid4().hex.upper()}", system_id=system.system_id,
                assessment=result.assessment, decision=result.decision,
                control_applicability=result.recommendations.model_dump(mode="json"),
            ))
            st.session_state["assessment_sequence"] = sequence + 1
            st.session_state["form_generation"] = form_generation + 1
            st.session_state["blank_assessment_form"] = True
            st.session_state.pop("draft_assessment", None)
            st.session_state["submission_notice"] = f"{assessment.assessment_id} was submitted to inventory."
            st.rerun()
        if discard.button("Discard draft"):
            st.session_state.pop("draft_assessment", None)
            st.rerun()
        download.download_button(
            "Download draft", data=json.dumps(result.model_dump(mode="json"), indent=2),
            file_name=f"{result.assessment.assessment_id}-assessment.json", mime="application/json",
        )
    if notice := st.session_state.pop("submission_notice", None):
        st.success(notice)
