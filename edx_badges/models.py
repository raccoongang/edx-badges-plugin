from django.db import models
from django.utils.translation import gettext_lazy as _
from lms.djangoapps.badges.models import BadgeAssertion


class BadgeStatus(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    REVOKED = 'revoked'
    REPLACED = 'replaced'
    STATE_CHOICES = (
        (PENDING, _('Pending')),
        (ACCEPTED, _('Accepted')),
        (REJECTED, _('Rejected')),
        (REVOKED, _('Revoked')),
        (REPLACED, _('Replaced')),
    )
    assertion = models.OneToOneField(
        BadgeAssertion,
        models.CASCADE,
        db_index=True,
        related_name="badge_status"
    )
    state = models.CharField(max_length=255, choices=STATE_CHOICES)
    credly_badge_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = _("Badge statuses")
