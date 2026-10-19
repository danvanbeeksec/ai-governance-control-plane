from streamlit.testing.v1 import AppTest


def widget(app, kind, label):
    return next(item for item in getattr(app, kind) if item.label == label)


def open_assessment(root):
    app = AppTest.from_file(str(root / 'app.py')).run(timeout=20)
    widget(app, 'selectbox', 'Go to').set_value('New assessment').run(timeout=20)
    return app


def test_visitor_can_choose_a_worked_journey(root):
    app = AppTest.from_file(str(root / 'app.py')).run(timeout=20)
    assert not app.exception
    widget(app, 'button', 'Explore a worked example').click().run(timeout=20)
    assert 'New assessment' in [item.value for item in app.title]
    assert widget(app, 'text_input', 'System name').value


def test_full_synthetic_record_shows_assessment_controls(root):
    app = AppTest.from_file(str(root / 'app.py')).run(timeout=20)
    widget(app, 'selectbox', 'Go to').set_value('AI inventory').run(timeout=20)
    widget(app, 'button', 'View full record').click().run(timeout=20)
    assert not app.exception
    assert 'Assessment history (1)' in [item.value for item in app.subheader]
    assert 'Required controls' in [item.label for item in app.tabs]


def test_seed_reassessment_preserves_newest_tier_and_facts(root):
    app = open_assessment(root)
    widget(app, 'selectbox', 'Inventory destination').set_value('SYS-SYN-001').run(timeout=20)
    widget(app, 'selectbox', 'Information sensitivity').set_value('Restricted').run(timeout=20)
    widget(app, 'text_input', 'Accountable owner').set_value('Fictional New Owner').run(timeout=20)
    widget(app, 'button', 'Run assessment').click().run(timeout=20)
    assert not app.exception
    assert widget(app, 'metric', 'Inherent risk').value == 'Tier 1: High'
    widget(app, 'button', 'Submit to inventory').click().run(timeout=20)
    assert not app.exception
    repository = app.session_state['inventory_repository:demo']
    record = repository.get_system('SYS-SYN-001')
    assert record.current_risk_tier == 'tier_1'
    assert record.information_sensitivity == 'restricted'
    assert record.owners.business_owner == 'Fictional New Owner'
    assert repository.list_history(record.system_id)[-1].decision.final_tier == record.current_risk_tier
    app.run(timeout=20)
    assert repository.get_system(record.system_id).current_risk_tier == 'tier_1'


def test_invalid_provider_and_stale_inputs_cannot_be_submitted(root):
    app = open_assessment(root)
    widget(app, 'text_input', 'Provider').set_value('').run(timeout=20)
    widget(app, 'button', 'Run assessment').click().run(timeout=20)
    assert not app.exception
    assert widget(app, 'button', 'Submit to inventory').disabled
    widget(app, 'text_input', 'Provider').set_value('Fictional Provider').run(timeout=20)
    assert widget(app, 'button', 'Submit to inventory').disabled
    widget(app, 'button', 'Run assessment').click().run(timeout=20)
    assert not widget(app, 'button', 'Submit to inventory').disabled
    widget(app, 'selectbox', 'Information sensitivity').set_value('Restricted').run(timeout=20)
    assert widget(app, 'button', 'Submit to inventory').disabled


def test_blank_intake_has_no_assumed_material_facts(root):
    app = open_assessment(root)
    widget(app, 'selectbox', 'Synthetic example').set_value('Start blank').run(timeout=20)
    assert widget(app, 'selectbox', 'Autonomy').value == 'Select one'
    assert widget(app, 'text_input', 'System name').value == ''
    widget(app, 'button', 'Run assessment').click().run(timeout=20)
    assert app.error
    assert not app.metric


def test_comparison_shows_rationale_and_explicit_outcome_transitions(root):
    app = AppTest.from_file(str(root / 'app.py')).run(timeout=20)
    widget(app, 'selectbox', 'Go to').set_value('Compare designs').run(timeout=20)
    widget(app, 'button', 'Compare designs').click().run(timeout=20)
    assert not app.exception
    assert widget(app, 'metric', 'Option A inherent risk').value.startswith('Tier ')
    assert widget(app, 'metric', 'Option B inherent risk').value.startswith('Tier ')
    assert 'Control applicability transitions' in [item.value for item in app.subheader]
