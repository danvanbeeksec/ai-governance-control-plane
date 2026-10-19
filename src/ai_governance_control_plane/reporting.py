"""Portable, executive-readable review records from the deterministic result."""
from .workflow import AssessmentResult
from .summarize import tier_display


def review_brief(result: AssessmentResult) -> str:
    def clean(value):
        # Keep user-supplied multiline text inside its own list item.
        return str(value).replace("\r", "").replace("\n", " ")
    decision, recs = result.decision, result.recommendations
    lines = ["# AI governance review brief", "", clean(result.assessment.system_name), "",
             f"**Inherent risk: {tier_display(decision.final_tier)}**", "",
             clean(decision.executive_summary), "", "## Submitted facts", ""]
    lines.extend(f"- {key.replace('_', ' ').capitalize()}: {clean(value)}"
                 for key, value in result.assessment.model_dump(mode="json").items())
    lines.extend(["", "## Decision rationale", "", *[f"- {clean(item)}" for item in decision.explanation]])
    for heading, controls in (("Required system controls", recs.applicable_system_controls),
                              ("Applicability questions", recs.undetermined_system_controls),
                              ("Enterprise inheritance", recs.enterprise_dependencies)):
        lines.extend(["", f"## {heading}", ""])
        for item in controls:
            lines.append(f"- **{item.control.control_id}: {item.control.title}**: {item.rationale}")
            lines.extend(f"  - {question}" for question in item.unresolved_questions)
    source = decision.framework_source
    lines.extend(["", "## Provenance and review", "", f"- Framework library: {source.library_version}",
                  f"- Framework commit: {source.commit}", f"- Framework digest: {source.digest}",
                  f"- Risk model: {decision.model_id} / {decision.model_version}",
                  f"- Applicability methodology: {recs.methodology_id} / {recs.methodology_version}",
                  "", "Fictional or synthetic demonstration. A qualified human must confirm applicability, inheritance, and the final governance decision. This is not approval, legal advice, or evidence of control effectiveness."])
    return "\n".join(lines) + "\n"
