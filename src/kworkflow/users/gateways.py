import logging

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kworkflow.users.exceptions import (
    CreateUserError,
    UserAlreadyExistsError,
    UserRoleCreationError,
    UserRoleNotFoundError,
)
from kworkflow.users.models import Role, User, UserRole

logger = logging.getLogger(__name__)


class UserGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, new_user: User):
        try:
            self.session.add(new_user)
            await self.session.flush()
        except IntegrityError as exc:
            if "unique constraint" in str(exc.orig).lower():
                raise UserAlreadyExistsError
            raise CreateUserError

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(stmt)

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return await self.session.scalar(stmt)


class UserRoleGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, new_role: UserRole):
        try:
            self.session.add(new_role)
            await self.session.flush()
        except IntegrityError:
            logger.exception(f"User role: {new_role} creation error")
            raise UserRoleCreationError(new_role)

    async def get_role_by_telegram_id(self, telegram_id: int) -> Role:
        stmt = (
            select(UserRole.name)
            .join_from(User, UserRole)
            .where(User.telegram_id == telegram_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        if not rows:
            raise UserRoleNotFoundError
        logger.info(f"Result: {result}")
        return Role(rows[0][0])

    async def get_role_by_user_id(self, user_id: UUID) -> Role:
        stmt = (
            select(UserRole.name)
            .join_from(User, UserRole)
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        if not rows:
            raise UserRoleNotFoundError
        logger.info(f"Result: {result}")
        return Role(rows[0][0])
