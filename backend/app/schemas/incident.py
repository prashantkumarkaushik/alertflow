from pydantic import field_validator
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import IncidentPriority, IncidentStatus
from app.schemas.alert import AlertResponse


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


class IncidentDetailResponse(IncidentResponse):
    """Full incident with linked alerts and audit logs."""

    alerts: list[AlertResponse] = []
    audit_logs: list["AuditLogResponse"] = []


class AuditLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    payload: dict
    incident_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusTransitionRequest(BaseModel):
    status: IncidentStatus
    reason: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def lowercase_status(cls, v: str) -> str:
        """Accept both ACKNOWLEDGED and acknowledged."""
        if isinstance(v, str):
            return v.lower()
        return v


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
