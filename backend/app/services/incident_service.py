from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.schemas.incident import IncidentListResponse, StatusTransitionRequest

# Valid transitions — key is current status, value is allowed next statuses
VALID_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.TRIGGERED: [
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.RESOLVED,
    ],
    IncidentStatus.ACKNOWLEDGED: [
        IncidentStatus.RESOLVED,
    ],
    IncidentStatus.RESOLVED: [
        IncidentStatus.TRIGGERED,  # re-open
    ],
}


async def get_incidents(
    db: AsyncSession,
    team_id: int,
    status_filter: IncidentStatus | None = None,
    priority_filter: str | None = None,
    sla_breached: bool | None = None,
    skip: int = 0,
    limit: int = 50,
) -> IncidentListResponse:
    """List incidents with optional filters."""
    query = select(Incident).where(Incident.team_id == team_id)

    if status_filter:
        query = query.where(Incident.status == status_filter)
    if priority_filter:
        query = query.where(Incident.priority == priority_filter)
    if sla_breached is not None:
        query = query.where(Incident.sla_breached == sla_breached)

    # Count total for pagination
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Fetch paginated results, newest first
    query = query.order_by(Incident.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(items=list(incidents), total=total)


async def get_incident_by_id(
    db: AsyncSession,
    incident_id: int,
    team_id: int,
) -> Incident:
    """
    Get a single incident with alerts and audit logs loaded.
    Uses selectinload to load relationships in a single extra query
    instead of N+1 queries.
    """
    result = await db.execute(
        select(Incident)
        .where(
            and_(
                Incident.id == incident_id,
                Incident.team_id == team_id,
            )
        )
        .options(
            selectinload(Incident.alerts),
            selectinload(Incident.audit_logs),
        )
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    return incident


async def transition_status(
    db: AsyncSession,
    incident_id: int,
    team_id: int,
    actor: str,
    payload: StatusTransitionRequest,
) -> Incident:
    """
    Transition incident status with validation.
    Writes audit log on every transition.
    """
    incident = await get_incident_by_id(db, incident_id, team_id)

    # Validate transition
    allowed = VALID_TRANSITIONS.get(incident.status, [])
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Cannot transition from {incident.status.value} "
                f"to {payload.status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            ),
        )

    old_status = incident.status
    now = datetime.now(timezone.utc)

    # Update status
    incident.status = payload.status

    # Set lifecycle timestamps
    if payload.status == IncidentStatus.ACKNOWLEDGED:
        incident.acknowledged_at = now
    elif payload.status == IncidentStatus.RESOLVED:
        incident.resolved_at = now
    elif payload.status == IncidentStatus.TRIGGERED:
        # Re-opening — clear resolved timestamp
        incident.resolved_at = None

    # Write audit log
    audit = AuditLog(
        incident_id=incident.id,
        actor=actor,
        action=f"incident.{payload.status.value}",
        payload={
            "from_status": old_status.value,
            "to_status": payload.status.value,
            "reason": payload.reason,
        },
    )
    db.add(audit)

    return incident


async def get_audit_log(
    db: AsyncSession,
    incident_id: int,
    team_id: int,
) -> list[AuditLog]:
    """Get full audit timeline for an incident."""
    # Verify incident belongs to team
    await get_incident_by_id(db, incident_id, team_id)

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.incident_id == incident_id)
        .order_by(AuditLog.created_at.asc())
    )
    return list(result.scalars().all())
