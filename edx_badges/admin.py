import os
from admin_extra_buttons.api import ExtraButtonsMixin, link
from django.conf import settings
from django.contrib import admin
from django.urls import reverse

from .models import BadgeStatus


class BadgeStatusAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    list_display = ['id', 'user', 'state', 'template_id', 'credly_badge_id']
    list_filter = ['state']
    search_fields = ['user__email', 'template_id', 'credly_badge_id']
    readonly_fields = ('state',)

    def user(self, badge_status):
        return badge_status.assertion.user.username

    def template_id(self, badge_status):
        return badge_status.assertion.badge_class.slug

    @link(href=None, change_list=False, change_form=True)
    def force_state_update(self, button):
        pk = button.request.resolver_match.kwargs.get('object_id')
        path = reverse("edx_badges:force_state_update", kwargs={'pk': pk})
        button.href = os.path.join(settings.LMS_ROOT_URL, path)


admin.site.register(BadgeStatus, BadgeStatusAdmin)
