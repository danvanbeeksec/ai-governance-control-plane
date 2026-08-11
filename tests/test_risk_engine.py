from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from ai_governance_control_plane import Assessment, DecisionRecord
from ai_governance_control_plane.risk_engine import (
    AssessmentError,
    evaluate_assessment,
    evaluate_assessment_record,
    load_model,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL = load_model(ROOT / "data" / "risk-model.yaml")


def base_assessment(**overrides):
    assessment = {
        "assessment_id": "TEST-001",
        "system_name": "Synthetic Test System",
        "business_purpose": "Validate independently authored decision rules.",
        "accountable_owner": "Fictional Owner",
        "autonomy_level": "human_supervised",
        "information_sensitivity": "public",
        "human_review": "prior_to_each_meaningful_action",
        "action_authority": "generate_only",
        "system_access": "none",
        "external_reach": "none",
        "reversibility": "easy",
        "decision_impact": "none",
        "agent_capabilities": [],
    }
    assessment.update(overrides)
    return assessment


@pytest.mark.parametrize(
    ("autonomy", "sensitivity", "expected"),
    [
        ("autonomous", "public", "tier_2"),
        ("autonomous", "internal", "tier_2"),
        ("autonomous", "confidential", "tier_1"),
        ("autonomous", "restricted", "tier_1"),
        ("conditionally_autonomous", "public", "tier_3"),
        ("conditionally_autonomous", "internal", "tier_3"),
        ("conditionally_autonomous", "confidential", "tier_2"),
        ("conditionally_autonomous", "restricted", "tier_1"),
        ("human_supervised", "public", "tier_3"),
        ("human_supervised", "internal", "tier_3"),
        ("human_supervised", "confidential", "tier_3"),
        ("human_supervised", "restricted", "tier_1"),
    ],
)
def test_all_baseline_matrix_combinations(autonomy, sensitivity, expected):
    result = evaluate_assessment(
        base_assessment(autonomy_level=autonomy, information_sensitivity=sensitivity), MODEL
    )
    assert result["baseline_tier"] == expected


@pytest.mark.parametrize(
    ("overrides", "rule_id", "expected"),
    [
        ({"action_authority": "modify_production", "human_review": "no_prior_review"}, "ER-001", "tier_1"),
        ({"system_access": "privileged", "agent_capabilities": ["external_tools"]}, "ER-002", "tier_2"),
        ({"decision_impact": "consequential", "reversibility": "difficult"}, "ER-003", "tier_1"),
        ({"decision_impact": "regulated_or_consequential", "human_review": "no_prior_review"}, "ER-004", "tier_1"),
        ({"autonomy_level": "autonomous", "external_reach": "broad", "agent_capabilities": ["external_communication"]}, "ER-005", "tier_1"),
    ],
)
def test_each_contextual_elevation_rule(overrides, rule_id, expected):
    result = evaluate_assessment(base_assessment(**overrides), MODEL)
    assert result["final_tier"] == expected
    assert rule_id in [rule["rule_id"] for rule in result["applied_rules"]]


def test_rules_never_lower_baseline_tier():
    result = evaluate_assessment(
        base_assessment(information_sensitivity="restricted", system_access="privileged", agent_capabilities=["external_tools"]),
        MODEL,
    )
    assert result["baseline_tier"] == "tier_1"
    assert result["final_tier"] == "tier_1"
    assert all(rule["resulting_tier"] == "tier_1" for rule in result["applied_rules"])


def test_missing_critical_input_fails_closed_without_tier():
    assessment = base_assessment()
    assessment["information_sensitivity"] = None
    result = evaluate_assessment(assessment, MODEL)
    assert result["status"] == "insufficient_information"
    assert result["missing_inputs"] == ["information_sensitivity"]
    assert result["baseline_tier"] is None
    assert result["final_tier"] is None


def test_missing_rule_driving_context_fails_closed():
    assessment = base_assessment()
    del assessment["system_access"]
    result = evaluate_assessment(assessment, MODEL)
    assert result["status"] == "insufficient_information"
    assert result["missing_inputs"] == ["system_access"]
    assert result["final_tier"] is None


def test_invalid_enum_is_rejected():
    with pytest.raises(AssessmentError, match="Assessment failed schema validation"):
        evaluate_assessment(base_assessment(autonomy_level="mostly_autonomous"), MODEL)


def test_explanation_is_traceable_and_versioned():
    result = evaluate_assessment(
        base_assessment(action_authority="execute_material_transaction", human_review="checkpoints_or_exceptions"),
        MODEL,
    )
    assert result["model_id"] == "ai-governance-inherent-risk"
    assert result["model_version"] == "0.1.0"
    assert result["baseline_inputs"] == {
        "autonomy_level": "human_supervised",
        "information_sensitivity": "public",
    }
    assert result["applied_rules"][0].keys() >= {
        "rule_id", "reason", "prior_tier", "resulting_tier", "changed_tier"
    }
    explanation = " ".join(result["explanation"])
    assert "starting point is Tier 3" in explanation
    assert "human supervised" in explanation
    assert "public information" in explanation
    assert "ER-001" in explanation
    assert "final inherent risk classification is Tier 1" in explanation
    assert "autonomy_level" not in explanation
    assert "tier_1" not in explanation
    assert result["human_review_required"] is True
    assert result["assessment_schema_version"] == "0.1.0"
    assert result["submitted_facts"]["assessment_id"] == "TEST-001"
    assert "Tier 1 inherent AI system risk" in result["executive_summary"]
    assert result["framework_source"]["status"] == "not_loaded"


def test_every_example_matches_its_expected_outcome():
    with (ROOT / "data" / "example-assessments.yaml").open(encoding="utf-8") as stream:
        examples = yaml.safe_load(stream)["assessments"]
    for example in examples:
        expected = example.pop("expected")
        result = evaluate_assessment(example, MODEL)
        assert result["status"] == expected["status"], example["assessment_id"]
        assert result["baseline_tier"] == expected["baseline_tier"], example["assessment_id"]
        assert result["final_tier"] == expected["final_tier"], example["assessment_id"]
        assert [rule["rule_id"] for rule in result["applied_rules"]] == expected["applied_rule_ids"], example["assessment_id"]
        if expected.get("missing_inputs"):
            assert result["missing_inputs"] == expected["missing_inputs"]


def test_policy_data_can_change_a_decision_without_code_change():
    altered = deepcopy(MODEL)
    altered["baseline_matrix"]["human_supervised"]["public"] = "tier_2"
    assert evaluate_assessment(base_assessment(), altered)["baseline_tier"] == "tier_2"


def test_typed_assessment_produces_typed_decision_record():
    assessment = Assessment.model_validate(base_assessment())
    result = evaluate_assessment_record(assessment, MODEL)
    assert isinstance(result, DecisionRecord)
    assert result.assessment_id == assessment.assessment_id
    assert result.submitted_facts["schema_version"] == "0.1.0"


def test_duplicate_agent_capabilities_are_rejected():
    with pytest.raises(AssessmentError, match="agent_capabilities must not contain duplicates"):
        evaluate_assessment(
            base_assessment(agent_capabilities=["external_tools", "external_tools"]), MODEL
        )


def test_extra_assessment_fields_are_rejected():
    with pytest.raises(AssessmentError, match="Assessment failed schema validation"):
        evaluate_assessment(base_assessment(uncontrolled_field="value"), MODEL)


def test_model_loader_rejects_incomplete_matrix(tmp_path):
    altered = deepcopy(MODEL)
    del altered["baseline_matrix"]["human_supervised"]["public"]
    path = tmp_path / "invalid-model.yaml"
    path.write_text(yaml.safe_dump(altered), encoding="utf-8")
    with pytest.raises(AssessmentError, match="must contain every information_sensitivity"):
        load_model(path)


def test_model_loader_rejects_duplicate_rule_ids(tmp_path):
    altered = deepcopy(MODEL)
    altered["elevation_rules"][1]["id"] = altered["elevation_rules"][0]["id"]
    path = tmp_path / "invalid-model.yaml"
    path.write_text(yaml.safe_dump(altered), encoding="utf-8")
    with pytest.raises(AssessmentError, match="rule IDs must be unique"):
        load_model(path)


def test_model_loader_rejects_enum_contract_drift(tmp_path):
    altered = deepcopy(MODEL)
    altered["enums"]["autonomy_level"].append("uncontrolled_new_value")
    path = tmp_path / "invalid-model.yaml"
    path.write_text(yaml.safe_dump(altered), encoding="utf-8")
    with pytest.raises(AssessmentError, match="does not match the typed assessment contract"):
        load_model(path)
