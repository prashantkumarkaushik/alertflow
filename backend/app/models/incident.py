from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import IncidentPriority, IncidentStatus


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incidentstatus"),
        default=IncidentStatus.TRIGGERED,
        nullable=False,
        index=True,  # we filter by status often
    )

    priority: Mapped[IncidentPriority] = mapped_column(
        SAEnum(IncidentPriority, name="incidentpriority"),
        default=IncidentPriority.P3,
        nullable=False,
        index=True,
    )

    # SLA tracking
    # Set at incident creation from the SLA policy
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Escalation tracking
    # Tracks which step we're currently at (0 = not started)
    current_escalation_step: Mapped[int] = mapped_column(default=0, nullable=False)

    # Timestamps for lifecycle tracking
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Foreign keys
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    sla_policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("sla_policies.id"), nullable=True
    )
    escalation_policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("escalation_policies.id"), nullable=True
    )

    # Relationships
    team: Mapped["Team"] = relationship()  # noqa: F821
    alerts: Mapped[list["Alert"]] = relationship(back_populates="incident")
    sla_policy: Mapped["SLAPolicy | None"] = relationship()  # noqa: F821
    escalation_policy: Mapped["EscalationPolicy | None"] = relationship()
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        back_populates="incident",
        order_by="AuditLog.created_at",
    )
