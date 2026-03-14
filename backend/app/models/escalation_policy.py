from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class EscalationPolicy(Base, TimestampMixin):
    __tablename__ = "escalation_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship()  # noqa: F821
    steps: Mapped[list["EscalationStep"]] = relationship(
        back_populates="policy",
        order_by="EscalationStep.step_order",  # always return steps in order
        cascade="all, delete-orphan",  # deleting policy deletes its steps
    )


class EscalationStep(Base, TimestampMixin):
    __tablename__ = "escalation_steps"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Which step this is in the policy (1, 2, 3...)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # How many minutes after incident creation before this step fires
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Who to notify — email, slack webhook, pagerduty URL etc.
    notify_target: Mapped[str] = mapped_column(String(500), nullable=False)

    # Human readable label e.g. "Notify on-call engineer"
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("escalation_policies.id"), nullable=False
    )

    # Relationships
    policy: Mapped["EscalationPolicy"] = relationship(back_populates="steps")
