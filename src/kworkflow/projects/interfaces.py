from abc import abstractmethod
from typing import Protocol
from uuid import UUID


class ProposalGenerationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError

