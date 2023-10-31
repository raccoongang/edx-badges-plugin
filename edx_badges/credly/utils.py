import base64
from functools import lru_cache
from urllib.parse import urljoin

from django.conf import settings
from pydantic import BaseModel

from ..models import BadgeStatus
from .serializers import BadgeDataModel


class CredlySettings(BaseModel):
    ORGANIZATION_ID: str
    BASE_URL: str
    API_BASE_URL: str
    AUTHORIZATION_TOKEN: str


@lru_cache
def get_credly_settings():
    return CredlySettings(
        ORGANIZATION_ID=settings.CREDLY_BADGES_CONFIGURATION.get("ORGANIZATION_ID"),
        BASE_URL=settings.CREDLY_BADGES_CONFIGURATION.get("BASE_URL"),
        API_BASE_URL=settings.CREDLY_BADGES_CONFIGURATION.get("API_BASE_URL"),
        AUTHORIZATION_TOKEN=settings.CREDLY_BADGES_CONFIGURATION.get("AUTHORIZATION_TOKEN")
    )


@lru_cache
def build_authorization_token(authorization_token):
    """
    Build authorization token for credly requests.
    """
    auth_token = authorization_token.encode("ascii")
    return base64.b64encode(auth_token).decode("ascii")


def update_badge_state(raw_data):
    badge_serializer = BadgeDataModel(data=raw_data)
    badge_serializer.is_valid(raise_exception=True)

    badge_status = BadgeStatus.objects.filter(credly_badge_id=badge_serializer.data["id"]).first()
    if badge_status:
        state = badge_serializer.data["state"]
        if state in (
            BadgeStatus.PENDING,
            BadgeStatus.REVOKED,
            BadgeStatus.ACCEPTED,
            BadgeStatus.REJECTED
        ):
            badge_status.state = state
            badge_status.save()

        badge_status.assertion.data = raw_data
        badge_status.assertion.save()


def get_badge_assertion_url(badge_id):
    """
    Returns URL for badge info.
    """
    return urljoin(get_credly_settings().BASE_URL, f"badges/{badge_id}")
