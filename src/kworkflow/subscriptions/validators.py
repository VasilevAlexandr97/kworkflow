import re

from kworkflow.subscriptions.exceptions import PaymentEmailValidationError

PAYMENT_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
)


def payment_email_validator(email: str):
    if (
        not email
        or not isinstance(email, str)
        or not bool(PAYMENT_EMAIL_REGEX.match(email))
    ):
        raise PaymentEmailValidationError
