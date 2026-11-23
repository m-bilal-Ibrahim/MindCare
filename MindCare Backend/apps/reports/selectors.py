"""Read-path logic for 6.14 patient reports (docs/decisions.md, 2026-11-23).

A report is calculated on every request from data that already exists and is
never stored. Access and the audit row are handled in services.py; these
functions only calculate, for one patient-psychologist pair and one range of
the patient's local days.

What a report contains, and what it never contains:
- sessions: counts by outcome, attendance, minutes attended, the next
  confirmed session. No fees (6.11).
- therapy notes: counts, progress ratings and risk levels. Never note text,
  addenda or the progress summary.
- mood: check-in counts, averages, distribution, top feelings, longest streak.
  Never the check-in note.
- care plan: adherence per plan, goal and task, completions, difficulty, goals
  achieved or dropped, goal and task titles. Never completion note text (only
  how many there are).
- SOS: the number of alerts and their dates and status. Never location or
  contacts.
- sensors: not available until 6.5.
- The journal is never read here, not even counted (project-vision section 11).

Everything is calculated, not AI-generated. Indicators are factual statements
about the numbers; no clinical threshold is applied.
"""

from collections import Counter
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import models
from django.utils import timezone

from apps.appointments.models import (
    AWAITING_STATUSES,
    CancelledBy,
    Session,
    SessionStatus,
)
from apps.clinical_notes.models import RiskLevel, TherapyNote
from apps.emergency.models import SOSEvent
from apps.journals.models import Mood, MoodCheckIn
from apps.journals.selectors import DEFAULT_TZ, TOP_TAGS
from apps.recommendations.models import GoalStatus, TaskCompletion, TaskFrequency
from apps.recommendations.selectors import (
    expected_and_done,
    history_range,
    local_date_of,
    percent,
    plan_for_pair,
)
from apps.relationships.models import CareRelationship, RelationshipStatus

DAILY_SERIES_MAX_DAYS = 31


class ReportPeriod(models.TextChoices):
    WEEK = "week", "Week (Monday to Sunday)"
    MONTH = "month", "Calendar month"
    CUSTOM = "custom", "Custom range"


class Granularity(models.TextChoices):
    DAY = "day", "Day"
    WEEK = "week", "Week (starting Monday)"


def patient_tz(patient_profile):
    try:
        return ZoneInfo(patient_profile.timezone or DEFAULT_TZ)
    except (ValueError, KeyError):
        return ZoneInfo(DEFAULT_TZ)


def care_started_on(rel):
    """The patient's local day this pair's care first started: the earliest
    accepted relationship row of the pair (accepted now or ended since)."""
    first = (
        CareRelationship.objects.filter(
            patient=rel.patient,
            psychologist=rel.psychologist,
            status__in=[RelationshipStatus.ACCEPTED, RelationshipStatus.ENDED],
            responded_at__isnull=False,
        )
        .order_by("responded_at")
        .values_list("responded_at", flat=True)
        .first()
    )
    return local_date_of(first or rel.requested_at, rel.patient)


def _bounds(start, end, tz):
    """Aware datetimes [start of `start`, start of the day after `end`)."""
    lo = datetime.combine(start, time.min, tzinfo=tz)
    hi = datetime.combine(end + timedelta(days=1), time.min, tzinfo=tz)
    return lo, hi


def buckets(start, end):
    """(granularity, [(label, first_day, last_day)]) covering [start, end]:
    days for up to 31 days, otherwise weeks starting Monday (the first and last
    week are clipped to the range; the label is the week's Monday)."""
    if (end - start).days + 1 <= DAILY_SERIES_MAX_DAYS:
        days = (end - start).days + 1
        return Granularity.DAY, [
            (start + timedelta(i), start + timedelta(i), start + timedelta(i))
            for i in range(days)
        ]
    rows = []
    monday = start - timedelta(days=start.weekday())
    while monday <= end:
        rows.append((monday, max(monday, start), min(monday + timedelta(6), end)))
        monday += timedelta(days=7)
    return Granularity.WEEK, rows


def _in(day, first, last):
    return first <= day <= last


def _average(values, digits=2):
    return round(sum(values) / len(values), digits) if values else None


def _series(bucket_rows, pick):
    return [
        {"date": label, "value": pick(first, last)}
        for label, first, last in bucket_rows
    ]


# --- sections ---------------------------------------------------------------


def sessions_section(*, rel, start, end, bucket_rows, now):
    tz = patient_tz(rel.patient)
    lo, hi = _bounds(start, end, tz)
    rows = Session.objects.filter(
        patient=rel.patient,
        psychologist=rel.psychologist,
        starts_at__gte=lo,
        starts_at__lt=hi,
    ).values(
        "status",
        "starts_at",
        "duration_minutes",
        "cancelled_by",
        "is_late_cancellation",
    )
    counts = Counter()
    days = {"completed": [], "no_show": []}
    minutes = 0
    for row in rows:
        status = row["status"]
        if status in AWAITING_STATUSES and row["starts_at"] <= now:
            status = SessionStatus.EXPIRED  # evaluated on read, like booking
        day = row["starts_at"].astimezone(tz).date()
        if status == SessionStatus.COMPLETED:
            counts["completed"] += 1
            minutes += row["duration_minutes"]
            days["completed"].append(day)
        elif status == SessionStatus.NO_SHOW:
            counts["no_show"] += 1
            days["no_show"].append(day)
        elif status == SessionStatus.EXPIRED:
            counts["expired"] += 1
        elif status == SessionStatus.CANCELLED:
            by = row["cancelled_by"]
            if by == CancelledBy.PATIENT:
                key = "late" if row["is_late_cancellation"] else "on_time"
                counts[f"cancelled_by_patient_{key}"] += 1
            elif by == CancelledBy.PSYCHOLOGIST:
                counts["cancelled_by_psychologist"] += 1
            else:
                counts["cancelled_by_system"] += 1
    attended = counts["completed"] + counts["no_show"]
    next_confirmed = (
        Session.objects.filter(
            patient=rel.patient,
            psychologist=rel.psychologist,
            status=SessionStatus.CONFIRMED,
            starts_at__gt=now,
        )
        .order_by("starts_at")
        .values_list("starts_at", flat=True)
        .first()
    )
    return {
        "completed": counts["completed"],
        "no_show": counts["no_show"],
        "cancelled_by_patient": {
            "on_time": counts["cancelled_by_patient_on_time"],
            "late": counts["cancelled_by_patient_late"],
        },
        "cancelled_by_psychologist": counts["cancelled_by_psychologist"],
        "cancelled_by_system": counts["cancelled_by_system"],
        "expired": counts["expired"],
        "attendance_rate": percent(attended, counts["completed"]),
        "minutes_attended": minutes,
        "next_confirmed_at": next_confirmed,
        "series": {
            key: _series(
                bucket_rows,
                lambda a, b, key=key: sum(1 for d in days[key] if _in(d, a, b)),
            )
            for key in ("completed", "no_show")
        },
    }


def notes_section(*, rel, start, end, bucket_rows):
    """Ratings and risk levels only: the encrypted sections are never loaded."""
    tz = patient_tz(rel.patient)
    lo, hi = _bounds(start, end, tz)
    notes = (
        TherapyNote.objects.filter(
            patient=rel.patient,
            psychologist=rel.psychologist,
            created_at__gte=lo,
            created_at__lt=hi,
        )
        .only("id", "created_at", "progress_rating", "risk_level")
        .order_by("created_at", "id")
    )
    rated, risks, count = [], [], 0
    for note in notes:
        count += 1
        day = note.created_at.astimezone(tz).date()
        if note.progress_rating is not None:
            rated.append((day, note.progress_rating))
        if note.risk_level:
            risks.append((day, note.risk_level))
    ratings = [r for _, r in rated]

    def avg_rating(a, b):
        return _average([r for d, r in rated if _in(d, a, b)])

    def latest_risk(a, b):
        picked = [level for d, level in risks if _in(d, a, b)]
        return picked[-1] if picked else None

    return {
        "count": count,
        "progress": {
            "rated_notes": len(ratings),
            "first": ratings[0] if ratings else None,
            "last": ratings[-1] if ratings else None,
            "average": _average(ratings),
            "change": ratings[-1] - ratings[0] if len(ratings) > 1 else None,
        },
        "risk": {
            "counts": {
                level: sum(1 for _, r in risks if r == level)
                for level in RiskLevel.values
            },
            "first": risks[0][1] if risks else None,
            "latest": risks[-1][1] if risks else None,
        },
        "series": {
            "progress_rating": _series(bucket_rows, avg_rating),
            "risk_level": _series(bucket_rows, latest_risk),
        },
    }


def _longest_streak(dates):
    best = run = 0
    previous = None
    for day in sorted(dates):
        run = run + 1 if previous is not None and day - previous == timedelta(1) else 1
        best = max(best, run)
        previous = day
    return best


def mood_section(*, rel, start, end, bucket_rows):
    """Mood and feelings only: the check-in note is never loaded."""
    rows = list(
        MoodCheckIn.objects.filter(
            patient=rel.patient, local_date__gte=start, local_date__lte=end
        ).values("local_date", "mood", "tags")
    )
    moods = [r["mood"] for r in rows]
    tags = Counter(tag for r in rows for tag in r["tags"])
    days = (end - start).days + 1
    return {
        "check_ins": len(rows),
        "days_with_check_in_percent": round(100 * len(rows) / days) if days else None,
        "average_mood": _average(moods),
        "distribution": {str(m): moods.count(m) for m in Mood.values},
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))[
                :TOP_TAGS
            ]
        ],
        "longest_streak": _longest_streak([r["local_date"] for r in rows]),
        "series": {
            "average_mood": _series(
                bucket_rows,
                lambda a, b: _average(
                    [r["mood"] for r in rows if _in(r["local_date"], a, b)]
                ),
            )
        },
    }


def _adherence(task, dates, schedule, first, last, today):
    """Shared calculation over [first, last], except that today, which isn't
    over yet, counts only once the task is done today (otherwise a partial
    period would read as missed)."""
    if last < today or today in dates:
        return expected_and_done(task, dates, schedule, first, last)
    return expected_and_done(task, dates, schedule, first, today - timedelta(1))


def _empty_plan_section(bucket_rows):
    return {
        "has_plan": False,
        "adherence": None,
        "completions": 0,
        "average_difficulty": None,
        "completion_notes": 0,
        "goals_achieved": 0,
        "goals_dropped": 0,
        "legacy_items_excluded": 0,
        "goals": [],
        "series": {"adherence": _series(bucket_rows, lambda a, b: None)},
    }


def care_plan_section(*, rel, start, end, today, bucket_rows):
    """Adherence over [start, end] with the shared calculation. Titles are the
    psychologist's own; completion notes are counted, never returned."""
    plan = plan_for_pair(patient=rel.patient, psychologist=rel.psychologist)
    if plan is None:
        return _empty_plan_section(bucket_rows)
    profile = rel.patient
    goals = list(plan.goals.prefetch_related("tasks"))
    task_ids = [task.pk for goal in goals for task in goal.tasks.all()]
    dates_by_task = {}
    difficulties, notes = [], 0
    completions = TaskCompletion.objects.filter(
        task_id__in=task_ids, local_date__gte=start, local_date__lte=end
    ).values_list("task_id", "local_date", "difficulty", "note")
    for task_id, day, difficulty, note in completions:
        dates_by_task.setdefault(task_id, []).append(day)
        if difficulty is not None:
            difficulties.append(difficulty)
        if note:
            notes += 1

    scheduled = []  # (task, schedule) of every recurring task that counts
    legacy = 0
    goal_rows = []
    for goal in goals:
        g_expected = g_done = 0.0
        task_rows = []
        for task in goal.tasks.all():
            if local_date_of(task.created_at, profile) > end:
                continue
            dates = dates_by_task.get(task.pk, [])
            row = {
                "id": task.pk,
                "title": task.title,
                "frequency": task.frequency,
                "times_per_week": task.times_per_week,
                "status": task.status,
                "completions": len(dates),
                "adherence": None,
                "done_in_period": bool(dates)
                if task.frequency == TaskFrequency.ONCE
                else None,
            }
            schedule = history_range(task, goal, profile, today)
            if schedule is None and task.frequency != TaskFrequency.ONCE:
                legacy += 1
            if schedule is not None:
                e, d = _adherence(task, dates, schedule, start, end, today)
                row["adherence"] = percent(e, d)
                g_expected += e
                g_done += d
                scheduled.append((task, schedule))
            task_rows.append(row)
        # A goal shows if it existed by the period's end or has a task that did
        # (each task's own schedule decides what counts).
        if not task_rows and local_date_of(goal.created_at, profile) > end:
            continue
        goal_rows.append(
            {
                "id": goal.pk,
                "title": goal.title,
                "category": goal.category,
                "status": goal.status,
                "adherence": percent(g_expected, g_done),
                "tasks": task_rows,
            }
        )

    def plan_adherence(a, b):
        expected = done = 0.0
        for task, schedule in scheduled:
            e, d = _adherence(
                task, dates_by_task.get(task.pk, []), schedule, a, b, today
            )
            expected += e
            done += d
        return percent(expected, done)

    def closed_in_period(status):
        return sum(
            1
            for goal in goals
            if goal.status == status
            and goal.closed_at is not None
            and _in(local_date_of(goal.closed_at, profile), start, end)
        )

    return {
        "has_plan": True,
        "adherence": plan_adherence(start, end),
        "completions": sum(len(v) for v in dates_by_task.values()),
        "average_difficulty": _average(difficulties),
        "completion_notes": notes,
        "goals_achieved": closed_in_period(GoalStatus.ACHIEVED),
        "goals_dropped": closed_in_period(GoalStatus.DROPPED),
        "legacy_items_excluded": legacy,
        "goals": goal_rows,
        "series": {"adherence": _series(bucket_rows, plan_adherence)},
    }


def sos_section(*, rel, start, end):
    """Count, dates and status only: never coordinates or contacts."""
    tz = patient_tz(rel.patient)
    lo, hi = _bounds(start, end, tz)
    rows = (
        SOSEvent.objects.filter(
            patient=rel.patient, created_at__gte=lo, created_at__lt=hi
        )
        .order_by("created_at")
        .values("created_at", "status")
    )
    alerts = [
        {"date": row["created_at"].astimezone(tz).date(), "status": row["status"]}
        for row in rows
    ]
    return {"count": len(alerts), "alerts": alerts}


# --- comparison and indicators --------------------------------------------------


def headline(report):
    return {
        "attendance_rate": report["sessions"]["attendance_rate"],
        "average_mood": report["mood"]["average_mood"],
        "adherence": report["care_plan"]["adherence"],
        "average_progress_rating": report["therapy_notes"]["progress"]["average"],
    }


def comparison(current, previous):
    def delta(a, b):
        if a is None or b is None:
            return None
        return round(a - b, 2)

    return {
        key: {
            "current": value,
            "previous": previous.get(key) if previous else None,
            "change": delta(value, previous.get(key)) if previous else None,
        }
        for key, value in current.items()
    }


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _direction(change):
    return "rose" if change > 0 else "fell"


def indicators(report):
    """Factual statements about the numbers. No clinical threshold is applied:
    any change is reported, and the psychologist judges what it means."""
    found = []
    notes = report["therapy_notes"]
    risk = notes["risk"]
    if risk["first"] and risk["latest"] and risk["first"] != risk["latest"]:
        found.append(
            (
                "risk_level_changed",
                f"Risk level went from {risk['first']} to {risk['latest']}.",
            )
        )
    if risk["latest"] == RiskLevel.HIGH:
        found.append(
            (
                "latest_risk_high",
                "The latest note in this period records a high risk level.",
            )
        )
    labels = {
        "average_mood": ("Average mood", ""),
        "average_progress_rating": ("Average progress rating", ""),
        "adherence": ("Care plan adherence", "%"),
        "attendance_rate": ("Attendance", "%"),
    }
    for key, (label, unit) in labels.items():
        row = report["comparison"][key]
        if row["change"]:
            amount = abs(row["change"])
            amount = f"{amount:g} percentage points" if unit else f"{amount:g}"
            found.append(
                (
                    f"{key}_changed",
                    f"{label} {_direction(row['change'])} by {amount} "
                    f"({row['previous']:g}{unit} to {row['current']:g}{unit}).",
                )
            )
    sessions = report["sessions"]
    if sessions["no_show"]:
        found.append(("no_shows", f"{_plural(sessions['no_show'], 'no-show')}."))
    late = sessions["cancelled_by_patient"]["late"]
    if late:
        found.append(
            (
                "late_cancellations",
                f"{_plural(late, 'late cancellation')} by the patient.",
            )
        )
    if report["sos"]["count"]:
        found.append(
            (
                "sos_alerts",
                f"{_plural(report['sos']['count'], 'SOS alert')} in this period.",
            )
        )
    if not report["mood"]["check_ins"]:
        found.append(("no_check_ins", "No mood check-ins in this period."))
    if not notes["count"]:
        found.append(("no_notes", "No therapy notes in this period."))
    return [{"code": code, "message": message} for code, message in found]


# --- the report -----------------------------------------------------------------


def sections(*, rel, start, end, today, now, with_series=True):
    granularity, bucket_rows = buckets(start, end)
    if not with_series:
        bucket_rows = []
    return granularity, {
        "sessions": sessions_section(
            rel=rel, start=start, end=end, bucket_rows=bucket_rows, now=now
        ),
        "therapy_notes": notes_section(
            rel=rel, start=start, end=end, bucket_rows=bucket_rows
        ),
        "mood": mood_section(rel=rel, start=start, end=end, bucket_rows=bucket_rows),
        "care_plan": care_plan_section(
            rel=rel, start=start, end=end, today=today, bucket_rows=bucket_rows
        ),
        "sos": sos_section(rel=rel, start=start, end=end),
        "sensors": {"available": False},
    }


def build_report(*, rel, period, viewer, now=None):
    """`period` comes from services.resolve_period(). Calculated, never stored."""
    from apps.patients.selectors import get_patient_display_identity

    now = now or timezone.now()
    today = period["today"]
    granularity, report = sections(
        rel=rel,
        start=period["data_start"],
        end=period["data_end"],
        today=today,
        now=now,
    )
    previous = period["previous"]
    previous_headline = None
    if previous is not None:
        _, previous_report = sections(
            rel=rel,
            start=previous["data_start"],
            end=previous["data_end"],
            today=today,
            now=now,
            with_series=False,
        )
        previous_headline = headline(previous_report)
    report["comparison"] = comparison(headline(report), previous_headline)
    identity = get_patient_display_identity(patient_profile=rel.patient, viewer=viewer)
    return {
        "generated_at": now,
        "relationship_id": rel.pk,
        "patient": {"display_name": identity["display_name"]},
        "period": {
            "type": period["type"],
            "start": period["start"],
            "end": period["end"],
            "data_start": period["data_start"],
            "data_end": period["data_end"],
            "days": (period["data_end"] - period["data_start"]).days + 1,
            "is_partial": period["is_partial"],
            "clipped_to_care_start": period["clipped_to_care_start"],
            "care_started_on": period["care_started_on"],
            "timezone": str(patient_tz(rel.patient)),
            "granularity": granularity,
        },
        "previous_period": None
        if previous is None
        else {"start": previous["data_start"], "end": previous["data_end"]},
        **report,
        "indicators": indicators(report),
    }
