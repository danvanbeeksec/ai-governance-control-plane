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

    assert framework.source.commit == "0df838abc7031635e57f67b99a9d1ae9b42dc346"
    assert framework.source.library_version == "1.0.0"
    assert framework.source.digest == (
        "sha256:8719eb521b8b12758d905e1dc51087f0f65ba9b74468b5e6cd3c79ea22f1acb9"
    )
    assert len(framework.controls) == 70
