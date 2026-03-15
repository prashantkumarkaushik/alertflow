from pydantic import BaseModel, field_validator


class SLAPolicyCreate(BaseModel):
    name: str
    priority: str
    response_minutes: int
    resolution_minutes: int

    @field_validator("priority", mode="before")
    @classmethod
    def uppercase_priority(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class SLAPolicyUpdate(BaseModel):
    name: str | None = None
    response_minutes: int | None = None
    resolution_minutes: int | None = None


class SLAPolicyResponse(BaseModel):
    id: int
    name: str
    priority: str
    response_minutes: int
    resolution_minutes: int
    team_id: int

    model_config = {"from_attributes": True}
