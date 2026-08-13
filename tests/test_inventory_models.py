from datetime import timezone

import pytest
from pydantic import ValidationError

from ai_governance_control_plane.models import AISystem, OwnerRoles


def make_system(**updates):
    values = dict(
        system_id="SYS-1", name="Research helper", purpose="Summarize public research.",
        provider="Example Provider", model="Example Model",
        owners=OwnerRoles(business_owner="Example owner"), lifecycle_state="proposed",
        record_type="temporary_submission", visibility="demo", autonomy_level="human_supervised",
        information_sensitivity="public", vendor_status="vendor",
    )
    values.update(updates)
    return AISystem(**values)


def test_ai_system_has_timezone_aware_timestamps_and_distinct_owner_roles():
    system = make_system(owners=OwnerRoles(business_owner="Business", technical_owner="Technical"))
    assert system.created_at.tzinfo == timezone.utc
    assert system.owners.business_owner == "Business"
    assert system.owners.technical_owner == "Technical"


def test_lifecycle_state_is_constrained():
    with pytest.raises(ValidationError):
        make_system(lifecycle_state="deleted")
