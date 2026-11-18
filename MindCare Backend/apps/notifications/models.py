"""In-app notifications (docs/decisions.md, 2026-11-18).

The title and body are built by the server from fixed templates
(apps/notifications/templates.py) and never hold sensitive data: no names, note
text, mood, SOS location, contact details or diagnosis. Only generic wording, a
session time, and an id to open the right screen. That's why nothing here is
encrypted. Rows older than 90 days are deleted (`purge_notifications`).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

RETENTION_DAYS = 90


class NotificationType(models.TextChoices):
    # Booking (Phase 2 module 4)
    SESSION_REQUESTED = "session_requested", "Session requested"
    SESSION_CONFIRMED = "session_confirmed", "Session confirmed"
    SESSION_PROPOSED = "session_proposed", "New time proposed"
    SESSION_DECLINED = "session_declined", "Session request declined"
    SESSION_CANCELLED = "session_cancelled", "Session cancelled"
    SESSION_PROPOSAL_ACCEPTED = "session_proposal_accepted", "Proposed time accepted"
    SESSION_COMPLETED = "session_completed", "Session completed"
    SESSION_NO_SHOW = "session_no_show", "Session missed"
    # Care relationships (Phase 3)
    CARE_REQUESTED = "care_requested", "New care request"
    CARE_ACCEPTED = "care_accepted", "Care request accepted"
    CARE_DECLINED = "care_declined", "Care request declined"
    CARE_ENDED = "care_ended", "Care ended"
    # SOS (Phase 2 module 2)
    SOS_ALERT = "sos_alert", "SOS alert"
    SOS_CANCELLED = "sos_cancelled", "SOS cancelled"
    # Accounts
    ACCOUNT_APPROVED = "account_approved", "Account approved"
    ACCOUNT_REJECTED = "account_rejected", "Application not approved"
    APPLICATION_SUBMITTED = "application_submitted", "New application"
    PASSWORD_CHANGED = "password_changed", "Password changed"
    # Therapy notes (Phase 2 module 5)
    PROGRESS_SUMMARY_UPDATED = "progress_summary_updated", "Progress summary updated"


class TargetType(models.TextChoices):
    """What `target_id` points at, so a client knows which screen to open."""

    SESSION = "session", "Session"
    CARE_RELATIONSHIP = "care_relationship", "Care relationship"
    SOS_EVENT = "sos_event", "SOS alert"
    PENDING_APPLICATION = "pending_application", "Pending application"
    PROGRESS_SUMMARY = "progress_summary", "Progress summary"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=40, choices=NotificationType.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=300)
    target_type = models.CharField(
        max_length=30, choices=TargetType.choices, blank=True
    )
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["recipient", "-created_at"], name="notif_recipient_recent"
            ),
            models.Index(
                fields=["recipient", "is_read"], name="notif_recipient_unread"
            ),
        ]

    def __str__(self):
        return f"{self.type} → user {self.recipient_id}"
