import logging

from uuid import UUID

from kworkflow.auth.exceptions import AuthenticationError
from kworkflow.common.dto import CurrentUser
from kworkflow.common.interfaces.id_provider import IdProvider
from kworkflow.subscriptions.interfaces import SubscriptionChecker
from kworkflow.users.interfaces import UserGateway, UserRoleGateway
from kworkflow.users.models import Role

logger = logging.getLogger(__name__)


class TelegramIdProvider(IdProvider):
    def __init__(
        self,
        telegram_id: int,
        user_gateway: UserGateway,
        user_role_gateway: UserRoleGateway,
        sub_checker: SubscriptionChecker,
    ):
        self.telegram_id = telegram_id
        self.user_gateway = user_gateway
        self.user_role_gateway = user_role_gateway
        self.sub_checker = sub_checker
        # TODO: Закэшировать пользователя

        self.cached_user_id: UUID | None = None
        self.cached_role: Role | None = None

    async def get_current_user_telegram_id(self):
        return self.telegram_id

    async def _get_user_id(self) -> UUID:
        if self.cached_user_id is not None:
            logger.debug(f"CACHED USER ID: {self.cached_user_id}")
            return self.cached_user_id
        user_id = await self.user_gateway.get_user_id_by_telegram_id(
            self.telegram_id,
        )
        if not user_id:
            raise AuthenticationError(
                f"User with telegram_id: {self.telegram_id} not found",
            )
        logger.debug(f"USER ID: {user_id}")
        self.cached_user_id = user_id
        return user_id

    async def _get_user_role(self) -> Role:
        if self.cached_role is not None:
            logger.debug(f"CACHED USER ROLE: {self.cached_role}")
            return self.cached_role
        role = await self.user_role_gateway.get_role_by_telegram_id(
            telegram_id=self.telegram_id,
        )
        logger.debug(f"USER ROLE: {role}")
        self.cached_role = role
        return role

    async def get_current_user_id(self) -> UUID:
        # TODO: Получать сразу user_id, а не всего юзера
        return await self._get_user_id()

    async def get_role(self) -> Role:
        return await self._get_user_role()

    async def get_current_user(self) -> CurrentUser:
        user_id = await self._get_user_id()
        is_pro = await self.sub_checker.is_pro_subscription(user_id)
        role = await self._get_user_role()
        return CurrentUser(
            id=user_id,
            is_pro=is_pro,
            is_admin=role == Role.ADMIN,
        )


class WorkerIdProvider(IdProvider):
    async def get_current_user_telegram_id(self) -> int:
        return 0

    async def get_current_user_id(self) -> UUID:
        return UUID("00000000-0000-0000-0000-000000000000")

    async def get_role(self) -> Role:
        return Role.USER

    async def get_current_user(self) -> CurrentUser:
        raise NotImplementedError


class AdminPanelIdProvider(IdProvider):
    async def get_current_user_telegram_id(self) -> int:
        return 0

    async def get_current_user_id(self) -> UUID:
        return UUID("00000000-0000-0000-0000-000000000000")

    async def get_role(self) -> Role:
        return Role.USER

    async def get_current_user(self) -> CurrentUser:
        raise NotImplementedError


class WebIdProvider(IdProvider):
    async def get_current_user_telegram_id(self) -> int:
        return 0

    async def get_current_user_id(self) -> UUID:
        return UUID("00000000-0000-0000-0000-000000000000")

    async def get_role(self) -> Role:
        return Role.USER

    async def get_current_user(self) -> CurrentUser:
        raise NotImplementedError
