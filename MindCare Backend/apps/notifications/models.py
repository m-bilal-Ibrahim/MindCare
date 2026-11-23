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
    # Messaging
    NEW_MESSAGE = "new_message", "New message"
    # Care plan
    CARE_PLAN_UPDATED = "care_plan_updated", "Care plan updated"
    # Scheduled reminders (docs/decisions.md, 2026-11-23: scheduler)
    SESSION_REMINDER = "session_reminder", "Session reminder"
    CARE_REQUEST_EXPIRING = "care_request_expiring", "Care request expiring"
    CARE_PLAN_REMINDER = "care_plan_reminder", "Care plan reminder"
    CHECK_IN_REMINDER = "check_in_reminder", "Check-in reminder"


class TargetType(models.TextChoices):
    """What `target_id` points at, so a client knows which screen to open."""

    SESSION = "session", "Session"
    CARE_RELATIONSHIP = "care_relationship", "Care relationship"
    SOS_EVENT = "sos_event", "SOS alert"
    PENDING_APPLICATION = "pending_application", "Pending application"
    PROGRESS_SUMMARY = "progress_summary", "Progress summary"
    CONVERSATION = "conversation", "Conversation"
    CARE_PLAN = "care_plan", "Care plan"
    CHECK_IN = "check_in", "Mood check-in"


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


# --- Scheduled reminders (docs/decisions.md, 2026-11-23: scheduler) ------------
# Run by `manage.py send_reminders` from a GitHub Actions cron, not Celery beat.

SENT_REMINDER_RETENTION_DAYS = 30


class ReminderPreference(models.Model):
    """A user's reminder switches. No row means every default (all on).

    In-app session and care-request reminders can't be turned off: they're about
    appointments and requests the user already made or must answer. The rows hold
    no health data, so nothing is encrypted or audited.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminder_preference",
    )
    # Patients only (in-app): "you haven't checked in today", 20:00 local.
    check_in_reminders = models.BooleanField(default=True)
    # Patients only (in-app): "you have care-plan tasks for today", 18:00 local.
    care_plan_reminders = models.BooleanField(default=True)
    # Patients and psychologists: the email copy of the 24-hour session reminder.
    session_reminder_emails = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reminder preferences of user {self.user_id}"


class ReminderKind(models.TextChoices):
    SESSION_24H = "session_24h", "Session in about 24 hours"
    SESSION_1H = "session_1h", "Session in about 1 hour"
    CARE_REQUEST_EXPIRING = "care_request_expiring", "Care request expiring"
    CARE_PLAN_DAILY = "care_plan_daily", "Care-plan tasks today"
    CHECK_IN_DAILY = "check_in_daily", "No check-in today"


class SentReminder(models.Model):
    """One row per reminder sent, written BEFORE it is sent: the unique key makes
    a re-run, an overlapping run or a late run send it at most once. Ids and a
    slot only (a session's start time or the recipient's local date); kept 30
    days."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_reminders",
    )
    kind = models.CharField(max_length=30, choices=ReminderKind.choices)
    # The session or care relationship it was about; 0 for the daily reminders.
    target_id = models.PositiveBigIntegerField(default=0)
    # Session reminders: the start time (UTC, ISO 8601), so a moved session
    # gets a fresh reminder. Daily reminders: the recipient's local date.
    slot = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "kind", "target_id", "slot"],
                name="notifications_one_reminder_per_slot",
            )
        ]

    def __str__(self):
        return f"{self.kind} → user {self.user_id}"
