from abc import abstractmethod
from typing import Protocol

from lansly.articles.models import Article


class ArticleGateway(Protocol):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Article | None:
        raise NotImplementedError

    @abstractmethod
    async def get_published_by_slug(self, slug: str) -> Article | None:
        raise NotImplementedError

    @abstractmethod
    async def get_published(self, limit: int, offset: int) -> list[Article]:
        raise NotImplementedError

    @abstractmethod
    async def get_published_all(self) -> list[Article]:
        raise NotImplementedError

    @abstractmethod
    async def get_count_published(self) -> int:
        raise NotImplementedError
