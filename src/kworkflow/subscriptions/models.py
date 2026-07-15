from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    UUID as SA_UUID,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kworkflow.infra.database.base import Base


class PlanSlug(StrEnum):
    PRO_INITIAL = "pro_initial"
    PRO_MONTHLY = "pro_monthly"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    price_rub: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duration_days: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan",
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
    )
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="RESTRICT"),
        unique=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    renewal_attempts: Mapped[int] = mapped_column(
        default=0,
        server_default=text("0"),
    )
    plan: Mapped["SubscriptionPlan"] = relationship(
        back_populates="subscriptions",
        lazy="raise",
    )

    def cancelled(self):
        now = datetime.now(UTC)
        self.cancelled_at = now
        self.updated_at = now

    def finish(self):
        now = datetime.now(UTC)
        self.cancelled_at = now
        self.expires_at = now
        self.updated_at = now


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    yookassa_payment_id: Mapped[str] = mapped_column(
        unique=True,
    )
    yookassa_payment_method_id: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str]

    email: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def mark_succeeded(
        self,
        payment_method_id: str,
        dt: datetime | None = None,
    ) -> None:
        if not payment_method_id:
            raise ValueError(
                "payment_method_id is required — subscription payments "
                "always have a saved payment method",
            )
        if dt is None:
            dt = datetime.now(UTC)
        self.yookassa_payment_method_id = payment_method_id
        self.status = PaymentStatus.SUCCEEDED
        self.paid_at = dt
        self.updated_at = dt

    def mark_canceled(
        self,
        error: str | None = None,
        dt: datetime | None = None,
    ) -> None:
        if dt is None:
            dt = datetime.now(UTC)
        self.status = PaymentStatus.CANCELED
        self.error = error
        self.updated_at = dt

    def __repr__(self) -> str:
        return (
            "Payment("
            f"id={self.id}, "
            f"yookassa_payment_id={self.yookassa_payment_id}, "
            f"amount={self.amount}"
            ")"
        )
