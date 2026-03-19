from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import AlertStatus


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Where the alert came from e.g. "prometheus", "grafana", "datadog"
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Alert name e.g. "HighCPUUsage", "DiskSpaceLow"
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Which service triggered this alert
    service_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # SHA-256 hash of source + name + labels — used for deduplication
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Raw labels from the monitoring system stored as JSON
    # e.g. {"env": "prod", "region": "us-east-1", "severity": "critical"}
    # labels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    labels: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=dict,
    )

    # Human readable description of the alert
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, name="alertstatus"),
        default=AlertStatus.OPEN,
        nullable=False,
    )

    # Set to True if suppressed by a maintenance window
    suppressed: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Foreign keys
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    # Which incident this alert was grouped into (nullable — set after grouping)
    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidents.id"), nullable=True
    )

    # Relationships
    team: Mapped["Team"] = relationship()  # noqa: F821
    incident: Mapped["Incident | None"] = relationship(  # noqa: F821
        back_populates="alerts"
    )
