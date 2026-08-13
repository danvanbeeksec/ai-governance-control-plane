"""Deterministic guided intake for incomplete assessment facts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from .models import Assessment


QUESTIONS = {
    "system_name": "What is the AI system or use case called?",
    "business_purpose": "What business purpose will the AI system serve?",
    "accountable_owner": "Who is accountable for the AI system or use case?",
    "autonomy_level": "How independently can the AI system act?",
    "information_sensitivity": "What is the highest sensitivity of information it can process?",
    "human_review": "When must a person review a meaningful action?",
    "action_authority": "What is the most consequential action the system may take?",
    "system_access": "What level of access does the system have to organizational systems?",
    "external_reach": "How broadly can the system interact outside its immediate environment?",
    "reversibility": "How difficult is it to reverse the system's material effects?",
    "decision_impact": "What is the highest potential impact of decisions it supports or makes?",
    "agent_capabilities": "Which agent capabilities are enabled, if any?",
}

MANAGED_FIELDS = ("assessment_id",)


class AssessmentFieldRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    required: bool = True
    question: str
    allowed_values: list[str] = Field(default_factory=list)
    accepts_multiple: bool = False


class AssessmentRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    fields: list[AssessmentFieldRequirement]
    managed_fields: list[str]
    inference_policy: str


class ProposedInference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    value: Any
    basis: str = Field(min_length=1)
    confirmed: bool = False


class IntakeIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    issue: Literal["missing", "invalid", "unconfirmed_inference"]
    question: str
    detail: str | None = None


class IntakeValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ready_for_assessment", "needs_information"]
    supplied_facts: dict[str, Any]
    confirmed_inferences: dict[str, Any]
    missing_managed_fields: list[str] = Field(default_factory=list)
    issues: list[IntakeIssue]
    assessment: Assessment | None = None


def assessment_requirements() -> AssessmentRequirements:
    schema = Assessment.model_json_schema()
    fields = []
    for name in schema["required"]:
        if name in MANAGED_FIELDS:
            continue
        definition = schema["properties"][name]
        values = definition.get("enum") or definition.get("items", {}).get("enum") or []
        fields.append(
            AssessmentFieldRequirement(
                field=name,
                question=QUESTIONS[name],
                allowed_values=list(values),
                accepts_multiple=definition.get("type") == "array",
            )
        )
    return AssessmentRequirements(
        schema_version="0.1.0",
        fields=fields,
        managed_fields=list(MANAGED_FIELDS),
        inference_policy=(
            "The service never infers facts. A client may propose an inference with its basis, "
            "but the value is excluded until confirmed is true."
        ),
    )


def validate_assessment_input(
    facts: dict[str, Any],
    proposed_inferences: list[ProposedInference | dict[str, Any]] | None = None,
    managed_facts: dict[str, Any] | None = None,
) -> IntakeValidationResult:
    requirements = assessment_requirements()
    known_fields = set(Assessment.model_fields)
    submitted = deepcopy(facts)
    managed = deepcopy(managed_facts or {})
    issues: list[IntakeIssue] = []
    unknown = sorted(set(submitted) - known_fields)
    for field in unknown:
        issues.append(IntakeIssue(field=field, issue="invalid", question="Remove the unsupported field.", detail="Unknown assessment field."))
    unsupported_managed = sorted(set(managed) - set(requirements.managed_fields))
    for field in unsupported_managed:
        issues.append(IntakeIssue(field=field, issue="invalid", question="Remove the unsupported managed field.", detail="Unknown managed assessment field."))
    duplicate_managed = sorted(set(managed) & set(submitted))
    for field in duplicate_managed:
        issues.append(IntakeIssue(field=field, issue="invalid", question="Supply the field once.", detail="A managed field duplicates a supplied fact."))

    confirmed: dict[str, Any] = {}
    for raw in proposed_inferences or []:
        inference = raw if isinstance(raw, ProposedInference) else ProposedInference.model_validate(raw)
        if inference.field not in known_fields:
            issues.append(IntakeIssue(field=inference.field, issue="invalid", question="Remove the unsupported inference.", detail="Unknown assessment field."))
        elif inference.field in submitted:
            issues.append(IntakeIssue(field=inference.field, issue="invalid", question="Use the supplied fact and remove the duplicate inference.", detail="A supplied fact takes precedence."))
        elif inference.confirmed:
            confirmed[inference.field] = deepcopy(inference.value)
        else:
            issues.append(IntakeIssue(field=inference.field, issue="unconfirmed_inference", question=f"Confirm or replace the proposed value for {inference.field}.", detail=inference.basis))

    candidate = {**managed, **submitted, **confirmed}
    requirement_by_field = {item.field: item for item in requirements.fields}
    for field, value in candidate.items():
        if field not in Assessment.model_fields:
            continue
        try:
            TypeAdapter(Assessment.model_fields[field].annotation).validate_python(value)
        except ValidationError as exc:
            issues.append(
                IntakeIssue(
                    field=field,
                    issue="invalid",
                    question=QUESTIONS.get(field, "Provide a supported value."),
                    detail=exc.errors()[0]["msg"],
                )
            )
    for field, requirement in requirement_by_field.items():
        if field not in candidate or candidate[field] in (None, ""):
            if not any(issue.field == field for issue in issues):
                issues.append(IntakeIssue(field=field, issue="missing", question=requirement.question))

    missing_managed = [
        field for field in requirements.managed_fields if field not in candidate
    ]
    assessment = None
    if not issues and not missing_managed:
        try:
            assessment = Assessment.model_validate(candidate)
        except ValidationError as exc:
            for error in exc.errors():
                field = str(error["loc"][0])
                issues.append(IntakeIssue(field=field, issue="invalid", question=QUESTIONS.get(field, "Provide a supported value."), detail=error["msg"]))

    return IntakeValidationResult(
        status="ready_for_assessment" if assessment is not None else "needs_information",
        supplied_facts=submitted,
        confirmed_inferences=confirmed,
        missing_managed_fields=missing_managed,
        issues=issues,
        assessment=assessment,
    )
