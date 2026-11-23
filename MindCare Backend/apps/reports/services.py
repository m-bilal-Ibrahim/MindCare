"""Business logic for 6.14 patient reports (docs/decisions.md, 2026-11-23).

- Only the patient's CURRENT assigned psychologist (accepted relationship,
  approved and active) generates a report, by relationship id; anyone else
  gets 404 (a paused psychologist already gets 403 from the permission class).
  Patients and admins never do.
- A report covers one period of the patient's local days: a week (Monday to
  Sunday), a calendar month, or a custom range of up to 183 days. It never
  reaches back before this pair's care first started, and never past today.
- It is calculated on every request and never stored. Every report writes one
  `patient_report` audit row in the same transaction (fail closed).
- No notification is sent to anyone.
"""

import calendar
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.journals.selectors import patient_today
from apps.reports import selectors
from apps.reports.selectors import ReportPeriod
from core.exceptions import DomainValidationError

CUSTOM_MAX_DAYS = 183
CUSTOM_NEEDS_DATES = "Choose a start and an end date for a custom period."
END_ONLY_CUSTOM = "An end date is only for custom periods."
END_BEFORE_START = "The end date can't be before the start date."
CUSTOM_TOO_LONG = f"A custom period can be at most {CUSTOM_MAX_DAYS} days."
START_IN_FUTURE = "The period can't start in the future."
BEFORE_CARE = "Choose a period after care with this patient started on {date}."


class NotYourPatient(Exception):
    pass


def _invalid(field, message):
    return DomainValidationError({field: [message]})


def _current(psychologist_user, relationship_id):
    from apps.relationships.selectors import psychologist_patient

    rel = psychologist_patient(
        psychologist_user=psychologist_user, relationship_id=relationship_id
    )
    if rel is None:
        raise NotYourPatient()
    return rel


def _nominal(period, start, end, today):
    """(first, last) day of the period as asked, before clipping."""
    if period == ReportPeriod.CUSTOM:
        if start is None or end is None:
            raise _invalid("start", CUSTOM_NEEDS_DATES)
        if end < start:
            raise _invalid("end", END_BEFORE_START)
        if (end - start).days + 1 > CUSTOM_MAX_DAYS:
            raise _invalid("end", CUSTOM_TOO_LONG)
        return start, end
    if end is not None:
        raise _invalid("end", END_ONLY_CUSTOM)
    anchor = start or today
    if period == ReportPeriod.WEEK:
        first = anchor - timedelta(days=anchor.weekday())
        return first, first + timedelta(days=6)
    first = anchor.replace(day=1)
    return first, first.replace(day=calendar.monthrange(first.year, first.month)[1])


def _previous(period, first, last):
    """The period of the same kind just before [first, last]."""
    if period == ReportPeriod.MONTH:
        prev_last = first - timedelta(days=1)
        return prev_last.replace(day=1), prev_last
    length = (last - first).days + 1
    return first - timedelta(days=length), first - timedelta(days=1)


def resolve_period(*, rel, period, start=None, end=None, today=None):
    """The period's nominal days, the days actually reported (clipped to the
    pair's care start and to today), and the previous period for comparison."""
    today = today or patient_today(rel.patient)
    care_start = selectors.care_started_on(rel)
    first, last = _nominal(period, start, end, today)
    if first > today:
        raise _invalid("start", START_IN_FUTURE)
    if last < care_start:
        raise _invalid("start", BEFORE_CARE.format(date=care_start.isoformat()))
    prev_first, prev_last = _previous(period, first, last)
    previous = None
    if prev_last >= care_start:
        previous = {
            "data_start": max(prev_first, care_start),
            "data_end": prev_last,
        }
    return {
        "type": period,
        "today": today,
        "start": first,
        "end": last,
        "data_start": max(first, care_start),
        "data_end": min(last, today),
        "is_partial": last > today,
        "clipped_to_care_start": first < care_start,
        "care_started_on": care_start,
        "previous": previous,
    }


def generate_report(
    *, psychologist_user, relationship_id, period, start=None, end=None, ip=None
):
    """The report for a current patient. Audited in the same transaction."""
    rel = _current(psychologist_user, relationship_id)
    resolved = resolve_period(rel=rel, period=period, start=start, end=end)
    with transaction.atomic():
        report = selectors.build_report(
            rel=rel, period=resolved, viewer=psychologist_user, now=timezone.now()
        )
        record_access(
            actor=psychologist_user,
            action=AuditAction.VIEW,
            resource_type=AuditResource.PATIENT_REPORT,
            resource_id=rel.pk,
            patient_user_id=rel.patient.user_id,
            ip=ip,
        )
    return report
