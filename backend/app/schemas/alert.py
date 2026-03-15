from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AlertStatus


class AlertIngestRequest(BaseModel):
    """
    Payload sent by monitoring systems (Prometheus, Grafana, Datadog etc.)
    """

    source: str  # e.g. "prometheus", "grafana"
    name: str  # e.g. "HighCPUUsage"
    service_name: str  # e.g. "payments-api"
    message: str | None = None
    priority: str = "P3"  # default to medium if not specified
    labels: dict = {}  # e.g. {"env": "prod", "region": "us-east-1"}


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
