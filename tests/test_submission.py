from copy import deepcopy
import sqlite3

import pytest
import yaml

from ai_governance_control_plane.inventory import SQLiteInventoryRepository, SessionInventoryRepository
from ai_governance_control_plane.service import GovernanceDecisionService
from ai_governance_control_plane.submission import InventoryDetails, prepare_submission


def result(root, **updates):
    facts = yaml.safe_load((root / 'data/example-assessments.yaml').read_text())['assessments'][0]
    facts.pop('expected')
    facts.update(updates)
    return GovernanceDecisionService.from_packaged_resources().assess_ai_system(facts)


@pytest.mark.parametrize('kind', ['session', 'sqlite'])
def test_reassessment_updates_current_facts_and_preserves_history(root, tmp_path, kind):
    repo = SessionInventoryRepository() if kind == 'session' else SQLiteInventoryRepository(tmp_path / 'test.db')
    first = prepare_submission(result(root), InventoryDetails(provider='Fictional Original Provider'), repo)
    repo.save_assessment(first.system, first.history)
    revised = prepare_submission(result(root, information_sensitivity='restricted', accountable_owner='Fictional New Owner', business_purpose='Revised purpose'),
                                 InventoryDetails(provider='Fictional New Provider'), repo, system_id=first.system.system_id)
    repo.save_assessment(revised.system, revised.history)
    current = repo.get_system(first.system.system_id)
    assert current.current_risk_tier == 'tier_1'
    assert current.information_sensitivity == 'restricted'
    assert current.provider == 'Fictional New Provider'
    assert current.owners.business_owner == 'Fictional New Owner'
    assert current.purpose == 'Revised purpose'
    history = repo.list_history(current.system_id)
    assert history[0].assessment.information_sensitivity == 'public'
    assert history[1].assessment.information_sensitivity == 'restricted'


@pytest.mark.parametrize('kind', ['session', 'sqlite'])
def test_history_failure_does_not_partially_update_system(root, tmp_path, kind):
    repo = SessionInventoryRepository() if kind == 'session' else SQLiteInventoryRepository(tmp_path / 'test.db')
    first = prepare_submission(result(root), InventoryDetails(provider='Fictional Provider'), repo)
    repo.save_assessment(first.system, first.history)
    revised = prepare_submission(result(root, information_sensitivity='restricted'), InventoryDetails(provider='Fictional Revised Provider'), repo, system_id=first.system.system_id)
    repeated_id = revised.history.model_copy(update={'history_id': first.history.history_id})
    with pytest.raises((ValueError, sqlite3.IntegrityError)):
        repo.save_assessment(revised.system, repeated_id)
    assert repo.get_system(first.system.system_id) == first.system
    assert len(repo.list_history(first.system.system_id)) == 1


def test_equal_names_do_not_implicitly_merge(root):
    repo = SessionInventoryRepository()
    first = prepare_submission(result(root), InventoryDetails(provider='Fictional Provider'), repo)
    repo.save_assessment(first.system, first.history)
    second = prepare_submission(result(root), InventoryDetails(provider='Fictional Provider'), repo)
    assert second.system.system_id != first.system.system_id
