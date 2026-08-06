from lansly.users.consts import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)
from lansly.users.exceptions import (
    InvalidPasswordError,
    InvalidUsernameError,
    PasswordLengthError,
    UsernameLengthError,
)


def username_validator(username: str):
    if not username:
        raise InvalidUsernameError
    if (
        len(username) < USERNAME_MIN_LENGTH
        or len(username) > USERNAME_MAX_LENGTH
    ):
        raise UsernameLengthError


def password_validator(password: str):
    if not password:
        raise InvalidPasswordError
    if (
        len(password) < PASSWORD_MIN_LENGTH
        or len(password) > PASSWORD_MAX_LENGTH
    ):
        raise PasswordLengthError
