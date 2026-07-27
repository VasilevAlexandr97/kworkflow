from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from kworkflow.preferences.models import UserFreelancerProfile, UserPriceFilter


class FreelancerProfileGateway(Protocol):
    @abstractmethod
    async def add(self, profile: UserFreelancerProfile) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, user_id: UUID) -> UserFreelancerProfile | None:
        raise NotImplementedError


class UserPriceFilterGateway(Protocol):
    @abstractmethod
    async def upsert(self, price_filter: UserPriceFilter) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> UserPriceFilter | None:
        raise NotImplementedError

    @abstractmethod
    async def get_filter_by_user_ids(
        self,
        user_ids: list[UUID],
    ) -> dict[UUID, tuple[int, int]]:
        raise NotImplementedError
