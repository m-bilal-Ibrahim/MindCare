"""Write-path business logic for appointments (Phase 2 module 4: booking and fees).

docs/decisions.md, 2026-10-28 (Q27-Q34):
- Only a patient with an accepted relationship books, and only with that
  psychologist. A booking is a request; the psychologist confirms it or
  proposes another free slot, which the patient accepts. Unanswered requests
  and proposals expire when their slot starts.
- At least 12 h notice, at most 30 days ahead, at most 2 upcoming sessions per
  patient. A patient's cancellation of a confirmed session less than 24 h
  before it starts is recorded as late (for 6.11; nothing is charged yet).
- The psychologist marks a confirmed session completed or no-show after it ends.
- The exclusion constraint is the final word on double booking; the slot
  check before it only gives a clearer message.
- Every session write is audited in its own transaction (fail closed). Emails
  go out after commit and never name the patient to the psychologist.
"""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.appointments import selectors
from apps.appointments.models import (
    AWAITING_STATUSES,
    BLOCKING_STATUSES,
    GAP_MINUTES,
    CancelledBy,
    DayOff,
    Session,
    SessionStatus,
    WorkingWindow,
)
from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.notifications import emails
from apps.notifications.services import send_email_after_commit
from apps.patients.models import PatientProfile
from apps.relationships.selectors import get_active_relationship
from core.exceptions import DomainValidationError

NO_PSYCHOLOGIST = "You need an accepted psychologist before booking a session."
NOT_OPEN = "Your psychologist hasn't opened bookings yet."
NOTICE = "Book at least 12 hours ahead."
HORIZON = "You can book up to 30 days ahead."
LIMIT = "You can have at most 2 upcoming sessions."
SLOT_UNAVAILABLE = "That time isn't available any more. Pick another slot."
SAME_TIME = "Choose a different time from the current one."
NEED_LINK = "Add your Zoom or Google Meet link before confirming sessions."
NOT_REQUESTED = "This session isn't waiting for your answer."
NOT_PROPOSED = "There's no new time to accept for this session."
NOT_CANCELLABLE = "This session can't be cancelled any more."
NOT_ENDED = "You can mark the outcome once a confirmed session has ended."
WINDOW_ORDER = "End time must be after the start time."
WINDOW_QUARTER = "Times must be on the quarter hour (e.g. 09:00, 09:15)."
WINDOW_OVERLAP = "Working hours on the same day can't overlap."
WINDOW_TOO_SHORT = "Each window must fit at least one session."
WINDOWS_PER_DAY = "You can set at most 3 windows per day."
DAY_OFF_PAST = "A day off can't be in the past."
DAY_OFF_HORIZON = "Choose a day within the next 365 days."
DAY_OFF_EXISTS = "That day is already a day off."
DAY_OFF_BUSY = "You have sessions on that day. Cancel or move them first."

MAX_WINDOWS_PER_DAY = 3
DAY_OFF_MAX_AHEAD = timedelta(days=365)


class NotFound(Exception):
    pass


def _audit(actor, action, session, ip):
    record_access(
        actor=actor,
        action=action,
        resource_type=AuditResource.APPOINTMENT,
        resource_id=session.pk,
        patient_user_id=session.patient.user_id,
        ip=ip,
    )


def _when(dt, tz_name):
    try:
        tz = ZoneInfo(tz_name or selectors.DEFAULT_TZ)
    except (ValueError, KeyError):
        tz = ZoneInfo(selectors.DEFAULT_TZ)
    return f"{dt.astimezone(tz):%a %d %b %Y, %H:%M} ({tz.key})"


def _email_psychologist(template, builder, session):
    psych = session.psychologist
    send_email_after_commit(
        template=template,
        to=psych.user.email,
        message=builder(
            psychologist_name=psych.user.full_name,
            when=_when(session.starts_at, psych.timezone),
        ),
    )


def _email_patient(template, builder, session):
    patient = session.patient
    send_email_after_commit(
        template=template,
        to=patient.user.email,
        message=builder(
            patient_name=patient.user.full_name,
            psychologist_name=session.psychologist.user.full_name,
            when=_when(session.starts_at, patient.timezone),
        ),
    )


def _set_times(session, starts_at, minutes):
    session.starts_at = starts_at
    session.duration_minutes = minutes
    session.ends_at = starts_at + timedelta(minutes=minutes)
    session.blocked_until = session.ends_at + timedelta(minutes=GAP_MINUTES)


def _expire_if_stale(session, now):
    if session.status in AWAITING_STATUSES and session.starts_at <= now:
        session.status = SessionStatus.EXPIRED
        session.save(update_fields=["status", "updated_at"])
    return session


def _lock(now, **filters):
    session = (
        Session.objects.select_for_update(of=("self",))
        .select_related("patient__user", "psychologist__user")
        .filter(**filters)
        .first()
    )
    if session is None:
        raise NotFound()
    return _expire_if_stale(session, now)


def _act(now, filters, apply):
    """Lock the session (expiring it if stale), then apply(session). The expiry
    commits even when apply() refuses: apply validates before it writes."""
    error = None
    with transaction.atomic():
        session = _lock(now, **filters)
        try:
            apply(session)
        except DomainValidationError as exc:
            error = exc
    if error is not None:
        raise error
    return session


def _require_link(psychologist_profile):
    if not selectors.booking_settings_for(psychologist_profile).video_link:
        raise DomainValidationError({"video_link": [NEED_LINK]})


# --- psychologist set-up -------------------------------------------------


def update_booking_settings(*, psychologist_profile, **changes):
    settings = selectors.booking_settings_for(psychologist_profile)
    for field in ("session_minutes", "fee_pkr", "video_link"):
        if field in changes:
            value = changes[field]
            setattr(
                settings, field, "" if field == "video_link" and not value else value
            )
    settings.save()
    return settings


def _check_windows(windows, session_minutes):
    by_day = {}
    for w in windows:
        start, end = w["start_time"], w["end_time"]
        for t in (start, end):
            if t.minute % 15 or t.second or t.microsecond:
                raise DomainValidationError({"windows": [WINDOW_QUARTER]})
        if start >= end:
            raise DomainValidationError({"windows": [WINDOW_ORDER]})
        minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
        if minutes < session_minutes:
            raise DomainValidationError({"windows": [WINDOW_TOO_SHORT]})
        by_day.setdefault(w["weekday"], []).append((start, end))
    for spans in by_day.values():
        if len(spans) > MAX_WINDOWS_PER_DAY:
            raise DomainValidationError({"windows": [WINDOWS_PER_DAY]})
        spans.sort()
        for (_, prev_end), (next_start, _) in zip(spans, spans[1:], strict=False):
            if next_start < prev_end:
                raise DomainValidationError({"windows": [WINDOW_OVERLAP]})


def replace_working_windows(*, psychologist_profile, windows):
    """Replace every weekly window. Existing sessions are kept as they are."""
    settings = selectors.booking_settings_for(psychologist_profile)
    _check_windows(windows, settings.session_minutes)
    with transaction.atomic():
        WorkingWindow.objects.filter(psychologist=psychologist_profile).delete()
        for w in windows:
            WorkingWindow.objects.create(psychologist=psychologist_profile, **w)
    return list(selectors.windows_for(psychologist_profile))


def add_day_off(*, psychologist_profile, date):
    tz = selectors._tz(psychologist_profile.timezone)
    now = timezone.now()
    today = now.astimezone(tz).date()
    if date < today:
        raise DomainValidationError({"date": [DAY_OFF_PAST]})
    if date > today + DAY_OFF_MAX_AHEAD:
        raise DomainValidationError({"date": [DAY_OFF_HORIZON]})
    with transaction.atomic():
        busy = [
            s
            for s in Session.objects.select_for_update().filter(
                psychologist=psychologist_profile,
                status__in=BLOCKING_STATUSES,
                starts_at__gt=now,
                starts_at__date__gte=date - timedelta(days=1),
                starts_at__date__lte=date + timedelta(days=1),
            )
            if s.starts_at.astimezone(tz).date() == date
        ]
        if busy:
            raise DomainValidationError({"date": [DAY_OFF_BUSY]})
        try:
            with transaction.atomic():
                return DayOff.objects.create(
                    psychologist=psychologist_profile, date=date
                )
        except IntegrityError as exc:
            raise DomainValidationError({"date": [DAY_OFF_EXISTS]}) from exc


def remove_day_off(*, psychologist_profile, day_off_id):
    deleted, _ = DayOff.objects.filter(
        pk=day_off_id, psychologist=psychologist_profile
    ).delete()
    if not deleted:
        raise NotFound()


# --- patient --------------------------------------------------------------


def book_session(*, patient_user, starts_at, ip=None, now=None):
    now = now or timezone.now()
    with transaction.atomic():
        # Locking the patient makes the "at most 2 upcoming" rule race-free.
        profile = PatientProfile.objects.select_for_update().get(user=patient_user)
        rel = get_active_relationship(patient=profile)
        if rel is None:
            raise DomainValidationError({"relationship": [NO_PSYCHOLOGIST]})
        psych = rel.psychologist
        settings = selectors.booking_settings_for(psych)
        has_windows = selectors.windows_for(psych).exists()
        if selectors.not_bookable_reason(settings, has_windows):
            raise DomainValidationError({"psychologist": [NOT_OPEN]})
        if starts_at < now + selectors.MIN_NOTICE:
            raise DomainValidationError({"starts_at": [NOTICE]})
        if starts_at > now + selectors.HORIZON:
            raise DomainValidationError({"starts_at": [HORIZON]})
        if (
            selectors.patient_upcoming_count(patient_profile=profile, now=now)
            >= selectors.MAX_UPCOMING_PER_PATIENT
        ):
            raise DomainValidationError({"non_field_errors": [LIMIT]})
        if starts_at not in selectors.free_slots(psych, now=now):
            raise DomainValidationError({"starts_at": [SLOT_UNAVAILABLE]})
        session = Session(
            relationship=rel,
            patient=profile,
            psychologist=psych,
            fee_pkr=settings.fee_pkr,
            requested_starts_at=starts_at,
        )
        _set_times(session, starts_at, settings.session_minutes)
        try:
            with transaction.atomic():
                session.save()
        except IntegrityError as exc:  # the exclusion constraint: a race lost
            raise DomainValidationError({"starts_at": [SLOT_UNAVAILABLE]}) from exc
        _audit(patient_user, AuditAction.CREATE, session, ip)
        _email_psychologist("session_requested", emails.session_requested, session)
    return session


def accept_proposal(*, patient_user, session_id, ip=None):
    now = timezone.now()

    def apply(session):
        if session.status != SessionStatus.PROPOSED:
            raise DomainValidationError({"session": [NOT_PROPOSED]})
        session.status = SessionStatus.CONFIRMED
        session.confirmed_at = now
        session.save(update_fields=["status", "confirmed_at", "updated_at"])
        _audit(patient_user, AuditAction.UPDATE, session, ip)
        _email_psychologist(
            "session_proposal_accepted", emails.session_proposal_accepted, session
        )

    return _act(now, {"pk": session_id, "patient__user": patient_user}, apply)


def _cancel(session, by, now):
    if session.status not in BLOCKING_STATUSES or session.starts_at <= now:
        raise DomainValidationError({"session": [NOT_CANCELLABLE]})
    session.is_late_cancellation = (
        by == CancelledBy.PATIENT
        and session.status == SessionStatus.CONFIRMED
        and session.starts_at - now < selectors.FREE_CANCELLATION
    )
    session.status = SessionStatus.CANCELLED
    session.cancelled_by = by
    session.cancelled_at = now
    session.save(
        update_fields=[
            "status",
            "cancelled_by",
            "cancelled_at",
            "is_late_cancellation",
            "updated_at",
        ]
    )


def patient_cancel_session(*, patient_user, session_id, ip=None):
    now = timezone.now()

    def apply(session):
        _cancel(session, CancelledBy.PATIENT, now)
        _audit(patient_user, AuditAction.UPDATE, session, ip)
        _email_psychologist(
            "session_cancelled_by_patient", emails.session_cancelled_by_patient, session
        )

    return _act(now, {"pk": session_id, "patient__user": patient_user}, apply)


# --- psychologist ---------------------------------------------------------


def confirm_session(*, psychologist_profile, session_id, ip=None):
    now = timezone.now()

    def apply(session):
        if session.status != SessionStatus.REQUESTED:
            raise DomainValidationError({"session": [NOT_REQUESTED]})
        _require_link(psychologist_profile)
        session.status = SessionStatus.CONFIRMED
        session.confirmed_at = now
        session.save(update_fields=["status", "confirmed_at", "updated_at"])
        _audit(psychologist_profile.user, AuditAction.UPDATE, session, ip)
        _email_patient("session_confirmed", emails.session_confirmed, session)

    return _act(now, {"pk": session_id, "psychologist": psychologist_profile}, apply)


def propose_time(*, psychologist_profile, session_id, starts_at, ip=None):
    """Move a request (or an earlier proposal) to another free slot; the
    patient then accepts it or cancels."""
    now = timezone.now()

    def apply(session):
        if session.status not in AWAITING_STATUSES:
            raise DomainValidationError({"session": [NOT_REQUESTED]})
        _require_link(psychologist_profile)
        if starts_at == session.starts_at:
            raise DomainValidationError({"starts_at": [SAME_TIME]})
        free = selectors.free_slots(
            psychologist_profile, now=now, exclude_session_id=session.pk
        )
        if starts_at not in free:
            raise DomainValidationError({"starts_at": [SLOT_UNAVAILABLE]})
        settings = selectors.booking_settings_for(psychologist_profile)
        _set_times(session, starts_at, settings.session_minutes)
        session.status = SessionStatus.PROPOSED
        try:
            with transaction.atomic():
                session.save()
        except IntegrityError as exc:
            raise DomainValidationError({"starts_at": [SLOT_UNAVAILABLE]}) from exc
        _audit(psychologist_profile.user, AuditAction.UPDATE, session, ip)
        _email_patient("session_proposed", emails.session_proposed, session)

    return _act(now, {"pk": session_id, "psychologist": psychologist_profile}, apply)


def psychologist_cancel_session(*, psychologist_profile, session_id, ip=None):
    now = timezone.now()

    def apply(session):
        _cancel(session, CancelledBy.PSYCHOLOGIST, now)
        _audit(psychologist_profile.user, AuditAction.UPDATE, session, ip)
        _email_patient(
            "session_cancelled_by_psychologist",
            emails.session_cancelled_by_psychologist,
            session,
        )

    return _act(now, {"pk": session_id, "psychologist": psychologist_profile}, apply)


OUTCOMES = (SessionStatus.COMPLETED, SessionStatus.NO_SHOW)


def mark_outcome(*, psychologist_profile, session_id, outcome, ip=None):
    now = timezone.now()

    def apply(session):
        if session.status != SessionStatus.CONFIRMED or session.ends_at > now:
            raise DomainValidationError({"session": [NOT_ENDED]})
        session.status = outcome
        session.outcome_marked_at = now
        session.save(update_fields=["status", "outcome_marked_at", "updated_at"])
        _audit(psychologist_profile.user, AuditAction.UPDATE, session, ip)

    return _act(now, {"pk": session_id, "psychologist": psychologist_profile}, apply)


# --- system -------------------------------------------------------------------


def cancel_for_ended_relationship(*, relationship):
    """Called by relationships.services.end_relationship() inside its
    transaction: future sessions of that relationship are cancelled (no emails:
    the relationship ending is the news) and stale requests expire."""
    now = timezone.now()
    rows = (
        Session.objects.select_for_update(of=("self",))
        .filter(relationship=relationship, status__in=BLOCKING_STATUSES)
        .select_related("patient")
    )
    for session in rows:
        _expire_if_stale(session, now)
        if session.status in BLOCKING_STATUSES and session.starts_at > now:
            _cancel(session, CancelledBy.SYSTEM, now)
            _audit(None, AuditAction.UPDATE, session, None)
