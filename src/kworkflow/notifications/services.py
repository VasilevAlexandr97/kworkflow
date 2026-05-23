import asyncio
import logging

from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio.client import Redis
from redis.asyncio.lock import Lock

from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.telegram.telegram_notifier import TelegramNotifier
from kworkflow.notifications.gateways import ProjectNotificationGateway
from kworkflow.notifications.models import ProjectNotification
from kworkflow.preferences.gateways import UserCategoryFollowGateway
from kworkflow.projects.gateway import ProjectGateway
from kworkflow.telegram_bot.keyboards import build_project_kbd
from kworkflow.telegram_bot.messages import project_message

logger = logging.getLogger(__name__)


class ProjectNotificationService:
    def __init__(
        self,
        project_gateway: ProjectGateway,
        follow_gateway: UserCategoryFollowGateway,
        notification_gateway: ProjectNotificationGateway,
        telegram_notifier: TelegramNotifier,
        transaction_manager: TransactionManager,
        redis: Redis,
    ):
        self.project_gateway = project_gateway
        self.follow_gateway = follow_gateway
        self.notification_gateway = notification_gateway
        self.telegram_notifier = telegram_notifier
        self.transaction_manager = transaction_manager
        self.redis = redis
        self.lock = Lock(self.redis, "project_notification", timeout=600)

    async def notify_new_projects(self, project_ids: list[UUID]):
        projects = await self.project_gateway.get_projects_by_ids(
            project_ids,
            with_category=True,
        )
        logger.info("projects: %s", projects)

        project_notifications = []

        async with self.lock:
            for project in projects:
                users = (
                    await self.follow_gateway.get_users_followed_to_category(
                        project.category_id,
                    )
                )
                for user in users:
                    try:
                        await self.telegram_notifier.send_message(
                            user.telegram_id,
                            project_message(project),
                            keyboard=build_project_kbd(project.id),
                        )
                        project_notifications.append(
                            ProjectNotification(
                                project_id=project.id,
                                user_id=user.id,
                                sent_at=datetime.now(tz=UTC),
                            ),
                        )
                    except Exception:
                        logger.exception("Failed to send message")
                    await asyncio.sleep(0.3)

        if project_notifications:
            await self.notification_gateway.bulk_insert(project_notifications)
            await self.transaction_manager.commit()
