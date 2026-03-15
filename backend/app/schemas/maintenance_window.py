from datetime import datetime

from pydantic import BaseModel, model_validator


class MaintenanceWindowCreate(BaseModel):
    name: str
    service_name: str
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_dates(self) -> "MaintenanceWindowCreate":
        """ends_at must be after starts_at."""
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class MaintenanceWindowResponse(BaseModel):
    id: int
    name: str
    service_name: str
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    team_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
