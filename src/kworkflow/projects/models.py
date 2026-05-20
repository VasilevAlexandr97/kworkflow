from uuid import UUID

from sqlalchemy import (
    UUID as SA_UUID,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from kworkflow.infra.database.base import Base


class ProjectCategory(Base):
    __tablename__ = "project_categories"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int]
    title: Mapped[str]
    parent_id: Mapped[UUID| None] = mapped_column(
        ForeignKey("project_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self):
        return f"ProjectCategory(id={self.id}, title={self.title})"
