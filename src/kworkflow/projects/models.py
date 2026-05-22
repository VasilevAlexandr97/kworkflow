from uuid import UUID

from sqlalchemy import (
    UUID as SA_UUID,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kworkflow.infra.database.base import Base


class ProjectCategory(Base):
    __tablename__ = "project_categories"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int]
    title: Mapped[str]
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("project_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"ProjectCategory(id={self.id}, title={self.title})"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("project_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    price: Mapped[int]
    possible_price_limit: Mapped[int]
    title: Mapped[str]
    description: Mapped[str]
    offers: Mapped[int]

    category: Mapped[ProjectCategory] = relationship(
        back_populates="projects",
    )

    def __repr__(self):
        return f"Project(id={self.id}, title={self.title})"
