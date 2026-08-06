from uuid import UUID

from lansly.subscriptions.gateways import SubscriptionGateway
from lansly.subscriptions.interfaces import SubscriptionChecker
from lansly.users.interfaces import UserRoleGateway
from lansly.users.models import Role


class SubscriptionCheckerImpl(SubscriptionChecker):
    def __init__(
        self,
        subscription_gateway: SubscriptionGateway,
        user_role_gateway: UserRoleGateway,
    ):
        self.subscription_gateway = subscription_gateway
        self.user_role_gateway = user_role_gateway

    async def is_pro_subscription(self, user_id: UUID) -> bool:
        return await self.subscription_gateway.has_active(user_id)

    async def is_pro_user(self, user_id: UUID) -> bool:
        role = await self.user_role_gateway.get_role_by_user_id(user_id)
        return await self.is_pro_subscription(user_id) or role == Role.ADMIN
