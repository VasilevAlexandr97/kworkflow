from datetime import UTC, datetime, timedelta, date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from kworkflow.subscriptions.models import (
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionPlan,
)


class SubscriptionPlanGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> SubscriptionPlan | None:
        stmt = select(SubscriptionPlan).where(
            SubscriptionPlan.slug == slug,
        )
        return await self.session.scalar(stmt)

    async def get_by_id(self, plan_id: UUID) -> SubscriptionPlan | None:
        stmt = select(SubscriptionPlan).where(
            SubscriptionPlan.id == plan_id,
        )
        return await self.session.scalar(stmt)


class SubscriptionGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, subscription: Subscription):
        self.session.add(subscription)
        await self.session.flush()

    async def get(self, user_id: UUID) -> list[Subscription]:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
        )
        return list(await self.session.scalars(stmt))

    async def has_active(self, user_id: UUID) -> bool:
        stmt = (
            select(Subscription.id)
            .where(
                Subscription.user_id == user_id,
                Subscription.expires_at > datetime.now(UTC),
            )
            .exists()
        )
        result = await self.session.execute(select(stmt))
        return result.scalar() or False

    async def get_latest_active(
        self,
        user_id: UUID,
        with_plan: bool = False,
    ) -> Subscription | None:
        stmt = select(Subscription)

        if with_plan:
            stmt = stmt.options(joinedload(Subscription.plan))

        stmt = (
            stmt.where(
                Subscription.user_id == user_id,
                Subscription.expires_at > datetime.now(UTC),
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def find_due_for_renewal(self) -> list[Subscription]:
        stmt = select(Subscription).where(
            Subscription.expires_at <= datetime.now(UTC) + timedelta(hours=6),
            Subscription.expires_at > datetime.now(UTC) - timedelta(days=2),
            Subscription.cancelled_at.is_(None),
            Subscription.renewal_attempts < 3,
        )
        return list(await self.session.scalars(stmt))


class PaymentGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, payment: Payment):
        self.session.add(payment)
        await self.session.flush()

    async def get_pending_payment(self, user_id: UUID) -> Payment | None:
        stmt = (
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.PENDING,
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_last_payment_email(
        self,
        user_id: UUID,
    ) -> str | None:
        stmt = (
            select(Payment.email)
            .where(
                Payment.user_id == user_id,
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_last_payment_method(
        self,
        user_id: UUID,
    ) -> str | None:
        stmt = (
            select(Payment.yookassa_payment_method_id)
            .where(
                Payment.user_id == user_id,
                Payment.yookassa_payment_method_id.is_not(None),
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_recent_unpaid_payments(self) -> list[Payment]:
        stmt = select(Payment).where(
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.EXPIRED]),
            Payment.paid_at.is_(None),
            Payment.created_at > datetime.now(UTC) - timedelta(hours=24),
        )
        return list(await self.session.scalars(stmt))
