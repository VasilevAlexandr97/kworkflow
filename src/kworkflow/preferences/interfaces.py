from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.preferences.models import UserFreelancerProfile


class FreelancerProfileGateway(Protocol):
    @abstractmethod
    async def add(self, profile: UserFreelancerProfile) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, user_id: UUID) -> UserFreelancerProfile | None:
        raise NotImplementedError
