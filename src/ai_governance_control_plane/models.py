"""Typed contracts for control-plane assessment and decision records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

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
LifecycleState = Literal["proposed", "assessing", "approved", "active", "suspended", "retired"]
RecordType = Literal["synthetic_example", "temporary_submission", "managed_inventory"]
Visibility = Literal["demo", "private", "enterprise"]
VendorStatus = Literal["internal", "vendor", "hybrid"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OwnerRoles(BaseModel):
    """Accountability roles kept distinct for future workflow use."""

    model_config = ConfigDict(extra="forbid")

    business_owner: str = Field(min_length=1, max_length=200)
    technical_owner: str | None = Field(default=None, max_length=200)
    governance_reviewer: str | None = Field(default=None, max_length=200)
    vendor_owner: str | None = Field(default=None, max_length=200)


class AISystem(BaseModel):
    """Durable conceptual parent for inventory, assessments, and decisions."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.2.0"] = "0.2.0"
    system_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=2000)
    provider: str = Field(min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=200)
    owners: OwnerRoles
    lifecycle_state: LifecycleState = "proposed"
    record_type: RecordType
    visibility: Visibility
    autonomy_level: AutonomyLevel
    information_sensitivity: InformationSensitivity
    current_risk_tier: Tier | None = None
    vendor_status: VendorStatus
    business_unit: str | None = Field(default=None, max_length=200)
    deployment_context: str | None = Field(default=None, max_length=500)
    change_triggers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AssessmentHistoryRecord(BaseModel):
    """Immutable assessment event and its provenance-bearing outputs."""

    model_config = ConfigDict(extra="forbid")

    history_id: str = Field(min_length=1, max_length=100)
    system_id: str = Field(min_length=1, max_length=100)
    assessment: "Assessment"
    decision: "DecisionRecord"
    control_applicability: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)


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
    baseline_tier_label: str | None = None
    final_tier: Tier | None
    final_tier_label: str | None = None
    applied_rules: list[AppliedRule]
    explanation: list[str]
    executive_summary: str
    missing_inputs: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    framework_source: FrameworkSource = Field(default_factory=FrameworkSource)
