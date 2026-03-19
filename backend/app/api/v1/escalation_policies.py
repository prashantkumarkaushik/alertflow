from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.schemas.escalation_policy import (
    EscalationPolicyCreate,
    EscalationPolicyResponse,
    EscalationPolicyUpdate,
    EscalationStepCreate,
)
from app.services.escalation_service import (
    add_escalation_step,
    create_escalation_policy,
    delete_escalation_policy,
    get_escalation_policies,
    get_escalation_policy,
    update_escalation_policy,
)

router = APIRouter(prefix="/escalation-policies", tags=["escalation-policies"])


@router.post("", response_model=EscalationPolicyResponse, status_code=201)
async def create(
    payload: EscalationPolicyCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create escalation policy. Optionally include steps in the request."""
    return await create_escalation_policy(db, current_user.team_id, payload)


@router.get("", response_model=list[EscalationPolicyResponse])
async def list_policies(
    current_user: CurrentUser,
    db: DBSession,
):
    """List all escalation policies with their steps."""
    return await get_escalation_policies(db, current_user.team_id)


@router.get("/{policy_id}", response_model=EscalationPolicyResponse)
async def get_one(
    policy_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a single escalation policy with steps."""
    return await get_escalation_policy(db, policy_id, current_user.team_id)


@router.put("/{policy_id}", response_model=EscalationPolicyResponse)
async def update(
    policy_id: int,
    payload: EscalationPolicyUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update policy name or description."""
    return await update_escalation_policy(db, policy_id, current_user.team_id, payload)


@router.post("/{policy_id}/steps", response_model=EscalationPolicyResponse)
async def add_step(
    policy_id: int,
    payload: EscalationStepCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Add a step to an existing escalation policy."""
    return await add_escalation_step(db, policy_id, current_user.team_id, payload)


@router.delete("/{policy_id}", status_code=204)
async def delete(
    policy_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete policy and all its steps."""
    await delete_escalation_policy(db, policy_id, current_user.team_id)
