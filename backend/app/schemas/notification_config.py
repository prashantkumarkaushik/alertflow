from pydantic import BaseModel


class NotificationConfigCreate(BaseModel):
    name: str
    webhook_url: str
    notify_on_new_incident: bool = True
    notify_on_sla_warning: bool = True
    notify_on_escalation: bool = True


class NotificationConfigResponse(BaseModel):
    id: int
    name: str
    channel: str
    webhook_url: str
    notify_on_new_incident: bool
    notify_on_sla_warning: bool
    notify_on_escalation: bool
    is_active: bool
    team_id: int

    model_config = {"from_attributes": True}
