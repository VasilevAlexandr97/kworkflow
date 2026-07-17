from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.common.dto import CurrentUser
from kworkflow.users.models import Role


class IdProvider(Protocol):
    @abstractmethod
    async def get_current_user_id(self) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_current_user_telegram_id(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_role(self) -> Role:
        raise NotImplementedError

    @abstractmethod
    async def get_current_user(self) -> CurrentUser:
        raise NotImplementedError
