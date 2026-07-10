from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class SubscriptionLimitsResetter(Protocol):
    @abstractmethod
    async def reset_limits(self, user_id: UUID) -> None:
        raise NotImplementedError
