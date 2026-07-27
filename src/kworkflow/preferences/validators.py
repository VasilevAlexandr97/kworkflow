from kworkflow.preferences.consts import MAX_LENGTH_FREELANCER_PROFILE
from kworkflow.preferences.exceptions import (
    FreelancerProfileLengthError,
    PriceFilterRangeError,
)


def freelancer_profile_about_validator(about_text: str):
    if len(about_text) > MAX_LENGTH_FREELANCER_PROFILE:
        raise FreelancerProfileLengthError


def price_filter_range_validator(min_price: int, max_price: int):
    if min_price > max_price:
        raise PriceFilterRangeError
