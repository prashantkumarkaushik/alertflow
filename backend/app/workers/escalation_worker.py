from app.services.notification_service import notify_escalation
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.enums import IncidentStatus
from app.models.escalation_policy import EscalationPolicy
from app.models.incident import Incident

logger = logging.getLogger(__name__)


async def run_escalations() -> None:
    """
    Runs every 60 seconds.
    Finds triggered incidents that need to be escalated
    based on their escalation policy steps.
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            # Only escalate triggered incidents with an escalation policy
            result = await db.execute(
                select(Incident)
                .where(
                    and_(
                        Incident.status == IncidentStatus.TRIGGERED,
                        Incident.escalation_policy_id.is_not(None),
                    )
                )
                .options(selectinload(Incident.escalation_policy))
            )
            incidents = result.scalars().all()

            if not incidents:
                return

            for incident in incidents:
                policy = incident.escalation_policy
                if not policy:
                    continue

                # Load steps for this policy
                step_result = await db.execute(
                    select(EscalationPolicy)
                    .where(EscalationPolicy.id == policy.id)
                    .options(selectinload(EscalationPolicy.steps))
                )
                policy_with_steps = step_result.scalar_one_or_none()
                if not policy_with_steps or not policy_with_steps.steps:
                    continue

                steps = sorted(policy_with_steps.steps, key=lambda s: s.step_order)

                # Find the next step to fire
                next_step_index = incident.current_escalation_step
                if next_step_index >= len(steps):
                    continue  # all steps exhausted

                next_step = steps[next_step_index]

                # Check if enough time has passed since incident creation
                threshold = incident.created_at + timedelta(
                    minutes=next_step.delay_minutes
                )

                if now >= threshold:
                    # Fire the escalation
                    logger.info(
                        f"Escalating incident {incident.id} "
                        f"to {next_step.notify_target} "
                        f"(step {next_step.step_order})"
                    )
                    await notify_escalation(
                        db=db,
                        team_id=incident.team_id,
                        incident_id=incident.id,
                        title=incident.title,
                        priority=incident.priority.value,
                        step_order=next_step.step_order,
                        notify_target=next_step.notify_target,
                    )

                    # In production: POST to webhook, send email etc.
                    # For now: log it and record in audit log

                    incident.current_escalation_step += 1

                    audit = AuditLog(
                        incident_id=incident.id,
                        actor="system:escalation_worker",
                        action="incident.escalated",
                        payload={
                            "step_order": next_step.step_order,
                            "notify_target": next_step.notify_target,
                            "delay_minutes": next_step.delay_minutes,
                            "escalated_at": now.isoformat(),
                        },
                    )
                    db.add(audit)

            await db.commit()
            logger.info(f"Escalation worker: processed {len(incidents)} incident(s)")

        except Exception as e:
            await db.rollback()
            logger.error(f"Escalation worker error: {e}")
