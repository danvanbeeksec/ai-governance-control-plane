"""Deterministic control recommendations from an approved applicability methodology."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .applicability_contract import (
    ApplicabilityMethodology,
    Condition,
    ControlTreatment,
    validate_applicability_methodology,
)
from .framework_loader import ControlRecord, LoadedFramework
from .models import Assessment, DecisionRecord, FrameworkSource, Tier


class RecommendationError(ValueError):
    """Raised when a recommendation set cannot be produced safely."""


class MatchedFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    operator: Literal["in", "contains_any"]
    submitted_value: Any
    expected_values: list[str]
    trigger_group: int = Field(ge=1)


class ControlRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control: ControlRecord
    section: Literal["enterprise_dependencies", "system_controls"]
    treatment: Literal["universal", "conditional", "human_determination"]
    outcome: Literal["applicable", "inherited_dependency", "undetermined"]
    enterprise_dependency: bool
    rationale: str
    matched_facts: list[MatchedFact] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    human_confirmation_required: bool = True


class RecommendationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_controls: int
    enterprise_dependencies: int
    applicable_system_controls: int
    undetermined_system_controls: int


class ControlRecommendationSet(BaseModel):
    """Versioned recommendation output kept separate from the risk decision."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["recommendations_generated"]
    assessment_id: str
    assessment_schema_version: str
    risk_model_id: str
    risk_model_version: str
    inherent_risk_tier: Tier
    framework_source: FrameworkSource
    methodology_id: str
    methodology_version: str
    methodology_schema_version: str
    enterprise_dependencies: list[ControlRecommendation]
    applicable_system_controls: list[ControlRecommendation]
    undetermined_system_controls: list[ControlRecommendation]
    summary: RecommendationSummary
    human_confirmation_required: bool = True


def _condition_matches(facts: dict[str, Any], condition: Condition) -> bool:
    actual = facts[condition.field]
    if condition.operator == "in":
        return actual in condition.values
    if condition.operator == "contains_any":
        return any(value in actual for value in condition.values)
    raise RecommendationError(f"Unsupported applicability operator: {condition.operator}")


def _matched_facts(
    facts: dict[str, Any], treatment: ControlTreatment
) -> list[MatchedFact]:
    matched: list[MatchedFact] = []
    for group_number, group in enumerate(treatment.triggers, start=1):
        if not all(_condition_matches(facts, condition) for condition in group.all):
            continue
        for condition in group.all:
            matched.append(
                MatchedFact(
                    field=condition.field,
                    operator=condition.operator,
                    submitted_value=deepcopy(facts[condition.field]),
                    expected_values=list(condition.values),
                    trigger_group=group_number,
                )
            )
    return matched


def _recommend_control(
    control: ControlRecord, treatment: ControlTreatment, facts: dict[str, Any]
) -> ControlRecommendation:
    if treatment.section == "enterprise_dependencies":
        outcome = "inherited_dependency"
        matched = []
        questions = [
            "Confirm the enterprise provider, inheritance scope, required configuration, exclusions, evidence, and review period."
        ]
    elif treatment.treatment == "universal":
        outcome = "applicable"
        matched = []
        questions = []
    elif treatment.treatment == "human_determination":
        outcome = "undetermined"
        matched = []
        questions = list(treatment.unresolved_questions)
    else:
        matched = _matched_facts(facts, treatment)
        outcome = "applicable" if matched else "undetermined"
        questions = [] if matched else list(treatment.unresolved_questions)

    return ControlRecommendation(
        control=control.model_copy(deep=True),
        section=treatment.section,
        treatment=treatment.treatment,
        outcome=outcome,
        enterprise_dependency=treatment.enterprise_dependency,
        rationale=treatment.rationale,
        matched_facts=matched,
        unresolved_questions=questions,
    )


def recommend_controls(
    assessment: Assessment | dict[str, Any],
    decision: DecisionRecord | dict[str, Any],
    framework: LoadedFramework,
    methodology: ApplicabilityMethodology,
) -> ControlRecommendationSet:
    """Create deterministic recommendations without changing the risk decision."""
    if methodology.methodology.status != "approved":
        raise RecommendationError("Applicability methodology must be approved")
    try:
        validate_applicability_methodology(methodology, framework)
    except ValueError as exc:
        raise RecommendationError(str(exc)) from exc

    validated_assessment = (
        assessment if isinstance(assessment, Assessment) else Assessment.model_validate(assessment)
    )
    validated_decision = (
        decision if isinstance(decision, DecisionRecord) else DecisionRecord.model_validate(decision)
    )
    facts = validated_assessment.model_dump(mode="json")
    if validated_decision.status != "evaluated" or validated_decision.final_tier is None:
        raise RecommendationError("A completed inherent-risk decision is required")
    if validated_decision.assessment_id != validated_assessment.assessment_id:
        raise RecommendationError("Assessment and risk decision identifiers do not match")
    if validated_decision.submitted_facts != facts:
        raise RecommendationError("Assessment facts do not match the risk decision")
    if validated_decision.framework_source != framework.source:
        raise RecommendationError("Risk decision framework provenance does not match the loaded framework")

    controls_by_id = {control.control_id: control for control in framework.controls}
    enterprise_dependencies: list[ControlRecommendation] = []
    applicable: list[ControlRecommendation] = []
    undetermined: list[ControlRecommendation] = []
    for treatment in methodology.controls:
        recommendation = _recommend_control(controls_by_id[treatment.control_id], treatment, facts)
        if recommendation.section == "enterprise_dependencies":
            enterprise_dependencies.append(recommendation)
        elif recommendation.outcome == "applicable":
            applicable.append(recommendation)
        else:
            undetermined.append(recommendation)

    summary = RecommendationSummary(
        total_controls=len(framework.controls),
        enterprise_dependencies=len(enterprise_dependencies),
        applicable_system_controls=len(applicable),
        undetermined_system_controls=len(undetermined),
    )
    return ControlRecommendationSet(
        status="recommendations_generated",
        assessment_id=validated_assessment.assessment_id,
        assessment_schema_version=validated_assessment.schema_version,
        risk_model_id=validated_decision.model_id,
        risk_model_version=validated_decision.model_version,
        inherent_risk_tier=validated_decision.final_tier,
        framework_source=framework.source,
        methodology_id=methodology.methodology.id,
        methodology_version=methodology.methodology.version,
        methodology_schema_version=methodology.schema_version,
        enterprise_dependencies=enterprise_dependencies,
        applicable_system_controls=applicable,
        undetermined_system_controls=undetermined,
        summary=summary,
    )
