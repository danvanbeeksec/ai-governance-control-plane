from ai_governance_control_plane.intake import assessment_requirements, validate_assessment_input


COMPLETE = {
    "assessment_id": "guided-001",
    "system_name": "Synthetic Assistant",
    "business_purpose": "Validate guided intake",
    "accountable_owner": "Synthetic Owner",
    "autonomy_level": "human_supervised",
    "information_sensitivity": "internal",
    "human_review": "prior_to_each_meaningful_action",
    "action_authority": "generate_only",
    "system_access": "none",
    "external_reach": "none",
    "reversibility": "easy",
    "decision_impact": "operational",
    "agent_capabilities": [],
}


def test_requirements_are_derived_from_assessment_contract():
    result = assessment_requirements()
    assert {item.field for item in result.fields} == set(COMPLETE)
    autonomy = next(item for item in result.fields if item.field == "autonomy_level")
    assert "autonomous" in autonomy.allowed_values
    assert "never infers facts" in result.inference_policy


def test_partial_input_returns_missing_questions_and_invalid_values():
    result = validate_assessment_input({"assessment_id": "guided-001", "autonomy_level": "magic"})
    assert result.status == "needs_information"
    assert any(item.field == "system_name" and item.issue == "missing" for item in result.issues)
    assert any(item.field == "autonomy_level" and item.issue == "invalid" for item in result.issues)


def test_unconfirmed_inference_is_not_used():
    facts = {key: value for key, value in COMPLETE.items() if key != "information_sensitivity"}
    result = validate_assessment_input(
        facts,
        [{"field": "information_sensitivity", "value": "internal", "basis": "User mentioned internal documents"}],
    )
    assert result.status == "needs_information"
    assert result.confirmed_inferences == {}
    assert any(item.issue == "unconfirmed_inference" for item in result.issues)


def test_confirmed_inference_can_complete_assessment():
    facts = {key: value for key, value in COMPLETE.items() if key != "information_sensitivity"}
    result = validate_assessment_input(
        facts,
        [{"field": "information_sensitivity", "value": "internal", "basis": "Confirmed by user", "confirmed": True}],
    )
    assert result.status == "ready_for_assessment"
    assert result.assessment is not None
    assert result.assessment.information_sensitivity == "internal"


def test_complete_supplied_facts_are_ready_without_inference():
    result = validate_assessment_input(COMPLETE)
    assert result.status == "ready_for_assessment"
    assert result.assessment is not None
