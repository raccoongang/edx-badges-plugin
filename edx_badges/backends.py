import base64
import logging
from datetime import datetime

import pytz
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from lms.djangoapps.badges.backends.base import BadgeBackend
from lms.djangoapps.badges.models import BadgeAssertion
from pydantic import BaseModel, ValidationError
from requests.packages.urllib3.exceptions import HTTPError

log = logging.getLogger(__name__)


class CredlySettings(BaseModel):
    ORGANIZATION_ID: str
    BASE_URL: str
    API_BASE_URL: str
    AUTHORIZATION_TOKEN: str


class CredlyBackend(BadgeBackend):
    """
    Backend for Credly Service. https://info.credly.com/
    """

    def __init__(self):
        super().__init__()
        try:
            self.credly_settings = CredlySettings(
                ORGANIZATION_ID=settings.CREDLY_BADGES_CONFIGURATION["ORGANIZATION_ID"],
                BASE_URL=settings.CREDLY_BADGES_CONFIGURATION["BASE_URL"],
                API_BASE_URL=settings.CREDLY_BADGES_CONFIGURATION["API_BASE_URL"],
                AUTHORIZATION_TOKEN=settings.CREDLY_BADGES_CONFIGURATION["AUTHORIZATION_TOKEN"]
            )
        except ValidationError:
            error_msg = (
                "One or more of the required settings are not defined. "
                "Required settings: ORGANIZATION_ID, BASE_URL, AUTHORIZATION_TOKEN, API_BASE_URL"
            )
            log.error(error_msg)
            raise ImproperlyConfigured(error_msg)  # pylint: disable=raise-missing-from

    @property
    def _base_api_url(self):
        """
        Base URL for API requests.
        """
        return f"{self.credly_settings.API_BASE_URL}/organizations/{self.credly_settings.ORGANIZATION_ID}"

    @property
    def _assertion_url(self):
        """
        URL for generating a new assertion.
        """
        return f"{self._base_api_url}/badges"

    def _get_badge_url(self, badge_id):
        """
        URL for badge info.
        """
        return f"{self.credly_settings.BASE_URL}/badges/{badge_id}"

    def _get_data_for_assertion(self, badge_class, user):
        """
        Generates data for request.
        """
        extended_user_profile = getattr(user, "extended_user_profile", None)

        return {
            "recipient_email": user.email,
            "badge_template_id": badge_class.slug,
            "issued_at": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S %z"),
            "issued_to_first_name": user.first_name,
            "issued_to_last_name": user.last_name,
            "issued_to_middle_name": getattr(extended_user_profile, "middle_name", None),
            "expires_at": None,
            "issuer_earner_id": getattr(extended_user_profile, "orcid_id", None),
            "locale": "en",
            "suppress_badge_notification_email": False,
        }

    @staticmethod
    def _build_authorization_token(authorization_token):
        """
        Build authorization token.
        """
        auth_token = authorization_token.encode("ascii")
        return base64.b64encode(auth_token).decode("ascii")

    def _get_headers(self):
        """
        Headers to send along with the request-- used for authentication.
        """
        auth_token = CredlyBackend._build_authorization_token(self.credly_settings.AUTHORIZATION_TOKEN)
        return {"Authorization": f"Basic {auth_token}"}

    def _log_if_raised(self, response, data):
        """
        Log server response if there was an error.
        """
        try:
            response.raise_for_status()
        except HTTPError:
            log.error(
                "Encountered an error when contacting the Credly Server. Request sent to %r with headers %r.\n"
                "and data values %r\n"
                "Response status was %s.\n%s\nResponse text: %s",
                response.request.url,
                response.request.headers,
                data,
                response.status_code,
                response.content,
                response.text,
            )
            raise

    def _create_badge_assertion(self, user, badge_class, data):
        """
        Create badge assertion.
        """
        assertion, __ = BadgeAssertion.objects.get_or_create(user=user, badge_class=badge_class)
        assertion.data = data
        assertion.image_url = assertion.data["image"]["url"]
        assertion.assertion_url = self._get_badge_url(assertion.data["id"])
        assertion.backend = "CredlyBackend"
        assertion.save()
        return assertion

    def award(self, badge_class, user, evidence_url=None):
        data = self._get_data_for_assertion(badge_class, user)
        response = requests.post(self._assertion_url, headers=self._get_headers(), json=data, timeout=10)

        self._log_if_raised(response, data)

        assertion = self._create_badge_assertion(user, badge_class, response.json()["data"])
        return assertion
