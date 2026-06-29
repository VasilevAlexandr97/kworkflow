from collections.abc import AsyncIterable

from aiogram import Bot
from aiogram.types import TelegramObject
from dishka import Provider, Scope, provide
from openai import AsyncOpenAI
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kworkflow.auth.id_provider import (
    IdProvider,
    TelegramIdProvider,
    WorkerIdProvider,
)
from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.kwork.client import KworkClient
from kworkflow.infra.telegram.telegram_notifier import TelegramNotifier
from kworkflow.main.config import Config
from kworkflow.notifications.gateways import ProjectNotificationGateway
from kworkflow.notifications.services import ProjectNotificationService
from kworkflow.preferences.gateways import (
    UserCategoryFollowGateway,
    UserFreelancerProfileGateway,
    UserStopWordsGateway,
)
from kworkflow.preferences.services import (
    UserCategoryFollowService,
    UserFreelancerProfileService,
    UserStopWordsService,
)
from kworkflow.projects.gateway import (
    ProjectCategoryGateway,
    ProjectGateway,
    ProjectProposalGateway,
)
from kworkflow.projects.generators import ProjectProposalGenerator
from kworkflow.projects.services import (
    ProjectCategoryService,
    ProjectProposalService,
    ProjectSyncService,
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
        await client.close()

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


class UserProvider(Provider):
    user_gateway = provide(UserGateway, scope=Scope.REQUEST)
    # user_service = provide(UserService, scope=Scope.REQUEST)
    user_role_gateway = provide(UserRoleGateway, scope=Scope.REQUEST)


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
        ProjectGateway,
        scope=Scope.REQUEST,
    )
    project_sync_service = provide(
        ProjectSyncService,
        scope=Scope.REQUEST,
    )
    project_proposal_gateway = provide(
        ProjectProposalGateway,
        scope=Scope.REQUEST,
    )
    project_proposal_generator = provide(
        ProjectProposalGenerator,
        scope=Scope.REQUEST,
    )
    project_proposal_service = provide(
        ProjectProposalService,
        scope=Scope.REQUEST,
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
    user_freelancer_profile_gateway = provide(
        UserFreelancerProfileGateway,
        scope=Scope.REQUEST,
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


class NotificationProvider(Provider):
    project_notification_gateway = provide(
        ProjectNotificationGateway,
        scope=Scope.REQUEST,
    )
    project_notification_service = provide(
        ProjectNotificationService,
        scope=Scope.REQUEST,
    )


class TelegramBotProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(
        self,
        event: TelegramObject,
        user_gateway: UserGateway,
        user_role_gateway: UserRoleGateway,
    ) -> TelegramIdProvider:
        return TelegramIdProvider(
            telegram_id=event.from_user.id,
            user_gateway=user_gateway,
            user_role_gateway=user_role_gateway,
        )

    telegram_auth = provide(TelegramAuth, scope=Scope.REQUEST)


class WorkerProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(self) -> WorkerIdProvider:
        return WorkerIdProvider()
