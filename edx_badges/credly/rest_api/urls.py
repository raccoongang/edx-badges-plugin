"""Root API URLs for credly."""
from django.conf.urls import include
from django.urls import re_path


urlpatterns = [
    re_path(r"^v1/", include(("edx_badges.credly.rest_api.v1.urls", "v1"), namespace="v1")),
]
