import pytest
import yaml

from ai_governance_control_plane.models import Assessment
from ai_governance_control_plane.service import GovernanceDecisionService


def make_service(root, framework_path):
    return GovernanceDecisionService.from_paths(framework_path, root / "data/framework-source.yaml", root / "data/risk-model.yaml", root / "data/control-applicability-rules.yaml")


def example(root):
    records = yaml.safe_load((root / "data/example-assessments.yaml").read_text())
    return Assessment.model_validate({k: v for k, v in records["assessments"][0].items() if k != "expected"})


def test_service_assesses_and_queries_controls(root, framework_path):
    subject = make_service(root, framework_path)
    item = example(root)
    result = subject.assess_ai_system(item)
    assert result.decision.status == "evaluated"
    assert subject.get_applicable_controls(item).assessment_id == item.assessment_id
    assert subject.explain_control("AI-GOV-001").applicability_metadata is not None


def test_service_compares_design_options(root, framework_path):
    subject = make_service(root, framework_path)
    left = example(root)
    right = left.model_copy(update={"assessment_id": "comparison-b", "autonomy_level": "autonomous"})
    result = subject.compare_ai_design_options(left, right)
    assert result.option_a.assessment.assessment_id != result.option_b.assessment.assessment_id


def test_service_rejects_unknown_control(root, framework_path):
    with pytest.raises(KeyError, match="Unknown control ID"):
        make_service(root, framework_path).explain_control("AI-NOT-999")


def test_service_constructs_from_packaged_resources(root):
    subject = GovernanceDecisionService.from_packaged_resources()
    result = subject.assess_ai_system(example(root))
    assert result.decision.framework_source.status == "loaded"
    assert result.decision.framework_source.library_version == "1.1.0"
    assert result.recommendations.summary.total_controls == 70
