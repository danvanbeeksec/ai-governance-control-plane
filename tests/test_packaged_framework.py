from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_SRC = ROOT.parent / "ai-governance-control-framework" / "src"
sys.path.insert(0, str(FRAMEWORK_SRC))

from ai_governance_control_framework import controls_bytes
from ai_governance_control_plane.framework_loader import load_framework_bytes


def test_packaged_framework_bytes_pass_the_control_plane_pin():
    framework = load_framework_bytes(
        controls_bytes(), ROOT / "data" / "framework-source.yaml"
    )

    assert framework.source.commit == "26b810fad250fa785bbd470a32dba9e795933ed1"
    assert framework.source.library_version == "1.2.0"
    assert framework.source.digest == (
        "sha256:e01c880933b3385f6b8a490f867cd5d2627a97134eaad8fced2a15d4831eb510"
    )
    assert len(framework.controls) == 70
