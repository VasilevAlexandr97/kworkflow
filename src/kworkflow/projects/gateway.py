from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.projects.models import ProjectCategory


class ProjectCategoryGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, categories_data: list[dict]):
        stmt = insert(ProjectCategory).values(categories_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "title": stmt.excluded.title,
                "parent_id": stmt.excluded.parent_id,
            },
        )
        await self.session.execute(stmt)

    async def get_root_categories(self) -> list[ProjectCategory]:
        stmt = select(ProjectCategory).where(
            ProjectCategory.parent_id.is_(None),
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_child_categories(
        self,
        parent_id: UUID,
    ) -> list[ProjectCategory]:
        stmt = select(ProjectCategory).where(
            ProjectCategory.parent_id == parent_id,
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_category_by_id(
        self,
        category_id: UUID,
    ) -> ProjectCategory | None:
        stmt = select(ProjectCategory).where(ProjectCategory.id == category_id)
        return await self.session.scalar(stmt)
