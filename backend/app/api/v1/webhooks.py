from fastapi import APIRouter, Header, HTTPException
from jose import JWTError

from app.core.deps import DBSession
from app.core.security import decode_access_token
from app.schemas.alert import AlertIngestRequest, AlertIngestResponse
from app.services.alert_service import ingest_alert

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _map_severity(severity: str) -> str:
    """Map Prometheus severity labels to AlertFlow priority."""
    mapping = {
        "critical": "P1",
        "high": "P2",
        "warning": "P3",
        "info": "P4",
    }
    return mapping.get(severity.lower(), "P3")


@router.post("/prometheus", response_model=list[AlertIngestResponse])
async def prometheus_webhook(
    payload: dict,
    db: DBSession,
    authorization: str = Header(...),
):
    """
    Accepts Prometheus Alertmanager webhook format and ingests
    each alert into AlertFlow.
    """
    try:
        token = authorization.replace("Bearer ", "")
        payload_jwt = decode_access_token(token)
        team_id = int(payload_jwt.get("team_id"))
    except (JWTError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    alerts = payload.get("alerts", [])
    results = []

    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        alert_request = AlertIngestRequest(
            source="prometheus",
            name=labels.get("alertname", "UnknownAlert"),
            service_name=labels.get("service", labels.get("job", "unknown")),
            message=annotations.get("summary") or annotations.get("description"),
            priority=_map_severity(labels.get("severity", "warning")),
            labels=labels,
        )

        result = await ingest_alert(db=db, team_id=team_id, payload=alert_request)
        results.append(result)

    return results


@router.post("/grafana", response_model=AlertIngestResponse)
async def grafana_webhook(
    payload: dict,
    db: DBSession,
    authorization: str = Header(...),
):
    """
    Accepts Grafana alerting webhook format and ingests
    the alert into AlertFlow.
    """
    try:
        token = authorization.replace("Bearer ", "")
        payload_jwt = decode_access_token(token)
        team_id = int(payload_jwt.get("team_id"))
    except (JWTError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    tags = payload.get("tags", {})

    alert_request = AlertIngestRequest(
        source="grafana",
        name=payload.get("ruleName") or payload.get("title", "GrafanaAlert"),
        service_name=tags.get("service", payload.get("dashboardId", "unknown")),
        message=payload.get("message") or payload.get("title"),
        priority=_map_severity(tags.get("severity", "warning")),
        labels=tags,
    )

    return await ingest_alert(db=db, team_id=team_id, payload=alert_request)
