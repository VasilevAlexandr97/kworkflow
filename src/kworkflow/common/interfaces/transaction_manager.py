from abc import abstractmethod
from typing import Protocol


class TransactionManager(Protocol):
    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def flush(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError
