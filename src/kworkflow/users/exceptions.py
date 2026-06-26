class CreateUserError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserRoleCreationError(Exception):
    pass


class UserRoleNotFoundError(Exception):
    pass
