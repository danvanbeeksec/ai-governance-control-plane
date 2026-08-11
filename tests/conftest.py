from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
FRAMEWORK_SRC = ROOT.parent / "ai-governance-control-framework" / "src"
if FRAMEWORK_SRC.is_dir():
    sys.path.insert(0, str(FRAMEWORK_SRC))


@pytest.fixture
def root():
    return ROOT


@pytest.fixture
def framework_path(tmp_path):
    path = ROOT.parent / "ai-governance-control-framework" / "data" / "controls.yaml"
    if path.is_file():
        return path

    from ai_governance_control_framework import controls_bytes

    packaged = tmp_path / "controls.yaml"
    packaged.write_bytes(controls_bytes())
    return packaged
