from uuid import UUID

from kworkflow.common.subscription_checker import SubscriptionChecker
from kworkflow.subscriptions.gateways import SubscriptionGateway


class SubscriptionCheckerImpl(SubscriptionChecker):
    def __init__(self, subscription_gateway: SubscriptionGateway):
        self.subscription_gateway = subscription_gateway

    async def is_pro_subscription(self, user_id: UUID) -> bool:
        return await self.subscription_gateway.has_active(user_id)
