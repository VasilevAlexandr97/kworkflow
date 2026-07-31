from collections.abc import AsyncIterable
from typing import Any

from aiogram import Bot
from aiogram.types import TelegramObject
from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
    provide,
)
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kworkflow.auth.id_provider import (
    AdminPanelIdProvider,
    IdProvider,
    TelegramIdProvider,
    WebIdProvider,
    WorkerIdProvider,
)
from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.common.dto import CurrentUser
from kworkflow.common.interfaces.generation_limit_checker import (
    GenerationLimitChecker,
)
from kworkflow.common.interfaces.subscription_checker import (
    SubscriptionChecker,
)
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.kwork.client import KworkClient
from kworkflow.infra.polza.limiter import PolzaRateLimiter
from kworkflow.infra.taskiq.queue import (
    TaskiqProposalGeneratedNotificationQueue,
    TaskiqProposalGenerationQueue,
    TaskiqSubscriptionActivatedNotificationQueue,
    TaskiqSubscriptionRenewalNotificationQueue,
)
from kworkflow.infra.telegram.telegram_notifier import TelegramNotifier
from kworkflow.infra.yookassa.client import YooKassaClient
from kworkflow.infra.yookassa.limiter import YookassaRateLimiter
from kworkflow.main.config import Config
from kworkflow.notifications.gateways import (
    SAChannelNotificationGateway,
    SAProjectNotificationGateway,
)
from kworkflow.notifications.interfaces import (
    ChannelNotificationGateway,
    ProjectNotificationGateway,
    ProposalGeneratedNotificationQueue,
    SubscriptionActivatedNotificationQueue,
    SubscriptionRenewalNotificationQueue,
)
from kworkflow.notifications.services import (
    ProjectNotificationService,
    ProjectProposalNotificationService,
    SubscriptionNotificationService,
)
from kworkflow.preferences.gateways import (
    SAFreelancerProfileGateway,
    SAUserPriceFilterGateway,
    UserCategoryFollowGateway,
    UserStopWordsGateway,
)
from kworkflow.preferences.interfaces import (
    FreelancerProfileGateway,
    UserPriceFilterGateway,
)
from kworkflow.preferences.services import (
    UserCategoryFollowService,
    UserFreelancerProfileService,
    UserPriceFilterService,
    UserStopWordsService,
)
from kworkflow.projects.gateways import (
    ProjectCategoryGateway,
    ProjectProposalGateway,
    ProjectProposalRequestGateway,
    SAProjectGateway,
    UserGenerationUsageGateway,
)
from kworkflow.projects.generators import ProjectProposalGenerator
from kworkflow.projects.interfaces import (
    ProjectGateway,
    ProposalGenerationQueue,
)
from kworkflow.projects.services import (
    ProjectCategoryService,
    ProjectProposalGenerationService,
    ProjectProposalRequestService,
    ProjectSyncService,
)
from kworkflow.projects.usage_checker import GenerationLimitCheckerImpl
from kworkflow.subscriptions.checker import (
    SubscriptionCheckerImpl,
)
from kworkflow.subscriptions.gateways import (
    PaymentGateway,
    SubscriptionGateway,
    SubscriptionPlanGateway,
)
from kworkflow.subscriptions.interfaces import SubscriptionLimitsResetter
from kworkflow.subscriptions.limits_resetter import (
    SubscriptionLimitsResetterImpl,
)
from kworkflow.subscriptions.services import (
    PaymentVerificationService,
    SubscriptionManagementService,
    SubscriptionPaymentService,
    SubscriptionRenewalService,
)
from kworkflow.users.gateways import UserGateway, UserRoleGateway


class InfraProvider(Provider):
    @provide(scope=Scope.APP)
    def get_engine(self, config: Config) -> AsyncEngine:
        return create_async_engine(config.postgres.connection_url)

    @provide(scope=Scope.APP)
    def get_session_maker(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session

    transaction_manager = provide(TransactionManager, scope=Scope.REQUEST)

    @provide(scope=Scope.APP)
    def get_redis_pool(self, config: Config) -> ConnectionPool:
        return ConnectionPool.from_url(
            config.redis.connection_url,
            max_connections=20,  # Пул из 20 соединений
            decode_responses=True,
            retry_on_timeout=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            socket_keepalive=True,
            health_check_interval=30,
        )

    @provide(scope=Scope.APP)
    async def get_redis_client(
        self,
        pool: ConnectionPool,
    ) -> AsyncIterable[Redis]:
        client = Redis(connection_pool=pool)
        yield client
        await client.aclose(close_connection_pool=True)

    @provide(scope=Scope.APP)
    def get_kwork_client(self, config: Config) -> KworkClient:
        return KworkClient(
            login=config.kwork.login,
            password=config.kwork.password,
        )

    @provide(scope=Scope.APP)
    def get_telegram_notifier(self, bot: Bot) -> TelegramNotifier:
        return TelegramNotifier(bot=bot)

    @provide(scope=Scope.APP)
    async def get_async_openai_client(
        self,
        config: Config,
    ) -> AsyncIterable[AsyncOpenAI]:
        client = AsyncOpenAI(
            api_key=config.polza.api_key,
            base_url=config.polza.base_url,
        )
        yield client
        await client.close()

    @provide(scope=Scope.APP)
    def get_yookassa_rate_limiter(
        self,
        config: Config,
    ) -> YookassaRateLimiter:
        return YookassaRateLimiter(
            shop_id=config.yookassa.shop_id,
            redis_uri=config.redis.async_connection_url,
            limit_per_minute=100,
        )

    @provide(scope=Scope.APP)
    async def get_yookassa_client(
        self,
        config: Config,
        limiter: YookassaRateLimiter,
    ) -> AsyncIterable[YooKassaClient]:
        client = YooKassaClient(
            shop_id=config.yookassa.shop_id,
            secret_key=config.yookassa.secret_key,
            limiter=limiter,
        )
        yield client
        await client.close()

    @provide(scope=Scope.APP)
    def get_polza_rate_limiter(
        self,
        config: Config,
    ) -> PolzaRateLimiter:
        return PolzaRateLimiter(
            redis_uri=config.redis.async_connection_url,
            limit_per_minute=180,
        )


class UserProvider(Provider):
    user_gateway = provide(UserGateway, scope=Scope.REQUEST)
    user_role_gateway = provide(UserRoleGateway, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    async def get_current_user(self, id_provider: IdProvider) -> CurrentUser:
        return await id_provider.get_current_user()


class ProjectProvider(Provider):
    project_category_gateway = provide(
        ProjectCategoryGateway,
        scope=Scope.REQUEST,
    )
    project_category_service = provide(
        ProjectCategoryService,
        scope=Scope.REQUEST,
    )
    project_gateway = provide(
        SAProjectGateway,
        scope=Scope.REQUEST,
        provides=ProjectGateway,
    )
    project_sync_service = provide(
        ProjectSyncService,
        scope=Scope.REQUEST,
    )
    project_proposal_gateway = provide(
        ProjectProposalGateway,
        scope=Scope.REQUEST,
    )
    project_proposal_request_gateway = provide(
        ProjectProposalRequestGateway,
        scope=Scope.REQUEST,
    )
    user_generation_usage_gateway = provide(
        UserGenerationUsageGateway,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    async def get_project_proposal_generator(
        self,
        client: AsyncOpenAI,
        limiter: PolzaRateLimiter,
    ) -> ProjectProposalGenerator:
        return ProjectProposalGenerator(client=client, limiter=limiter)

    project_proposal_request_service = provide(
        ProjectProposalRequestService,
        scope=Scope.REQUEST,
    )
    project_proposal_generation_service = provide(
        ProjectProposalGenerationService,
        scope=Scope.REQUEST,
    )
    limit_checker = provide(
        GenerationLimitCheckerImpl,
        scope=Scope.REQUEST,
        provides=GenerationLimitChecker,
    )
    # TODO: подумать какой scope нужен для queue классов
    proposal_generation_queue = provide(
        TaskiqProposalGenerationQueue,
        scope=Scope.REQUEST,
        provides=ProposalGenerationQueue,
    )


class PreferenceProvider(Provider):
    user_category_follow_gateway = provide(
        UserCategoryFollowGateway,
        scope=Scope.REQUEST,
    )
    user_category_follow_service = provide(
        UserCategoryFollowService,
        scope=Scope.REQUEST,
    )
    freelancer_profile_gateway = provide(
        SAFreelancerProfileGateway,
        scope=Scope.REQUEST,
        provides=FreelancerProfileGateway,
    )
    user_freelancer_profile_service = provide(
        UserFreelancerProfileService,
        scope=Scope.REQUEST,
    )
    user_stop_words_gateway = provide(
        UserStopWordsGateway,
        scope=Scope.REQUEST,
    )
    user_stop_words_service = provide(
        UserStopWordsService,
        scope=Scope.REQUEST,
    )
    user_price_filter_gateway = provide(
        SAUserPriceFilterGateway,
        scope=Scope.REQUEST,
        provides=UserPriceFilterGateway,
    )
    user_price_filter_service = provide(
        UserPriceFilterService,
        scope=Scope.REQUEST,
    )


class NotificationProvider(Provider):
    project_notification_gateway = provide(
        SAProjectNotificationGateway,
        scope=Scope.REQUEST,
        provides=ProjectNotificationGateway,
    )
    channel_notification_gateway = provide(
        SAChannelNotificationGateway,
        scope=Scope.REQUEST,
        provides=ChannelNotificationGateway,
    )

    @provide(scope=Scope.REQUEST)
    async def get_project_notification_service(
        self,
        project_gateway: ProjectGateway,
        follow_gateway: UserCategoryFollowGateway,
        stop_words_gateway: UserStopWordsGateway,
        price_filter_gateway: UserPriceFilterGateway,
        project_notification_gateway: ProjectNotificationGateway,
        channel_notification_gateway: ChannelNotificationGateway,
        telegram_notifier: TelegramNotifier,
        transaction_manager: TransactionManager,
        redis: Redis,
        config: Config,
    ) -> ProjectNotificationService:
        return ProjectNotificationService(
            project_gateway=project_gateway,
            follow_gateway=follow_gateway,
            stop_words_gateway=stop_words_gateway,
            price_filter_gateway=price_filter_gateway,
            project_notification_gateway=project_notification_gateway,
            channel_notification_gateway=channel_notification_gateway,
            telegram_notifier=telegram_notifier,
            transaction_manager=transaction_manager,
            redis=redis,
            kwork_ref_id=config.kwork.ref_id,
            channel_id=config.telegram_channel_id,
        )

    project_proposal_notification_service = provide(
        ProjectProposalNotificationService,
        scope=Scope.REQUEST,
    )
    subscription_notification_service = provide(
        SubscriptionNotificationService,
        scope=Scope.REQUEST,
    )
    # TODO: подумать какой Scope нужен для Queue
    proposal_notification_queue = provide(
        TaskiqProposalGeneratedNotificationQueue,
        scope=Scope.REQUEST,
        provides=ProposalGeneratedNotificationQueue,
    )
    subscription_activated_notification_queue = provide(
        TaskiqSubscriptionActivatedNotificationQueue,
        scope=Scope.REQUEST,
        provides=SubscriptionActivatedNotificationQueue,
    )
    subscription_renewal_notification_queue = provide(
        TaskiqSubscriptionRenewalNotificationQueue,
        scope=Scope.REQUEST,
        provides=SubscriptionRenewalNotificationQueue,
    )


class SubscriptionProvider(Provider):
    subscription_plan_gateway = provide(
        SubscriptionPlanGateway,
        scope=Scope.REQUEST,
    )
    subscription_gateway = provide(
        SubscriptionGateway,
        scope=Scope.REQUEST,
    )
    payment_gateway = provide(
        PaymentGateway,
        scope=Scope.REQUEST,
    )
    subscription_payment_service = provide(
        SubscriptionPaymentService,
        scope=Scope.REQUEST,
    )
    subscription_management_service = provide(
        SubscriptionManagementService,
        scope=Scope.REQUEST,
    )
    subscription_renewal_service = provide(
        SubscriptionRenewalService,
        scope=Scope.REQUEST,
    )
    payment_verification_service = provide(
        PaymentVerificationService,
        scope=Scope.REQUEST,
    )
    subscription_checker = provide(
        SubscriptionCheckerImpl,
        scope=Scope.REQUEST,
        provides=SubscriptionChecker,
    )
    subscription_limits_resetter = provide(
        SubscriptionLimitsResetterImpl,
        scope=Scope.REQUEST,
        provides=SubscriptionLimitsResetter,
    )


class TelegramBotProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(
        self,
        event: TelegramObject,
        user_gateway: UserGateway,
        user_role_gateway: UserRoleGateway,
        sub_checker: SubscriptionChecker,
    ) -> TelegramIdProvider:
        return TelegramIdProvider(
            telegram_id=event.from_user.id,
            user_gateway=user_gateway,
            user_role_gateway=user_role_gateway,
            sub_checker=sub_checker,
        )

    telegram_auth = provide(TelegramAuth, scope=Scope.REQUEST)


class WorkerProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(self) -> WorkerIdProvider:
        return WorkerIdProvider()


class AdminPanelProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(self) -> AdminPanelIdProvider:
        return AdminPanelIdProvider()


class WebProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(self) -> WebIdProvider:
        return WebIdProvider()

    @provide(scope=Scope.APP)
    def get_templates(self, config: Config) -> Jinja2Templates:
        return Jinja2Templates(directory=config.web.templates_dir)


def create_container(
    providers: list[Provider],
    context: dict[Any, Any] | None = None,
) -> AsyncContainer:
    return make_async_container(
        InfraProvider(),
        UserProvider(),
        ProjectProvider(),
        PreferenceProvider(),
        NotificationProvider(),
        SubscriptionProvider(),
        *providers,
        context=context,
    )
