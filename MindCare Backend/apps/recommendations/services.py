"""Write-path (and audited read-path) logic for the care plan (docs/decisions.md,
2026-11-19).

- Only the CURRENT assigned psychologist (accepted relationship, approved and
  active) reads or changes a patient's plan, by relationship id. The plan
  belongs to the pair, so a returning patient keeps it.
- Every psychologist change bumps the plan version and stores an encrypted
  snapshot; completed history is never changed. Nothing is hard-deleted.
- The patient logs completions for today or yesterday (their timezone) while
  the plan's psychologist is their current one; undo only on the day it was
  logged.
- Every psychologist read and every write is audited in the same transaction
  (fail closed). The patient's own reads aren't.
- The patient gets a content-free "care plan updated" notification.
- Content is psychologist-written only: no AI output enters a plan here.
"""

import json
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.journals.selectors import patient_today
from apps.notifications.models import NotificationType
from apps.notifications.services import notify
from apps.recommendations import selectors
from apps.recommendations.models import (
    MAX_ACTIVE_GOALS,
    MAX_ACTIVE_TASKS,
    MAX_ACTIVE_TASKS_PER_GOAL,
    CarePlan,
    CarePlanGoal,
    CarePlanTask,
    CarePlanVersion,
    GoalStatus,
    TaskCompletion,
    TaskFrequency,
    TaskStatus,
)
from core.exceptions import DomainValidationError

NotFound = selectors.NotFound

DATE_WINDOW_DAYS = 365
TARGET_DATE_RANGE = "Target date must be between today and one year from now."
TASK_DATE_RANGE = "Dates must be between today and one year from now."
END_BEFORE_START = "End date can't be before the start date."
WEEKLY_NEEDS_TIMES = "Choose how many times a week (1 to 7)."
TIMES_ONLY_WEEKLY = "Times per week is only for weekly tasks."
TOO_MANY_GOALS = f"A care plan can have at most {MAX_ACTIVE_GOALS} active goals."
TOO_MANY_GOAL_TASKS = (
    f"A goal can have at most {MAX_ACTIVE_TASKS_PER_GOAL} active tasks."
)
TOO_MANY_TASKS = f"A care plan can have at most {MAX_ACTIVE_TASKS} active tasks."
GOAL_NOT_ACTIVE = "You can only add tasks to an active goal."
READ_ONLY = (
    "This care plan is read-only because care with this psychologist has ended "
    "or is paused."
)
COMPLETION_DAY = "You can mark a task done for today or yesterday only."
TASK_NOT_ACTIVE = "This task isn't active any more."
NOT_SCHEDULED = "This task isn't scheduled for that day."
ALREADY_DONE = "You've already marked this task done for that day."
ONCE_DONE = "This one-off task is already done."
UNDO_TOO_LATE = "You can only undo a completion on the day you marked it."

GOAL_FIELDS = ("title", "description", "category", "target_date", "status")
TASK_FIELDS = (
    "title",
    "instructions",
    "frequency",
    "times_per_week",
    "start_date",
    "end_date",
    "status",
)
BLANKABLE = ("description", "instructions")


class NotYourPatient(Exception):
    pass


class Forbidden(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


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


def _audit(actor, action, resource, resource_id, patient_user_id, ip):
    record_access(
        actor=actor,
        action=action,
        resource_type=resource,
        resource_id=resource_id,
        patient_user_id=patient_user_id,
        ip=ip,
    )


def _plan(rel, *, create=False):
    """The pair's plan, row-locked. Created when `create` (first goal)."""
    qs = CarePlan.objects.select_for_update().filter(
        patient=rel.patient, psychologist=rel.psychologist
    )
    plan = qs.first()
    if plan is None and create:
        try:
            with transaction.atomic():
                CarePlan.objects.create(
                    patient=rel.patient, psychologist=rel.psychologist
                )
        except IntegrityError:
            pass  # created by a parallel request
        plan = qs.first()
    if plan is None:
        raise NotFound()
    return plan


def _snapshot(plan):
    goals = []
    for goal in plan.goals.prefetch_related("tasks"):
        goals.append(
            {
                "id": goal.pk,
                "title": goal.title,
                "description": goal.description,
                "category": goal.category,
                "target_date": goal.target_date and goal.target_date.isoformat(),
                "status": goal.status,
                "tasks": [
                    {
                        "id": task.pk,
                        "title": task.title,
                        "instructions": task.instructions,
                        "frequency": task.frequency,
                        "times_per_week": task.times_per_week,
                        "start_date": task.start_date and task.start_date.isoformat(),
                        "end_date": task.end_date and task.end_date.isoformat(),
                        "status": task.status,
                    }
                    for task in goal.tasks.all()
                ],
            }
        )
    return json.dumps({"goals": goals})


def _changed(plan, psychologist_user, action, resource_id, ip):
    """After every psychologist change: new version + snapshot, audit row and
    the patient's notification, all in the caller's transaction."""
    now = timezone.now()
    plan.version += 1
    plan.updated_at = now
    plan.save(update_fields=["version", "updated_at"])
    CarePlanVersion.objects.create(
        plan=plan, version=plan.version, content=_snapshot(plan), saved_at=now
    )
    _audit(
        psychologist_user,
        action,
        AuditResource.CARE_PLAN,
        resource_id,
        plan.patient.user_id,
        ip,
    )
    notify(
        recipients=[plan.patient.user_id],
        type=NotificationType.CARE_PLAN_UPDATED,
        target_id=plan.pk,
    )


def _check_future_date(value, today, field, message):
    if value is not None and not (
        today <= value <= today + timedelta(days=DATE_WINDOW_DAYS)
    ):
        raise _invalid(field, message)


def _active_task_count(plan):
    return CarePlanTask.objects.filter(
        goal__plan=plan, goal__status=GoalStatus.ACTIVE, status=TaskStatus.ACTIVE
    ).count()


# --- psychologist: reading -------------------------------------------------


def get_plan(*, psychologist_user, relationship_id, ip=None):
    """The plan with adherence (an empty plan if none yet). Audited."""
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        plan = selectors.plan_for_pair(
            patient=rel.patient, psychologist=rel.psychologist
        )
        data = (
            selectors.plan_detail(plan=plan)
            if plan
            else selectors.empty_plan(patient_profile=rel.patient)
        )
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.CARE_PLAN,
            plan.pk if plan else "",
            rel.patient.user_id,
            ip,
        )
    return data


def list_completions(*, psychologist_user, relationship_id, days, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        plan = selectors.plan_for_pair(
            patient=rel.patient, psychologist=rel.psychologist
        )
        rows = (
            list(selectors.completions_for_plan(plan=plan, days=days)) if plan else []
        )
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.CARE_PLAN_COMPLETION,
            plan.pk if plan else "",
            rel.patient.user_id,
            ip,
        )
    return rows


def list_versions(*, psychologist_user, relationship_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        plan = selectors.plan_for_pair(
            patient=rel.patient, psychologist=rel.psychologist
        )
        versions = (
            [
                {"version": v.version, "saved_at": v.saved_at, **json.loads(v.content)}
                for v in selectors.versions_for_plan(plan=plan)
            ]
            if plan
            else []
        )
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.CARE_PLAN,
            plan.pk if plan else "",
            rel.patient.user_id,
            ip,
        )
    return versions


# --- psychologist: goals -----------------------------------------------------


def create_goal(*, psychologist_user, relationship_id, ip=None, **fields):
    rel = _current(psychologist_user, relationship_id)
    today = patient_today(rel.patient)
    _check_future_date(
        fields.get("target_date"), today, "target_date", TARGET_DATE_RANGE
    )
    with transaction.atomic():
        plan = _plan(rel, create=True)
        if plan.goals.filter(status=GoalStatus.ACTIVE).count() >= MAX_ACTIVE_GOALS:
            raise _invalid("non_field_errors", TOO_MANY_GOALS)
        goal = CarePlanGoal.objects.create(
            plan=plan,
            **{
                f: fields[f]
                for f in GOAL_FIELDS
                if f in fields and f != "status" and fields[f] is not None
            },
        )
        _changed(plan, psychologist_user, AuditAction.CREATE, goal.pk, ip)
    return goal


def _goal(plan, goal_id):
    goal = (
        CarePlanGoal.objects.select_for_update().filter(pk=goal_id, plan=plan).first()
    )
    if goal is None:
        raise NotFound()
    return goal


def update_goal(*, psychologist_user, relationship_id, goal_id, ip=None, **changes):
    rel = _current(psychologist_user, relationship_id)
    today = patient_today(rel.patient)
    with transaction.atomic():
        plan = _plan(rel)
        goal = _goal(plan, goal_id)
        fields = [f for f in GOAL_FIELDS if f in changes]
        if not fields:
            return goal
        if "target_date" in changes and changes["target_date"] != goal.target_date:
            _check_future_date(
                changes["target_date"], today, "target_date", TARGET_DATE_RANGE
            )
        reactivating = (
            changes.get("status") == GoalStatus.ACTIVE
            and goal.status != GoalStatus.ACTIVE
        )
        if reactivating:
            if plan.goals.filter(status=GoalStatus.ACTIVE).count() >= MAX_ACTIVE_GOALS:
                raise _invalid("status", TOO_MANY_GOALS)
            own = goal.tasks.filter(status=TaskStatus.ACTIVE).count()
            if _active_task_count(plan) + own > MAX_ACTIVE_TASKS:
                raise _invalid("status", TOO_MANY_TASKS)
        for field in fields:
            value = changes[field]
            if field in BLANKABLE:
                value = value or ""
            setattr(goal, field, value)
        goal.save(update_fields=[*fields, "updated_at"])
        _changed(plan, psychologist_user, AuditAction.UPDATE, goal.pk, ip)
    return goal


# --- psychologist: tasks -----------------------------------------------------


def _check_task(task, today, changed):
    """Frequency and date rules on the task as it will be saved."""
    if task.frequency == TaskFrequency.WEEKLY and not task.times_per_week:
        raise _invalid("times_per_week", WEEKLY_NEEDS_TIMES)
    if task.frequency != TaskFrequency.WEEKLY and task.times_per_week:
        raise _invalid("times_per_week", TIMES_ONLY_WEEKLY)
    for field in ("start_date", "end_date"):
        if field in changed:
            _check_future_date(getattr(task, field), today, field, TASK_DATE_RANGE)
    if task.start_date and task.end_date and task.end_date < task.start_date:
        raise _invalid("end_date", END_BEFORE_START)


def _check_task_limits(plan, goal, field):
    if goal.tasks.filter(status=TaskStatus.ACTIVE).count() >= MAX_ACTIVE_TASKS_PER_GOAL:
        raise _invalid(field, TOO_MANY_GOAL_TASKS)
    if _active_task_count(plan) >= MAX_ACTIVE_TASKS:
        raise _invalid(field, TOO_MANY_TASKS)


def create_task(*, psychologist_user, relationship_id, goal_id, ip=None, **fields):
    rel = _current(psychologist_user, relationship_id)
    today = patient_today(rel.patient)
    with transaction.atomic():
        plan = _plan(rel)
        goal = _goal(plan, goal_id)
        if goal.status != GoalStatus.ACTIVE:
            raise _invalid("non_field_errors", GOAL_NOT_ACTIVE)
        _check_task_limits(plan, goal, "non_field_errors")
        task = CarePlanTask(
            goal=goal,
            **{
                f: fields[f]
                for f in TASK_FIELDS
                if f in fields and f != "status" and fields[f] is not None
            },
        )
        _check_task(task, today, changed=fields.keys())
        task.save()
        _changed(plan, psychologist_user, AuditAction.CREATE, task.pk, ip)
    return task


def update_task(*, psychologist_user, relationship_id, task_id, ip=None, **changes):
    rel = _current(psychologist_user, relationship_id)
    today = patient_today(rel.patient)
    with transaction.atomic():
        plan = _plan(rel)
        task = (
            CarePlanTask.objects.select_for_update()
            .select_related("goal")
            .filter(pk=task_id, goal__plan=plan)
            .first()
        )
        if task is None:
            raise NotFound()
        fields = [f for f in TASK_FIELDS if f in changes]
        if not fields:
            return task
        if (
            changes.get("status") == TaskStatus.ACTIVE
            and task.status != TaskStatus.ACTIVE
        ):
            if task.goal.status != GoalStatus.ACTIVE:
                raise _invalid("status", GOAL_NOT_ACTIVE)
            _check_task_limits(plan, task.goal, "status")
        changed = [
            f
            for f in fields
            if f in ("start_date", "end_date") and changes[f] != getattr(task, f)
        ]
        for field in fields:
            value = changes[field]
            if field in BLANKABLE:
                value = value or ""
            setattr(task, field, value)
        _check_task(task, today, changed=changed)
        task.save(update_fields=[*fields, "updated_at"])
        _changed(plan, psychologist_user, AuditAction.UPDATE, task.pk, ip)
    return task


# --- patient: tracking -------------------------------------------------------


def _patient_task(plan, task_id):
    task = (
        CarePlanTask.objects.select_for_update()
        .select_related("goal")
        .filter(pk=task_id, goal__plan=plan)
        .first()
    )
    if task is None:
        raise NotFound()
    return task


def log_completion(
    *,
    patient_profile,
    plan_id,
    task_id,
    local_date=None,
    note="",
    difficulty=None,
    ip=None,
):
    plan = selectors.patient_plan(patient_profile=patient_profile, plan_id=plan_id)
    if not selectors.can_track(plan=plan):
        raise Forbidden(READ_ONLY)
    today = patient_today(patient_profile)
    day = local_date or today
    if day not in (today, today - timedelta(days=1)):
        raise _invalid("local_date", COMPLETION_DAY)
    with transaction.atomic():
        task = _patient_task(plan, task_id)
        if task.status != TaskStatus.ACTIVE or task.goal.status != GoalStatus.ACTIVE:
            raise _invalid("non_field_errors", TASK_NOT_ACTIVE)
        start, _ = selectors.task_range(task, patient_profile, today)
        if day < start or (task.end_date and day > task.end_date):
            raise _invalid("local_date", NOT_SCHEDULED)
        if task.frequency == TaskFrequency.ONCE and task.completions.exists():
            raise _invalid("non_field_errors", ONCE_DONE)
        try:
            with transaction.atomic():
                completion = TaskCompletion.objects.create(
                    task=task,
                    local_date=day,
                    note=note or "",
                    difficulty=difficulty,
                )
        except IntegrityError as exc:  # one per task per day
            raise _invalid("non_field_errors", ALREADY_DONE) from exc
        _audit(
            patient_profile.user,
            AuditAction.CREATE,
            AuditResource.CARE_PLAN_COMPLETION,
            completion.pk,
            patient_profile.user_id,
            ip,
        )
    return completion


def undo_completion(*, patient_profile, plan_id, task_id, completion_id, ip=None):
    plan = selectors.patient_plan(patient_profile=patient_profile, plan_id=plan_id)
    if not selectors.can_track(plan=plan):
        raise Forbidden(READ_ONLY)
    today = patient_today(patient_profile)
    with transaction.atomic():
        completion = (
            TaskCompletion.objects.select_for_update()
            .filter(pk=completion_id, task_id=task_id, task__goal__plan=plan)
            .first()
        )
        if completion is None:
            raise NotFound()
        if selectors.local_date_of(completion.created_at, patient_profile) != today:
            raise _invalid("non_field_errors", UNDO_TOO_LATE)
        _audit(
            patient_profile.user,
            AuditAction.DELETE,
            AuditResource.CARE_PLAN_COMPLETION,
            completion.pk,
            patient_profile.user_id,
            ip,
        )
        completion.delete()
