import logging

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid7

from redis import RedisError
from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockError

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
    Status,
    YooKassaClient,
)
from kworkflow.notifications.interfaces import (
    SubscriptionActivatedNotificationQueue,
)
from kworkflow.subscriptions.dto import SubscriptionInfo
from kworkflow.subscriptions.exceptions import (
    ActiveSubscriptionExistsError,
    PaymentEmailRequiredError,
    ServiceTemporarilyUnavailableError,
    SubscriptionAlreadyCancelledError,
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
    Subscription,
    SubscriptionPlan,
)
from kworkflow.subscriptions.validators import payment_email_validator

logger = logging.getLogger(__name__)


class SubscriptionPaymentService:
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
        is_active = await self.subscription_gateway.has_active(user_id)
        if is_active:
            raise ActiveSubscriptionExistsError
        return await self._get_initial_or_monthly_plan(user_id)

    async def get_or_create_pending_payment(
        self,
        email: str | None = None,
    ) -> Payment:
        user_id = await self.id_provider.get_current_user_id()
        lock = self._payment_lock(user_id)
        try:
            async with lock:
                is_active = await self.subscription_gateway.has_active(user_id)
                if is_active:
                    raise ActiveSubscriptionExistsError
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
                    # TODO: урл захардкожен, возможно стоит вынести в конфиг
                    confirmation=ConfirmationRedirectData(
                        type=ConfirmationType.REDIRECT,
                        return_url="https://t.me/kworkflowbot",
                    ),
                    metadata={
                        "plan_id": str(plan.id),
                    },
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
                    yookassa_payment_method_id=None,
                    amount=Decimal(yookassa_payment.amount.value),
                    status=PaymentStatus.PENDING,
                    email=email,
                    link=yookassa_payment.confirmation.confirmation_url,
                    paid_at=None,
                    created_at=now,
                    updated_at=now,
                )
                await self.payment_gateway.add(new_payment)
                await self.transaction_manager.commit()
                return new_payment
        except RedisError:
            raise ServiceTemporarilyUnavailableError


class PaymentVerificationService:
    def __init__(
        self,
        payment_gateway: PaymentGateway,
        payment_client: YooKassaClient,
        subscription_plan_gateway: SubscriptionPlanGateway,
        subscription_gateway: SubscriptionGateway,
        transaction_manager: TransactionManager,
        notify_queue: SubscriptionActivatedNotificationQueue,
        redis_client: Redis,
    ):
        self.payment_gateway = payment_gateway
        self.payment_client = payment_client
        self.subscription_plan_gateway = subscription_plan_gateway
        self.subscription_gateway = subscription_gateway
        self.transaction_manager = transaction_manager
        self.notify_queue = notify_queue
        self.redis_client = redis_client

    def _verification_lock(self) -> Lock:
        return Lock(
            self.redis_client,
            "payment_verification",
            timeout=60,
            blocking_timeout=0,
        )

    # TODO: слишком большой метод, подумать как правильно его разбить
    async def verify_pending_payments(self):
        try:
            lock = self._verification_lock()
            async with lock:
                unpaid_payments = (
                    await self.payment_gateway.get_recent_unpaid_payments()
                )
                logger.info(f"UNPAID_PAYMENTS: {unpaid_payments}")
                if not unpaid_payments:
                    return

                now = datetime.now(UTC)
                for payment in unpaid_payments:
                    try:
                        yookassa_payment = (
                            await self.payment_client.get_payment(
                                payment.yookassa_payment_id,
                            )
                        )
                        logger.info(f"YOOKASSA PAYMENT: {yookassa_payment}")
                        if yookassa_payment.status == Status.SUCCEEDED:
                            pm = yookassa_payment.payment_method
                            if not pm or not pm.id:
                                logger.error(
                                    f"SUCCEEDED payment {payment.id} "
                                    "has no payment_method — skipping",
                                )
                                continue
                            if not yookassa_payment.metadata:
                                logger.error(
                                    f"SUCCEEDED payment {payment.id} "
                                    f"(yookassa_id={payment.yookassa_payment_id}) "
                                    " has no metadata - cannot determine plan, skipping",
                                )
                                continue
                            plan_id = yookassa_payment.metadata.get(
                                "plan_id",
                            )
                            if not plan_id:
                                logger.error(
                                    f"SUCCEEDED payment {payment.id} "
                                    f"(yookassa_id={payment.yookassa_payment_id}) "
                                    f" has metadata without 'plan_id' "
                                    f"(metadata={yookassa_payment.metadata}) — skipping",
                                )
                                continue
                            plan = (
                                await self.subscription_plan_gateway.get_by_id(
                                    UUID(plan_id),
                                )
                            )
                            if not plan:
                                logger.error(
                                    f"Subscription plan id={plan_id} "
                                    f"(from payment {payment.id} metadata) "
                                    "not found in DB — skipping",
                                )
                                continue
                            payment.mark_succeeded(pm.id)
                            subscription = Subscription(
                                id=uuid7(),
                                user_id=payment.user_id,
                                plan_id=plan.id,
                                payment_id=payment.id,
                                started_at=now,
                                expires_at=now
                                + timedelta(days=plan.duration_days),
                                created_at=now,
                                updated_at=now,
                            )
                            await self.subscription_gateway.add(
                                subscription,
                            )
                            await self.transaction_manager.commit()
                            await self.notify_queue.enqueue(
                                payment.user_id,
                            )
                            await lock.extend(60)
                        elif yookassa_payment.status == Status.CANCELED:
                            payment.status = PaymentStatus.CANCELED
                            await self.transaction_manager.commit()
                    except Exception:
                        logger.exception("VERIFY PAYMENT ERROR")
        except LockError:
            logger.info("Verification skipped — lock held by another worker")
        except RedisError:
            raise ServiceTemporarilyUnavailableError


class SubscriptionManagementService:
    def __init__(
        self,
        subscription_gateway: SubscriptionGateway,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.subscription_gateway = subscription_gateway
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def get_active_subscription_info(self) -> SubscriptionInfo | None:
        user_id = await self.id_provider.get_current_user_id()
        subscription = await self.subscription_gateway.get_latest_active(
            user_id,
            with_plan=True,
        )
        if not subscription:
            return None
        is_cancelled = False
        if subscription.cancelled_at:
            is_cancelled = True
        days_left = (subscription.expires_at - datetime.now(UTC)).days
        return SubscriptionInfo(
            plan_name=subscription.plan.name,
            plan_slug=PlanSlug(subscription.plan.slug),
            is_cancelled=is_cancelled,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
            days_left=days_left,
        )

    async def cancel_subscription(self) -> Subscription:
        user_id = await self.id_provider.get_current_user_id()
        subscription = await self.subscription_gateway.get_latest_active(
            user_id,
        )
        if not subscription or subscription.cancelled_at is not None:
            raise SubscriptionAlreadyCancelledError
        subscription.cancelled()
        await self.transaction_manager.commit()
        return subscription
