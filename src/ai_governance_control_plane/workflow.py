"""End-to-end assessment workflow shared by human interfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from .applicability import ControlRecommendationSet, recommend_controls
from .applicability_contract import load_applicability_methodology
from .applicability_contract import ApplicabilityMethodology
from .framework_loader import LoadedFramework
from .models import Assessment, DecisionRecord
from .risk_engine import evaluate_assessment_record, load_model


class AssessmentResult(BaseModel):
    """Combined presentation contract without merging risk and control authority."""

    model_config = ConfigDict(extra="forbid")

    assessment: Assessment
    decision: DecisionRecord
    recommendations: ControlRecommendationSet


def run_assessment_workflow(
    assessment: Assessment | dict[str, Any],
    framework: LoadedFramework,
    risk_model_path: str | Path | dict[str, Any],
    methodology_path: str | Path | ApplicabilityMethodology,
) -> AssessmentResult:
    """Run validated risk evaluation followed by control recommendation."""
    validated = (
        assessment if isinstance(assessment, Assessment) else Assessment.model_validate(assessment)
    )
    risk_model = risk_model_path if isinstance(risk_model_path, dict) else load_model(risk_model_path)
    methodology = (
        methodology_path
        if isinstance(methodology_path, ApplicabilityMethodology)
        else load_applicability_methodology(methodology_path)
    )
    decision = evaluate_assessment_record(validated, risk_model, framework.source)
    recommendations = recommend_controls(validated, decision, framework, methodology)
    return AssessmentResult(
        assessment=validated,
        decision=decision,
        recommendations=recommendations,
    )
