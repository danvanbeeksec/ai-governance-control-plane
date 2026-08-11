from copy import deepcopy
import hashlib
from pathlib import Path

import pytest
import yaml

from ai_governance_control_plane.framework_loader import FrameworkIngestionError, load_framework
from ai_governance_control_plane.risk_engine import evaluate_assessment, load_model


ROOT = Path(__file__).resolve().parents[1]
RISK_MODEL = load_model(ROOT / "data" / "risk-model.yaml")


def framework_document():
    return {
        "schema_version": "1.0",
        "library": {
            "name": "Synthetic Test Control Library",
            "version": "0.1.0",
            "status": "test",
            "description": "A minimal synthetic framework ingestion fixture.",
        },
        "reference_catalog": {"PUBLIC-REF": "Synthetic public reference"},
        "controls": [
            {
                "control_id": "AI-TST-001",
                "domain": "synthetic_test",
                "layer": "ai_system",
                "title": "Synthetic test control",
                "objective": "Validate the ingestion boundary.",
                "requirement": "The synthetic system shall support a deterministic test.",
                "applicability": "Applies only to this synthetic test fixture.",
                "evidence_examples": ["synthetic test result"],
                "implementation_notes": "Do not treat this fixture as a real control.",
                "references": ["PUBLIC-REF"],
            }
        ],
    }


def write_contract(tmp_path, document=None, **expected_overrides):
    artifact = tmp_path / "controls.yaml"
    artifact.write_text(yaml.safe_dump(document or framework_document(), sort_keys=False), encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    expected = {"schema_version": "1.0", "library_version": "0.1.0", "control_count": 1}
    expected.update(expected_overrides)
    manifest = tmp_path / "framework-source.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "source": {
                    "repository": "synthetic/framework",
                    "commit": "a" * 40,
                    "path": "data/controls.yaml",
                    "sha256": digest,
                },
                "expected": expected,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return artifact, manifest


def assessment():
    return {
        "assessment_id": "TEST-INGEST-001",
        "system_name": "Synthetic Ingestion Test",
        "business_purpose": "Validate framework provenance in a decision record.",
        "accountable_owner": "Fictional Owner",
        "autonomy_level": "human_supervised",
        "information_sensitivity": "public",
        "human_review": "prior_to_each_meaningful_action",
        "action_authority": "generate_only",
        "system_access": "none",
        "external_reach": "none",
        "reversibility": "easy",
        "decision_impact": "none",
        "agent_capabilities": [],
    }


def test_loads_pinned_framework_and_records_provenance(tmp_path):
    artifact, manifest = write_contract(tmp_path)
    loaded = load_framework(artifact, manifest)
    result = evaluate_assessment(assessment(), RISK_MODEL, loaded.source)
    assert len(loaded.controls) == 1
    assert result["framework_source"]["status"] == "loaded"
    assert result["framework_source"]["commit"] == "a" * 40
    assert result["framework_source"]["digest"].startswith("sha256:")


def test_rejects_digest_mismatch(tmp_path):
    artifact, manifest = write_contract(tmp_path)
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(FrameworkIngestionError, match="digest mismatch"):
        load_framework(artifact, manifest)


def test_rejects_unexpected_library_version(tmp_path):
    artifact, manifest = write_contract(tmp_path, library_version="9.9.9")
    with pytest.raises(FrameworkIngestionError, match="library version"):
        load_framework(artifact, manifest)


def test_rejects_duplicate_control_ids(tmp_path):
    document = framework_document()
    document["controls"].append(deepcopy(document["controls"][0]))
    artifact, manifest = write_contract(tmp_path, document=document, control_count=2)
    with pytest.raises(FrameworkIngestionError, match="control IDs must be unique"):
        load_framework(artifact, manifest)


def test_rejects_unknown_control_reference(tmp_path):
    document = framework_document()
    document["controls"][0]["references"] = ["UNKNOWN-REF"]
    artifact, manifest = write_contract(tmp_path, document=document)
    with pytest.raises(FrameworkIngestionError, match="unknown references"):
        load_framework(artifact, manifest)
