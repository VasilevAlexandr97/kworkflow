from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from lansly.articles.interfaces import ArticleGateway
from lansly.articles.models import Article


class SAArticleGateway(ArticleGateway):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> Article | None:
        stmt = select(Article).where(Article.slug == slug)
        return await self.session.scalar(stmt)

    async def get_published_by_slug(self, slug: str) -> Article | None:
        stmt = select(Article).where(
            Article.slug == slug,
            Article.is_published.is_(True),
            Article.published_at.is_not(None),
        )
        return await self.session.scalar(stmt)

    async def get_published(self, limit: int, offset: int) -> list[Article]:
        stmt = (
            select(Article)
            .where(
                Article.is_published.is_(True),
                Article.published_at.is_not(None),
            )
            .order_by(Article.published_at.desc(), Article.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(await self.session.scalars(stmt))

    async def get_published_all(self) -> list[Article]:
        stmt = (
            select(Article)
            .where(
                Article.is_published.is_(True),
                Article.published_at.is_not(None),
            )
            .order_by(Article.published_at.desc(), Article.created_at.desc())
        )
        return list(await self.session.scalars(stmt))

    async def get_count_published(self) -> int:
        stmt = select(count(Article.id)).where(
            Article.is_published.is_(True),
            Article.published_at.is_not(None),
        )
        return (await self.session.scalar(stmt)) or 0
