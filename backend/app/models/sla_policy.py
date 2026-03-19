from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class SLAPolicy(Base, TimestampMixin):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Priority: P1, P2, P3, P4
    priority: Mapped[str] = mapped_column(String(10), nullable=False)

    # How many minutes until response is required
    response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # How many minutes until resolution is required
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Foreign key — which team this policy belongs to
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
