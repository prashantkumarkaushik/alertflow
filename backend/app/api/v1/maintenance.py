from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DBSession
from app.schemas.maintenance_window import (
    MaintenanceWindowCreate,
    MaintenanceWindowResponse,
)
from app.services.maintenance_service import (
    cancel_maintenance_window,
    create_maintenance_window,
    delete_maintenance_window,
    get_maintenance_window,
    get_maintenance_windows,
)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("", response_model=MaintenanceWindowResponse, status_code=201)
async def create(
    payload: MaintenanceWindowCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a maintenance window. Alerts for this service will be suppressed."""
    return await create_maintenance_window(db, current_user.team_id, payload)


@router.get("", response_model=list[MaintenanceWindowResponse])
async def list_windows(
    current_user: CurrentUser,
    db: DBSession,
    active_only: bool = Query(default=False),
):
    """
    List maintenance windows.
    Use ?active_only=true to see only currently active windows.
    """
    return await get_maintenance_windows(db, current_user.team_id, active_only)


@router.get("/{window_id}", response_model=MaintenanceWindowResponse)
async def get_one(
    window_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a single maintenance window."""
    return await get_maintenance_window(db, window_id, current_user.team_id)


@router.patch("/{window_id}/cancel", response_model=MaintenanceWindowResponse)
async def cancel(
    window_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Cancel a maintenance window early. Sets is_active=False."""
    return await cancel_maintenance_window(db, window_id, current_user.team_id)


@router.delete("/{window_id}", status_code=204)
async def delete(
    window_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Hard delete a maintenance window."""
    await delete_maintenance_window(db, window_id, current_user.team_id)
