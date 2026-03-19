from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.escalation_policy import EscalationPolicy, EscalationStep
from app.schemas.escalation_policy import (
    EscalationPolicyCreate,
    EscalationPolicyUpdate,
    EscalationStepCreate,
)


async def create_escalation_policy(
    db: AsyncSession,
    team_id: int,
    payload: EscalationPolicyCreate,
) -> EscalationPolicy:
    """Create escalation policy with optional steps."""
    policy = EscalationPolicy(
        name=payload.name,
        description=payload.description,
        team_id=team_id,
    )
    db.add(policy)
    await db.flush()  # get policy.id

    # Create steps if provided
    for step_data in payload.steps:
        step = EscalationStep(
            policy_id=policy.id,
            step_order=step_data.step_order,
            delay_minutes=step_data.delay_minutes,
            notify_target=step_data.notify_target,
            description=step_data.description,
        )
        db.add(step)

    await db.flush()
    return await _get_policy_with_steps(db, policy.id, team_id)


async def _get_policy_with_steps(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
) -> EscalationPolicy:
    """Internal helper — load policy with steps."""
    result = await db.execute(
        select(EscalationPolicy)
        .where(
            and_(
                EscalationPolicy.id == policy_id,
                EscalationPolicy.team_id == team_id,
            )
        )
        .options(selectinload(EscalationPolicy.steps))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation policy {policy_id} not found",
        )
    return policy


async def get_escalation_policies(
    db: AsyncSession,
    team_id: int,
) -> list[EscalationPolicy]:
    """List all escalation policies with their steps."""
    result = await db.execute(
        select(EscalationPolicy)
        .where(EscalationPolicy.team_id == team_id)
        .options(selectinload(EscalationPolicy.steps))
        .order_by(EscalationPolicy.created_at.desc())
    )
    return list(result.scalars().all())


async def get_escalation_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
) -> EscalationPolicy:
    """Get single escalation policy with steps."""
    return await _get_policy_with_steps(db, policy_id, team_id)


async def update_escalation_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
    payload: EscalationPolicyUpdate,
) -> EscalationPolicy:
    """Update policy name/description."""
    policy = await _get_policy_with_steps(db, policy_id, team_id)
    if payload.name is not None:
        policy.name = payload.name
    if payload.description is not None:
        policy.description = payload.description
    return policy


async def add_escalation_step(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
    payload: EscalationStepCreate,
) -> EscalationPolicy:
    """Add a step to an existing policy."""
    policy = await _get_policy_with_steps(db, policy_id, team_id)
    step = EscalationStep(
        policy_id=policy.id,
        step_order=payload.step_order,
        delay_minutes=payload.delay_minutes,
        notify_target=payload.notify_target,
        description=payload.description,
    )
    db.add(step)
    await db.flush()
    return await _get_policy_with_steps(db, policy_id, team_id)


async def delete_escalation_policy(
    db: AsyncSession,
    policy_id: int,
    team_id: int,
) -> None:
    """Delete policy and all its steps (cascade)."""
    policy = await _get_policy_with_steps(db, policy_id, team_id)
    await db.delete(policy)
