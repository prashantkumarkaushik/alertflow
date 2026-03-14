from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Who performed the action e.g. "user:5", "system:sla_worker"
    actor: Mapped[str] = mapped_column(String(100), nullable=False)

    # What happened e.g. "incident.acknowledged", "sla.breached"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Any extra data about the action stored as JSON
    # e.g. {"from_status": "triggered", "to_status": "acknowledged"}
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Foreign key — every log entry belongs to an incident
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"), nullable=False, index=True
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(back_populates="audit_logs")
