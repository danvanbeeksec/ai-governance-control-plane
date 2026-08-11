from pathlib import Path

import pytest
import yaml

from ai_governance_control_framework import controls_bytes
from ai_governance_control_plane.applicability_contract import (
    ApplicabilityContractError,
    assess_methodology_compatibility,
    load_applicability_methodology,
    validate_applicability_methodology,
)
from ai_governance_control_plane.framework_loader import (
    ControlRecord,
    LoadedFramework,
    load_framework_bytes,
)
from ai_governance_control_plane.models import FrameworkSource


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "data" / "control-applicability-rules.yaml"


def synthetic_framework_for(methodology):
    controls = []
    for treatment in methodology.controls:
        controls.append(
            ControlRecord(
                control_id=treatment.control_id,
                domain="synthetic_test",
                layer="enterprise" if treatment.section == "enterprise_dependencies" else "ai_system",
                title="Synthetic compatibility control",
                objective="Validate version compatibility.",
                requirement="The synthetic contract shall support compatibility testing.",
                applicability="Applies only to the synthetic compatibility test.",
                evidence_examples=["synthetic result"],
                implementation_notes="Not a real control.",
                references=["SYNTHETIC"],
            )
        )
    return LoadedFramework(
        source=FrameworkSource(
            repository="synthetic/framework",
            library_version=methodology.methodology.framework_library_version,
            schema_version="1.0",
            commit="a" * 40,
            digest="sha256:" + "b" * 64,
            status="loaded",
        ),
        reference_catalog={"SYNTHETIC": "Synthetic compatibility reference"},
        controls=controls,
    )


def test_methodology_control_ids_are_unique():
    methodology = load_applicability_methodology(RULES)
    control_ids = [control.control_id for control in methodology.controls]
    assert len(control_ids) == len(set(control_ids))


def test_methodology_never_automates_non_applicability():
    methodology = load_applicability_methodology(RULES)
    assert "not_applicable" not in methodology.outcomes
    assert {item.treatment for item in methodology.controls} == {
        "universal",
        "conditional",
        "human_determination",
    }


def test_every_condition_can_read_each_canonical_synthetic_assessment():
    methodology = load_applicability_methodology(RULES)
    with (ROOT / "data" / "example-assessments.yaml").open(encoding="utf-8") as stream:
        assessments = yaml.safe_load(stream)["assessments"]
    referenced_fields = {
        condition.field
        for treatment in methodology.controls
        for group in treatment.triggers
        for condition in group.all
    }
    for assessment in assessments:
        assert referenced_fields <= set(assessment)


def test_unknown_assessment_field_is_rejected(tmp_path):
    raw = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    conditional = next(item for item in raw["controls"] if item["treatment"] == "conditional")
    conditional["triggers"][0]["all"][0]["field"] = "unsupported_fact"
    path = tmp_path / "invalid-rules.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    with pytest.raises(ApplicabilityContractError, match="unknown assessment field"):
        load_applicability_methodology(path)


def test_new_framework_control_requires_methodology_update():
    methodology = load_applicability_methodology(RULES)
    framework = synthetic_framework_for(methodology)
    framework.controls.append(
        ControlRecord(
            control_id="AI-NEW-001",
            domain="synthetic_test",
            layer="ai_system",
            title="New synthetic framework control",
            objective="Simulate framework expansion.",
            requirement="The methodology shall not ignore a newly added control.",
            applicability="Applies only to this compatibility test.",
            evidence_examples=["synthetic result"],
            implementation_notes="Requires an explicit methodology treatment.",
            references=["SYNTHETIC"],
        )
    )

    report = assess_methodology_compatibility(methodology, framework)
    assert report.status == "methodology_update_required"
    assert report.missing_controls == ["AI-NEW-001"]
    with pytest.raises(ApplicabilityContractError, match="methodology_update_required"):
        validate_applicability_methodology(methodology, framework)


def test_framework_version_change_requires_methodology_update():
    methodology = load_applicability_methodology(RULES)
    framework = synthetic_framework_for(methodology)
    framework.source.library_version = "0.2.0"
    report = assess_methodology_compatibility(methodology, framework)
    assert report.status == "methodology_update_required"
    assert report.version_match is False


def test_methodology_covers_actual_pinned_framework():
    framework = load_framework_bytes(
        controls_bytes(), ROOT / "data" / "framework-source.yaml"
    )
    methodology = load_applicability_methodology(RULES)
    validate_applicability_methodology(methodology, framework)
