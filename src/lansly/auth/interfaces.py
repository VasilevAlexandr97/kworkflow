from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from lansly.auth.session import AuthSession
from lansly.common.dto import CurrentUser
from lansly.users.models import Role


class IdProvider(Protocol):
    @abstractmethod
    async def get_current_user_id(self) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_current_user_telegram_id(self) -> int | None:
        raise NotImplementedError

    @abstractmethod
    async def get_role(self) -> Role:
        raise NotImplementedError

    @abstractmethod
    async def get_current_user(self) -> CurrentUser:
        raise NotImplementedError


class SessionStorage(Protocol):
    @abstractmethod
    async def add(
        self,
        session: AuthSession,
        ttl_seconds: int | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, session_id: str) -> AuthSession | None:
        raise NotImplementedError


class SessionTransport(Protocol):
    @abstractmethod
    def extract_id(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delivery(self, session_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class SessionManager(Protocol):
    @abstractmethod
    async def init_session(self, user_id: UUID) -> AuthSession:
        raise NotImplementedError

    @abstractmethod
    async def clear_session(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self) -> AuthSession | None:
        raise NotImplementedError
