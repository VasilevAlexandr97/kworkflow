from kworkflow.preferences.consts import MAX_LENGTH_STOP_WORD
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, func, UUID as SA_UUID, String
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class UserFreelancerProfile(Base):
    __tablename__ = "user_freelancer_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    about: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class UserStopWord(Base):
    __tablename__ = "user_stop_words"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    word: Mapped[str] = mapped_column(
        String(MAX_LENGTH_STOP_WORD),
        nullable=False,
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
