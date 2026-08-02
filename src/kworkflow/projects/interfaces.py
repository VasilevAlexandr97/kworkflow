from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.projects.models import Project, UserGenerationUsage


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


class ProposalGenerationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError


class GenerationLimitChecker(Protocol):
    @abstractmethod
    async def can_generate(self, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_limit(self, user_id: UUID) -> int:
        raise NotImplementedError


class UserGenerationUsageGateway:
    @abstractmethod
    async def get_or_create(self, user_id: UUID) -> UserGenerationUsage:
        raise NotImplementedError
