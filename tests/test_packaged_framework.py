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

    assert framework.source.commit == "78865d5fbe8d9fc83389b03bd34b44c27040d81a"
    assert framework.source.library_version == "1.1.0"
    assert framework.source.digest == (
        "sha256:c0cef3a0046aa74b1705382d56a8d4659f86d119e7635dfefe8804d6e51d0fe2"
    )
    assert len(framework.controls) == 70
