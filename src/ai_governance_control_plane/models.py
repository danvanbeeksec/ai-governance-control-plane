"""Typed contracts for control-plane assessment and decision records."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AutonomyLevel = Literal["autonomous", "conditionally_autonomous", "human_supervised"]
InformationSensitivity = Literal["public", "internal", "confidential", "restricted"]
HumanReview = Literal[
    "prior_to_each_meaningful_action", "checkpoints_or_exceptions", "no_prior_review"
]
ActionAuthority = Literal[
    "generate_only",
    "recommend",
    "modify_nonproduction",
    "modify_production",
    "execute_material_transaction",
    "safety_relevant_action",
]
SystemAccess = Literal["none", "standard", "privileged"]
ExternalReach = Literal["none", "bounded", "broad"]
Reversibility = Literal["easy", "recoverable_with_effort", "difficult"]
DecisionImpact = Literal["none", "operational", "consequential", "regulated_or_consequential"]
AgentCapability = Literal["external_tools", "external_communication", "delegation", "persistent_memory"]
Tier = Literal["tier_1", "tier_2", "tier_3"]


class Assessment(BaseModel):
    """Canonical executable assessment input."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1.0"] = "0.1.0"
    assessment_id: str = Field(min_length=1, max_length=100)
    system_name: str = Field(min_length=1, max_length=200)
    business_purpose: str = Field(min_length=1, max_length=2000)
    accountable_owner: str = Field(min_length=1, max_length=200)
    autonomy_level: AutonomyLevel
    information_sensitivity: InformationSensitivity
    human_review: HumanReview
    action_authority: ActionAuthority
    system_access: SystemAccess
    external_reach: ExternalReach
    reversibility: Reversibility
    decision_impact: DecisionImpact
    agent_capabilities: list[AgentCapability]

    @field_validator("agent_capabilities")
    @classmethod
    def capabilities_are_unique(cls, value: list[AgentCapability]) -> list[AgentCapability]:
        if len(value) != len(set(value)):
            raise ValueError("agent_capabilities must not contain duplicates")
        return value


class AppliedRule(BaseModel):
    rule_id: str
    reason: str
    prior_tier: Tier
    resulting_tier: Tier
    changed_tier: bool


class FrameworkSource(BaseModel):
    """Framework provenance attached before or after validated ingestion."""

    repository: str = "danvanbeeksec/ai-governance-control-framework"
    library_version: str | None = None
    schema_version: str | None = None
    commit: str | None = None
    digest: str | None = None
    status: Literal["not_loaded", "loaded"] = "not_loaded"


class DecisionRecord(BaseModel):
    """Canonical, versioned output from an assessment evaluation."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["evaluated", "insufficient_information"]
    assessment_id: str | None
    assessment_schema_version: str
    model_id: str
    model_version: str
    submitted_facts: dict
    baseline_inputs: dict[str, str | None]
    baseline_tier: Tier | None
    final_tier: Tier | None
    applied_rules: list[AppliedRule]
    explanation: list[str]
    executive_summary: str
    missing_inputs: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    framework_source: FrameworkSource = Field(default_factory=FrameworkSource)
