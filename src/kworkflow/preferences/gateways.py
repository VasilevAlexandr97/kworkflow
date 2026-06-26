from uuid import UUID

from sqlalchemy import and_, case, delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.preferences.dto import CategoryFollowStatusDTO
from kworkflow.preferences.models import (
    UserCategoryFollow,
    UserFreelancerProfile,
)
from kworkflow.projects.models import ProjectCategory
from kworkflow.users.models import User


class UserCategoryFollowGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_delete(self, user_id: UUID, category_ids: list[UUID]):
        stmt = delete(UserCategoryFollow).where(
            and_(
                UserCategoryFollow.user_id == user_id,
                UserCategoryFollow.category_id.in_(category_ids),
            ),
        )
        await self.session.execute(stmt)

    async def delete_all(self, user_id: UUID):
        stmt = delete(UserCategoryFollow).where(
            UserCategoryFollow.user_id == user_id,
        )
        await self.session.execute(stmt)

    async def bulk_insert(self, follows_data: list[dict]):
        stmt = insert(UserCategoryFollow).values(follows_data)
        await self.session.execute(stmt)

    async def get_category_follow_ids(self, user_id: UUID) -> list[UUID]:
        stmt = select(UserCategoryFollow.category_id).where(
            UserCategoryFollow.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_followed_categories(
        self,
        user_id: UUID,
    ) -> list[ProjectCategory]:
        stmt = (
            select(ProjectCategory)
            .join(
                UserCategoryFollow,
                ProjectCategory.id == UserCategoryFollow.category_id,
            )
            .where(UserCategoryFollow.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_categories_with_follow_status(
        self,
        user_id: UUID,
    ) -> list[CategoryFollowStatusDTO]:
        stmt = (
            select(
                ProjectCategory,
                case(
                    (UserCategoryFollow.user_id.is_not(None), True),
                    else_=False,
                ).label("is_followed"),
            )
            .outerjoin(
                UserCategoryFollow,
                and_(
                    ProjectCategory.id == UserCategoryFollow.category_id,
                    UserCategoryFollow.user_id == user_id,
                ),
            )
            .order_by(ProjectCategory.id)
        )
        result = await self.session.execute(stmt)
        return [
            CategoryFollowStatusDTO(
                category=row.ProjectCategory,
                is_followed=row.is_followed,
            )
            for row in result
        ]

    async def get_users_followed_to_category(
        self,
        category_id: UUID,
    ) -> list[User]:
        stmt = (
            select(User)
            .join(
                UserCategoryFollow,
                and_(UserCategoryFollow.user_id == User.id),
            )
            .where(UserCategoryFollow.category_id == category_id)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())


class UserFreelancerProfileGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, profile: UserFreelancerProfile):
        self.session.add(profile)
        await self.session.flush()

    async def get(self, user_id: UUID) -> UserFreelancerProfile | None:
        stmt = select(UserFreelancerProfile).where(
            UserFreelancerProfile.user_id == user_id,
        )
        return await self.session.scalar(stmt)
