"""Read-path query logic for in-app notifications. Every query is scoped to the
requesting user: nobody ever reads another user's notifications."""

from apps.notifications.models import Notification


def notifications_for(*, user, unread=None, type=None):
    rows = Notification.objects.filter(recipient=user)
    if unread is True:
        rows = rows.filter(is_read=False)
    elif unread is False:
        rows = rows.filter(is_read=True)
    if type:
        rows = rows.filter(type=type)
    return rows.order_by("-created_at", "-id")


def unread_count(*, user):
    return Notification.objects.filter(recipient=user, is_read=False).count()


# --- Scheduled reminders (docs/decisions.md, 2026-11-23: scheduler) ------------
# None of these load an encrypted column, so the scheduler runs without
# FIELD_ENCRYPTION_KEY. User and profile rows are loaded with `.only()`: the
# scheduler's database role may read just these columns (docs/deployment.md,
# "Scheduler"), never password hashes, dates of birth or phone numbers.

USER_COLUMNS = ("id", "email", "full_name", "is_active", "approval_status", "role")
PROFILE_COLUMNS = ("id", "user_id", "timezone")


def _only(prefix, columns):
    return [f"{prefix}__{c}" for c in columns]


def reminder_preferences_for(*, user):
    """The user's switches, or an unsaved row with every default (all on)."""
    from apps.notifications.models import ReminderPreference

    return ReminderPreference.objects.filter(user=user).first() or (
        ReminderPreference(user=user)
    )


def reminder_preferences_by_user(*, user_ids):
    """{user_id: ReminderPreference}; a user without a row gets the defaults."""
    from apps.notifications.models import ReminderPreference

    rows = {
        row.user_id: row
        for row in ReminderPreference.objects.filter(user_id__in=set(user_ids))
    }
    return {uid: rows.get(uid) or ReminderPreference(user_id=uid) for uid in user_ids}


def _visible_psychologist():
    from apps.relationships.selectors import visible_psychologist_q

    return visible_psychologist_q()


def sessions_to_remind(*, now, within):
    """Confirmed sessions starting in (now, now + within], between an active
    patient and an approved, active psychologist (a paused psychologist gets
    no reminders, like every other psychologist path)."""
    from apps.appointments.models import Session, SessionStatus

    return (
        Session.objects.filter(
            status=SessionStatus.CONFIRMED,
            starts_at__gt=now,
            starts_at__lte=now + within,
            patient__user__is_active=True,
        )
        .filter(_visible_psychologist())
        .select_related("patient__user", "psychologist__user")
        .only(
            "id",
            "status",
            "starts_at",
            "confirmed_at",
            "patient",
            "psychologist",
            *_only("patient", ("timezone", "user")),
            *_only("psychologist", ("timezone", "user")),
            *_only("patient__user", USER_COLUMNS),
            *_only("psychologist__user", USER_COLUMNS),
        )
        .order_by("starts_at", "id")
    )


def care_requests_to_remind(*, now, within):
    """Pending care requests that expire in (now, now + within], sent to an
    approved, active psychologist by an active patient."""
    from apps.relationships.models import CareRelationship, RelationshipStatus

    return (
        CareRelationship.objects.filter(
            status=RelationshipStatus.PENDING,
            expires_at__gt=now,
            expires_at__lte=now + within,
            patient__user__is_active=True,
        )
        .filter(_visible_psychologist())
        .select_related("psychologist__user")
        .only(
            "id",
            "status",
            "expires_at",
            "psychologist",
            *_only("psychologist", ("timezone", "user")),
            *_only("psychologist__user", USER_COLUMNS),
        )
        .order_by("expires_at", "id")
    )


def patients_for_daily_reminders():
    """Every active patient account: profile id, user id and timezone only."""
    from apps.patients.models import PatientProfile

    return (
        PatientProfile.objects.filter(user__is_active=True)
        .only(*PROFILE_COLUMNS)
        .order_by("id")
    )
