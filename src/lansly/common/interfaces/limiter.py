from abc import abstractmethod
from typing import Protocol


class RateLimiter(Protocol):
    @abstractmethod
    async def acquire(self) -> None:
        raise NotImplementedError
