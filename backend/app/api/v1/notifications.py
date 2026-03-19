from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.models.notification_config import NotificationConfig
from app.schemas.notification_config import (
    NotificationConfigCreate,
    NotificationConfigResponse,
)
from sqlalchemy import select, and_

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationConfigResponse, status_code=201)
async def create_config(
    payload: NotificationConfigCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Add a Slack webhook for your team."""
    config = NotificationConfig(
        team_id=current_user.team_id,
        channel="slack",
        name=payload.name,
        webhook_url=payload.webhook_url,
        notify_on_new_incident=payload.notify_on_new_incident,
        notify_on_sla_warning=payload.notify_on_sla_warning,
        notify_on_escalation=payload.notify_on_escalation,
    )
    db.add(config)
    await db.flush()
    return config


@router.get("", response_model=list[NotificationConfigResponse])
async def list_configs(current_user: CurrentUser, db: DBSession):
    """List all notification configs for your team."""
    result = await db.execute(
        select(NotificationConfig).where(
            NotificationConfig.team_id == current_user.team_id
        )
    )
    return list(result.scalars().all())


@router.delete("/{config_id}", status_code=204)
async def delete_config(
    config_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete a notification config."""
    result = await db.execute(
        select(NotificationConfig).where(
            and_(
                NotificationConfig.id == config_id,
                NotificationConfig.team_id == current_user.team_id,
            )
        )
    )
    config = result.scalar_one_or_none()
    if config:
        await db.delete(config)
