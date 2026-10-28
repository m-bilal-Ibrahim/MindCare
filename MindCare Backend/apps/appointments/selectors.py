"""Read-path query logic for appointments (Phase 2 module 4).

Slots are generated from the psychologist's weekly windows in THEIR timezone,
stepped by session length + the 10-minute gap, minus days off and minus every
blocking session's [start, end + gap) range. Only slots between now + 12 h and
now + 30 days are offered. Every psychologist-facing query is scoped to that
psychologist's own sessions; every patient-facing one to the patient's own.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.appointments.models import (
    AWAITING_STATUSES,
    BLOCKING_STATUSES,
    GAP_MINUTES,
    BookingSettings,
    DayOff,
    Session,
    SessionStatus,
    WorkingWindow,
)

MIN_NOTICE = timedelta(hours=12)
HORIZON = timedelta(days=30)
FREE_CANCELLATION = timedelta(hours=24)
MAX_UPCOMING_PER_PATIENT = 2
DEFAULT_TZ = "Asia/Karachi"


def _tz(name):
    try:
        return ZoneInfo(name or DEFAULT_TZ)
    except (ValueError, KeyError):
        return ZoneInfo(DEFAULT_TZ)


def booking_settings_for(psychologist_profile):
    """The psychologist's settings, or an unsaved default row."""
    return BookingSettings.objects.filter(
        psychologist=psychologist_profile
    ).first() or BookingSettings(psychologist=psychologist_profile)


def windows_for(psychologist_profile):
    return WorkingWindow.objects.filter(psychologist=psychologist_profile)


def days_off_for(psychologist_profile, *, upcoming_only=True):
    rows = DayOff.objects.filter(psychologist=psychologist_profile)
    if upcoming_only:
        today = timezone.now().astimezone(_tz(psychologist_profile.timezone)).date()
        rows = rows.filter(date__gte=today)
    return rows


def not_bookable_reason(settings, has_windows):
    """None when bookable, else a short machine code."""
    if settings.pk is None or not settings.fee_pkr:
        return "no_fee"
    if not settings.video_link:
        return "no_video_link"
    if not has_windows:
        return "no_working_hours"
    return None


def free_slots(psychologist_profile, *, now=None, exclude_session_id=None):
    """Free slot starts (aware datetimes, UTC) for the psychologist, oldest
    first. `exclude_session_id` ignores one session's own range (a proposal)."""
    now = now or timezone.now()
    settings = booking_settings_for(psychologist_profile)
    windows = list(windows_for(psychologist_profile))
    if not_bookable_reason(settings, bool(windows)):
        return []
    tz = _tz(psychologist_profile.timezone)
    duration = timedelta(minutes=settings.session_minutes)
    step = duration + timedelta(minutes=GAP_MINUTES)
    earliest, latest = now + MIN_NOTICE, now + HORIZON

    off = set(
        DayOff.objects.filter(psychologist=psychologist_profile).values_list(
            "date", flat=True
        )
    )
    busy = Session.objects.filter(
        psychologist=psychologist_profile,
        status__in=BLOCKING_STATUSES,
        blocked_until__gt=earliest,
        starts_at__lt=latest + step,
    )
    if exclude_session_id is not None:
        busy = busy.exclude(pk=exclude_session_id)
    busy = list(busy.values_list("starts_at", "blocked_until"))

    by_day = {}
    for w in windows:
        by_day.setdefault(w.weekday, []).append(w)

    slots = []
    day = earliest.astimezone(tz).date()
    last_day = latest.astimezone(tz).date()
    while day <= last_day:
        if day not in off:
            for w in by_day.get(day.weekday(), ()):
                start = datetime.combine(day, w.start_time, tzinfo=tz)
                window_end = datetime.combine(day, w.end_time, tzinfo=tz)
                while start + duration <= window_end:
                    if earliest <= start <= latest and not any(
                        start < b_end and b_start < start + step
                        for b_start, b_end in busy
                    ):
                        slots.append(start.astimezone(UTC))
                    start += step
        day += timedelta(days=1)
    return sorted(slots)


def slots_for_patient(*, patient_profile, now=None):
    """What the patient's booking screen needs, or None without an accepted
    psychologist."""
    from apps.relationships.selectors import get_active_relationship

    rel = get_active_relationship(patient=patient_profile)
    if rel is None:
        return None
    psych = rel.psychologist
    settings = booking_settings_for(psych)
    reason = not_bookable_reason(settings, windows_for(psych).exists())
    return {
        "bookable": reason is None,
        "not_bookable_reason": reason,
        "psychologist_timezone": psych.timezone,
        "session_minutes": settings.session_minutes if reason is None else None,
        "fee_pkr": settings.fee_pkr,
        "upcoming_sessions": patient_upcoming_count(
            patient_profile=patient_profile, now=now
        ),
        "max_upcoming_sessions": MAX_UPCOMING_PER_PATIENT,
        "slots": free_slots(psych, now=now),
    }


def _psych_related(qs):
    return qs.select_related(
        "psychologist__user", "psychologist__booking_settings", "patient__user"
    )


def patient_sessions(*, patient_profile):
    return _psych_related(Session.objects.filter(patient=patient_profile)).order_by(
        "-starts_at", "-id"
    )


def patient_upcoming_count(*, patient_profile, now=None):
    return Session.objects.filter(
        patient=patient_profile,
        status__in=BLOCKING_STATUSES,
        starts_at__gt=now or timezone.now(),
    ).count()


PSYCHOLOGIST_VIEWS = ("requests", "upcoming", "past")


def psychologist_sessions(*, psychologist_profile, view="upcoming", now=None):
    """`requests`: awaiting an answer (requested or proposed, not yet started);
    `upcoming`: confirmed and not yet ended; `past`: everything else."""
    now = now or timezone.now()
    qs = _psych_related(Session.objects.filter(psychologist=psychologist_profile))
    if view == "requests":
        return qs.filter(status__in=AWAITING_STATUSES, starts_at__gt=now)
    if view == "upcoming":
        return qs.filter(status=SessionStatus.CONFIRMED, ends_at__gt=now)
    awaiting_past = qs.filter(status__in=AWAITING_STATUSES, starts_at__lte=now)
    confirmed_past = qs.filter(status=SessionStatus.CONFIRMED, ends_at__lte=now)
    closed = qs.exclude(status__in=BLOCKING_STATUSES)
    return (awaiting_past | confirmed_past | closed).order_by("-starts_at", "-id")
