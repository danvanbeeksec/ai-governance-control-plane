"""Prepare an explicit inventory update without merging systems by name."""
from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .inventory import InventoryRepository
from .models import AISystem, AssessmentHistoryRecord, OwnerRoles, utc_now
from .workflow import AssessmentResult


class InventoryDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    provider: str = Field(min_length=1, max_length=200)
    model: str | None = Field(default=None, max_length=200)


class InventorySubmission(BaseModel):
    system: AISystem
    history: AssessmentHistoryRecord
    changes: list[dict]


def prepare_submission(result: AssessmentResult, details: InventoryDetails,
                       repository: InventoryRepository, *, system_id: str | None = None,
                       demo: bool = True) -> InventorySubmission:
    """Return the complete proposed state and a reviewable before/after list."""
    previous = repository.get_system(system_id) if system_id else None
    if system_id and previous is None:
        raise ValueError("The selected inventory system no longer exists")
    assessment = result.assessment
    updates = dict(name=assessment.system_name, purpose=assessment.business_purpose,
                   provider=details.provider, model=details.model or None,
                   autonomy_level=assessment.autonomy_level,
                   information_sensitivity=assessment.information_sensitivity,
                   current_risk_tier=result.decision.final_tier, updated_at=utc_now())
    if previous:
        owners = previous.owners.model_copy(update={"business_owner": assessment.accountable_owner})
        system = AISystem.model_validate({**previous.model_dump(), **updates, "owners": owners})
    else:
        system = AISystem(
            system_id=f"TEMP-{uuid4().hex[:12].upper()}", **updates,
            owners=OwnerRoles(business_owner=assessment.accountable_owner), lifecycle_state="assessing",
            record_type="temporary_submission" if demo else "managed_inventory",
            visibility="demo" if demo else "private", vendor_status="vendor",
            metadata={"created_from": "assessment_interface"},
        )
    before = previous.model_dump(mode="json") if previous else {}
    after = system.model_dump(mode="json")
    changes = [{"field": field, "before": before.get(field), "after": after[field]}
               for field in [*updates, "owners"] if field != "updated_at" and before.get(field) != after[field]]
    history = AssessmentHistoryRecord(
        history_id=f"HIST-{uuid4().hex.upper()}", system_id=system.system_id,
        assessment=assessment, decision=result.decision,
        control_applicability=result.recommendations.model_dump(mode="json"),
    )
    return InventorySubmission(system=system, history=history, changes=changes)
