from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.notifications.models import ProjectNotification


class ProjectNotificationGateway:
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
