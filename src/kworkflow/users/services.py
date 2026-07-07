from kworkflow.auth.id_provider import IdProvider
from kworkflow.subscriptions.gateways import SubscriptionGateway
from kworkflow.users.dto import CurrentUser
from kworkflow.users.gateways import UserGateway


class UserService:
    def __init__(
        self,
        user_gateway: UserGateway,
        sub_gateway: SubscriptionGateway,
        id_provider: IdProvider,
    ):
        self.user_gateway = user_gateway
        self.sub_gateway = sub_gateway
        self.id_provider = id_provider

    async def get_current_user(self) -> CurrentUser:
        user_id = await self.id_provider.get_current_user_id()
        is_pro = await self.sub_gateway.has_active(user_id)
        return CurrentUser(id=user_id, is_pro=is_pro)
