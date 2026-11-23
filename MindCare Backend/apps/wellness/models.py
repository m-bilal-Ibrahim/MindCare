"""Wellness content library (6.9; docs/decisions.md, 2026-11-23).

Admin-managed, general wellbeing content: articles, guided practices and
routines across nutrition, exercise, yoga, stress reduction, mindfulness,
relaxation and sleep. It is not personal data and not health data, so nothing
here is encrypted or audited; reading it needs no ownership check.

- New items start hidden (is_published=False) until an admin publishes them.
- A psychologist can link one published item to a care-plan task
  (CarePlanTask.content). Once an item has ever been linked, it can't be
  deleted, only hidden (ever_linked), so plan history keeps its references.
- Personalised and AI suggestions are out of scope (6.6 / 6.5).
- The seeded items are PLACEHOLDER content that a clinical advisor must review
  before launch; they are seeded hidden.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.fields import FreeTextField, HttpsUrlField
from core.models import ValidatedModelMixin
from core.validators import (
    FreeTextValidator,
    normalize_single_line,
    whole_number_message,
)

TITLE_MIN, TITLE_MAX = 3, 120
SUMMARY_MIN, SUMMARY_MAX = 10, 300
BODY_MIN, BODY_MAX = 30, 20000
STEP_MIN, STEP_MAX = 3, 500
MAX_STEPS = 20
SAFETY_MIN, SAFETY_MAX = 10, 500
SOURCE_MIN, SOURCE_MAX = 3, 200
DURATION_MIN, DURATION_MAX = 1, 180
BREATH_MAX = 20
SORT_MAX = 32767
MAX_FAVOURITES = 200
VIDEO_DOMAINS = ["youtube.com", "youtu.be", "vimeo.com"]

DURATION_MESSAGE = whole_number_message("Duration", DURATION_MIN, DURATION_MAX)
SORT_MESSAGE = whole_number_message("Sort order", 0, SORT_MAX)
TOO_MANY_STEPS = f"Add at most {MAX_STEPS} steps."
STEP_NOT_TEXT = "Each step must be text."
BODY_REQUIRED = "Write the article text."
STEPS_REQUIRED = "Add at least one step."
BREATHING_ONLY_PRACTICE = "A breathing pattern is only for practices."
BREATHING_ALL_OR_NONE = "Set all four breathing times, or none."


class WellnessKind(models.TextChoices):
    ARTICLE = "article", "Article"
    PRACTICE = "practice", "Practice"
    ROUTINE = "routine", "Routine"


class WellnessCategory(models.TextChoices):
    NUTRITION = "nutrition", "Nutrition"
    EXERCISE = "exercise", "Exercise"
    YOGA = "yoga", "Yoga"
    STRESS_REDUCTION = "stress_reduction", "Stress reduction"
    MINDFULNESS = "mindfulness", "Mindfulness"
    RELAXATION = "relaxation", "Relaxation"
    SLEEP = "sleep", "Sleep"


class Difficulty(models.TextChoices):
    GENTLE = "gentle", "Gentle"
    MODERATE = "moderate", "Moderate"
    DEMANDING = "demanding", "Demanding"


STEP_VALIDATOR = FreeTextValidator("Step", STEP_MIN, STEP_MAX)


def normalise_steps(value):
    if isinstance(value, list):
        return [normalize_single_line(s) if isinstance(s, str) else s for s in value]
    return value


def validate_steps(value):
    if not isinstance(value, list):
        raise ValidationError(STEP_NOT_TEXT)
    if len(value) > MAX_STEPS:
        raise ValidationError(TOO_MANY_STEPS)
    for step in value:
        if not isinstance(step, str):
            raise ValidationError(STEP_NOT_TEXT)
        STEP_VALIDATOR(step)


class StepsField(models.JSONField):
    """An ordered list of short, single-line steps (free-text rule 3-500)."""

    def to_python(self, value):
        return normalise_steps(super().to_python(value))


def _breath(label, minimum):
    message = whole_number_message(label, minimum, BREATH_MAX)
    return models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(minimum, message=message),
            MaxValueValidator(BREATH_MAX, message=message),
        ],
    )


BREATH_FIELDS = (
    "breath_in_seconds",
    "breath_hold_seconds",
    "breath_out_seconds",
    "breath_hold_after_out_seconds",
)


class WellnessItem(ValidatedModelMixin, models.Model):
    kind = models.CharField(max_length=10, choices=WellnessKind.choices)
    category = models.CharField(max_length=20, choices=WellnessCategory.choices)
    title = FreeTextField(
        label="Title", min_length=TITLE_MIN, rule_max_length=TITLE_MAX
    )
    summary = FreeTextField(
        label="Summary", min_length=SUMMARY_MIN, rule_max_length=SUMMARY_MAX
    )
    # Required for articles; optional for practices and routines.
    body = FreeTextField(
        label="Body",
        min_length=BODY_MIN,
        rule_max_length=BODY_MAX,
        blank=True,
        default="",
    )
    # Required (at least one) for practices and routines.
    steps = StepsField(default=list, blank=True, validators=[validate_steps])
    duration_minutes = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(DURATION_MIN, message=DURATION_MESSAGE),
            MaxValueValidator(DURATION_MAX, message=DURATION_MESSAGE),
        ]
    )
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.GENTLE
    )
    safety_note = FreeTextField(
        label="Safety note",
        min_length=SAFETY_MIN,
        rule_max_length=SAFETY_MAX,
        blank=True,
        default="",
    )
    source = FreeTextField(
        label="Source",
        min_length=SOURCE_MIN,
        rule_max_length=SOURCE_MAX,
        blank=True,
        default="",
    )
    video_url = HttpsUrlField(
        label="Video link", allowed_domains=VIDEO_DOMAINS, blank=True, default=""
    )
    # Optional breathing pattern for practices (the App's breathing player):
    # all four or none. Seconds per phase.
    breath_in_seconds = _breath("Breath in", 1)
    breath_hold_seconds = _breath("Hold", 0)
    breath_out_seconds = _breath("Breath out", 1)
    breath_hold_after_out_seconds = _breath("Hold after breathing out", 0)
    # Private storage keys ("" = none) and detected types.
    image_key = models.CharField(max_length=255, blank=True, default="")
    image_type = models.CharField(max_length=10, blank=True, default="")
    audio_key = models.CharField(max_length=255, blank=True, default="")
    audio_type = models.CharField(max_length=10, blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(SORT_MAX, message=SORT_MESSAGE)],
    )
    is_published = models.BooleanField(
        default=False,
        help_text="New items stay hidden until an admin publishes them.",
    )
    # Set the first time a care-plan task links to the item; it can then only
    # be hidden, never deleted.
    ever_linked = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at", "-id"]
        indexes = [models.Index(fields=["is_published", "category", "kind"])]

    def __str__(self):
        return self.title[:60]

    def clean(self):
        errors = {}
        if self.kind == WellnessKind.ARTICLE and not self.body:
            errors["body"] = [BODY_REQUIRED]
        if self.kind in (WellnessKind.PRACTICE, WellnessKind.ROUTINE) and not (
            self.steps
        ):
            errors["steps"] = [STEPS_REQUIRED]
        breaths = [getattr(self, f) for f in BREATH_FIELDS]
        if any(b is not None for b in breaths):
            if self.kind != WellnessKind.PRACTICE:
                errors["breath_in_seconds"] = [BREATHING_ONLY_PRACTICE]
            elif any(b is None for b in breaths):
                errors["breath_in_seconds"] = [BREATHING_ALL_OR_NONE]
        if errors:
            raise ValidationError(errors)


class WellnessFavourite(models.Model):
    """A patient saved an item. Private to the patient: never shown to the
    psychologist or admins, not audited (no health data)."""

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="wellness_favourites",
    )
    item = models.ForeignKey(
        WellnessItem, on_delete=models.CASCADE, related_name="favourites"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "item"], name="wellness_one_favourite_per_item"
            )
        ]
