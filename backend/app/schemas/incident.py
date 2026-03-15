from datetime import datetime

from pydantic import BaseModel

from app.models.enums import IncidentPriority, IncidentStatus


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: IncidentStatus
    priority: IncidentPriority
    sla_deadline: datetime | None
    sla_breached: bool
    current_escalation_step: int
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    team_id: int
    sla_policy_id: int | None
    escalation_policy_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
