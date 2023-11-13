"""
edx_badges URL Configuration
"""

from django.conf.urls import include
from django.urls import re_path, path

from .views import force_state_update_view

urlpatterns = [
    re_path(r"^api/credly/", include(("edx_badges.credly.rest_api.urls", "credly-api"), namespace="credly-api")),
    path('force_state_update/<int:pk>/', force_state_update_view, name='force_state_update'),
]
