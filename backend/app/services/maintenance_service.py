from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_window import MaintenanceWindow
from app.schemas.maintenance_window import MaintenanceWindowCreate


async def create_maintenance_window(
    db: AsyncSession,
    team_id: int,
    payload: MaintenanceWindowCreate,
) -> MaintenanceWindow:
    """Create a new maintenance window."""
    window = MaintenanceWindow(
        name=payload.name,
        service_name=payload.service_name,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_active=True,
        team_id=team_id,
    )
    db.add(window)
    await db.flush()
    return window


async def get_maintenance_windows(
    db: AsyncSession,
    team_id: int,
    active_only: bool = False,
) -> list[MaintenanceWindow]:
    """
    List maintenance windows.
    active_only=True returns only currently active windows.
    """
    query = select(MaintenanceWindow).where(MaintenanceWindow.team_id == team_id)

    if active_only:
        now = datetime.now(timezone.utc)
        query = query.where(
            and_(
                MaintenanceWindow.is_active == True,  # noqa: E712
                MaintenanceWindow.starts_at <= now,
                MaintenanceWindow.ends_at >= now,
            )
        )

    query = query.order_by(MaintenanceWindow.starts_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_maintenance_window(
    db: AsyncSession,
    window_id: int,
    team_id: int,
) -> MaintenanceWindow:
    """Get a single maintenance window. Raises 404 if not found."""
    result = await db.execute(
        select(MaintenanceWindow).where(
            and_(
                MaintenanceWindow.id == window_id,
                MaintenanceWindow.team_id == team_id,
            )
        )
    )
    window = result.scalar_one_or_none()
    if not window:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance window {window_id} not found",
        )
    return window


async def cancel_maintenance_window(
    db: AsyncSession,
    window_id: int,
    team_id: int,
) -> MaintenanceWindow:
    """
    Cancel a maintenance window early by setting is_active=False.
    We don't delete — keeps the history.
    """
    window = await get_maintenance_window(db, window_id, team_id)
    window.is_active = False
    return window


async def delete_maintenance_window(
    db: AsyncSession,
    window_id: int,
    team_id: int,
) -> None:
    """Hard delete a maintenance window."""
    window = await get_maintenance_window(db, window_id, team_id)
    await db.delete(window)
