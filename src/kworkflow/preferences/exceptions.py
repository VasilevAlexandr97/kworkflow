class UserCategoryFollowAlreadyExistsError(Exception):
    pass


class UserCategoryFollowLimitExceededError(Exception):
    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(f"Category follow limit exceeded: {limit}")


class UserCategoryFollowCreationError(Exception):
    pass


class UserFreelancerProfileNotFoundError(Exception):
    pass


class FreelancerProfileLengthError(Exception):
    pass
