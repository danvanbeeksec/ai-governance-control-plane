"""Executive-readable summaries for deterministic decision records."""

from __future__ import annotations

from typing import Any


def build_executive_summary(facts: dict[str, Any], result: dict[str, Any]) -> str:
    system_name = facts.get("system_name") or "The proposed AI system"
    purpose = facts.get("business_purpose") or "No business purpose was supplied."
    if result["status"] == "insufficient_information":
        missing = ", ".join(result["missing_inputs"])
        return (
            f"{system_name} could not be assigned an inherent risk tier because required "
            f"information is missing: {missing}. A qualified human must resolve the missing "
            "facts before the assessment proceeds."
        )

    rule_ids = [rule["rule_id"] for rule in result["applied_rules"]]
    final_tier = result["final_tier"].replace("_", " ").title()
    baseline_tier = result["baseline_tier"].replace("_", " ").title()
    rule_text = (
        f" Elevation rules {', '.join(rule_ids)} applied."
        if rule_ids
        else " No elevation rule applied."
    )
    return (
        f"{system_name}. Purpose: {purpose.rstrip('.')}. The current rules assign "
        f"{final_tier} inherent AI system risk from a {baseline_tier} "
        f"baseline.{rule_text} This is a review-routing result, not an approval or a residual-risk decision."
    )
