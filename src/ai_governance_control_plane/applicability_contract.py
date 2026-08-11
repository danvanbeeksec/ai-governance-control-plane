"""Validation contract for the control-applicability methodology."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .framework_loader import LoadedFramework
from .models import Assessment


class ApplicabilityContractError(ValueError):
    """Raised when the methodology is incomplete or inconsistent."""


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    operator: Literal["in", "contains_any"]
    values: list[str] = Field(min_length=1)


class TriggerGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    all: list[Condition] = Field(min_length=1)


class ControlTreatment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str
    section: Literal["enterprise_dependencies", "system_controls"]
    treatment: Literal["universal", "conditional", "human_determination"]
    enterprise_dependency: bool
    rationale: str = Field(min_length=1)
    triggers: list[TriggerGroup] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def treatment_has_required_support(self):
        if self.treatment == "conditional" and not self.triggers:
            raise ValueError("conditional treatments require at least one trigger group")
        if self.treatment != "conditional" and self.triggers:
            raise ValueError("only conditional treatments may define trigger groups")
        if self.treatment in {"conditional", "human_determination"} and not self.unresolved_questions:
            raise ValueError("conditional and human-determination treatments require questions")
        return self


class MethodologyMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Literal["ai-control-applicability"]
    version: str = Field(min_length=1)
    status: Literal["ready_for_review", "approved"]
    framework_library_version: str = Field(min_length=1)
    principle: str = Field(min_length=1)


class ApplicabilityMethodology(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    methodology: MethodologyMetadata
    outcomes: dict[str, str]
    controls: list[ControlTreatment] = Field(min_length=1)

    @model_validator(mode="after")
    def outcomes_are_explicit(self):
        expected = {"applicable", "inherited_dependency", "undetermined"}
        if set(self.outcomes) != expected:
            raise ValueError(f"outcomes must be exactly {sorted(expected)}")
        return self


class CompatibilityReport(BaseModel):
    """Compatibility state between one framework and one methodology version."""

    status: Literal["compatible", "methodology_update_required"]
    framework_library_version: str | None
    methodology_framework_library_version: str
    version_match: bool
    missing_controls: list[str] = Field(default_factory=list)
    unknown_controls: list[str] = Field(default_factory=list)
    duplicate_treatments: list[str] = Field(default_factory=list)


def load_applicability_methodology(path: str | Path) -> ApplicabilityMethodology:
    try:
        with Path(path).open(encoding="utf-8") as stream:
            methodology = ApplicabilityMethodology.model_validate(yaml.safe_load(stream))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ApplicabilityContractError(f"Applicability methodology is invalid: {exc}") from exc
    _validate_assessment_conditions(methodology)
    return methodology


def _validate_assessment_conditions(methodology: ApplicabilityMethodology) -> None:
    assessment_schema = Assessment.model_json_schema()["properties"]
    for treatment in methodology.controls:
        for group in treatment.triggers:
            for condition in group.all:
                if condition.field not in assessment_schema:
                    raise ApplicabilityContractError(
                        f"Control {treatment.control_id} references unknown assessment field {condition.field}"
                    )
                property_schema = assessment_schema[condition.field]
                allowed = property_schema.get("enum") or property_schema.get("items", {}).get("enum")
                if allowed is None or not set(condition.values) <= set(allowed):
                    raise ApplicabilityContractError(
                        f"Control {treatment.control_id} uses values outside the {condition.field} contract"
                    )


def assess_methodology_compatibility(
    methodology: ApplicabilityMethodology, framework: LoadedFramework
) -> CompatibilityReport:
    """Report whether a methodology completely treats one framework version."""
    framework_by_id = {control.control_id: control for control in framework.controls}
    treatment_counts = Counter(item.control_id for item in methodology.controls)
    treatment_by_id = {item.control_id: item for item in methodology.controls}
    missing = sorted(set(framework_by_id) - set(treatment_by_id))
    unknown = sorted(set(treatment_by_id) - set(framework_by_id))
    duplicates = sorted(control_id for control_id, count in treatment_counts.items() if count > 1)
    version_match = (
        methodology.methodology.framework_library_version == framework.source.library_version
    )
    update_required = bool(missing or unknown or duplicates or not version_match)
    return CompatibilityReport(
        status="methodology_update_required" if update_required else "compatible",
        framework_library_version=framework.source.library_version,
        methodology_framework_library_version=methodology.methodology.framework_library_version,
        version_match=version_match,
        missing_controls=missing,
        unknown_controls=unknown,
        duplicate_treatments=duplicates,
    )


def validate_applicability_methodology(
    methodology: ApplicabilityMethodology, framework: LoadedFramework
) -> None:
    """Fail closed unless the methodology is compatible with the loaded framework."""
    report = assess_methodology_compatibility(methodology, framework)
    if report.status == "methodology_update_required":
        raise ApplicabilityContractError(
            "methodology_update_required: "
            f"missing={report.missing_controls}, unknown={report.unknown_controls}, "
            f"duplicates={report.duplicate_treatments}, version_match={report.version_match}"
        )

    framework_by_id = {control.control_id: control for control in framework.controls}
    treatment_by_id = {item.control_id: item for item in methodology.controls}
    for control_id, treatment in treatment_by_id.items():
        framework_control = framework_by_id[control_id]
        if framework_control.layer == "enterprise" and treatment.section != "enterprise_dependencies":
            raise ApplicabilityContractError(
                f"Enterprise control {control_id} must appear in enterprise_dependencies"
            )
        if treatment.section == "enterprise_dependencies" and (
            treatment.treatment != "universal" or not treatment.enterprise_dependency
        ):
            raise ApplicabilityContractError(
                f"Enterprise dependency {control_id} must be universal and require inheritance confirmation"
            )
