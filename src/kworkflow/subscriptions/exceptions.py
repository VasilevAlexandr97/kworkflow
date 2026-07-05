class SubscriptionPlanNotFoundError(Exception):
    pass


class ServiceTemporarilyUnavailableError(Exception):
    pass


class PaymentEmailRequiredError(Exception):
    pass


class PaymentEmailValidationError(Exception):
    pass
