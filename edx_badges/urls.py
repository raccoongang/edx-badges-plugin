"""
edx_badges URL Configuration
"""

from django.conf.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r"^api/credly/", include(("edx_badges.credly.rest_api.urls", "credly-api"), namespace="credly-api")),
]
