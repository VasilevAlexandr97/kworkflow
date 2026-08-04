import logging
import secrets

from datetime import UTC, datetime, timedelta
from uuid import UUID

from kworkflow.auth.interfaces import SessionStorage, SessionTransport
from kworkflow.auth.session import AuthSession

logger = logging.getLogger(__name__)


class SessionManagerImpl:
    def __init__(
        self,
        session_storage: SessionStorage,
        session_transport: SessionTransport,
        ttl_seconds: int = 3600,
    ):
        self.session_storage = session_storage
        self.session_transport = session_transport
        self.ttl_seconds = ttl_seconds

        self._cached_session: AuthSession | None = None

    def _generate_id(self):
        return secrets.token_urlsafe(32)

    def _is_valid(self, session: AuthSession) -> bool:
        now = datetime.now(UTC)
        return session.expires_at >= now

    async def _extend_session(self, session: AuthSession) -> None:
        now = datetime.now(UTC)
        if now >= session.expires_at - timedelta(
            seconds=self.ttl_seconds // 2,
        ):
            session.expires_at = now + timedelta(seconds=self.ttl_seconds)
            await self.session_storage.add(session, self.ttl_seconds)
        self.session_transport.delivery(session.id)
        self._cached_session = session

    async def _invalidate_session(self, session_id: str) -> None:
        await self.session_storage.delete(session_id)
        self.session_transport.clear()
        self._cached_session = None

    async def init_session(self, user_id: UUID) -> AuthSession:
        now = datetime.now(UTC)
        session_id = self._generate_id()
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        session = AuthSession(
            id=session_id,
            user_id=user_id,
            expires_at=expires_at,
        )
        await self.session_storage.add(session, self.ttl_seconds)
        self.session_transport.delivery(session_id)
        self._cached_session = session
        return session

    async def clear_session(self) -> None:
        session = await self.get_session()
        if session is not None:
            await self._invalidate_session(session.id)

    async def get_session(self) -> AuthSession | None:
        if self._cached_session is not None:
            session = self._cached_session
            logger.debug("Session was retrieved from the cache")
        else:
            session_id = self.session_transport.extract_id()
            if session_id is None:
                return None
            session = await self.session_storage.get(session_id)

        if session is None:
            return None
        if not self._is_valid(session):
            await self._invalidate_session(session.id)
            return None
        await self._extend_session(session)
        return session

