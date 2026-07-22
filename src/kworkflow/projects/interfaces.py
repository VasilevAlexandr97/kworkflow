from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.projects.models import Project


class ProjectGateway(Protocol):
    @abstractmethod
    async def bulk_insert(self, projects: list[Project]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_missing_external_ids(
        self,
        external_ids: list[int],
    ) -> set[int]:
        raise NotImplementedError

    @abstractmethod
    async def get_projects_by_ids(
        self,
        project_ids: list[UUID],
        with_category: bool = False,
    ) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    async def get_recent_projects_by_min_price(
        self,
        min_price: int = 30000,
        limit: int = 10,
    ) -> list[Project]:
        raise NotImplementedError


class ProposalGenerationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError
