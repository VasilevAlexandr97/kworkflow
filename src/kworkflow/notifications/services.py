import asyncio
import logging

from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio.client import Redis
from redis.asyncio.lock import Lock

from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.infra.telegram.telegram_notifier import TelegramNotifier
from kworkflow.notifications.interfaces import (
    ChannelNotificationGateway,
    ProjectNotificationGateway,
)
from kworkflow.notifications.models import (
    ChannelNotification,
    ProjectNotification,
)
from kworkflow.preferences.gateways import (
    UserCategoryFollowGateway,
    UserStopWordsGateway,
)
from kworkflow.preferences.interfaces import UserPriceFilterGateway
from kworkflow.projects.exceptions import ProjectProposalNotFoundError
from kworkflow.projects.gateways import ProjectProposalGateway
from kworkflow.projects.interfaces import ProjectGateway
from kworkflow.telegram_bot.keyboards import (
    build_no_active_subscription_kbd,
    build_project_kbd,
    build_subscription_activated_kbd,
)
from kworkflow.telegram_bot.messages import project_message
from kworkflow.users.exceptions import UserNotFoundError
from kworkflow.users.gateways import UserGateway

logger = logging.getLogger(__name__)


class ProjectNotificationService:
    def __init__(
        self,
        project_gateway: ProjectGateway,
        follow_gateway: UserCategoryFollowGateway,
        stop_words_gateway: UserStopWordsGateway,
        price_filter_gateway: UserPriceFilterGateway,
        project_notification_gateway: ProjectNotificationGateway,
        channel_notification_gateway: ChannelNotificationGateway,
        telegram_notifier: TelegramNotifier,
        transaction_manager: TransactionManager,
        redis: Redis,
        kwork_ref_id: int | None = None,
    ):
        self.project_gateway = project_gateway
        self.follow_gateway = follow_gateway
        self.stop_words_gateway = stop_words_gateway
        self.price_filter_gateway = price_filter_gateway
        self.project_notification_gateway = project_notification_gateway
        self.channel_notification_gateway = channel_notification_gateway
        self.telegram_notifier = telegram_notifier
        self.transaction_manager = transaction_manager
        self.redis = redis
        self.lock = Lock(self.redis, "project_notification", timeout=600)
        self.kwork_ref_id = kwork_ref_id

    def _contains_stop_word(self, text: str, stop_words: list[str]) -> bool:
        if not stop_words:
            return False
        text_lower = text.lower()
        return any(sw.lower() in text_lower for sw in stop_words)

    async def notify_new_projects(self, project_ids: list[UUID]):
        projects = await self.project_gateway.get_projects_by_ids(
            project_ids,
            with_category=True,
        )
        logger.info("projects: %s", projects)

        project_notifications = []

        async with self.lock:
            for project in projects:
                if not project.category_id:
                    continue
                users = (
                    await self.follow_gateway.get_users_followed_to_category(
                        project.category_id,
                    )
                )
                user_ids = [user.id for user in users]
                stop_words_map = (
                    await self.stop_words_gateway.get_stop_words_by_user_ids(
                        user_ids,
                    )
                )
                price_filter_map = (
                    await self.price_filter_gateway.get_filter_by_user_ids(
                        user_ids,
                    )
                )
                project_text = f"{project.title} {project.description}"
                for user in users:
                    user_stop_words = stop_words_map.get(user.id, [])
                    if self._contains_stop_word(project_text, user_stop_words):
                        continue
                    price_filter = price_filter_map.get(user.id)
                    if price_filter is not None:
                        min_price = price_filter[0]
                        max_price = price_filter[1]
                        if (
                            min_price > project.price
                            or project.price > max_price
                        ):
                            continue
                    try:
                        await self.telegram_notifier.send_message(
                            chat_id=user.telegram_id,
                            text=project_message(
                                project,
                                ref_id=self.kwork_ref_id,
                            ),
                            keyboard=build_project_kbd(
                                project,
                                ref_id=self.kwork_ref_id,
                            ),
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
            await self.project_notification_gateway.bulk_insert(
                project_notifications,
            )
            await self.transaction_manager.commit()

    async def notify_high_value_projects_channel(self, channel_id: int):
        projects = await self.project_gateway.get_recent_projects_by_min_price(
            min_price=30000,
            limit=10,
        )
        already_sent = await self.channel_notification_gateway.already_sent(
            [p.id for p in projects],
        )
        new_projects = [p for p in projects if p.id not in already_sent]
        logger.info(f"HIGH VALUE PROJECTS: {new_projects}")
        channel_notifications = []
        for project in new_projects:
            try:
                await self.telegram_notifier.send_message(
                    chat_id=channel_id,
                    text=project_message(project, ref_id=self.kwork_ref_id),
                )
                channel_notifications.append(
                    ChannelNotification(
                        project_id=project.id,
                        sent_at=datetime.now(UTC),
                    ),
                )
            except Exception:
                logger.exception(
                    f"Failed to send message to channel: {channel_id}",
                )
        if channel_notifications:
            await self.channel_notification_gateway.bulk_insert(
                channel_notifications,
            )
            await self.transaction_manager.commit()


class ProjectProposalNotificationService:
    def __init__(
        self,
        proposal_gateway: ProjectProposalGateway,
        telegram_notifier: TelegramNotifier,
    ):
        self.proposal_gateway = proposal_gateway
        self.telegram_notifier = telegram_notifier

    async def notify_generated(self, user_id: UUID, project_id: UUID):
        logger.info(
            f"NOTIFY PROJECT PROPOSAL: user_id={user_id}, project_id: {project_id}",
        )
        proposal = await self.proposal_gateway.get_with_user(
            user_id=user_id,
            project_id=project_id,
        )
        if not proposal:
            raise ProjectProposalNotFoundError

        await self.telegram_notifier.send_message(
            chat_id=proposal.user.telegram_id,
            text=proposal.generated_text,
        )


class SubscriptionNotificationService:
    def __init__(
        self,
        user_gateway: UserGateway,
        telegram_notifier: TelegramNotifier,
    ):
        self.user_gateway = user_gateway
        self.telegram_notifier = telegram_notifier

    async def notify_activated(self, user_id: UUID):
        user = await self.user_gateway.get_by_id(user_id)
        if not user:
            raise UserNotFoundError
        await self.telegram_notifier.send_message(
            chat_id=user.telegram_id,
            text="👑 PRO подписка активирована!",
            keyboard=build_subscription_activated_kbd(),
        )

    async def notify_renewed(self, user_id: UUID, new_expires_at: datetime):
        user = await self.user_gateway.get_by_id(user_id)
        await self.telegram_notifier.send_message(
            chat_id=user.telegram_id,
            text=f"✅ PRO подписка продлена до {new_expires_at.strftime('%d.%m.%Y')}",
        )

    async def notify_retry(self, user_id: UUID):
        user = await self.user_gateway.get_by_id(user_id)
        await self.telegram_notifier.send_message(
            chat_id=user.telegram_id,
            text="⚠️ Не удалось списать оплату за подписку.",
        )

    async def notify_revoked(self, user_id: UUID):
        user = await self.user_gateway.get_by_id(user_id)
        await self.telegram_notifier.send_message(
            chat_id=user.telegram_id,
            text="❌ PRO доступ отключён за неуплату",
            keyboard=build_no_active_subscription_kbd(),
        )
