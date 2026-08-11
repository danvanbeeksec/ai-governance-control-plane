from streamlit.testing.v1 import AppTest


def test_switching_example_loads_its_values_and_applies_risk_rule(root, monkeypatch):
    monkeypatch.delenv("AI_CONTROL_FRAMEWORK_PATH", raising=False)
    app = AppTest.from_file(str(root / "app.py")).run(timeout=10)

    example_selector = next(
        item for item in app.selectbox if item.label == "Start with a synthetic example"
    )
    example_selector.set_value("Procurement Workflow Agent").run(timeout=10)

    selected_values = {item.label: item.value for item in app.selectbox}
    assert selected_values["Autonomy"] == "Conditionally autonomous"
    assert selected_values["Information sensitivity"] == "Confidential"
    assert selected_values["Action authority"] == "Execute a material transaction"

    app.button[0].click().run(timeout=10)

    assert not app.exception
    metrics = {item.label: item.value for item in app.metric}
    assert metrics["Inherent risk"] == "Tier 1: High"
    assert metrics["Baseline"] == "Tier 2: Moderate"
    assert metrics["Risk elevation rules"] == "1"
    assert metrics["Required controls"] == "21"
    assert "Framework controls" not in metrics
    rendered_text = " ".join(item.value for item in app.markdown)
    assert "Risk elevation rule ER-001 applied" in rendered_text
    assert "autonomy_level" not in rendered_text
    subheadings = [item.value for item in app.subheader]
    required_index = next(
        index for index, value in enumerate(subheadings) if value.startswith("Required system controls")
    )
    decision_index = next(
        index
        for index, value in enumerate(subheadings)
        if value.startswith("Controls requiring an applicability decision")
    )
    enterprise_index = next(
        index for index, value in enumerate(subheadings) if value.startswith("Enterprise dependencies")
    )
    assert required_index < decision_index < enterprise_index
    assert "These controls are not optional" in rendered_text
    assert "assign an accountable provider" not in rendered_text
    assert "the owner remains accountable for confirming completion" in rendered_text
    assert any(item.label == "Autonomy" for item in app.sidebar.expander)
    assert any(item.label == "Action authority" for item in app.sidebar.expander)
    assert any(item.label == "Understanding risk tiers" for item in app.expander)
    assert not app.get("file_uploader")
    assert any("use fictional or synthetic information only" in item.value for item in app.warning)
    assert "About this demonstration" in [item.label for item in app.sidebar.expander]
