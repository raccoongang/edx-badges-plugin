import base64
import logging
import pytz
import os

import requests
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from lms.djangoapps.badges.backends.base import BadgeBackend
from lms.djangoapps.badges.models import BadgeAssertion
from requests.packages.urllib3.exceptions import HTTPError  # lint-amnesty, pylint: disable=import-error
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.badges.models import BadgeClass, CourseEventBadgesConfiguration
from rest_framework.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import ugettext as _

from credly_integration.models import CredlyCourseData

log = logging.getLogger(__name__)


class CredlyBackend(BadgeBackend):
    """
    Backend for Credly Service. https://info.credly.com/
    """

    def __init__(self):
        super().__init__()
        if None in (
            settings.FEATURES["CREDLY"].get("ORGANIZATION_ID"),
            settings.FEATURES["CREDLY"].get("BASE_URL"),
            settings.FEATURES["CREDLY"].get("API_BASE_URL"),
            settings.FEATURES["CREDLY"].get("AUTHORIZATION_TOKEN"),
        ):
            error_msg = (
                "One or more of the required settings are not defined. "
                "Required settings: ORGANIZATION_ID, BASE_URL"
                "AUTHORIZATION_TOKEN, API_BASE_URL"
            )
            log.error(error_msg)
            raise ImproperlyConfigured(error_msg)

    @property
    def _base_api_url(self):
        """
        Base URL for API requests.
        """
        api_base_url = settings.FEATURES['CREDLY'].get('API_BASE_URL')
        organization_id = settings.FEATURES['CREDLY'].get('ORGANIZATION_ID')

        return f"{api_base_url}/organizations/{organization_id}"

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
        base_url = settings.FEATURES['CREDLY'].get('BASE_URL')

        return f"{base_url}/badges/{badge_id}"

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
        authorization_token = settings.FEATURES["CREDLY"].get("AUTHORIZATION_TOKEN")
        auth_token = CredlyBackend._build_authorization_token(authorization_token)
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
        try:
            assertion.data = data
            assertion.image_url = assertion.data["image"]["url"]
            assertion.assertion_url = self._get_badge_url(assertion.data["id"])
            assertion.backend = "CredlyBackend"
            assertion.save()
            return assertion

        except Exception as exc:  # pylint: disable=broad-except
            log.error(
                'Error saving BadgeAssertion for user: "{0}" '
                "Encountered exception: {1}".format(user.email, exc)
            )

    def award(self, badge_class, user, evidence_url=None):
        data = self._get_data_for_assertion(badge_class, user)
        response = requests.post(self._assertion_url, headers=self._get_headers(), json=data, timeout=10)

        self._log_if_raised(response, data)

        assertion = self._create_badge_assertion(user, badge_class, response.json()["data"])
        return assertion

    @staticmethod
    def create_badge_class(badge_id, course_id):
        if not badge_id:
            return

        if None in (
            settings.FEATURES["CREDLY"].get("API_BASE_URL"),
            settings.FEATURES["CREDLY"].get("ORGANIZATION_ID"),
            settings.FEATURES["CREDLY"].get("AUTHORIZATION_TOKEN")
        ):
            response_message = [
                {
                    'message': _('One or more of the required credly settings are not defined.'),
                    'model': {'display_name': _('Credly Badge Template ID')}
                }
            ]
            raise ValidationError(response_message)

        CredlyBackend._check_badge_template_id(badge_id)

    @staticmethod
    def _check_badge_template_id(template_id):
        api_base_url = settings.FEATURES["CREDLY"].get("API_BASE_URL")
        organization_id = settings.FEATURES["CREDLY"].get("ORGANIZATION_ID")
        authorization_token = settings.FEATURES["CREDLY"].get("AUTHORIZATION_TOKEN")

        url = f"{api_base_url}/organizations/{organization_id}/badge_templates/{template_id}"
        token = CredlyBackend._build_authorization_token(authorization_token)
        response = requests.get(url, headers={"Authorization": f"Basic {token}"}, timeout=10)
        if response.status_code == 200:
            data = response.json()["data"]
            BadgeClass.objects.update_or_create(
                slug=template_id,
                defaults={
                    "badgr_server_slug": template_id,
                    "issuing_component": "openedx__course",
                    "display_name": data["name"],
                    "description": data["description"],
                    "image": CredlyBackend._get_image(data["image_url"]),
                }
            )
        else:
            response_message = [
                {
                    'message': _(f'Encountered an error when contacting the Credly Server.\nResponse text: {response.text}'),
                    'model': {'display_name': _('Credly Badge Template ID')}
                }
            ]
            raise ValidationError(response_message)

    @staticmethod
    def _get_image(url):
        response = requests.get(url)
        if response.status_code == 200:
            return SimpleUploadedFile(os.path.basename(url), response.content)
        else:
            response_message = [
                {
                    'message': _('Encountered an error when downloading image from the Credly Server.\nResponse text: {response.text}'),
                    'model': {'display_name': _('Credly Badge Template ID')}
                }
            ]
            raise ValidationError(response_message)

    @staticmethod
    def update_badge_configuration():
        badge_conf = CourseEventBadgesConfiguration.objects.last()
        if not badge_conf:
            badge_conf = CourseEventBadgesConfiguration.objects.create()
        badge_conf.enabled = True
        badge_conf.course_groups = CredlyBackend._collect_course_groups()
        badge_conf.save()

    @staticmethod
    def _collect_course_groups():
        course_groups = ""
        badge_classses = BadgeClass.objects.all()
        for badge_class in badge_classses:
            for credly_course_data in CredlyCourseData.objects.filter(badge_id=badge_class.slug):
                course_groups += f"{badge_class.slug},{credly_course_data.course.id}\n"

        sixth_badge_template_id = settings.FEATURES["CREDLY"]["6TH_BADGE"].get("BADGE_TEMPLATE_ID")
        sixth_badge_courses = settings.FEATURES["CREDLY"]["6TH_BADGE"].get("COURSE_IDS")
        if sixth_badge_template_id and sixth_badge_courses:
            CredlyBackend._check_badge_template_id(sixth_badge_template_id)
            course_groups += f"{sixth_badge_template_id},{','.join(sixth_badge_courses)}\n"
        return course_groups
