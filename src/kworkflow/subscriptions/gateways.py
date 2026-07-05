from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


class SubscriptionGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> list[Subscription]:
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
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
