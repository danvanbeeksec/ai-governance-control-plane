from streamlit.testing.v1 import AppTest


def test_inventory_and_assessment_are_separate_views(root, monkeypatch):
    monkeypatch.delenv("AI_CONTROL_FRAMEWORK_PATH", raising=False)
    app = AppTest.from_file(str(root / "app.py")).run(timeout=10)

    assert "AI inventory" in [item.value for item in app.title]
    assert any(item.label == "Risk tier" for item in app.metric)
    assert next(item for item in app.metric if item.label == "Session assessments").value == "1"
    assert any(item.label == "View full record" for item in app.button)
    assert not any(item.label == "Run assessment" for item in app.button)

    navigation = next(item for item in app.selectbox if item.label == "Go to")
    navigation.set_value("➕  New assessment").run(timeout=10)
    assert "New assessment" in [item.value for item in app.title]
    assert any(item.label == "Run assessment" for item in app.button)
    assert not any(item.label == "Submit to inventory" for item in app.button)


def test_full_synthetic_record_shows_assessment_controls(root, monkeypatch):
    monkeypatch.delenv("AI_CONTROL_FRAMEWORK_PATH", raising=False)
    app = AppTest.from_file(str(root / "app.py")).run(timeout=10)
    next(item for item in app.button if item.label == "View full record").click().run(timeout=10)

    assert not app.exception
    assert "Assessment history (1)" in [item.value for item in app.subheader]
    assert "Required controls" in [item.label for item in app.tabs]
    rendered = " ".join(item.value for item in app.markdown)
    assert "AI-GOV-003" in rendered
    assert "Framework version:" in rendered


def test_assessment_is_draft_until_explicit_submission(root, monkeypatch):
    monkeypatch.delenv("AI_CONTROL_FRAMEWORK_PATH", raising=False)
    app = AppTest.from_file(str(root / "app.py")).run(timeout=10)
    next(item for item in app.selectbox if item.label == "Go to").set_value("➕  New assessment").run(timeout=10)

    example = next(item for item in app.selectbox if item.label == "Synthetic example")
    example.set_value("Procurement Workflow Agent").run(timeout=10)
    assessment_id = next(item for item in app.text_input if item.label == "Assessment ID")
    assert assessment_id.value == "DEMO-001"

    next(item for item in app.button if item.label == "Run assessment").click().run(timeout=10)
    metrics = {item.label: item.value for item in app.metric}
    assert metrics["Inherent risk"] == "Tier 1"
    assert any(item.label == "Submit to inventory" for item in app.button)
    assert "Nothing has been added to inventory yet" in " ".join(item.value for item in app.info)

    next(item for item in app.button if item.label == "Submit to inventory").click().run(timeout=10)
    assert any("DEMO-001 was submitted" in item.value for item in app.success)
    next_id = next(item for item in app.text_input if item.label == "Assessment ID")
    assert next_id.value == "DEMO-002"
    assert next(item for item in app.text_input if item.label == "System name").value == ""
