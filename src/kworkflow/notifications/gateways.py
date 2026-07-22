from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.notifications.interfaces import (
    ChannelNotificationGateway,
    ProjectNotificationGateway,
)
from kworkflow.notifications.models import (
    ChannelNotification,
    ProjectNotification,
)


class SAProjectNotificationGateway(ProjectNotificationGateway):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert(
        self,
        notifications: list[ProjectNotification],
    ) -> None:
        if not notifications:
            return
        values = [
            {
                "project_id": notification.project_id,
                "user_id": notification.user_id,
                "sent_at": notification.sent_at,
            }
            for notification in notifications
        ]
        stmt = insert(ProjectNotification).values(values)
        await self.session.execute(stmt)


class SAChannelNotificationGateway(ChannelNotificationGateway):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def already_sent(self, project_ids: list[UUID]) -> set[UUID]:
        stmt = select(ChannelNotification.project_id).where(
            ChannelNotification.project_id.in_(project_ids),
        )
        result = await self.session.scalars(stmt)
        return set(result.all())

    async def bulk_insert(
        self,
        notifications: list[ChannelNotification],
    ) -> None:
        if not notifications:
            return
        values = [
            {
                "project_id": notification.project_id,
                "sent_at": notification.sent_at,
            }
            for notification in notifications
        ]
        stmt = insert(ChannelNotification).values(values)
        await self.session.execute(stmt)
