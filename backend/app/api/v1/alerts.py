from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.schemas.alert import AlertIngestRequest, AlertIngestResponse
from app.services.alert_service import ingest_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/ingest", response_model=AlertIngestResponse, status_code=201)
async def ingest(
    payload: AlertIngestRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Ingest an alert from a monitoring system.
    Handles deduplication, maintenance window suppression,
    incident grouping, and SLA deadline calculation.
    """
    return await ingest_alert(
        db=db,
        team_id=current_user.team_id,
        payload=payload,
    )
