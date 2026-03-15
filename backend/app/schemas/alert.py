from datetime import datetime

from pydantic import BaseModel

from pydantic import field_validator
from app.models.enums import AlertStatus


class AlertIngestRequest(BaseModel):
    source: str
    name: str
    service_name: str
    message: str | None = None
    priority: str = "P3"
    labels: dict = {}

    @field_validator("priority", mode="before")
    @classmethod
    def uppercase_priority(cls, v: str) -> str:
        """Accept both p1 and P1."""
        if isinstance(v, str):
            return v.upper()
        return v


class AlertResponse(BaseModel):
    id: int
    source: str
    name: str
    service_name: str
    fingerprint: str
    labels: dict
    message: str | None
    status: AlertStatus
    suppressed: bool
    team_id: int
    incident_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertIngestResponse(BaseModel):
    """
    Returned after successful ingestion.
    Tells the caller what happened to the alert.
    """

    alert: AlertResponse | None = None  # None when deduplicated
    incident_id: int | None = None
    deduplicated: bool = False
    suppressed: bool = False
    message: str
