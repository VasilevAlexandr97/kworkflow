from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class SubscriptionChecker(Protocol):
    @abstractmethod
    async def is_pro_subscription(self, user_id: UUID) -> bool:
        raise NotImplementedError
