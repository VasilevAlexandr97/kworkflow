from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kworkflow.projects.models import Project, ProjectCategory, ProjectProposal


class ProjectCategoryGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, categories_data: list[dict]):
        stmt = pg_insert(ProjectCategory).values(categories_data)
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

    async def get_categories_by_external_ids(
        self,
        external_ids: list[int],
    ) -> list[ProjectCategory]:
        stmt = select(ProjectCategory).where(
            ProjectCategory.external_id.in_(external_ids),
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class ProjectGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert(self, projects: list[Project]):
        if not projects:
            return
        values = [
            {
                "id": project.id,
                "external_id": project.external_id,
                "title": project.title,
                "category_id": project.category_id,
                "price": project.price,
                "possible_price_limit": project.possible_price_limit,
                "description": project.description,
                "offers": project.offers,
            }
            for project in projects
        ]
        stmt = (
            pg_insert(Project)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=["external_id"],
            )
        )
        await self.session.execute(stmt)

    async def get_missing_external_ids(
        self,
        external_ids: list[int],
    ) -> set[int]:
        stmt = select(Project.external_id).where(
            Project.external_id.in_(external_ids),
        )
        existing_ids = await self.session.scalars(stmt)
        return set(external_ids) - set(existing_ids)

    async def get_projects_by_ids(
        self,
        project_ids: list[UUID],
        with_category: bool = False,
    ) -> list[Project]:
        stmt = select(Project).where(Project.id.in_(project_ids))
        if with_category:
            stmt = stmt.options(selectinload(Project.category))
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_id(self, project_id: UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id)
        return await self.session.scalar(stmt)


class ProjectProposalGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, project_proposal: ProjectProposal):
        self.session.add(project_proposal)
        await self.session.flush()

    async def get(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> ProjectProposal | None:
        stmt = select(ProjectProposal).where(
            and_(
                ProjectProposal.project_id == project_id,
                ProjectProposal.user_id == user_id,
            ),
        )
        return await self.session.scalar(stmt)
