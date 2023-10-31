"""
Edx badges Credly API v1 views.
"""
import logging
from urllib.parse import urljoin

import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from requests.packages.urllib3.exceptions import HTTPError

from .serializers import BadgeStateChangedSerializer
from ...utils import build_authorization_token, get_credly_settings, update_badge_state


log = logging.getLogger(__name__)


class CredlyWebhook(APIView):
    """
    API takes credly webhook request and handle update state.

    POST: /edx_badges/api/credly/v1/webhook
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        request_data_serializer = BadgeStateChangedSerializer(data=request.data)
        request_data_serializer.is_valid(raise_exception=True)

        event_info_response = requests.get(
            self._build_event_info_url(request_data_serializer.data["id"]),
            headers=self._get_headers()
        )

        try:
            event_info_response.raise_for_status()
        except HTTPError:
            log.error(  # pylint: disable=logging-fstring-interpolation
                "Encountered an error when contacting the Credly Server.\n"
                f"Request sent to {self._build_event_info_url(request_data_serializer.data['id'])}.\n"
                f"Response status was {event_info_response.status_code}.\n"
                f"Response text: {event_info_response.text}",
            )
            raise

        update_badge_state(event_info_response.json()["data"]["badge"])

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _build_event_info_url(self, event_id):
        return (
            urljoin(
                get_credly_settings().API_BASE_URL,
                f"organizations/{get_credly_settings().ORGANIZATION_ID}/events/{event_id}"
            ),
        )

    def _get_headers(self):
        """
        Builds authorization headers.
        """
        auth_token = build_authorization_token(get_credly_settings().AUTHORIZATION_TOKEN)
        return {"Authorization": f"Basic {auth_token}"}
