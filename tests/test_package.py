from ai_governance_control_plane import __version__
from ai_governance_control_plane.resources import (
    applicability_methodology_bytes,
    framework_manifest_bytes,
    risk_model_bytes,
)


def test_package_exposes_runtime_resources():
    assert __version__ == "0.5.0"
    assert b"baseline_matrix:" in risk_model_bytes()
    assert b"ai-control-applicability" in applicability_methodology_bytes()
    assert b"danvanbeeksec/ai-governance-control-framework" in framework_manifest_bytes()
