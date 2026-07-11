from uuid import UUID

from kworkflow.preferences.consts import (
    MAX_FREE_CATEGORIES,
    MAX_FREE_STOP_WORDS,
)
from kworkflow.preferences.gateways import (
    UserCategoryFollowGateway,
    UserStopWordsGateway,
)
from kworkflow.subscriptions.interfaces import SubscriptionLimitsResetter


class SubscriptionLimitsResetterImpl(SubscriptionLimitsResetter):
    def __init__(
        self,
        follows_gateway: UserCategoryFollowGateway,
        stop_words_gateway: UserStopWordsGateway,
    ):
        self.follows_gateway = follows_gateway
        self.stop_words_gateway = stop_words_gateway

    async def reset_limits(self, user_id: UUID) -> None:
        await self.follows_gateway.deactivate_excess_follows(
            user_id=user_id,
            keep_count=MAX_FREE_CATEGORIES,
        )
        await self.stop_words_gateway.delete_excess(
            user_id=user_id,
            keep_count=MAX_FREE_STOP_WORDS,
        )
