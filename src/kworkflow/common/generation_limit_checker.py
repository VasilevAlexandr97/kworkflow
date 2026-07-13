from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class GenerationLimitChecker(Protocol):
    @abstractmethod
    async def can_generate(self, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_limit(self, user_id: UUID) -> int:
        raise NotImplementedError
