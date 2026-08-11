from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from ai_governance_control_plane.applicability import RecommendationError, recommend_controls
from ai_governance_control_plane.applicability_contract import (
    ApplicabilityMethodology,
    load_applicability_methodology,
)
from ai_governance_control_framework import controls_bytes
from ai_governance_control_plane.framework_loader import (
    ControlRecord,
    LoadedFramework,
    load_framework_bytes,
)
from ai_governance_control_plane.models import Assessment, FrameworkSource
from ai_governance_control_plane.risk_engine import evaluate_assessment_record, load_model


ROOT = Path(__file__).resolve().parents[1]
RISK_MODEL = load_model(ROOT / "data" / "risk-model.yaml")


def control(control_id, layer="ai_system"):
    return ControlRecord(
        control_id=control_id,
        domain="synthetic_test",
        layer=layer,
        title=f"Synthetic {control_id}",
        objective="Validate deterministic recommendations.",
        requirement="The synthetic system shall support recommendation testing.",
        applicability="Applies only to this synthetic test.",
        evidence_examples=["synthetic result"],
        implementation_notes="Not a real control.",
        references=["SYNTHETIC"],
    )


def synthetic_framework():
    return LoadedFramework(
        source=FrameworkSource(
            repository="synthetic/framework",
            library_version="0.1.0",
            schema_version="1.0",
            commit="a" * 40,
            digest="sha256:" + "b" * 64,
            status="loaded",
        ),
        reference_catalog={"SYNTHETIC": "Synthetic recommendation reference"},
        controls=[
            control("AI-ENT-001", layer="enterprise"),
            control("AI-UNI-001"),
            control("AI-CON-001"),
            control("AI-HUM-001"),
        ],
    )


def synthetic_methodology(status="approved"):
    return ApplicabilityMethodology.model_validate(
        {
            "schema_version": "1.0",
            "methodology": {
                "id": "ai-control-applicability",
                "version": "0.1.0",
                "status": status,
                "framework_library_version": "0.1.0",
                "principle": "Synthetic recommendation methodology.",
            },
            "outcomes": {
                "applicable": "Applies.",
                "inherited_dependency": "Requires inheritance confirmation.",
                "undetermined": "Requires more information.",
            },
            "controls": [
                {
                    "control_id": "AI-ENT-001",
                    "section": "enterprise_dependencies",
                    "treatment": "universal",
                    "enterprise_dependency": True,
                    "rationale": "Synthetic enterprise dependency.",
                },
                {
                    "control_id": "AI-UNI-001",
                    "section": "system_controls",
                    "treatment": "universal",
                    "enterprise_dependency": False,
                    "rationale": "Synthetic universal control.",
                },
                {
                    "control_id": "AI-CON-001",
                    "section": "system_controls",
                    "treatment": "conditional",
                    "enterprise_dependency": False,
                    "rationale": "Synthetic tool control.",
                    "triggers": [
                        {
                            "all": [
                                {
                                    "field": "agent_capabilities",
                                    "operator": "contains_any",
                                    "values": ["external_tools"],
                                }
                            ]
                        },
                        {
                            "all": [
                                {
                                    "field": "information_sensitivity",
                                    "operator": "in",
                                    "values": ["internal", "confidential", "restricted"],
                                }
                            ]
                        },
                    ],
                    "unresolved_questions": ["Does the system use an external tool?"],
                },
                {
                    "control_id": "AI-HUM-001",
                    "section": "system_controls",
                    "treatment": "human_determination",
                    "enterprise_dependency": False,
                    "rationale": "Synthetic human determination.",
                    "unresolved_questions": ["What additional context is required?"],
                },
            ],
        }
    )


def assessment(**overrides):
    values = {
        "assessment_id": "TEST-REC-001",
        "system_name": "Synthetic Recommendation Test",
        "business_purpose": "Validate deterministic control recommendations.",
        "accountable_owner": "Fictional Owner",
        "autonomy_level": "human_supervised",
        "information_sensitivity": "public",
        "human_review": "prior_to_each_meaningful_action",
        "action_authority": "generate_only",
        "system_access": "none",
        "external_reach": "none",
        "reversibility": "easy",
        "decision_impact": "none",
        "agent_capabilities": ["external_tools"],
    }
    values.update(overrides)
    return Assessment.model_validate(values)


def decision_for(item, framework):
    return evaluate_assessment_record(item, RISK_MODEL, framework.source)


def test_generates_separate_enterprise_applicable_and_undetermined_sections():
    framework = synthetic_framework()
    item = assessment()
    result = recommend_controls(
        item, decision_for(item, framework), framework, synthetic_methodology()
    )
    assert result.summary.total_controls == 4
    assert result.summary.enterprise_dependencies == 1
    assert result.summary.applicable_system_controls == 2
    assert result.summary.undetermined_system_controls == 1
    assert result.enterprise_dependencies[0].outcome == "inherited_dependency"
    assert result.undetermined_system_controls[0].outcome == "undetermined"


def test_conditional_match_preserves_fact_and_rule_trace():
    framework = synthetic_framework()
    item = assessment()
    result = recommend_controls(
        item, decision_for(item, framework), framework, synthetic_methodology()
    )
    recommendation = next(
        entry for entry in result.applicable_system_controls if entry.control.control_id == "AI-CON-001"
    )
    assert recommendation.matched_facts[0].field == "agent_capabilities"
    assert recommendation.matched_facts[0].submitted_value == ["external_tools"]
    assert recommendation.unresolved_questions == []


def test_unmatched_conditional_is_undetermined_not_not_applicable():
    framework = synthetic_framework()
    item = assessment(agent_capabilities=[])
    result = recommend_controls(
        item, decision_for(item, framework), framework, synthetic_methodology()
    )
    recommendation = next(
        entry for entry in result.undetermined_system_controls if entry.control.control_id == "AI-CON-001"
    )
    assert recommendation.outcome == "undetermined"
    assert recommendation.unresolved_questions


def test_all_matching_trigger_groups_are_preserved():
    framework = synthetic_framework()
    item = assessment(information_sensitivity="internal")
    result = recommend_controls(
        item, decision_for(item, framework), framework, synthetic_methodology()
    )
    recommendation = next(
        entry for entry in result.applicable_system_controls if entry.control.control_id == "AI-CON-001"
    )
    assert {fact.trigger_group for fact in recommendation.matched_facts} == {1, 2}


def test_recommendations_are_deterministic_and_do_not_change_risk():
    framework = synthetic_framework()
    item = assessment()
    decision = decision_for(item, framework)
    first = recommend_controls(item, decision, framework, synthetic_methodology())
    second = recommend_controls(item, decision, framework, synthetic_methodology())
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.inherent_risk_tier == decision.final_tier


def test_inputs_and_imported_controls_remain_unchanged():
    framework = synthetic_framework()
    item = assessment()
    decision = decision_for(item, framework)
    before_framework = framework.model_dump(mode="json")
    before_assessment = item.model_dump(mode="json")
    recommend_controls(item, decision, framework, synthetic_methodology())
    assert framework.model_dump(mode="json") == before_framework
    assert item.model_dump(mode="json") == before_assessment


def test_unapproved_methodology_is_rejected():
    framework = synthetic_framework()
    item = assessment()
    with pytest.raises(RecommendationError, match="must be approved"):
        recommend_controls(
            item, decision_for(item, framework), framework, synthetic_methodology("ready_for_review")
        )


def test_methodology_drift_blocks_recommendations():
    framework = synthetic_framework()
    framework.controls.append(control("AI-NEW-001"))
    item = assessment()
    with pytest.raises(RecommendationError, match="methodology_update_required"):
        recommend_controls(item, decision_for(item, framework), framework, synthetic_methodology())


def test_mismatched_decision_facts_are_rejected():
    framework = synthetic_framework()
    item = assessment()
    changed = assessment(system_name="Changed After Risk Decision")
    with pytest.raises(RecommendationError, match="facts do not match"):
        recommend_controls(changed, decision_for(item, framework), framework, synthetic_methodology())


def test_all_synthetic_assessments_run_against_actual_framework():
    framework = load_framework_bytes(
        controls_bytes(), ROOT / "data" / "framework-source.yaml"
    )
    methodology = load_applicability_methodology(ROOT / "data" / "control-applicability-rules.yaml")
    with (ROOT / "data" / "example-assessments.yaml").open(encoding="utf-8") as stream:
        examples = yaml.safe_load(stream)["assessments"]
    for example in examples:
        expected = example.pop("expected")
        if expected["status"] != "evaluated":
            continue
        item = Assessment.model_validate(example)
        decision = decision_for(item, framework)
        before_tier = decision.final_tier
        result = recommend_controls(item, decision, framework, methodology)
        assert result.summary.total_controls == len(framework.controls)
        assert (
            result.summary.enterprise_dependencies
            + result.summary.applicable_system_controls
            + result.summary.undetermined_system_controls
            == len(framework.controls)
        )
        assert result.inherent_risk_tier == before_tier
