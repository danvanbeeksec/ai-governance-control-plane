from pathlib import Path

import pytest

from ai_governance_control_plane.inventory import (
    SQLiteInventoryRepository, SessionInventoryRepository, add_seed_history, find_potential_duplicates,
    load_seed_systems, repository_for_mode,
)
from ai_governance_control_plane.models import AssessmentHistoryRecord


def seeds(root):
    return load_seed_systems(root / "data" / "inventory-seed.json")


def test_demo_mode_is_session_only_and_never_creates_sqlite(root, tmp_path):
    database = tmp_path / "must-not-exist.db"
    first = repository_for_mode("demo", seeds(root), database)
    system = first.list_systems()[0].model_copy(update={"system_id": "TEMP-1", "record_type": "temporary_submission"})
    first.save_system(system)
    assert first.get_system("TEMP-1") is not None
    assert not database.exists()
    second = repository_for_mode("demo", seeds(root), database)
    assert second.get_system("TEMP-1") is None
    assert not database.exists()


def test_local_mode_persists_systems_across_repository_instances(root, tmp_path):
    database = tmp_path / "control-plane.db"
    first = repository_for_mode("local", seeds(root), database)
    system = first.list_systems()[0].model_copy(update={"system_id": "LOCAL-1", "record_type": "managed_inventory", "visibility": "private"})
    first.save_system(system)
    second = SQLiteInventoryRepository(database)
    assert second.get_system("LOCAL-1") == system


def test_duplicate_awareness_flags_name_and_provider_model_matches(root):
    existing = seeds(root)
    candidate = existing[0].model_copy(update={"system_id": "TEMP-2", "name": "Public Research Summary Tool"})
    assert existing[0] in find_potential_duplicates(candidate, existing)


def test_assessment_history_is_append_only(root, tmp_path, framework_path):
    from ai_governance_control_plane.framework_loader import load_framework
    from ai_governance_control_plane.models import Assessment
    from ai_governance_control_plane.workflow import run_assessment_workflow
    import yaml

    repository = SQLiteInventoryRepository(tmp_path / "history.db")
    system = seeds(root)[0]
    repository.save_system(system)
    example = yaml.safe_load((root / "data" / "example-assessments.yaml").read_text())["assessments"][0]
    example.pop("expected")
    framework = load_framework(framework_path, root / "data" / "framework-source.yaml")
    result = run_assessment_workflow(Assessment.model_validate(example), framework, root / "data" / "risk-model.yaml", root / "data" / "control-applicability-rules.yaml")
    record = AssessmentHistoryRecord(history_id="H-1", system_id=system.system_id, assessment=result.assessment, decision=result.decision, control_applicability=result.recommendations.model_dump(mode="json"))
    repository.add_history(record)
    repository.add_history(record.model_copy(update={"history_id": "H-2"}))
    history = repository.list_history(system.system_id)
    assert [item.history_id for item in history] == ["H-1", "H-2"]
    assert history[0].decision.framework_source.digest


def test_history_requires_known_parent(tmp_path):
    repository = SQLiteInventoryRepository(tmp_path / "history.db")
    with pytest.raises(ValueError, match="Unknown AI system"):
        repository.add_history(AssessmentHistoryRecord.model_construct(history_id="H-X", system_id="missing"))


def test_seed_history_is_idempotent(root, tmp_path, framework_path):
    from datetime import datetime, timezone
    import yaml
    from ai_governance_control_plane.framework_loader import load_framework
    from ai_governance_control_plane.models import Assessment
    from ai_governance_control_plane.workflow import run_assessment_workflow

    repository = SQLiteInventoryRepository(tmp_path / "seed-history.db")
    system = seeds(root)[0]
    repository.save_system(system)
    example = yaml.safe_load((root / "data" / "example-assessments.yaml").read_text())["assessments"][0]
    example.pop("expected")
    result = run_assessment_workflow(
        Assessment.model_validate(example),
        load_framework(framework_path, root / "data" / "framework-source.yaml"),
        root / "data" / "risk-model.yaml",
        root / "data" / "control-applicability-rules.yaml",
    )
    record = AssessmentHistoryRecord(
        history_id="HIST-SEED-001", system_id=system.system_id,
        assessment=result.assessment, decision=result.decision,
        control_applicability=result.recommendations.model_dump(mode="json"),
        created_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )
    add_seed_history(repository, [record])
    add_seed_history(repository, [record])
    assert [item.history_id for item in repository.list_history(system.system_id)] == ["HIST-SEED-001"]
