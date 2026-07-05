import logging

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid7

from redis import RedisError
from redis.asyncio import Redis
from redis.asyncio.lock import Lock

from kworkflow.auth.id_provider import IdProvider
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.yookassa.client import (
    AmountData,
    ConfirmationRedirectData,
    ConfirmationType,
    Currency,
    CustomerData,
    PaymentRequest,
    ReceiptData,
    ReceiptItemData,
    YooKassaClient,
)
from kworkflow.subscriptions.exceptions import (
    PaymentEmailRequiredError,
    ServiceTemporarilyUnavailableError,
    SubscriptionPlanNotFoundError,
)
from kworkflow.subscriptions.gateways import (
    PaymentGateway,
    SubscriptionGateway,
    SubscriptionPlanGateway,
)
from kworkflow.subscriptions.models import (
    Payment,
    PaymentStatus,
    PlanSlug,
    SubscriptionPlan,
)
from kworkflow.subscriptions.validators import payment_email_validator

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(
        self,
        subscription_plan_gateway: SubscriptionPlanGateway,
        subscription_gateway: SubscriptionGateway,
        payment_gateway: PaymentGateway,
        id_provider: IdProvider,
        payment_client: YooKassaClient,
        transaction_manager: TransactionManager,
        redis_client: Redis,
    ):
        self.subscription_plan_gateway = subscription_plan_gateway
        self.subscription_gateway = subscription_gateway
        self.payment_gateway = payment_gateway
        self.id_provider = id_provider
        self.payment_client = payment_client
        self.transaction_manager = transaction_manager
        self.redis_client = redis_client

    def _payment_lock(self, user_id: UUID):
        return Lock(
            self.redis_client,
            f"create_payment:{user_id}",
            timeout=120,
            blocking_timeout=30,
        )

    async def _get_initial_or_monthly_plan(
        self,
        user_id: UUID,
    ) -> SubscriptionPlan:
        previous_subscriptions = await self.subscription_gateway.get(user_id)
        if previous_subscriptions:
            plan = await self.subscription_plan_gateway.get_by_slug(
                PlanSlug.PRO_MONTHLY,
            )
        else:
            plan = await self.subscription_plan_gateway.get_by_slug(
                PlanSlug.PRO_INITIAL,
            )
        if not plan:
            raise SubscriptionPlanNotFoundError
        return plan

    async def get_plan_for_user(self) -> SubscriptionPlan:
        user_id = await self.id_provider.get_current_user_id()
        return await self._get_initial_or_monthly_plan(user_id)

    async def get_or_create_pending_payment(
        self,
        email: str | None = None,
    ) -> Payment:
        user_id = await self.id_provider.get_current_user_id()
        lock = self._payment_lock(user_id)
        try:
            async with lock:
                if email is None:
                    email = await self.payment_gateway.get_last_payment_email(
                        user_id,
                    )
                if not email:
                    raise PaymentEmailRequiredError
                payment_email_validator(email)
                existing = await self.payment_gateway.get_pending_payment(
                    user_id,
                )
                now = datetime.now(UTC)
                payment_link_ttl = timedelta(seconds=300)
                if existing and existing.created_at > now - payment_link_ttl:
                    return existing

                if existing:
                    existing.status = PaymentStatus.EXPIRED
                plan = await self._get_initial_or_monthly_plan(user_id)
                payment_request = PaymentRequest(
                    amount=AmountData(
                        value=str(plan.price_rub),
                        currency=Currency.RUB,
                    ),
                    description=plan.name,
                    receipt=ReceiptData(
                        customer=CustomerData(
                            email=email,
                        ),
                        items=[
                            ReceiptItemData(
                                description=plan.name,
                                amount=AmountData(
                                    value=str(plan.price_rub),
                                    currency=Currency.RUB,
                                ),
                                vat_code=1,
                                quantity=1,
                            ),
                        ],
                    ),
                    confirmation=ConfirmationRedirectData(
                        type=ConfirmationType.REDIRECT,
                        return_url="https://t.me/kworkflowbot",
                    ),
                    save_payment_method=True,
                    capture=True,
                )
                yookassa_payment = await self.payment_client.create_payment(
                    payment_request,
                )
                logger.debug(f"YOOKASSA_PAYMENT: {yookassa_payment}")
                new_payment = Payment(
                    id=uuid7(),
                    user_id=user_id,
                    yookassa_payment_id=yookassa_payment.id,
                    amount=Decimal(yookassa_payment.amount.value),
                    status=PaymentStatus.PENDING,
                    email=email,
                    link=yookassa_payment.confirmation.confirmation_url,
                    paid_at=None,
                    created_at=now,
                )
                await self.payment_gateway.add(new_payment)
                await self.transaction_manager.commit()
                return new_payment
        except RedisError:
            raise ServiceTemporarilyUnavailableError
