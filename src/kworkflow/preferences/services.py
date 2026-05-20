from uuid import UUID

from kworkflow.auth.id_provider import IdProvider
from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.preferences.dto import CategoryFollowStatusDTO
from kworkflow.preferences.gateways import UserCategoryFollowGateway
from kworkflow.projects.gateway import ProjectCategoryGateway


class UserCategoryFollowService:
    def __init__(
        self,
        category_gateway: ProjectCategoryGateway,
        follow_gateway: UserCategoryFollowGateway,
        id_provider: IdProvider,
        transaction_manager: TransactionManager,
    ):
        self.category_gateway = category_gateway
        self.follow_gateway = follow_gateway
        self.id_provider = id_provider
        self.transaction_manager = transaction_manager

    async def get_categories_with_follow_status(
        self,
    ) -> list[CategoryFollowStatusDTO]:
        user_id = await self.id_provider.get_current_user_id()
        return await self.follow_gateway.get_categories_with_follow_status(
            user_id,
        )

    async def sync_user_follows(self, new_follow_ids: list[UUID]):
        user_id = await self.id_provider.get_current_user_id()
        follow_ids = await self.follow_gateway.get_category_follow_ids(user_id)
        exsisting_ids = set(follow_ids)
        new_ids = set(new_follow_ids)

        to_delete = exsisting_ids - new_ids
        to_add = new_ids - exsisting_ids

        if to_delete:
            await self.follow_gateway.bulk_delete(user_id, list(to_delete))

        if to_add:
            follows_data = [
                {
                    "user_id": user_id,
                    "category_id": category_id,
                }
                for category_id in to_add
            ]
            await self.follow_gateway.bulk_insert(follows_data)

        await self.transaction_manager.commit()
        return await self.follow_gateway.get_user_followed_categories(user_id)
