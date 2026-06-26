from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.auth.exceptions import AuthenticationError
from kworkflow.users.gateways import UserGateway, UserRoleGateway
from kworkflow.users.models import Role


class IdProvider(Protocol):
    @abstractmethod
    async def get_current_user_id(self) -> UUID: ...

    @abstractmethod
    async def get_current_user_telegram_id(self) -> int: ...

    @abstractmethod
    async def get_role(self) -> Role: ...


class TelegramIdProvider(IdProvider):
    def __init__(
        self,
        telegram_id: int,
        user_gateway: UserGateway,
        user_role_gateway: UserRoleGateway,
    ):
        self.telegram_id = telegram_id
        self.user_gateway = user_gateway
        self.user_role_gateway = user_role_gateway

    async def get_current_user_telegram_id(self):
        return self.telegram_id

    async def get_current_user_id(self) -> UUID:
        user = await self.user_gateway.get_by_telegram_id(self.telegram_id)
        if user is None:
            raise AuthenticationError(
                f"User with telegram_id: {self.telegram_id} not found",
            )
        return user.id

    async def get_role(self) -> Role:
        return await self.user_role_gateway.get_user_role_by_telegram_id(
            telegram_id=self.telegram_id,
        )


class WorkerIdProvider(IdProvider):
    async def get_current_user_telegram_id(self) -> int:
        return 0

    async def get_current_user_id(self) -> UUID:
        return UUID("00000000-0000-0000-0000-000000000000")

    async def get_role(self) -> Role:
        return Role.USER
