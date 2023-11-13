from django.contrib import admin

from .models import BadgeStatus


class BadgeStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'state', 'template_id', 'credly_badge_id']
    list_filter = ['state']
    search_fields = ['user__email', 'template_id', 'credly_badge_id']
    readonly_fields = ('state',)

    def user(self, badge_status):
        return badge_status.assertion.user.username

    def template_id(self, badge_status):
        return badge_status.assertion.badge_class.slug


admin.site.register(BadgeStatus, BadgeStatusAdmin)
