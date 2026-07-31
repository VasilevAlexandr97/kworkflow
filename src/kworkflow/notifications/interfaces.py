from abc import abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from kworkflow.notifications.models import (
    ChannelNotification,
    ProjectNotification,
)


class ProposalGeneratedNotificationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID, project_id: UUID) -> None:
        raise NotImplementedError


class SubscriptionActivatedNotificationQueue(Protocol):
    @abstractmethod
    async def enqueue(self, user_id: UUID) -> None:
        raise NotImplementedError


class SubscriptionRenewalNotificationQueue(Protocol):
    @abstractmethod
    async def enqueue_renewed(
        self,
        user_id: UUID,
        new_expires_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_retry(
        self,
        user_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_revoked(self, user_id: UUID) -> None:
        raise NotImplementedError


class ProjectNotificationGateway:
    @abstractmethod
    async def bulk_insert(
        self,
        notifications: list[ProjectNotification],
    ) -> None:
        raise NotImplementedError


class ChannelNotificationGateway:
    @abstractmethod
    async def bulk_insert(
        self,
        notifications: list[ChannelNotification],
    ) -> None:
        raise NotImplementedError
