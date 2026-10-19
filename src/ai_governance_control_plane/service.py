"""Reusable application service for governance assessments and control queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

from pydantic import BaseModel, ConfigDict

from .applicability import ControlRecommendationSet
from .applicability_contract import (
    ApplicabilityMethodology,
    load_applicability_methodology,
    load_applicability_methodology_bytes,
)
from .framework_loader import (
    ControlRecord,
    LoadedFramework,
    load_framework,
    load_framework_packaged_bytes,
)
from .models import Assessment
from .intake import (
    AssessmentRequirements,
    IntakeValidationResult,
    ProposedInference,
    assessment_requirements,
    validate_assessment_input,
)
from .resources import (
    applicability_methodology_bytes,
    framework_manifest_bytes,
    risk_model_bytes,
)
from .risk_engine import load_model, load_model_bytes
from .workflow import AssessmentResult, run_assessment_workflow


class DesignComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    option_a: AssessmentResult
    option_b: AssessmentResult
    tier_changed: bool
    controls_added: list[str]
    controls_removed: list[str]
    changed_facts: list[dict[str, Any]]
    rules_added: list[str]
    rules_removed: list[str]
    control_transitions: list[dict[str, str]]


class GovernanceDecisionService:
    """UI-independent facade over the deterministic domain engines."""

    def __init__(self, framework: LoadedFramework, risk_model: dict[str, Any], methodology: ApplicabilityMethodology) -> None:
        self.framework = framework
        self.risk_model = risk_model
        self.methodology = methodology

    @classmethod
    def from_paths(cls, framework_path: str | Path, manifest_path: str | Path, risk_model_path: str | Path, methodology_path: str | Path) -> "GovernanceDecisionService":
        return cls(
            load_framework(framework_path, manifest_path),
            load_model(risk_model_path),
            load_applicability_methodology(methodology_path),
        )

    @classmethod
    def from_packaged_resources(cls) -> "GovernanceDecisionService":
        """Construct the service entirely from installed package resources."""
        from ai_governance_control_framework import controls_bytes

        return cls(
            load_framework_packaged_bytes(controls_bytes(), framework_manifest_bytes()),
            load_model_bytes(risk_model_bytes()),
            load_applicability_methodology_bytes(applicability_methodology_bytes()),
        )

    def get_assessment_requirements(self) -> AssessmentRequirements:
        return assessment_requirements()

    def runtime_identity(self) -> dict[str, str]:
        """Identify actual executable source and policy bytes, including source overrides."""
        from . import __version__
        import json
        digest = hashlib.sha256()
        for path in sorted(Path(__file__).parent.glob("*.py")):
            digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
        policy = {"risk_model": self.risk_model, "methodology": self.methodology.model_dump(mode="json")}
        return {"version": __version__, "implementation_sha256": digest.hexdigest(),
                "policy_sha256": hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest(),
                "framework_digest": self.framework.source.digest,
                "framework_commit": self.framework.source.commit}

    def validate_assessment_input(
        self,
        facts: dict[str, Any],
        proposed_inferences: list[ProposedInference | dict[str, Any]] | None = None,
        managed_facts: dict[str, Any] | None = None,
    ) -> IntakeValidationResult:
        return validate_assessment_input(facts, proposed_inferences, managed_facts)

    def assess_ai_system(self, assessment: Assessment | dict[str, Any]) -> AssessmentResult:
        return run_assessment_workflow(
            assessment, self.framework, self.risk_model, self.methodology
        )

    def get_applicable_controls(self, assessment: Assessment | dict[str, Any]) -> ControlRecommendationSet:
        return self.assess_ai_system(assessment).recommendations

    def explain_control(self, control_id: str) -> ControlRecord:
        for control in self.framework.controls:
            if control.control_id == control_id:
                return control.model_copy(deep=True)
        raise KeyError(f"Unknown control ID: {control_id}")

    def compare_ai_design_options(self, option_a: Assessment | dict[str, Any], option_b: Assessment | dict[str, Any]) -> DesignComparison:
        left = self.assess_ai_system(option_a)
        right = self.assess_ai_system(option_b)
        left_ids = {item.control.control_id for item in left.recommendations.applicable_system_controls}
        right_ids = {item.control.control_id for item in right.recommendations.applicable_system_controls}
        def outcomes(result):
            return {item.control.control_id: item.outcome for group in
                    (result.recommendations.applicable_system_controls,
                     result.recommendations.undetermined_system_controls,
                     result.recommendations.enterprise_dependencies) for item in group}
        left_outcomes, right_outcomes = outcomes(left), outcomes(right)
        left_rules = {rule.rule_id for rule in left.decision.applied_rules}
        right_rules = {rule.rule_id for rule in right.decision.applied_rules}
        a, b = left.assessment.model_dump(mode="json"), right.assessment.model_dump(mode="json")
        return DesignComparison(
            option_a=left, option_b=right, tier_changed=left.decision.final_tier != right.decision.final_tier,
            controls_added=sorted(right_ids - left_ids), controls_removed=sorted(left_ids - right_ids),
            changed_facts=[{"field": key, "option_a": a[key], "option_b": b[key]} for key in a
                           if key not in {"assessment_id", "schema_version"} and a[key] != b[key]],
            rules_added=sorted(right_rules - left_rules), rules_removed=sorted(left_rules - right_rules),
            control_transitions=[{"control_id": key, "option_a": left_outcomes[key], "option_b": right_outcomes[key]}
                                 for key in sorted(left_outcomes) if left_outcomes[key] != right_outcomes[key]],
        )
