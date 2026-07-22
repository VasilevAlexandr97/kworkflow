from kworkflow.preferences.consts import MAX_LENGTH_FREELANCER_PROFILE
from kworkflow.preferences.exceptions import FreelancerProfileLengthError


def freelancer_profile_about_validator(about_text: str):
    if len(about_text) > MAX_LENGTH_FREELANCER_PROFILE:
        raise FreelancerProfileLengthError
