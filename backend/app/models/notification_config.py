from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationConfig(Base, TimestampMixin):
    __tablename__ = "notification_configs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Which team this config belongs to
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    # Notification channel type — slack for now, extensible later
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="slack")

    # Slack incoming webhook URL
    # e.g. https://hooks.slack.com/services/T00000/B00000/XXXXX
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Human readable name e.g. "#incidents-channel"
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Which events to notify on
    notify_on_new_incident: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_sla_warning: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_escalation: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    team: Mapped["Team"] = relationship()  # noqa: F821
