from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    UUID as SA_UUID,
    DateTime,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from lansly.infra.database.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Article=(id={self.id}, title={self.title})"
