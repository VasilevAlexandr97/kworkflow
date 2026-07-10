from uuid import UUID

from kworkflow.preferences.gateways import UserCategoryFollowGateway
from kworkflow.projects.consts import MAX_FREE_CATEGORIES
from kworkflow.subscriptions.interfaces import SubscriptionLimitsResetter


class SubscriptionLimitsResetterImpl(SubscriptionLimitsResetter):
    def __init__(self, follows_gateway: UserCategoryFollowGateway):
        self.follows_gateway = follows_gateway

    async def reset_limits(self, user_id: UUID) -> None:
        await self.follows_gateway.deactivate_excess_follows(
            user_id=user_id,
            keep_count=MAX_FREE_CATEGORIES,
        )
