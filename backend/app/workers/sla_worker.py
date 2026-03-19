import logging
from datetime import datetime, timezone

from sqlalchemy import and_, select

from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.enums import IncidentStatus
from app.models.incident import Incident

logger = logging.getLogger(__name__)


async def check_sla_breaches() -> None:
    """
    Runs every 60 seconds.
    Finds incidents past their SLA deadline and marks them breached.
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            # Find all non-resolved incidents past their deadline
            result = await db.execute(
                select(Incident).where(
                    and_(
                        Incident.sla_deadline < now,
                        Incident.sla_breached == False,  # noqa: E712
                        Incident.status != IncidentStatus.RESOLVED,
                        Incident.sla_deadline.is_not(None),
                    )
                )
            )
            incidents = result.scalars().all()

            if not incidents:
                return

            for incident in incidents:
                incident.sla_breached = True

                audit = AuditLog(
                    incident_id=incident.id,
                    actor="system:sla_worker",
                    action="sla.breached",
                    payload={
                        "sla_deadline": incident.sla_deadline.isoformat(),
                        "breached_at": now.isoformat(),
                        "priority": incident.priority.value,
                    },
                )
                db.add(audit)

            await db.commit()
            logger.info(f"SLA worker: marked {len(incidents)} incident(s) as breached")

        except Exception as e:
            await db.rollback()
            logger.error(f"SLA worker error: {e}")
