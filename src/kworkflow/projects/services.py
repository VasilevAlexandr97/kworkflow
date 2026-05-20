from uuid import UUID

from kwork import KworkClient
from uuid6 import uuid7

from kworkflow.infra.database.transaction_manager import TransactionManager
from kworkflow.projects.gateway import ProjectCategoryGateway
from kworkflow.projects.models import ProjectCategory


class ProjectCategoryService:
    def __init__(
        self,
        gateway: ProjectCategoryGateway,
        kwork_client: KworkClient,
        transaction_manager: TransactionManager,
    ):
        self.gateway = gateway
        self.kwork_client = kwork_client
        self.transaction_manager = transaction_manager

    async def import_categories(self):
        categories_data = []
        categories = await self.kwork_client.get_categories()
        for category in categories:
            parent_id = uuid7()
            categories_data.extend(
                (
                    {
                        "id": parent_id,
                        "external_id": category.id,
                        "title": category.name,
                        "parent_id": None,
                    },
                    *(
                        {
                            "id": uuid7(),
                            "external_id": sub.id,
                            "title": sub.name,
                            "parent_id": parent_id,
                        }
                        for sub in category.subcategories or []
                    ),
                ),
            )
        await self.gateway.upsert(categories_data)
        await self.transaction_manager.commit()

    async def get_root_categories(self) -> list[ProjectCategory]:
        return await self.gateway.get_root_categories()

    async def get_subcategories(
        self,
        parent_id: UUID,
    ) -> list[ProjectCategory]:
        return await self.gateway.get_child_categories(parent_id)
