from uuid import UUID

from kworkflow.common.interfaces.generation_limit_checker import (
    GenerationLimitChecker,
)
from kworkflow.common.interfaces.subscription_checker import (
    SubscriptionChecker,
)
from kworkflow.projects.consts import MAX_FREE_GENERATIONS, MAX_PRO_GENERATIONS
from kworkflow.projects.gateways import UserGenerationUsageGateway
from kworkflow.users.gateways import UserRoleGateway
from kworkflow.users.models import Role


class GenerationLimitCheckerImpl(GenerationLimitChecker):
    def __init__(
        self,
        usage_gateway: UserGenerationUsageGateway,
        user_role_gateway: UserRoleGateway,
        subscription_checker: SubscriptionChecker,
    ):
        self.usage_gateway = usage_gateway
        self.user_role_gateway = user_role_gateway
        self.subscription_checker = subscription_checker

    async def can_generate(self, user_id: UUID) -> bool:
        usage = await self.usage_gateway.get_or_create(user_id)
        role = await self.user_role_gateway.get_role_by_user_id(user_id)
        if role == Role.ADMIN:
            return True
        is_pro = await self.subscription_checker.is_pro_subscription(user_id)
        if is_pro:
            return usage.pro_generations < MAX_PRO_GENERATIONS
        return usage.free_generations < MAX_FREE_GENERATIONS

    async def get_limit(self, user_id: UUID) -> int:
        is_pro_user = await self.subscription_checker.is_pro_user(
            user_id=user_id,
        )
        return MAX_FREE_GENERATIONS if not is_pro_user else MAX_PRO_GENERATIONS
