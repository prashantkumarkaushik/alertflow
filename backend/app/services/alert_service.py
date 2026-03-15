import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.enums import AlertStatus, IncidentPriority, IncidentStatus
from app.models.incident import Incident
from app.models.maintenance_window import MaintenanceWindow
from app.models.sla_policy import SLAPolicy
from app.schemas.alert import AlertIngestRequest, AlertIngestResponse, AlertResponse
from app.services.redis_service import redis_service


def compute_fingerprint(source: str, name: str, labels: dict) -> str:
    """
    Create a unique fingerprint for this alert.
    Same source + name + labels = same fingerprint = duplicate.
    We sort the labels dict so {"a":1,"b":2} == {"b":2,"a":1}
    """
    raw = f"{source}:{name}:{json.dumps(labels, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _is_under_maintenance(
    db: AsyncSession,
    team_id: int,
    service_name: str,
) -> bool:
    """Check if service has an active maintenance window right now."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(MaintenanceWindow).where(
            and_(
                MaintenanceWindow.team_id == team_id,
                MaintenanceWindow.service_name == service_name,
                MaintenanceWindow.is_active == True,  # noqa: E712
                MaintenanceWindow.starts_at <= now,
                MaintenanceWindow.ends_at >= now,
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def _get_sla_deadline(
    db: AsyncSession,
    team_id: int,
    priority: str,
) -> tuple[datetime | None, int | None]:
    """
    Find matching SLA policy and calculate deadline.
    Returns (deadline, policy_id) or (None, None) if no policy found.
    """
    result = await db.execute(
        select(SLAPolicy).where(
            and_(
                SLAPolicy.team_id == team_id,
                SLAPolicy.priority == priority,
            )
        )
    )
    policy = result.scalar_one_or_none()

    if not policy:
        return None, None

    deadline = datetime.now(timezone.utc) + timedelta(minutes=policy.resolution_minutes)
    return deadline, policy.id


async def _find_or_create_incident(
    db: AsyncSession,
    team_id: int,
    service_name: str,
    alert_name: str,
    priority: str,
    sla_deadline: datetime | None,
    sla_policy_id: int | None,
) -> tuple[Incident, bool]:
    """
    Find an open incident for this team+service or create a new one.
    Returns (incident, created) where created=True if new incident.
    """
    # Look for an existing open/acknowledged incident for this service
    result = await db.execute(
        select(Incident).where(
            and_(
                Incident.team_id == team_id,
                Incident.status.in_(
                    [IncidentStatus.TRIGGERED, IncidentStatus.ACKNOWLEDGED]
                ),
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing, False

    # No open incident — create one
    incident = Incident(
        title=f"{service_name}: {alert_name}",
        team_id=team_id,
        priority=IncidentPriority(priority),
        status=IncidentStatus.TRIGGERED,
        sla_deadline=sla_deadline,
        sla_policy_id=sla_policy_id,
    )
    db.add(incident)
    await db.flush()  # get incident.id without committing
    return incident, True


async def ingest_alert(
    db: AsyncSession,
    team_id: int,
    payload: AlertIngestRequest,
) -> AlertIngestResponse:
    """
    Main alert ingestion flow.
    This is called by the API route and orchestrates all steps.
    """

    # ── Step 1: Compute fingerprint ────────────────────────
    fingerprint = compute_fingerprint(payload.source, payload.name, payload.labels)

    # # ── Step 2: Redis deduplication check ──────────────────
    # is_dup = await redis_service.is_duplicate(fingerprint, team_id)
    # if is_dup:
    #     # Return early — don't save anything
    #     return AlertIngestResponse(
    #         alert=None,  # type: ignore
    #         incident_id=None,
    #         deduplicated=True,
    #         suppressed=False,
    #         message="Alert deduplicated — same fingerprint seen recently",
    #     )
    # ── Step 2: Redis deduplication check ──────────────────
    is_dup = await redis_service.is_duplicate(fingerprint, team_id)
    if is_dup:
        return AlertIngestResponse(
            alert=None,  # type: ignore
            incident_id=None,
            deduplicated=True,
            suppressed=False,
            message="Alert deduplicated — same fingerprint seen recently",
        )

    # ── Step 3: Maintenance window check ───────────────────
    under_maintenance = await _is_under_maintenance(db, team_id, payload.service_name)

    if under_maintenance:
        # Save alert as suppressed but don't create incident
        alert = Alert(
            source=payload.source,
            name=payload.name,
            service_name=payload.service_name,
            fingerprint=fingerprint,
            labels=payload.labels,
            message=payload.message,
            status=AlertStatus.SUPPRESSED,
            suppressed=True,
            team_id=team_id,
        )
        db.add(alert)
        await db.flush()

        return AlertIngestResponse(
            alert=AlertResponse.model_validate(alert),
            incident_id=None,
            deduplicated=False,
            suppressed=True,
            message=f"Alert suppressed — {payload.service_name} is under maintenance",
        )

    # ── Step 4: Save alert ─────────────────────────────────
    alert = Alert(
        source=payload.source,
        name=payload.name,
        service_name=payload.service_name,
        fingerprint=fingerprint,
        labels=payload.labels,
        message=payload.message,
        status=AlertStatus.OPEN,
        suppressed=False,
        team_id=team_id,
    )
    db.add(alert)
    await db.flush()  # get alert.id

    # ── Step 5: SLA deadline calculation ───────────────────
    sla_deadline, sla_policy_id = await _get_sla_deadline(db, team_id, payload.priority)

    # ── Step 6: Find or create incident ────────────────────
    incident, created = await _find_or_create_incident(
        db=db,
        team_id=team_id,
        service_name=payload.service_name,
        alert_name=payload.name,
        priority=payload.priority,
        sla_deadline=sla_deadline,
        sla_policy_id=sla_policy_id,
    )

    # ── Step 7: Link alert to incident ─────────────────────
    alert.incident_id = incident.id

    # ── Step 8: Write audit log ────────────────────────────
    action = "incident.created" if created else "alert.added_to_incident"
    audit = AuditLog(
        incident_id=incident.id,
        actor="system:ingest",
        action=action,
        payload={
            "alert_id": alert.id,
            "alert_name": payload.name,
            "service_name": payload.service_name,
            "source": payload.source,
            "priority": payload.priority,
            "sla_deadline": sla_deadline.isoformat() if sla_deadline else None,
        },
    )
    db.add(audit)

    return AlertIngestResponse(
        alert=AlertResponse.model_validate(alert),
        incident_id=incident.id,
        deduplicated=False,
        suppressed=False,
        message="incident.created" if created else "alert.added_to_incident",
    )
