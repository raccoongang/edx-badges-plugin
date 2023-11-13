import logging
from django.shortcuts import get_object_or_404, redirect
import requests

from .credly.utils import (
    get_badge_info_url,
    get_credly_auth_headers,
    update_badge_state,
)
from .models import BadgeStatus


log = logging.getLogger(__name__)


def force_state_update_view(request, **kwargs):
    pk = kwargs.get("pk")
    badge_status = get_object_or_404(BadgeStatus, id=pk)

    badge_info_response = requests.get(
        get_badge_info_url(badge_status.credly_badge_id),
        headers=get_credly_auth_headers(),
    )

    try:
        badge_info_response.raise_for_status()
    except Exception:
        log.error(  # pylint: disable=logging-fstring-interpolation
            "Encountered an error when contacting the Credly Server.\n"
            f"Response text: {badge_info_response.text}",
        )
        raise

    update_badge_state(badge_info_response.json()["data"])
    return redirect(request.META.get("HTTP_REFERER", "/"))
