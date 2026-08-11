"""Executive-readable summaries for deterministic decision records."""

from __future__ import annotations

from typing import Any


TIER_QUALITATIVE_LABELS = {
    "tier_1": "High",
    "tier_2": "Moderate",
    "tier_3": "Lower",
}


def tier_qualitative_label(tier: str | None) -> str | None:
    """Return the executive-readable risk label for a canonical tier."""
    return TIER_QUALITATIVE_LABELS.get(tier) if tier else None


def tier_display(tier: str) -> str:
    """Combine the canonical tier number with its qualitative meaning."""
    numeric = tier.replace("_", " ").title()
    return f"{numeric}: {TIER_QUALITATIVE_LABELS[tier]}"


def tier_summary_display(tier: str) -> str:
    """Format a tier naturally when it appears inside a sentence."""
    numeric = tier.replace("_", " ").title()
    return f"{numeric} ({TIER_QUALITATIVE_LABELS[tier]})"


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
    final_tier = tier_summary_display(result["final_tier"])
    baseline_tier = tier_summary_display(result["baseline_tier"])
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
