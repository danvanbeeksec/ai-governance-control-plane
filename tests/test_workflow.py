import yaml

from ai_governance_control_plane.framework_loader import load_framework
from ai_governance_control_plane.models import Assessment
from ai_governance_control_plane.workflow import run_assessment_workflow


def test_end_to_end_workflow_uses_external_framework(root, framework_path):
    framework = load_framework(framework_path, root / "data" / "framework-source.yaml")
    with (root / "data" / "example-assessments.yaml").open(encoding="utf-8") as stream:
        example = yaml.safe_load(stream)["assessments"][5]
    example.pop("expected")

    result = run_assessment_workflow(
        Assessment.model_validate(example),
        framework,
        root / "data" / "risk-model.yaml",
        root / "data" / "control-applicability-rules.yaml",
    )

    assert result.decision.final_tier == "tier_1"
    assert result.decision.final_tier_label == "High"
    assert result.decision.framework_source == framework.source
    assert result.recommendations.summary.total_controls == len(framework.controls)
    assert result.recommendations.summary.applicable_system_controls == len(
        result.recommendations.applicable_system_controls
    )
    assert (
        result.recommendations.summary.enterprise_dependencies
        + result.recommendations.summary.applicable_system_controls
        + result.recommendations.summary.undetermined_system_controls
        == len(framework.controls)
    )
