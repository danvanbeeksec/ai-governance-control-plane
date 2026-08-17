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

    assert framework.source.commit == "8c95890cb2baf298e460a9a24978503286bc6e2f"
    assert framework.source.library_version == "1.2.0"
    assert framework.source.digest == (
        "sha256:dd7f696df558302808e71a0fab74153f815b86fa923335806a791146d78fdcc6"
    )
    assert len(framework.controls) == 70
