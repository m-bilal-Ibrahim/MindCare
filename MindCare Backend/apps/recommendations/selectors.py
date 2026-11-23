"""Read-path query logic for the care plan (docs/decisions.md, 2026-11-19).

Who may open a plan:
- the patient: always (read-only once care with that psychologist has ended, or
  while the psychologist is paused);
- the psychologist: only while they are the patient's CURRENT assigned
  psychologist; the services resolve that through the relationship id.
Admins never see plans.

Adherence (calculated, not AI) per task, goal and plan over the last 7, 30 and
90 local days of the patient, today included:
- a task's scheduled range runs from its start date (or the day it was added,
  whichever is later) to its end date (or today);
- daily: one expected completion per scheduled day; weekly N: N per 7 days;
- completions above the expected number don't count extra;
- one-off tasks and archived tasks are left out of the percentages (one-off
  tasks report `is_done` instead); goals that are achieved or dropped are left
  out of the plan's total.

Reports (6.14) reuse `expected_and_done()` over past periods with
`history_range()`, which counts archived tasks and closed goals up to when
they were archived or closed.
"""

from datetime import timedelta
from zoneinfo import ZoneInfo

from apps.journals.selectors import DEFAULT_TZ, patient_today
from apps.recommendations.models import (
    CarePlan,
    GoalStatus,
    TaskCompletion,
    TaskFrequency,
    TaskStatus,
)
from apps.wellness.selectors import content_summary

WINDOWS = (7, 30, 90)


class NotFound(Exception):
    pass


def local_date_of(dt, patient_profile):
    try:
        tz = ZoneInfo(patient_profile.timezone or DEFAULT_TZ)
    except (ValueError, KeyError):
        tz = ZoneInfo(DEFAULT_TZ)
    return dt.astimezone(tz).date()


def plan_for_pair(*, patient, psychologist):
    return CarePlan.objects.filter(patient=patient, psychologist=psychologist).first()


def can_track(*, plan):
    """The patient can log completions only while this plan's psychologist is
    their current, approved and active psychologist."""
    from apps.relationships.selectors import get_active_relationship

    rel = get_active_relationship(patient=plan.patient)
    return rel is not None and rel.psychologist_id == plan.psychologist_id


def patient_plans(*, patient_profile):
    return CarePlan.objects.filter(patient=patient_profile).select_related(
        "psychologist__user", "patient"
    )


def patient_plan(*, patient_profile, plan_id):
    plan = patient_plans(patient_profile=patient_profile).filter(pk=plan_id).first()
    if plan is None:
        raise NotFound()
    return plan


def task_range(task, patient_profile, today):
    """(first, last) scheduled local day of a task, up to today."""
    created = local_date_of(task.created_at, patient_profile)
    start = max(task.start_date or created, created)
    end = min(task.end_date or today, today)
    return start, end


def history_range(task, goal, patient_profile, today):
    """(first, last) scheduled local day of a recurring task for reports over
    past periods (6.14), or None if it never counts. Unlike the live plan view,
    an archived task counts until the day before it was archived, and a task of
    an achieved or dropped goal until the day before the goal closed. Archived
    tasks and closed goals without a timestamp (from before 2026-11-23) are
    left out."""
    if task.frequency == TaskFrequency.ONCE:
        return None
    start, end = task_range(task, patient_profile, today)
    if task.status == TaskStatus.ARCHIVED:
        if task.archived_at is None:
            return None
        end = min(end, local_date_of(task.archived_at, patient_profile) - timedelta(1))
    if goal.status != GoalStatus.ACTIVE:
        if goal.closed_at is None:
            return None
        end = min(end, local_date_of(goal.closed_at, patient_profile) - timedelta(1))
    return start, end


def expected_and_done(task, dates, scheduled, window_start, window_end):
    """(expected, done) for one recurring task whose schedule is `scheduled`
    (first, last), inside the window [window_start, window_end]. The one
    adherence calculation, shared by the care plan and reports."""
    start = max(scheduled[0], window_start)
    end = min(scheduled[1], window_end)
    days = (end - start).days + 1
    if days <= 0:
        return 0.0, 0.0
    if task.frequency == TaskFrequency.DAILY:
        expected = float(days)
    else:
        expected = days * (task.times_per_week or 1) / 7
    done = sum(1 for d in dates if start <= d <= end)
    return expected, min(float(done), expected)


def _expected_and_done(task, dates, patient_profile, today, window_start):
    """(expected, done) for one recurring task in a window ending today."""
    scheduled = task_range(task, patient_profile, today)
    return expected_and_done(task, dates, scheduled, window_start, today)


def percent(expected, done):
    return round(100 * done / expected) if expected > 0 else None


def _counts_toward_adherence(task):
    return task.status == TaskStatus.ACTIVE and task.frequency != TaskFrequency.ONCE


def _windows(tasks, dates_by_task, patient_profile, today):
    result = {}
    for days in WINDOWS:
        window_start = today - timedelta(days=days - 1)
        expected = done = 0.0
        for task in tasks:
            if not _counts_toward_adherence(task):
                continue
            e, d = _expected_and_done(
                task,
                dates_by_task.get(task.pk, []),
                patient_profile,
                today,
                window_start,
            )
            expected += e
            done += d
        result[str(days)] = percent(expected, done)
    return result


def _task_data(task, dates, patient_profile, today):
    adherence = (
        _windows([task], {task.pk: dates}, patient_profile, today)
        if _counts_toward_adherence(task)
        else {str(days): None for days in WINDOWS}
    )
    return {
        "id": task.pk,
        "title": task.title,
        "instructions": task.instructions,
        "frequency": task.frequency,
        "times_per_week": task.times_per_week,
        "start_date": task.start_date,
        "end_date": task.end_date,
        "status": task.status,
        "content": content_summary(task.content),
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "done_today": today in dates,
        "last_completed_on": max(dates) if dates else None,
        "is_done": bool(dates) if task.frequency == TaskFrequency.ONCE else None,
        "adherence": adherence,
    }


def empty_plan(*, patient_profile):
    return {
        "id": None,
        "version": 0,
        "created_at": None,
        "updated_at": None,
        "can_track": False,
        "today": patient_today(patient_profile),
        "psychologist": None,
        "adherence": {str(days): None for days in WINDOWS},
        "goals": [],
    }


def plan_detail(*, plan):
    """The whole plan with adherence. Titles and instructions only; completion
    notes are listed separately."""
    profile = plan.patient
    today = patient_today(profile)
    goals = list(plan.goals.prefetch_related("tasks__content"))
    task_ids = [task.pk for goal in goals for task in goal.tasks.all()]
    dates_by_task = {}
    for task_id, local_date in TaskCompletion.objects.filter(
        task_id__in=task_ids
    ).values_list("task_id", "local_date"):
        dates_by_task.setdefault(task_id, []).append(local_date)

    goal_rows = []
    plan_tasks = []
    for goal in goals:
        tasks = list(goal.tasks.all())
        if goal.status == GoalStatus.ACTIVE:
            plan_tasks.extend(tasks)
        goal_rows.append(
            {
                "id": goal.pk,
                "title": goal.title,
                "description": goal.description,
                "category": goal.category,
                "target_date": goal.target_date,
                "status": goal.status,
                "created_at": goal.created_at,
                "updated_at": goal.updated_at,
                "adherence": _windows(tasks, dates_by_task, profile, today),
                "tasks": [
                    _task_data(task, dates_by_task.get(task.pk, []), profile, today)
                    for task in tasks
                ],
            }
        )
    psych = plan.psychologist
    return {
        "id": plan.pk,
        "version": plan.version,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "can_track": can_track(plan=plan),
        "today": today,
        "psychologist": {"id": psych.pk, "name": psych.user.full_name},
        "adherence": _windows(plan_tasks, dates_by_task, profile, today),
        "goals": goal_rows,
    }


def plan_summary(*, plan):
    """What the patient's plan list shows."""
    psych = plan.psychologist
    return {
        "id": plan.pk,
        "psychologist": {"id": psych.pk, "name": psych.user.full_name},
        "can_track": can_track(plan=plan),
        "active_goals": plan.goals.filter(status=GoalStatus.ACTIVE).count(),
        "updated_at": plan.updated_at,
    }


def completions_for_plan(*, plan, days):
    """Completions in the last `days` local days of the patient, newest first,
    notes included."""
    today = patient_today(plan.patient)
    return (
        TaskCompletion.objects.filter(
            task__goal__plan=plan, local_date__gte=today - timedelta(days=days - 1)
        )
        .select_related("task")
        .order_by("-local_date", "-id")
    )


def versions_for_plan(*, plan):
    return plan.versions.all()
