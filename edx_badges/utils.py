import logging
import json
from urllib.parse import urljoin
import requests
from django.conf import settings
from django.template.loader import render_to_string

from user_extensions.utils import get_orcid_provider_name

log = logging.getLogger(__name__)


def build_orcid_headers(user):
    access_token = ""
    orcid_providers = ['orcid', 'orcid-sandbox']
    for social_auth in user.social_auth.all():
        if social_auth.provider in orcid_providers:
            access_token = social_auth.extra_data.get('access_token')

    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.orcid+json",
    }


def create_orcid_qualification(assertion):
    def build_url():
        extended_user_profile = getattr(assertion.user, "extended_user_profile", None)
        orcid_id = extended_user_profile.orcid_id if extended_user_profile else ''

        if not orcid_id:
            raise  # pylint: disable=misplaced-bare-raise

        return urljoin(
            settings.ORCID_CONFIG.get('BASE_API_URL', {}).get(get_orcid_provider_name(assertion.user)),
            f"{orcid_id}/qualification",
        )

    context = {
        "start_date_year": assertion.created.strftime('%Y'),
        "start_date_month": assertion.created.strftime('%m'),
        "start_date_day": assertion.created.strftime('%d'),
        "url": assertion.assertion_url
    }
    json_string = render_to_string("orcid/write_qualification.json", context)
    response = requests.post(
        build_url(),
        json=json.loads(json_string),
        headers=build_orcid_headers(assertion.user),
    )
    try:
        response.raise_for_status()
        assertion.badge_status.credly_qualification_id = response.headers.get("Location", "").split('/')[-1]
        assertion.badge_status.save()
    except Exception:
        # pylint: disable=logging-fstring-interpolation
        log.error(
            "Encountered an error when creating qualification on ORCID.\n"
            f"Error text: {response.text}\nBody: {response.request.body}"
        )
        raise


def delete_orcid_qualification(assertion):
    def build_url():
        extended_user_profile = getattr(assertion.user, "extended_user_profile", None)
        orcid_id = extended_user_profile.orcid_id if extended_user_profile else ''
        qualification_id = assertion.badge_status.credly_qualification_id

        if not orcid_id or not qualification_id:
            raise  # pylint: disable=misplaced-bare-raise

        return urljoin(
            settings.ORCID_CONFIG.get('BASE_API_URL', {}).get(get_orcid_provider_name(assertion.user)),
            f"{orcid_id}/qualification/{assertion.badge_status.credly_qualification_id}",
        )

    response = requests.delete(build_url(), headers=build_orcid_headers(assertion.user))

    try:
        response.raise_for_status()
    except Exception:
        # pylint: disable=logging-fstring-interpolation
        log.error(f"Encountered an error when deleting qualification on ORCID. Error text: {response.text}")
        raise
