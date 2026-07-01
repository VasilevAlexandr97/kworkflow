from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class ProposalGeneratedNotificationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError
