from uuid import UUID

from lansly.users.exceptions import CreateUserError, UserAlreadyExistsError
from lansly.users.models import Role, User, UserRole


class FakeUserGateway:
    def __init__(
        self,
        users: list[User] | None = None,
        force_usernames: set[str] | None = None,
        create_error_usernames: set[str] | None = None,
    ):
        self.users: list[User] = users or []
        self.force_usernames = force_usernames or set()
        self.create_error_usernames = create_error_usernames or set()
        self.added_users: list[User] = []

    async def add(self, new_user: User) -> None:
        if new_user.username in self.force_usernames or any(
            u.username == new_user.username for u in self.users
        ):
            raise UserAlreadyExistsError
        if new_user.username in self.create_error_usernames:
            raise CreateUserError
        self.users.append(new_user)
        self.added_users.append(new_user)

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self.users if u.username == username), None)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return next(
            (u for u in self.users if u.telegram_id == telegram_id),
            None,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((u for u in self.users if u.id == user_id), None)

    async def get_user_id_by_telegram_id(
        self,
        telegram_id: int,
    ) -> UUID | None:
        user = await self.get_by_telegram_id(telegram_id)
        return user.id if user else None


class FakeUserRoleGateway:
    def __init__(self, roles: list[UserRole] | None = None):
        self.roles = roles or []
        self.added_roles: list[UserRole] = []

    async def add(self, new_role: UserRole) -> None:
        self.roles.append(new_role)
        self.added_roles.append(new_role)

    async def get_role_by_telegram_id(self, telegram_id: int) -> Role:
        raise NotImplementedError

    async def get_role_by_user_id(self, user_id: UUID) -> Role:
        raise NotImplementedError
