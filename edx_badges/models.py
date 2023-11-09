from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from lms.djangoapps.badges.models import BadgeAssertion

from .utils import create_orcid_qualification, delete_orcid_qualification


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
    state = FSMField(default=PENDING, choices=STATE_CHOICES)
    credly_badge_id = models.CharField(max_length=255, blank=True)
    credly_qualification_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = _("Badge statuses")

    @transition(field=state, source=PENDING, target=ACCEPTED)
    def accept(self):
        create_orcid_qualification(self.assertion)

    @transition(field=state, source=[PENDING, ACCEPTED], target=REVOKED)
    def revoke(self):
        delete_orcid_qualification(self.assertion)

    @transition(field=state, source=PENDING, target=REJECTED)
    def reject(self):
        pass

    @transition(field=state, source=[ACCEPTED, REJECTED, REVOKED, REPLACED], target=PENDING)
    def pending(self):
        pass
