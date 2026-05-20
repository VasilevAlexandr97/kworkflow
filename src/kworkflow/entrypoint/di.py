from kworkflow.preferences.services import UserCategoryFollowService
from kworkflow.preferences.gateways import UserCategoryFollowGateway
from collections.abc import AsyncIterable

from aiogram.types import TelegramObject
from dishka import Provider, Scope, provide
from kwork import KworkClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kworkflow.auth.id_provider import IdProvider, TelegramIdProvider
from kworkflow.auth.telegram_auth import TelegramAuth
from kworkflow.entrypoint.config import Config
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.projects.gateway import ProjectCategoryGateway
from kworkflow.projects.services import ProjectCategoryService
from kworkflow.users.gateways import UserGateway


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
    def get_kwork_client(self, config: Config) -> KworkClient:
        return KworkClient(
            login=config.kwork.login,
            password=config.kwork.password,
        )


class UserProvider(Provider):
    user_gateway = provide(UserGateway, scope=Scope.REQUEST)
    # user_service = provide(UserService, scope=Scope.REQUEST)


class ProjectProvider(Provider):
    project_category_gateway = provide(
        ProjectCategoryGateway,
        scope=Scope.REQUEST,
    )
    project_category_service = provide(
        ProjectCategoryService,
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


class TelegramBotProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=IdProvider)
    def get_id_provider(
        self,
        event: TelegramObject,
        gateway: UserGateway,
    ) -> TelegramIdProvider:
        return TelegramIdProvider(
            telegram_id=event.from_user.id,
            gateway=gateway,
        )

    telegram_auth = provide(TelegramAuth, scope=Scope.REQUEST)
