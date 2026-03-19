from pydantic import BaseModel


class EscalationStepCreate(BaseModel):
    step_order: int
    delay_minutes: int
    notify_target: str
    description: str | None = None


class EscalationStepResponse(BaseModel):
    id: int
    step_order: int
    delay_minutes: int
    notify_target: str
    description: str | None
    policy_id: int

    model_config = {"from_attributes": True}


class EscalationPolicyCreate(BaseModel):
    name: str
    description: str | None = None
    steps: list[EscalationStepCreate] = []


class EscalationPolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class EscalationPolicyResponse(BaseModel):
    id: int
    name: str
    description: str | None
    team_id: int
    steps: list[EscalationStepResponse] = []

    model_config = {"from_attributes": True}
