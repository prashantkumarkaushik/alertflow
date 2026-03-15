from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.schemas.sla_policy import (
    SLAPolicyCreate,
    SLAPolicyResponse,
    SLAPolicyUpdate,
)
from app.services.sla_service import (
    create_sla_policy,
    delete_sla_policy,
    get_sla_policies,
    get_sla_policy,
    update_sla_policy,
)

router = APIRouter(prefix="/sla-policies", tags=["sla-policies"])


@router.post("", response_model=SLAPolicyResponse, status_code=201)
async def create(
    payload: SLAPolicyCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new SLA policy for your team."""
    return await create_sla_policy(db, current_user.team_id, payload)


@router.get("", response_model=list[SLAPolicyResponse])
async def list_policies(
    current_user: CurrentUser,
    db: DBSession,
):
    """List all SLA policies for your team."""
    return await get_sla_policies(db, current_user.team_id)


@router.get("/{policy_id}", response_model=SLAPolicyResponse)
async def get_one(
    policy_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a single SLA policy."""
    return await get_sla_policy(db, policy_id, current_user.team_id)


@router.put("/{policy_id}", response_model=SLAPolicyResponse)
async def update(
    policy_id: int,
    payload: SLAPolicyUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update an SLA policy."""
    return await update_sla_policy(db, policy_id, current_user.team_id, payload)


@router.delete("/{policy_id}", status_code=204)
async def delete(
    policy_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete an SLA policy."""
    await delete_sla_policy(db, policy_id, current_user.team_id)
