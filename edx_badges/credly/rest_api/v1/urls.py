"""
Edx badges Credly API v1 URLs.
"""
from django.urls import path

from .views import CredlyWebhook


urlpatterns = [
    path(r"webhook", CredlyWebhook.as_view(), name="credly-webhook"),
]
