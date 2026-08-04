from datetime import datetime
from uuid import UUID

import orjson

from redis.asyncio import Redis

from kworkflow.auth.interfaces import SessionStorage
from kworkflow.auth.session import AuthSession


class RedisSessionStorage(SessionStorage):
    def __init__(self, client: Redis, key_prefix: str = "__auth_session"):
        self.client = client
        self.key_prefix = key_prefix

    def _get_key(self, session_id: str) -> str:
        return f"{self.key_prefix}_{session_id}"

    def _serialize(self, session: AuthSession) -> dict:
        return {
            "id": session.id,
            "user_id": str(session.user_id),
            "expires_at": session.expires_at.isoformat(),
        }

    def _deserialize(self, session_data: dict) -> AuthSession:
        return AuthSession(
            id=session_data["id"],
            user_id=UUID(session_data["user_id"]),
            expires_at=datetime.fromisoformat(session_data["expires_at"]),
        )

    async def add(
        self,
        session: AuthSession,
        ttl_seconds: int | None = None,
    ) -> None:
        key = self._get_key(session.id)
        value = orjson.dumps(self._serialize(session))
        await self.client.set(key, value, ex=ttl_seconds)

    async def delete(self, session_id: str) -> None:
        key = self._get_key(session_id)
        await self.client.delete(key)

    async def get(self, session_id: str) -> AuthSession | None:
        key = self._get_key(session_id)
        data = await self.client.get(key)
        if data is None:
            return None
        return self._deserialize(orjson.loads(data))
