import logging

from uuid import UUID

from kworkflow.auth.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
)
from kworkflow.auth.interfaces import IdProvider, SessionManager
from kworkflow.common.interfaces.password_hasher import PasswordHasher
from kworkflow.users.exceptions import (
    UserNotFoundByUsernameError,
    UserRoleNotFoundError,
)
from kworkflow.users.interfaces import UserGateway, UserRoleGateway
from kworkflow.users.models import Role
from kworkflow.users.validators import password_validator, username_validator

logger = logging.getLogger(__name__)


class LogIn:
    def __init__(
        self,
        user_gateway: UserGateway,
        user_role_gateway: UserRoleGateway,
        session_manager: SessionManager,
        id_provider: IdProvider,
        password_hasher: PasswordHasher,
    ):
        self.user_gateway = user_gateway
        self.user_role_gateway = user_role_gateway
        self.session_manager = session_manager
        self.id_provider = id_provider
        self.password_hasher = password_hasher

    async def authenticate(
        self,
        username: str,
        password: str,
        required_role: Role | None = None,
    ) -> UUID:
        try:
            await self.id_provider.get_current_user_id()
            raise AlreadyAuthenticatedError
        except AuthenticationError:
            pass
        username_validator(username)
        password_validator(password)
        user = await self.user_gateway.get_by_username(username)
        if user is None:
            raise UserNotFoundByUsernameError(
                f"User with username={username} not found",
            )
        if user.password_hash is None or not self.password_hasher.verify(
            password,
            user.password_hash,
        ):
            raise AuthenticationError("Invalid password")
        try:
            user_role = await self.user_role_gateway.get_role_by_user_id(
                user.id,
            )
        except UserRoleNotFoundError:
            logger.info(f"User Role not found for {user.id} user")
            raise AuthenticationError("User Role not found")

        if required_role is not None and required_role != user_role:
            raise AuthenticationError("Invalid role")
        await self.session_manager.init_session(user.id)
        logger.info(
            f"Log in: done. User, ID:{user.id}, username: {user.username}",
        )
        return user.id
