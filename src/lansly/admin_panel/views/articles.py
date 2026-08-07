import logging

from datetime import UTC, datetime
from typing import Any
from uuid import uuid7

from dishka import AsyncContainer
from starlette.requests import Request
from starlette_admin import TinyMCEEditorField
from starlette_admin.contrib.sqla import ModelView

from lansly.articles.models import Article
from lansly.articles.service import ArticleService

logger = logging.getLogger(__name__)


class ArticleView(ModelView):
    fields = [  # noqa: RUF012
        Article.id,
        Article.title,
        Article.slug,
        Article.description,
        TinyMCEEditorField(
            "content",
            menubar=True,
            height=500,
            toolbar=(
                "undo redo | blocks | bold italic underline strikethrough | "
                "forecolor backcolor | alignleft aligncenter alignright alignjustify | "
                "bullist numlist outdent indent | blockquote | link image | "
                "table | code | removeformat"
            ),
            extra_options={
                "plugins": (
                    "advlist autolink link image lists charmap code table "
                    "preview fullscreen searchreplace wordcount"
                ),
                "block_formats": (
                    "Paragraph=p; Heading 1=h1; Heading 2=h2; Heading 3=h3; "
                    "Heading 4=h4; Heading 5=h5; Heading 6=h6"
                ),
                "link_target": "_blank",
                "branding": False,
            },
        ),
        Article.meta_title,
        Article.meta_description,
        Article.is_published,
        Article.published_at,
        Article.created_at,
        Article.updated_at,
    ]
    exclude_fields_from_create = [  # noqa: RUF012
        "slug",
        "published_at",
        "created_at",
        "updated_at",
    ]
    exclude_fields_from_edit = [  # noqa: RUF012
        "published_at",
        "updated_at",
    ]
    fields_default_sort = [(Article.created_at, True)]

    async def before_create(
        self,
        request: Request,
        data: dict[Any, Any],
        obj: Article,
    ) -> None:
        logger.debug(f"{request.state.dishka_container}")
        logger.debug(f"BEFORE CREATE DATA: {data}")
        logger.debug(f"BEFORE CREATE obj: {obj}")
        container: AsyncContainer = request.state.dishka_container
        async with container() as req_c:
            service = await req_c.get(ArticleService)
            now = datetime.now(UTC)
            obj.id = uuid7()
            obj.slug = await service.make_unique_slug(obj.title)
            if obj.is_published:
                obj.published_at = now
            obj.created_at = now
            obj.updated_at = now

    async def before_edit(
        self,
        request: Request,
        data: dict[Any, Any],
        obj: Article,
    ) -> None:
        logger.debug(f"BEFORE EDIT DATA: {data}")
        logger.debug(f"BEFORE EDIT obj: {obj}")
        now = datetime.now(UTC)
        if obj.is_published and obj.published_at is None:
            obj.published_at = now
        obj.updated_at = now
