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

    assert framework.source.commit == "1ce00c84845ba3fa808d16fc2537fa7414b6a8a2"
    assert framework.source.library_version == "0.1.0"
    assert framework.source.digest == (
        "sha256:ba2c9b793fe239dbe63432fd6c0c06f1abf3b09b2ef5dafeafc7e10df330fc84"
    )
    assert len(framework.controls) == 35
