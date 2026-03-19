from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class MaintenanceWindow(Base, TimestampMixin):
    __tablename__ = "maintenance_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Which service this window covers
    # Alert ingestion checks this before creating incidents
    service_name: Mapped[str] = mapped_column(String(200), nullable=False)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Foreign key
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship()  # noqa: F821 # pyright: ignore[reportUndefinedVariable]
