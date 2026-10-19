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
from ai_governance_control_plane.service import GovernanceDecisionService
from ai_governance_control_plane.submission import InventoryDetails, prepare_submission
from ai_governance_control_plane.reporting import review_brief
from ai_governance_control_plane.summarize import tier_display
from ai_governance_control_plane.risk_engine import load_model
from ai_governance_control_plane.applicability_contract import load_applicability_methodology
from pydantic import ValidationError

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
    return tier_display(value) if value in {"tier_1", "tier_2", "tier_3"} else LABELS.get(value, value.replace("_", " ").title())


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
        if system is None or inventory.list_history(system_id):
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
        ROOT.parent / "ai-governance-control-framework" / "data" / "controls.yaml" if packaged_controls_bytes is None else None,
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
    default = example.get(field)
    index = values.index(default) + 1 if default in values else 0
    display_values = ["Select one"] + [label(value) for value in values]
    selected = st.selectbox(
        prompt,
        display_values,
        index=index,
        key=f"{example_key}:{field}",
        help=FIELD_HELP[field],
    )
    return values[display_values.index(selected) - 1] if selected != "Select one" else None


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
    tabs = st.tabs(["Required system controls", "Needs an applicability decision", "Enterprise dependencies"])
    groups = [
        ("Required system controls", "Controls established as applicable from submitted facts.", result.recommendations.applicable_system_controls),
        ("Controls requiring an applicability decision", "Additional facts and human confirmation are required.", result.recommendations.undetermined_system_controls),
        ("Enterprise dependencies", "Confirm inheritance scope, configuration, and supporting evidence.", result.recommendations.enterprise_dependencies),
    ]
    for tab, (title, guidance, items) in zip(tabs, groups):
        with tab:
            render_control_group(title, guidance, items, "No controls in this group.")


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


def decision_service(framework):
    return GovernanceDecisionService(framework, load_model(RISK_MODEL), load_applicability_methodology(METHODOLOGY))


def render_characteristics(service, example, key):
    requirements = {item.field: item for item in service.get_assessment_requirements().fields}
    groups = [
        [('Autonomy', 'autonomy_level'), ('Information sensitivity', 'information_sensitivity'), ('Human review', 'human_review')],
        [('Action authority', 'action_authority'), ('System access', 'system_access'), ('External reach', 'external_reach')],
        [('Reversibility', 'reversibility'), ('Decision impact', 'decision_impact')],
    ]
    facts = {}
    for column, group in zip(st.columns(3), groups):
        with column:
            for prompt, field in group:
                facts[field] = select_value(prompt, field, requirements[field].allowed_values, example, key)
    options = requirements['agent_capabilities'].allowed_values
    facts['agent_capabilities'] = st.multiselect(
        'Agent capabilities', options, default=example.get('agent_capabilities', []),
        format_func=label, key=f'{key}:agent_capabilities', help=FIELD_HELP['agent_capabilities'])
    return facts


def render_start():
    st.title('From AI use case to a reviewable governance decision')
    st.write('Explore how system facts lead to an explainable inherent-risk tier, practical controls, and questions for human review.')
    st.caption('Independent governance product demonstration. All examples and records are fictional.')
    for title, description, target in [
        ('Explore a worked example', 'Follow a public research assistant from intake through its rationale and control requirements.', 'New assessment'),
        ('Assess a fictional design', 'Start with blank facts. Confirm the characteristics that determine the decision.', 'New assessment'),
        ('Compare two designs', 'See how different autonomy, permissions, or data change the rules and control applicability.', 'Compare designs'),
    ]:
        with st.container(border=True):
            st.subheader(title)
            st.write(description)
            if st.button(title, key=f'start:{title}'):
                st.session_state['next_navigation'] = target
                if title == 'Assess a fictional design':
                    st.session_state['start_choice'] = 'Start blank'
                elif title == 'Explore a worked example':
                    st.session_state['start_choice'] = load_examples()[0]['system_name']
                st.rerun()
    st.markdown('[Read the walkthrough](https://github.com/danvanbeeksec/ai-governance-control-plane/blob/main/docs/demo-walkthrough.md) · [Explore the control library](https://github.com/danvanbeeksec/ai-governance-control-framework)')
    st.write('The Framework owns control requirements. The Control Plane applies visible rules. The Assistant and Copilot kit provide alternative interfaces. A qualified human owns the final governance decision.')


def render_inventory(inventory):
    detail_id = st.session_state.get('detail_system_id')
    detail_system = inventory.get_system(detail_id) if detail_id else None
    if detail_system:
        render_record_detail(detail_system, inventory)
        return
    st.title('AI inventory')
    st.caption('Review fictional systems, their current assessed facts, and immutable decision history.')
    search = st.text_input('Search systems', help='Search by system name, ID, owner, or provider.')
    risk_filter = st.selectbox('Risk filter', ['All tiers', 'tier_1', 'tier_2', 'tier_3'], format_func=label)
    lifecycle_filter = st.selectbox('Lifecycle filter', ['All states', 'proposed', 'assessing', 'approved', 'active', 'suspended', 'retired'], format_func=label)
    systems = [item for item in inventory.list_systems()
               if (risk_filter == 'All tiers' or item.current_risk_tier == risk_filter)
               and (lifecycle_filter == 'All states' or item.lifecycle_state == lifecycle_filter)
               and search.casefold() in f'{item.system_id} {item.name} {item.provider} {item.owners.business_owner}'.casefold()]
    if not systems:
        st.info('No records match these filters.')
        return
    st.dataframe([{'System ID': item.system_id, 'System': item.name,
                   'Risk tier': label(item.current_risk_tier) if item.current_risk_tier else 'Not assessed',
                   'Lifecycle': label(item.lifecycle_state), 'Autonomy': label(item.autonomy_level),
                   'Sensitivity': label(item.information_sensitivity), 'Provider': item.provider} for item in systems],
                 width='stretch', hide_index=True)
    by_id = {item.system_id: item for item in systems}
    selected_id = st.selectbox('Select an inventory record', list(by_id), format_func=lambda value: f'{by_id[value].name} ({value})')
    selected = by_id[selected_id]
    risk, lifecycle, assessments = st.columns(3)
    risk.metric('Risk tier', label(selected.current_risk_tier) if selected.current_risk_tier else 'Not assessed')
    lifecycle.metric('Lifecycle', label(selected.lifecycle_state))
    assessments.metric('Session assessments', len(inventory.list_history(selected_id)))
    st.write(selected.purpose)
    if st.button('View full record', type='primary'):
        st.session_state['detail_system_id'] = selected_id
        st.rerun()
    if st.button('Reassess selected system'):
        st.session_state['reassess_target'] = selected_id
        st.session_state['next_navigation'] = 'New assessment'
        st.rerun()


def render_new_assessment(service, inventory, data_mode):
    st.title('New assessment')
    st.caption('Confirm the facts, review the draft, then choose whether to update inventory.')
    examples = [item for item in load_examples() if item.get('information_sensitivity')]
    choices = ['Start blank'] + [item['system_name'] for item in examples]
    if 'start_choice' in st.session_state:
        st.session_state['synthetic_example'] = st.session_state.pop('start_choice')
    selected_name = st.selectbox('Synthetic example', choices, index=1, key='synthetic_example',
                                help='Choose blank intake or load a worked fictional example.')
    example = next((item for item in examples if item['system_name'] == selected_name), {})
    targets = {item.system_id: item for item in inventory.list_systems()}
    requested = st.session_state.pop('reassess_target', None)
    if requested in targets:
        st.session_state['inventory_destination'] = requested
    if st.session_state.pop('reset_destination', False):
        st.session_state['inventory_destination'] = None
    selected_id = st.selectbox('Inventory destination', [None] + list(targets),
                              key='inventory_destination',
                              format_func=lambda value: 'Create a new system' if value is None else f'Update {targets[value].name} ({value})',
                              help='Choose an existing system explicitly. Matching names are never merged automatically.')
    sequence = st.session_state.setdefault('assessment_sequence', 1)
    generation = st.session_state.setdefault('form_generation', 1)
    key = f'assessment:{selected_name}:{selected_id}:{generation}'
    existing = targets.get(selected_id)
    if existing:
        history = inventory.list_history(selected_id)
        if history:
            example = history[-1].assessment.model_dump(mode='json')
        else:
            example = {**example, 'system_name': existing.name, 'business_purpose': existing.purpose,
                       'accountable_owner': existing.owners.business_owner, 'autonomy_level': existing.autonomy_level,
                       'information_sensitivity': existing.information_sensitivity}
    with st.container(border=True):
        st.subheader('1. Describe the proposed AI use')
        left, right = st.columns(2)
        with left:
            system_name = st.text_input('System name', value=example.get('system_name', ''), max_chars=200, key=f'{key}:name')
            accountable_owner = st.text_input('Accountable owner', value=example.get('accountable_owner', ''), max_chars=200, key=f'{key}:owner')
        with right:
            provider = st.text_input('Provider', value=existing.provider if existing else ('Synthetic provider' if example else ''), max_chars=200, key=f'{key}:provider')
            provider_model = st.text_input('Model', value=(existing.model or '') if existing else '', max_chars=200, key=f'{key}:model')
        business_purpose = st.text_area('Business purpose', value=example.get('business_purpose', ''), max_chars=2000, key=f'{key}:purpose')
        st.subheader('2. Confirm material characteristics')
        facts = render_characteristics(service, example, key)
        facts.update(assessment_id=f'DEMO-{sequence:03d}', system_name=system_name,
                     accountable_owner=accountable_owner, business_purpose=business_purpose)
        details = None
        try:
            details = InventoryDetails(provider=provider, model=provider_model or None)
        except ValidationError:
            st.warning('Provider is required before this draft can be submitted to inventory.')
        inputs = {'facts': facts, 'provider': provider, 'model': provider_model, 'system_id': selected_id}
        if st.button('Run assessment', type='primary'):
            st.session_state.pop('draft_assessment', None)
            validation = service.validate_assessment_input(facts)
            if validation.assessment:
                st.session_state['draft_assessment'] = {'result': service.assess_ai_system(validation.assessment), 'inputs': inputs}
            else:
                for issue in validation.issues:
                    st.error(f'{label(issue.field)}: {issue.detail or issue.question}')
    draft = st.session_state.get('draft_assessment')
    if draft:
        result = draft['result']
        stale = inputs != draft['inputs']
        if stale:
            st.warning('The inputs have changed. Run the assessment again before submitting or downloading this draft.')
        render_assessment_result(result)
        with st.expander('Facts used for this decision'):
            st.json(result.assessment.model_dump(mode='json'))
        submission = prepare_submission(result, details, inventory, system_id=selected_id, demo=data_mode == 'demo') if details and not stale else None
        if submission:
            with st.expander('Review proposed inventory changes', expanded=selected_id is not None):
                st.dataframe([{'Field': label(item['field']), 'Before': json.dumps(item['before']), 'After': json.dumps(item['after'])}
                              for item in submission.changes], hide_index=True, width='stretch')
            duplicates = find_potential_duplicates(submission.system, inventory.list_systems()) if selected_id is None else []
            if duplicates:
                st.info('Similar records exist: ' + ', '.join(item.name for item in duplicates) + '. Select an existing inventory destination if you mean to reassess it.')
        st.info('This is a draft. Nothing has been added to inventory yet.')
        if st.button('Submit to inventory', type='primary', disabled=submission is None):
            try:
                inventory.save_assessment(submission.system, submission.history)
            except (ValueError, OSError) as exc:
                st.error(f'The record could not be saved: {exc}')
            else:
                st.session_state['assessment_sequence'] = sequence + 1
                st.session_state['form_generation'] = generation + 1
                st.session_state['start_choice'] = 'Start blank'
                st.session_state['reset_destination'] = True
                st.session_state.pop('draft_assessment', None)
                st.session_state['submission_notice'] = f'{result.assessment.assessment_id} was submitted to inventory.'
                st.rerun()
        if st.button('Discard draft'):
            st.session_state.pop('draft_assessment', None)
            st.rerun()
        st.download_button('Download review brief', review_brief(result),
                           file_name=f'{result.assessment.assessment_id}-review.md', mime='text/markdown', disabled=stale)
        st.download_button('Download draft JSON', json.dumps(result.model_dump(mode='json'), indent=2),
                           file_name=f'{result.assessment.assessment_id}-assessment.json', mime='application/json', disabled=stale)
    if notice := st.session_state.pop('submission_notice', None):
        st.success(notice)
    with st.expander('Assessment identifiers and provenance'):
        st.caption(f'Next managed assessment ID: DEMO-{sequence:03d}')
        st.json(service.framework.source.model_dump(mode='json'))


def render_comparison(service):
    st.title('Compare AI designs')
    st.write('Compare two complete fictional designs. A lower inherent-risk result is not approval, and a control moving to undetermined still requires human review.')
    examples = [item for item in load_examples() if item.get('information_sensitivity')]
    by_name = {item['system_name']: item for item in examples}
    facts = []
    for index, column in enumerate(st.columns(2)):
        with column:
            heading = 'Option A' if index == 0 else 'Option B'
            st.subheader(heading)
            name = st.selectbox(f'{heading} example', list(by_name), index=0 if index == 0 else min(5, len(examples)-1))
            original = by_name[name]
            st.write(original['business_purpose'])
            with st.expander(f'Edit {heading} characteristics'):
                changes = render_characteristics(service, original, f'comparison:{index}:{name}')
            facts.append({**original, **changes, 'assessment_id': f'COMPARE-{index+1}'})
    if st.button('Compare designs', type='primary'):
        st.session_state.pop('design_comparison', None)
        validations = [service.validate_assessment_input(item) for item in facts]
        if all(item.assessment is not None for item in validations):
            st.session_state['design_comparison'] = {'inputs': facts, 'result': service.compare_ai_design_options(*facts)}
        else:
            st.error('Complete every characteristic in both designs before comparison.')
    stored = st.session_state.get('design_comparison')
    if not stored:
        return
    if stored['inputs'] != facts:
        st.info('Design inputs changed. Compare again to refresh the result.')
        return
    comparison = stored['result']
    a, b = st.columns(2)
    a.metric('Option A inherent risk', label(comparison.option_a.decision.final_tier))
    b.metric('Option B inherent risk', label(comparison.option_b.decision.final_tier))
    st.subheader('What changed')
    st.dataframe([{'Fact': label(item['field']), 'Option A': display_fact_value(item['option_a']), 'Option B': display_fact_value(item['option_b'])}
                  for item in comparison.changed_facts], width='stretch', hide_index=True)
    st.write('Newly matched risk rules: ' + (', '.join(comparison.rules_added) or 'None'))
    st.write('Rules no longer matched: ' + (', '.join(comparison.rules_removed) or 'None'))
    st.subheader('Control applicability transitions')
    if comparison.control_transitions:
        st.dataframe(comparison.control_transitions, width='stretch', hide_index=True)
    else:
        st.info('No control applicability outcomes changed.')
    st.caption('Undetermined means further facts or qualified human judgment are needed. It does not mean not applicable.')
    for heading, result in [('Option A rationale', comparison.option_a), ('Option B rationale', comparison.option_b)]:
        with st.expander(heading):
            st.write(result.decision.executive_summary)
            for reason in result.decision.explanation:
                st.write(reason)
    st.download_button('Download comparison JSON', comparison.model_dump_json(indent=2), 'design-comparison.json', 'application/json')
    st.download_button('Download comparison brief', review_brief(comparison.option_a) + '\n---\n\n' + review_brief(comparison.option_b), 'design-comparison.md', 'text/markdown')


st.set_page_config(page_title='AI Governance Control Plane', page_icon='🧭', layout='wide')
data_mode, inventory = inventory_repository()
if 'next_navigation' in st.session_state:
    st.session_state['navigation'] = st.session_state.pop('next_navigation')
with st.sidebar:
    st.title('Control Plane')
    page = st.selectbox('Go to', ['Start here', 'AI inventory', 'New assessment', 'Compare designs'], key='navigation')
    st.divider()
    framework = load_verified_framework()
    if framework:
        st.success(f'Framework {framework.source.library_version} verified')
    else:
        st.warning('The verified framework dependency is unavailable.')
    with st.expander('Understanding risk tiers'):
        st.write('Tier 1: High. Enhanced multidisciplinary review.')
        st.write('Tier 2: Moderate. Targeted specialist review.')
        st.write('Tier 3: Lower. Standard governance review and testing.')
        st.caption('Inherent risk before controls. Every result requires human review.')
    render_characteristic_reference()
    with st.expander('About this demonstration'):
        st.write('A synthetic prototype showing transparent risk classification and control applicability.')
        st.markdown('[Source and walkthrough](https://github.com/danvanbeeksec/ai-governance-control-plane)')
        st.markdown('[Control authority](https://github.com/danvanbeeksec/ai-governance-control-framework)')
seed_assessment_history(inventory, framework)
if data_mode == 'demo':
    st.info('Demo Mode: use fictional information. New records exist only in this browser session and are not retained.')
else:
    st.warning('Local developer mode: records are retained in the configured SQLite database.')
if page == 'Start here':
    render_start()
elif page == 'AI inventory':
    render_inventory(inventory)
elif framework is None:
    st.error('Assessment is unavailable until the framework dependency is repaired. You can still explore the walkthrough and fictional inventory.')
    st.markdown('[Read the walkthrough](https://github.com/danvanbeeksec/ai-governance-control-plane/blob/main/docs/demo-walkthrough.md)')
elif page == 'New assessment':
    render_new_assessment(decision_service(framework), inventory, data_mode)
else:
    render_comparison(decision_service(framework))
