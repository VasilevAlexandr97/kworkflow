from uuid import UUID

from sqlalchemy import and_, case, delete, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import functions

from kworkflow.preferences.dto import CategoryFollowStatusDTO
from kworkflow.preferences.models import (
    UserCategoryFollow,
    UserFreelancerProfile,
    UserStopWord,
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


class UserStopWordsGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_batch(self, words: list[UserStopWord]):
        values = [
            {
                "user_id": word.user_id,
                "word": word.word,
                "created_at": word.created_at,
            }
            for word in words
        ]
        stmt = (
            pg_insert(UserStopWord)
            .values(values)
            .on_conflict_do_nothing(index_elements=["user_id", "word"])
        )
        await self.session.execute(stmt)

    async def delete_batch(self, user_id: UUID, words: list[str]):
        stmt = delete(UserStopWord).where(
            and_(
                UserStopWord.user_id == user_id,
                UserStopWord.word.in_(words),
            ),
        )
        await self.session.execute(stmt)

    async def get_stop_words_by_user_id(self, user_id: UUID) -> list[str]:
        stmt = (
            select(UserStopWord.word)
            .where(UserStopWord.user_id == user_id)
            .order_by(UserStopWord.created_at.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [row[0] for row in rows]

    async def count_stop_words_by_user_id(self, user_id: UUID) -> int:
        stmt = select(functions.count(UserStopWord.word)).where(
            UserStopWord.user_id == user_id,
        )
        result = await self.session.scalar(stmt)
        if result is None:
            return 0
        return result

    async def get_stop_words_by_user_ids(
        self, user_ids: list[UUID],
    ) -> dict[UUID, list[str]]:
        if not user_ids:
            return {}
        stmt = select(UserStopWord.user_id, UserStopWord.word).where(
            UserStopWord.user_id.in_(user_ids)
        ).order_by(UserStopWord.created_at.asc())

        result = await self.session.execute(stmt)
        rows = result.all()
        stop_words_map: dict[UUID, list[str]] = {}
        for user_id, word in rows:
            stop_words_map.setdefault(user_id, []).append(word)
        return stop_words_map
