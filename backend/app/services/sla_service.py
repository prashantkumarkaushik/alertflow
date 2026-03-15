from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sla_policy import SLAPolicy
from app.schemas.sla_policy import SLAPolicyCreate, SLAPolicyUpdate


async def create_sla_policy(
    db: AsyncSession,
    team_id: int,
    payload: SLAPolicyCreate,
) -> SLAPolicy:
    """
    Create a new SLA policy.
    Each team can only have one policy per priority level.
    """
    # Check for duplicate priority
    result = await db.execute(
        select(SLAPolicy).where(
            and_(
                SLAPolicy.team_id == team_id,
                SLAPolicy.priority == payload.priority,
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SLA policy for priority {payload.priority} already exists",
        )

    policy = SLAPolicy(
        name=payload.name,
        priority=payload.priority,
        response_minutes=payload.response_minutes,
        resolution_minutes=payload.resolution_minutes,
        team_id=team_id,
    )
    db.add(policy)
    await db.flush()
    return policy


async def get_sla_policies(
    db: AsyncSession,
    team_id: int,
) -> list[SLAPolicy]:
    """List all SLA policies for this team."""
    result = await db.execute(
        select(SLAPolicy)
        .where(SLAPolicy.team_id == team_id)
        .order_by(SLAPolicy.priority)
    )
    return list(result.scalars().all())


async def get_sla_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
) -> SLAPolicy:
    """Get a single SLA policy. Raises 404 if not found."""
    result = await db.execute(
        select(SLAPolicy).where(
            and_(
                SLAPolicy.id == policy_id,
                SLAPolicy.team_id == team_id,
            )
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SLA policy {policy_id} not found",
        )
    return policy


async def update_sla_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
    payload: SLAPolicyUpdate,
) -> SLAPolicy:
    """Update an existing SLA policy."""
    policy = await get_sla_policy(db, policy_id, team_id)

    # Only update fields that were actually provided
    if payload.name is not None:
        policy.name = payload.name
    if payload.response_minutes is not None:
        policy.response_minutes = payload.response_minutes
    if payload.resolution_minutes is not None:
        policy.resolution_minutes = payload.resolution_minutes

    return policy


async def delete_sla_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
) -> None:
    """Delete an SLA policy."""
    policy = await get_sla_policy(db, policy_id, team_id)
    await db.delete(policy)
