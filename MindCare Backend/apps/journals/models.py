"""Database models for the journals app.

Phase 2 module 3: daily mood check-ins (docs/decisions.md, 2026-10-28). One per
patient per local day (the patient's timezone). The mood and tags stay readable
so insights can be calculated; the optional note is encrypted at rest, private
to the patient, and never shown to the psychologist.
"""

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.encryption import EncryptedFreeTextField
from core.models import ValidatedModelMixin

MOOD_MIN, MOOD_MAX = 1, 5
MAX_TAGS = 5


class Mood(models.IntegerChoices):
    VERY_LOW = 1, "Very low"
    LOW = 2, "Low"
    OKAY = 3, "Okay"
    GOOD = 4, "Good"
    GREAT = 5, "Great"


class EmotionTag(models.TextChoices):
    CALM = "calm", "Calm"
    HAPPY = "happy", "Happy"
    GRATEFUL = "grateful", "Grateful"
    HOPEFUL = "hopeful", "Hopeful"
    MOTIVATED = "motivated", "Motivated"
    TIRED = "tired", "Tired"
    ANXIOUS = "anxious", "Anxious"
    STRESSED = "stressed", "Stressed"
    SAD = "sad", "Sad"
    LONELY = "lonely", "Lonely"
    ANGRY = "angry", "Angry"
    OVERWHELMED = "overwhelmed", "Overwhelmed"


class MoodCheckIn(ValidatedModelMixin, models.Model):
    patient = models.ForeignKey(
        "patients.PatientProfile", on_delete=models.CASCADE, related_name="check_ins"
    )
    # The patient's local date when the check-in was made (their timezone).
    local_date = models.DateField()
    mood = models.PositiveSmallIntegerField(
        choices=Mood.choices,
        validators=[MinValueValidator(MOOD_MIN), MaxValueValidator(MOOD_MAX)],
    )
    tags = ArrayField(
        models.CharField(max_length=20, choices=EmotionTag.choices),
        default=list,
        blank=True,
        size=MAX_TAGS,
    )
    # Private to the patient: never returned to the psychologist or admins.
    note = EncryptedFreeTextField(
        label="Note", min_length=10, rule_max_length=500, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-local_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "local_date"],
                name="journals_one_check_in_per_local_day",
            )
        ]

    def __str__(self):
        return f"Check-in #{self.pk} ({self.local_date})"
