"""Database models for the journals app.

Phase 2 module 3: daily mood check-ins (docs/decisions.md, 2026-10-28). One per
patient per local day (the patient's timezone). The mood and tags stay readable
so insights can be calculated; the optional note is encrypted at rest, private
to the patient, and never shown to the psychologist.
"""

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.encryption import EncryptedFreeTextField, EncryptedTextField
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


ENTRY_TITLE_MIN, ENTRY_TITLE_MAX = 3, 120
ENTRY_BODY_MIN, ENTRY_BODY_MAX = 10, 10000
MAX_ENTRIES_PER_DAY = 20


class JournalEntry(ValidatedModelMixin, models.Model):
    """The patient's private journal (docs/decisions.md, 2026-11-19; project-vision
    section 11). Strictly private: no psychologist or admin endpoint, not in
    Django admin. Title, body and tags are encrypted; the patient can edit at any
    time and hard-delete. Encrypted columns can't be searched, so there is no
    text search; the tag filter runs on the decrypted rows of one patient."""

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="journal_entries",
    )
    # The patient's local date when the entry was written (their timezone).
    local_date = models.DateField()
    title = EncryptedFreeTextField(
        label="Title",
        min_length=ENTRY_TITLE_MIN,
        rule_max_length=ENTRY_TITLE_MAX,
        blank=True,
        default="",
    )
    body = EncryptedFreeTextField(
        label="Entry", min_length=ENTRY_BODY_MIN, rule_max_length=ENTRY_BODY_MAX
    )
    # Comma-separated EmotionTag slugs, encrypted (like the history concerns).
    tags = EncryptedTextField(blank=True, default="")
    # Optional link to the mood check-in of the same local day.
    check_in = models.ForeignKey(
        MoodCheckIn,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-local_date", "-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["patient", "local_date"], name="journals_entry_patient_day"
            )
        ]

    def __str__(self):
        return f"Journal entry #{self.pk} ({self.local_date})"

    @property
    def tag_list(self):
        return [slug for slug in (self.tags or "").split(",") if slug]
