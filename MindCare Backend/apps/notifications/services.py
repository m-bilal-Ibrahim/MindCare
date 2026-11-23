"""Write-path business logic for notifications.

Email delivery (docs/decisions.md, 2026-10-19): `send_email_after_commit()` is the
only way the rest of the backend sends mail. It waits for the caller's
transaction to commit (so a rolled-back action never emails anyone), then sends
on a background thread (so a slow provider never delays the response, and the
response time can't reveal whether an account exists). Failures are caught and
logged with the template name and the failure kind only, never the address or
the body, and never raised into the request.
"""

import json
import logging
import threading
from contextlib import contextmanager
from datetime import UTC, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from integrations.email_client.client import EmailNotSent, send_email

logger = logging.getLogger("mindcare.email")


def _deliver(*, template, to, subject, text, html):
    try:
        send_email(to=to, subject=subject, text=text, html=html)
    except EmailNotSent as exc:
        logger.warning(
            json.dumps(
                {"event": "email_failed", "template": template, "reason": exc.reason}
            )
        )
        return False
    except Exception as exc:  # never let email break anything
        logger.warning(
            json.dumps(
                {
                    "event": "email_failed",
                    "template": template,
                    "reason": type(exc).__name__,
                }
            )
        )
        return False
    logger.info(json.dumps({"event": "email_sent", "template": template}))
    return True


def send_email_after_commit(*, template, to, message):
    """Queue one email. `message` is (subject, text, html) from
    apps.notifications.emails. Outside a transaction it is sent at once (still in
    the background)."""
    subject, text, html = message

    def start():
        kwargs = {
            "template": template,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
        }
        if settings.EMAIL_SEND_IN_BACKGROUND:
            threading.Thread(target=_deliver, kwargs=kwargs, daemon=True).start()
        else:
            _deliver(**kwargs)

    transaction.on_commit(start)


# --- In-app notifications (docs/decisions.md, 2026-11-18) ----------------------
# Created after the caller's transaction commits (a rolled-back action notifies
# nobody), synchronously, and `robust`: a failure here is logged by Django and
# never breaks the action that caused it (an SOS above all).


class NotFound(Exception):
    pass


def purge_old_notifications(*, now=None):
    """Delete notifications older than 90 days. Returns how many were deleted."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.notifications.models import RETENTION_DAYS, Notification

    cutoff = (now or timezone.now()) - timedelta(days=RETENTION_DAYS)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    return deleted


def _create(user_ids, type, target_id, when):
    from apps.notifications.models import Notification
    from apps.notifications.templates import render

    title, body, target_type = render(type, when=when)
    user_ids = list(dict.fromkeys(uid for uid in user_ids if uid))
    if not user_ids:
        return
    purge_old_notifications()
    # bulk_create is fine: every field is server-built, nothing user-entered.
    Notification.objects.bulk_create(
        [
            Notification(
                recipient_id=uid,
                type=type,
                title=title,
                body=body,
                target_type=target_type,
                target_id=target_id if target_type else None,
            )
            for uid in user_ids
        ]
    )


def notify(*, recipients, type, target_id=None, when=""):
    """Queue one notification per recipient (users or user ids). The wording
    comes from apps/notifications/templates.py; it is rendered now so a bad
    call fails in tests, not silently after commit."""
    from apps.notifications.templates import render

    render(type, when=when)
    user_ids = [getattr(r, "pk", r) for r in recipients]
    transaction.on_commit(lambda: _create(user_ids, type, target_id, when), robust=True)


def notify_admins(*, type, target_id=None):
    """Notify every active admin (resolved after commit)."""
    from apps.accounts.models import Role, User
    from apps.notifications.templates import render

    render(type)

    def create():
        ids = User.objects.filter(role=Role.ADMIN, is_active=True).values_list(
            "pk", flat=True
        )
        _create(list(ids), type, target_id, "")

    transaction.on_commit(create, robust=True)


def _own(user, notification_id):
    from apps.notifications.models import Notification

    row = (
        Notification.objects.select_for_update()
        .filter(pk=notification_id, recipient=user)
        .first()
    )
    if row is None:
        raise NotFound()
    return row


def mark_read(*, user, notification_id):
    from django.utils import timezone

    with transaction.atomic():
        row = _own(user, notification_id)
        if not row.is_read:
            row.is_read = True
            row.read_at = timezone.now()
            row.save(update_fields=["is_read", "read_at"])
    return row


def mark_all_read(*, user):
    """Returns how many were marked."""
    from django.utils import timezone

    from apps.notifications.models import Notification

    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def update_reminder_preferences(*, user, **changes):
    """Set any of check_in_reminders, care_plan_reminders and
    session_reminder_emails (booleans). Creates the row on first change."""
    from apps.notifications.models import ReminderPreference

    with transaction.atomic():
        row, _ = ReminderPreference.objects.select_for_update().get_or_create(user=user)
        for field, value in changes.items():
            setattr(row, field, value)
        if changes:
            row.save()
    return row


def delete_notification(*, user, notification_id, ip=None):
    """Delete one of your own notifications. Audited (fail closed)."""
    from apps.accounts.models import Role
    from apps.audit.models import AuditAction, AuditResource
    from apps.audit.services import record_access

    with transaction.atomic():
        row = _own(user, notification_id)
        record_access(
            actor=user,
            action=AuditAction.DELETE,
            resource_type=AuditResource.NOTIFICATION,
            resource_id=row.pk,
            patient_user_id=user.pk if user.role == Role.PATIENT else None,
            ip=ip,
        )
        row.delete()


# --- Scheduler (docs/decisions.md, 2026-11-23) ---------------------------------
# Run from a GitHub Actions cron through `manage.py run_maintenance` (daily) and
# `manage.py send_reminders` (every 15 minutes), not Celery beat. Every job:
# - works on time WINDOWS, not exact times, so a late or skipped GitHub run
#   still sends a reminder while it's useful and skips it once it isn't;
# - claims a SentReminder row before sending, so nothing is sent twice;
# - reads no encrypted column, so it runs without FIELD_ENCRYPTION_KEY;
# - returns counts only (GitHub logs are public: no names, emails or ids).

QUIET_START_HOUR, QUIET_END_HOUR = 22, 8  # recipient's local time
CARE_PLAN_HOUR = 18
CHECK_IN_HOUR = 20
SESSION_24H_MAX = timedelta(hours=24)
SESSION_24H_MIN = timedelta(hours=2)
SESSION_1H_MAX = timedelta(minutes=90)
SESSION_1H_MIN = timedelta(minutes=5)
CARE_REQUEST_WINDOW = timedelta(hours=5)
DEFAULT_TZ = "Asia/Karachi"

REMINDER_JOBS = ("sessions", "care_requests", "care_plan", "check_in")
MAINTENANCE_JOBS = ("notifications", "sos_locations", "reset_codes", "sent_reminders")
# pg_try_advisory_lock keys: one run of each command at a time.
LOCK_KEYS = {"maintenance": 730_101, "reminders": 730_102}


@contextmanager
def advisory_lock(name):
    """Yield True if this process holds the job's Postgres advisory lock (held
    for the connection's session, released at the end), False if another run
    has it."""
    key = LOCK_KEYS[name]
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        acquired = cursor.fetchone()[0]
    try:
        yield acquired
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [key])


def _tz(name):
    try:
        return ZoneInfo(name or DEFAULT_TZ)
    except (ValueError, KeyError):
        return ZoneInfo(DEFAULT_TZ)


def _when(dt, tz_name):
    """The same wording as the booking notifications."""
    tz = _tz(tz_name)
    return f"{dt.astimezone(tz):%a %d %b %Y, %H:%M} ({tz.key})"


def in_quiet_hours(local_dt):
    return local_dt.hour >= QUIET_START_HOUR or local_dt.hour < QUIET_END_HOUR


def _claim(*, user_id, kind, target_id=0, slot=""):
    """Record the reminder before sending it. False if it was already sent."""
    from apps.notifications.models import SentReminder

    _, created = SentReminder.objects.get_or_create(
        user_id=user_id, kind=kind, target_id=target_id, slot=slot
    )
    return created


def send_session_reminders(*, now):
    """~24 h (2-24 h before; only for sessions confirmed at least 24 h ahead,
    the others just got the confirmation) and ~1 h (5-90 min before) to the
    patient and the psychologist. The 24-hour one also goes by email unless the
    recipient turned that off. No quiet hours: it's about a session they booked."""
    from apps.notifications import emails, selectors
    from apps.notifications.models import NotificationType, ReminderKind

    counts = {"session_reminders": 0, "session_reminder_emails": 0}
    sessions = list(selectors.sessions_to_remind(now=now, within=SESSION_24H_MAX))
    user_ids = [
        uid for s in sessions for uid in (s.patient.user_id, s.psychologist.user_id)
    ]
    prefs = selectors.reminder_preferences_by_user(user_ids=user_ids)
    for session in sessions:
        remaining = session.starts_at - now
        if SESSION_1H_MIN < remaining <= SESSION_1H_MAX:
            kind = ReminderKind.SESSION_1H
        elif SESSION_24H_MIN < remaining <= SESSION_24H_MAX and (
            session.confirmed_at is None
            or session.confirmed_at <= session.starts_at - SESSION_24H_MAX
        ):
            kind = ReminderKind.SESSION_24H
        else:
            continue
        slot = session.starts_at.astimezone(UTC).isoformat(timespec="minutes")
        patient, psych = session.patient, session.psychologist
        for profile, builder in (
            (
                patient,
                lambda when: emails.session_reminder_patient(
                    patient_name=patient.user.full_name,
                    psychologist_name=psych.user.full_name,
                    when=when,
                ),
            ),
            (
                psych,
                lambda when: emails.session_reminder_psychologist(
                    psychologist_name=psych.user.full_name, when=when
                ),
            ),
        ):
            user = profile.user
            when = _when(session.starts_at, profile.timezone)
            with transaction.atomic():
                if not _claim(
                    user_id=user.pk, kind=kind, target_id=session.pk, slot=slot
                ):
                    continue
                notify(
                    recipients=[user],
                    type=NotificationType.SESSION_REMINDER,
                    target_id=session.pk,
                    when=when,
                )
                counts["session_reminders"] += 1
                if (
                    kind == ReminderKind.SESSION_24H
                    and prefs[user.pk].session_reminder_emails
                ):
                    send_email_after_commit(
                        template="session_reminder",
                        to=user.email,
                        message=builder(when),
                    )
                    counts["session_reminder_emails"] += 1
    return counts


def send_care_request_reminders(*, now):
    """In-app and email to the psychologist when a pending care request expires
    within 5 hours (the 2026-10-06 forward-note). Never names the patient. Not
    optional: it's a request waiting on them."""
    from apps.notifications import emails, selectors
    from apps.notifications.models import NotificationType, ReminderKind

    counts = {"care_request_reminders": 0}
    for rel in selectors.care_requests_to_remind(now=now, within=CARE_REQUEST_WINDOW):
        psych = rel.psychologist
        when = _when(rel.expires_at, psych.timezone)
        with transaction.atomic():
            if not _claim(
                user_id=psych.user_id,
                kind=ReminderKind.CARE_REQUEST_EXPIRING,
                target_id=rel.pk,
            ):
                continue
            notify(
                recipients=[psych.user_id],
                type=NotificationType.CARE_REQUEST_EXPIRING,
                target_id=rel.pk,
                when=when,
            )
            send_email_after_commit(
                template="care_request_expiring",
                to=psych.user.email,
                message=emails.care_request_expiring(
                    psychologist_name=psych.user.full_name, when=when
                ),
            )
            counts["care_request_reminders"] += 1
    return counts


def _daily_candidates(*, now, hour, pref_field):
    """{PatientProfile: local today} for active patients whose local time is
    between `hour` and the start of quiet hours, with the switch on."""
    from apps.notifications import selectors

    patients = list(selectors.patients_for_daily_reminders())
    prefs = selectors.reminder_preferences_by_user(
        user_ids=[p.user_id for p in patients]
    )
    candidates = {}
    for profile in patients:
        local = now.astimezone(_tz(profile.timezone))
        if local.hour < hour or in_quiet_hours(local):
            continue
        if getattr(prefs[profile.user_id], pref_field):
            candidates[profile] = local.date()
    return candidates


def send_care_plan_reminders(*, now):
    """At most one a day, from 18:00 local until quiet hours, when the current
    psychologist's plan has a task due today that isn't done. Never task text."""
    from apps.notifications.models import NotificationType, ReminderKind
    from apps.recommendations.selectors import plans_with_tasks_due

    counts = {"care_plan_reminders": 0}
    candidates = _daily_candidates(
        now=now, hour=CARE_PLAN_HOUR, pref_field="care_plan_reminders"
    )
    if not candidates:
        return counts
    due = plans_with_tasks_due(patients_today=candidates)
    for profile, today in candidates.items():
        plan_id = due.get(profile.pk)
        if plan_id is None:
            continue
        with transaction.atomic():
            if not _claim(
                user_id=profile.user_id,
                kind=ReminderKind.CARE_PLAN_DAILY,
                slot=today.isoformat(),
            ):
                continue
            notify(
                recipients=[profile.user_id],
                type=NotificationType.CARE_PLAN_REMINDER,
                target_id=plan_id,
            )
            counts["care_plan_reminders"] += 1
    return counts


def send_check_in_reminders(*, now):
    """At most one a day, from 20:00 local until quiet hours, to patients who
    haven't checked in today. No mood follow-up and no thresholds (§27)."""
    from apps.journals.selectors import patients_checked_in
    from apps.notifications.models import NotificationType, ReminderKind

    counts = {"check_in_reminders": 0}
    candidates = _daily_candidates(
        now=now, hour=CHECK_IN_HOUR, pref_field="check_in_reminders"
    )
    if not candidates:
        return counts
    done = patients_checked_in(patient_days={p.pk: d for p, d in candidates.items()})
    for profile, today in candidates.items():
        if profile.pk in done:
            continue
        with transaction.atomic():
            if not _claim(
                user_id=profile.user_id,
                kind=ReminderKind.CHECK_IN_DAILY,
                slot=today.isoformat(),
            ):
                continue
            notify(
                recipients=[profile.user_id], type=NotificationType.CHECK_IN_REMINDER
            )
            counts["check_in_reminders"] += 1
    return counts


def send_reminders(*, now=None, only=None):
    """Run the reminder jobs (`only`: a subset of REMINDER_JOBS). Returns counts."""
    now = now or timezone.now()
    jobs = {
        "sessions": send_session_reminders,
        "care_requests": send_care_request_reminders,
        "care_plan": send_care_plan_reminders,
        "check_in": send_check_in_reminders,
    }
    counts = {}
    for name in only or REMINDER_JOBS:
        counts.update(jobs[name](now=now))
    return counts


def purge_old_sent_reminders(*, now=None):
    from apps.notifications.models import SENT_REMINDER_RETENTION_DAYS, SentReminder

    cutoff = (now or timezone.now()) - timedelta(days=SENT_REMINDER_RETENTION_DAYS)
    deleted, _ = SentReminder.objects.filter(created_at__lt=cutoff).delete()
    return deleted


def run_maintenance(*, now=None, only=None):
    """The daily clean-up (`only`: a subset of MAINTENANCE_JOBS). The queries
    also count as activity for Supabase's free-tier pause, so this doubles as
    the heartbeat; a database that can't be reached makes the run fail."""
    from apps.accounts.services import purge_old_reset_codes
    from apps.emergency.services import purge_old_locations

    now = now or timezone.now()
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    jobs = {
        "notifications": ("notifications_deleted", purge_old_notifications),
        "sos_locations": ("sos_locations_cleared", purge_old_locations),
        "reset_codes": (
            "reset_codes_deleted",
            lambda now: purge_old_reset_codes(current=now),
        ),
        "sent_reminders": ("sent_reminders_deleted", purge_old_sent_reminders),
    }
    counts = {"database": "ok"}
    for name in only or MAINTENANCE_JOBS:
        key, job = jobs[name]
        counts[key] = job(now=now)
    return counts
