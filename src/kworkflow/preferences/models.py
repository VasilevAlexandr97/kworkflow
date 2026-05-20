from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from kworkflow.infra.database.base import Base


class UserCategoryFollow(Base):
    __tablename__ = "user_category_follows"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("project_categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
