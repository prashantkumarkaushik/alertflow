from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DBSession
from app.models.enums import IncidentPriority, IncidentStatus
from app.schemas.incident import (
    AuditLogResponse,
    IncidentDetailResponse,
    IncidentListResponse,
    StatusTransitionRequest,
)
from app.services.incident_service import (
    get_audit_log,
    get_incident_by_id,
    get_incidents,
    transition_status,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    current_user: CurrentUser,
    db: DBSession,
    status: IncidentStatus | None = Query(default=None),
    priority: IncidentPriority | None = Query(default=None),
    sla_breached: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List incidents for your team.
    Filter by: status, priority, sla_breached
    """
    return await get_incidents(
        db=db,
        team_id=current_user.team_id,
        status_filter=status,
        priority_filter=priority.value if priority else None,
        sla_breached=sla_breached,
        skip=skip,
        limit=limit,
    )


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get full incident detail with alerts and audit log."""
    return await get_incident_by_id(
        db=db,
        incident_id=incident_id,
        team_id=current_user.team_id,
    )


@router.patch("/{incident_id}/status", response_model=IncidentDetailResponse)
async def update_status(
    incident_id: int,
    payload: StatusTransitionRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Transition incident status.
    Valid transitions:
    - triggered → acknowledged
    - triggered → resolved
    - acknowledged → resolved
    - resolved → triggered (re-open)
    """
    actor = f"user:{current_user.id}"
    return await transition_status(
        db=db,
        incident_id=incident_id,
        team_id=current_user.team_id,
        actor=actor,
        payload=payload,
    )


@router.get("/{incident_id}/audit", response_model=list[AuditLogResponse])
async def get_incident_audit(
    incident_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get full audit timeline for an incident."""
    return await get_audit_log(
        db=db,
        incident_id=incident_id,
        team_id=current_user.team_id,
    )


@router.patch("/{incident_id}/assign-escalation", response_model=IncidentDetailResponse)
async def assign_escalation_policy(
    incident_id: int,
    escalation_policy_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Assign an escalation policy to an incident."""
    incident = await get_incident_by_id(db, incident_id, current_user.team_id)
    incident.escalation_policy_id = escalation_policy_id
    return incident
