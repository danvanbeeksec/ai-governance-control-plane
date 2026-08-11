"""Deterministic, policy-data-driven inherent AI risk evaluation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import Assessment, DecisionRecord, FrameworkSource
from .summarize import build_executive_summary, tier_qualitative_label


class AssessmentError(ValueError):
    """Raised when an assessment or policy model is invalid."""


def load_model(path: str | Path) -> dict[str, Any]:
    """Load and validate a YAML risk model and its decision-affecting contracts."""
    model_path = Path(path)
    with model_path.open(encoding="utf-8") as stream:
        model = yaml.safe_load(stream)
    required = {
        "model", "enums", "required_inputs", "baseline_matrix", "elevation_rules", "explainability"
    }
    if not isinstance(model, dict) or not required.issubset(model):
        missing = sorted(required - set(model or {}))
        raise AssessmentError(f"Risk model is missing required sections: {missing}")
    _validate_model(model)
    return model


def _validate_model(model: dict[str, Any]) -> None:
    metadata = model["model"]
    tiers = metadata.get("tier_order")
    if not isinstance(tiers, list) or not tiers or len(tiers) != len(set(tiers)):
        raise AssessmentError("model.tier_order must be a non-empty list of unique tiers")

    required_inputs = model["required_inputs"]
    if len(required_inputs) != len(set(required_inputs)):
        raise AssessmentError("required_inputs contains duplicates")

    assessment_properties = Assessment.model_json_schema()["properties"]
    for field, allowed in model["enums"].items():
        if field not in assessment_properties:
            raise AssessmentError(f"enums references unknown assessment field {field}")
        property_schema = assessment_properties[field]
        contract_values = property_schema.get("enum") or property_schema.get("items", {}).get("enum")
        if contract_values is None or set(allowed) != set(contract_values):
            raise AssessmentError(f"enums.{field} does not match the typed assessment contract")

    autonomy_values = model["enums"].get("autonomy_level", [])
    sensitivity_values = model["enums"].get("information_sensitivity", [])
    matrix = model["baseline_matrix"]
    if set(matrix) != set(autonomy_values):
        raise AssessmentError("baseline_matrix must contain every autonomy_level exactly once")
    for autonomy in autonomy_values:
        if set(matrix[autonomy]) != set(sensitivity_values):
            raise AssessmentError(
                f"baseline_matrix.{autonomy} must contain every information_sensitivity exactly once"
            )
        if any(tier not in tiers for tier in matrix[autonomy].values()):
            raise AssessmentError(f"baseline_matrix.{autonomy} references an unknown tier")

    rule_ids: list[str] = []
    allowed_operators = {"equals", "in", "any_of"}
    for rule in model["elevation_rules"]:
        required_rule_fields = {"id", "name", "when", "minimum_tier", "reason"}
        if not required_rule_fields.issubset(rule):
            raise AssessmentError(f"elevation rule is missing fields: {sorted(required_rule_fields - set(rule))}")
        rule_ids.append(rule["id"])
        if rule["minimum_tier"] not in tiers:
            raise AssessmentError(f"rule {rule['id']} references an unknown minimum_tier")
        for field, condition in rule["when"].items():
            if field not in required_inputs:
                raise AssessmentError(f"rule {rule['id']} references unknown input {field}")
            if isinstance(condition, dict):
                operators = set(condition)
                if len(operators) != 1 or not operators <= allowed_operators:
                    raise AssessmentError(f"rule {rule['id']} uses an unsupported condition operator")
    if len(rule_ids) != len(set(rule_ids)):
        raise AssessmentError("elevation rule IDs must be unique")


def _matches(assessment: dict[str, Any], conditions: dict[str, Any]) -> bool:
    for field, expected in conditions.items():
        actual = assessment.get(field)
        if isinstance(expected, dict):
            if "equals" in expected and actual != expected["equals"]:
                return False
            if "in" in expected and actual not in expected["in"]:
                return False
            if "any_of" in expected:
                actual_values = actual if isinstance(actual, list) else [actual]
                if not any(value in actual_values for value in expected["any_of"]):
                    return False
        elif actual != expected:
            return False
    return True


def _higher_tier(left: str, right: str, order: list[str]) -> str:
    """Return the more rigorous tier, where the earliest tier is highest."""
    return left if order.index(left) <= order.index(right) else right


def evaluate_assessment_record(
    assessment: dict[str, Any] | Assessment,
    model: dict[str, Any],
    framework_source: FrameworkSource | None = None,
) -> DecisionRecord:
    """Evaluate an assessment and return a typed, auditable decision record."""
    facts = assessment.model_dump(mode="json") if isinstance(assessment, Assessment) else deepcopy(assessment)
    assessment_schema_version = str(facts.get("schema_version", "0.1.0"))
    missing = [field for field in model["required_inputs"] if facts.get(field) in (None, "")]
    if missing:
        partial = {
            "status": "insufficient_information",
            "assessment_id": facts.get("assessment_id"),
            "model_id": model["model"]["id"],
            "model_version": str(model["model"]["version"]),
            "assessment_schema_version": assessment_schema_version,
            "submitted_facts": facts,
            "missing_inputs": missing,
            "baseline_inputs": {
                "autonomy_level": facts.get("autonomy_level"),
                "information_sensitivity": facts.get("information_sensitivity"),
            },
            "baseline_tier": None,
            "baseline_tier_label": None,
            "final_tier": None,
            "final_tier_label": None,
            "applied_rules": [],
            "explanation": [f"No tier assigned because required inputs are missing: {', '.join(missing)}."],
            "human_review_required": True,
            "framework_source": framework_source or FrameworkSource(),
        }

        partial["unresolved_questions"] = [f"Provide a supported value for {field}." for field in missing]
        partial["executive_summary"] = build_executive_summary(facts, partial)
        return DecisionRecord.model_validate(partial)

    try:
        validated = Assessment.model_validate(facts)
    except ValidationError as exc:
        raise AssessmentError(f"Assessment failed schema validation: {exc}") from exc
    facts = validated.model_dump(mode="json")

    autonomy = facts["autonomy_level"]
    sensitivity = facts["information_sensitivity"]
    try:
        baseline = model["baseline_matrix"][autonomy][sensitivity]
    except KeyError as exc:
        raise AssessmentError(f"No baseline mapping for {autonomy}/{sensitivity}") from exc

    tier_order = model["model"]["tier_order"]
    final_tier = baseline
    applied_rules: list[dict[str, Any]] = []
    baseline_display = baseline.replace("_", " ").title()
    autonomy_display = autonomy.replace("_", " ")
    sensitivity_display = sensitivity.replace("_", " ")
    explanation = [
        f"The starting point is {baseline_display} because the system is "
        f"{autonomy_display} and uses {sensitivity_display} information."
    ]

    for rule in model["elevation_rules"]:
        if not _matches(facts, rule["when"]):
            continue
        prior_tier = final_tier
        final_tier = _higher_tier(final_tier, rule["minimum_tier"], tier_order)
        applied = {
            "rule_id": rule["id"],
            "reason": rule["reason"],
            "prior_tier": prior_tier,
            "resulting_tier": final_tier,
            "changed_tier": final_tier != prior_tier,
        }
        applied_rules.append(applied)
        prior_display = prior_tier.replace("_", " ").title()
        final_display = final_tier.replace("_", " ").title()
        explanation.append(
            f"Risk elevation rule {rule['id']} applied because {rule['reason'].lower()} "
            f"The classification increased from {prior_display} to {final_display}."
            if final_tier != prior_tier
            else f"Risk elevation rule {rule['id']} applied because {rule['reason'].lower()} "
            f"The classification remained {final_display} because it was already at least that high."
        )

    final_display = final_tier.replace("_", " ").title()
    explanation.append(
        f"The final inherent risk classification is {final_display}. Implementing controls does not "
        f"reduce this inherent-risk result under model version {model['model']['version']}."
    )
    result = {
        "status": "evaluated",
        "assessment_id": facts.get("assessment_id"),
        "assessment_schema_version": facts["schema_version"],
        "model_id": model["model"]["id"],
        "model_version": str(model["model"]["version"]),
        "submitted_facts": facts,
        "baseline_inputs": {
            "autonomy_level": autonomy,
            "information_sensitivity": sensitivity,
        },
        "baseline_tier": baseline,
        "baseline_tier_label": tier_qualitative_label(baseline),
        "final_tier": final_tier,
        "final_tier_label": tier_qualitative_label(final_tier),
        "applied_rules": applied_rules,
        "explanation": explanation,
        "human_review_required": True,
        "framework_source": framework_source or FrameworkSource(),
    }
    result["executive_summary"] = build_executive_summary(facts, result)
    return DecisionRecord.model_validate(result)


def evaluate_assessment(
    assessment: dict[str, Any] | Assessment,
    model: dict[str, Any],
    framework_source: FrameworkSource | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper returning the typed decision record as a plain dictionary."""
    return evaluate_assessment_record(assessment, model, framework_source).model_dump(mode="json")
