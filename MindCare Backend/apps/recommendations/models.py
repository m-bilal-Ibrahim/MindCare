"""Database models for the recommendations app: the care plan (docs/decisions.md,
2026-11-19, care plan Q1-Q18).

A care plan is written by the psychologist, never by AI: AI drafts and their
approval workflow (stored triple, separate training consent, age gate) come
with Phase 6 and will feed into this same plan only after approval.

- One plan per patient-psychologist PAIR, so a returning patient keeps it.
- Plan -> goals -> tasks. The patient logs completions per local day.
- Titles, descriptions, instructions, completion notes and every stored
  version are encrypted. Status, category, frequency, dates and the difficulty
  rating stay readable so adherence can be calculated.
- Nothing is hard-deleted through the app: goals are dropped, tasks archived.
  Plans PROTECT the profiles (erasure anonymises, 2026-10-06). The models aren't
  registered in Django admin: admins never see plans.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.encryption import EncryptedFreeTextField, EncryptedTextField
from core.models import ValidatedModelMixin
from core.validators import whole_number_message

TITLE_MIN, TITLE_MAX = 3, 120
DESCRIPTION_MIN, DESCRIPTION_MAX = 10, 1000
COMPLETION_NOTE_MIN, COMPLETION_NOTE_MAX = 10, 500
DIFFICULTY_MIN, DIFFICULTY_MAX = 1, 5
TIMES_PER_WEEK_MIN, TIMES_PER_WEEK_MAX = 1, 7
DIFFICULTY_MESSAGE = whole_number_message("Difficulty", DIFFICULTY_MIN, DIFFICULTY_MAX)
TIMES_PER_WEEK_MESSAGE = whole_number_message(
    "Times per week", TIMES_PER_WEEK_MIN, TIMES_PER_WEEK_MAX
)
MAX_ACTIVE_GOALS = 10
MAX_ACTIVE_TASKS_PER_GOAL = 10
MAX_ACTIVE_TASKS = 30


class GoalCategory(models.TextChoices):
    EXERCISE = "exercise", "Exercise"
    SLEEP = "sleep", "Sleep"
    DIET = "diet", "Diet"
    MINDFULNESS = "mindfulness", "Mindfulness"
    SOCIAL = "social", "Social"
    THERAPY_HOMEWORK = "therapy_homework", "Therapy homework"
    OTHER = "other", "Other"


class GoalStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ACHIEVED = "achieved", "Achieved"
    DROPPED = "dropped", "Dropped"


class TaskFrequency(models.TextChoices):
    ONCE = "once", "Once"
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"


class TaskStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


def _title():
    return EncryptedFreeTextField(
        label="Title", min_length=TITLE_MIN, rule_max_length=TITLE_MAX
    )


class CarePlan(models.Model):
    patient = models.ForeignKey(
        "patients.PatientProfile", on_delete=models.PROTECT, related_name="care_plans"
    )
    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.PROTECT,
        related_name="care_plans",
    )
    # Bumped on every psychologist change; each value has a CarePlanVersion.
    version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "psychologist"],
                name="recommendations_one_care_plan_per_pair",
            )
        ]

    def __str__(self):
        return f"Care plan #{self.pk}"


class CarePlanGoal(ValidatedModelMixin, models.Model):
    plan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="goals")
    title = _title()
    description = EncryptedFreeTextField(
        label="Description",
        min_length=DESCRIPTION_MIN,
        rule_max_length=DESCRIPTION_MAX,
        blank=True,
        default="",
    )
    category = models.CharField(max_length=20, choices=GoalCategory.choices)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=GoalStatus.choices, default=GoalStatus.ACTIVE
    )
    # When the goal was last marked achieved or dropped; cleared when it is made
    # active again. Reports use it for adherence in past periods (6.14). Goals
    # closed before 2026-11-23 have none and are left out of report adherence.
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Goal #{self.pk}"


class CarePlanTask(ValidatedModelMixin, models.Model):
    goal = models.ForeignKey(
        CarePlanGoal, on_delete=models.CASCADE, related_name="tasks"
    )
    title = _title()
    instructions = EncryptedFreeTextField(
        label="Instructions",
        min_length=DESCRIPTION_MIN,
        rule_max_length=DESCRIPTION_MAX,
        blank=True,
        default="",
    )
    frequency = models.CharField(max_length=10, choices=TaskFrequency.choices)
    # Only for weekly tasks: how many days a week.
    times_per_week = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(TIMES_PER_WEEK_MIN, message=TIMES_PER_WEEK_MESSAGE),
            MaxValueValidator(TIMES_PER_WEEK_MAX, message=TIMES_PER_WEEK_MESSAGE),
        ],
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=TaskStatus.choices, default=TaskStatus.ACTIVE
    )
    # When the task was last archived; cleared when it is made active again.
    # Reports treat the task as scheduled until then (6.14). Tasks archived
    # before 2026-11-23 have none and are left out of report adherence.
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Task #{self.pk}"


class TaskCompletion(ValidatedModelMixin, models.Model):
    """The patient marked a task done for one of their local days."""

    task = models.ForeignKey(
        CarePlanTask, on_delete=models.CASCADE, related_name="completions"
    )
    local_date = models.DateField()
    # Written for the plan: the current psychologist reads it (audited).
    note = EncryptedFreeTextField(
        label="Note",
        min_length=COMPLETION_NOTE_MIN,
        rule_max_length=COMPLETION_NOTE_MAX,
        blank=True,
        default="",
    )
    difficulty = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(DIFFICULTY_MIN, message=DIFFICULTY_MESSAGE),
            MaxValueValidator(DIFFICULTY_MAX, message=DIFFICULTY_MESSAGE),
        ],
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-local_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "local_date"],
                name="recommendations_one_completion_per_task_day",
            )
        ]

    def __str__(self):
        return f"Completion #{self.pk} ({self.local_date})"


class CarePlanVersion(models.Model):
    """A full snapshot of the plan's goals and tasks after a psychologist change."""

    plan = models.ForeignKey(
        CarePlan, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    # JSON of every goal and task, encrypted as one value.
    content = EncryptedTextField()
    saved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "version"],
                name="recommendations_unique_plan_version",
            )
        ]

    def __str__(self):
        return f"Care plan #{self.plan_id} v{self.version}"
