from slugify import slugify

from lansly.articles.exceptions import ArticleNotFoundError
from lansly.articles.interfaces import ArticleGateway
from lansly.articles.models import Article
from lansly.common.pagination import PaginationParams, PaginationResponse


class ArticleService:
    def __init__(self, gateway: ArticleGateway):
        self.gateway = gateway

    async def get_article(self, slug: str) -> Article:
        article = await self.gateway.get_published_by_slug(slug)
        if article is None:
            raise ArticleNotFoundError(
                f"Article with slug={slug} not found error",
            )
        return article

    async def get_articles(
        self,
        pagination: PaginationParams,
    ) -> PaginationResponse[Article]:
        total = await self.gateway.get_count_published()
        page = pagination.page
        per_page = pagination.per_page
        if total > 0:
            total_pages = (total + per_page - 1) // per_page
            page = min(page, total_pages)
        offset = (page - 1) * per_page
        articles = await self.gateway.get_published(
            limit=pagination.per_page,
            offset=offset,
        )
        return PaginationResponse(
            items=articles,
            total=total,
            page=page,
            per_page=per_page,
        )

    async def make_unique_slug(self, title: str) -> str:
        base = slugify(title) or "article"
        candidate = base
        suffix = 2
        while await self.gateway.get_by_slug(candidate) is not None:
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate
