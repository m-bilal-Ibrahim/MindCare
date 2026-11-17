"""Database models for the clinical_notes app (Phase 2 module 5: therapy notes, 6.4).

docs/decisions.md, 2026-11-18 (Q35-Q39):
- Notes belong to the patient-psychologist pair (2026-10-06 forward-note), so a
  returning patient continues the same notes, but only the CURRENTLY assigned
  psychologist can read or write them.
- Every section is optional and encrypted at rest, as are the risk level, the
  addenda, every stored version and the summary written for the patient. The
  progress rating stays a plain number so it can be charted (like mood, 2026-10-28).
- A note is editable for 24 hours, then locked; later changes are addenda. Every
  version is kept. Nothing here is ever deleted through the app or Django admin
  (the models aren't registered there); erasure anonymises (2026-10-06).
"""

from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.encryption import EncryptedFreeTextField, EncryptedTextField
from core.models import ValidatedModelMixin
from core.validators import whole_number_message

EDIT_WINDOW = timedelta(hours=24)
PROGRESS_MIN, PROGRESS_MAX = 1, 10
PROGRESS_MESSAGE = whole_number_message("Progress", PROGRESS_MIN, PROGRESS_MAX)
SECTION_MIN, SECTION_MAX = 10, 5000
SUMMARY_MIN, SUMMARY_MAX = 10, 2000
SECTIONS = ("observations", "interventions", "plan")


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


def _section(label):
    return EncryptedFreeTextField(
        label=label,
        min_length=SECTION_MIN,
        rule_max_length=SECTION_MAX,
        blank=True,
        default="",
    )


class TherapyNote(ValidatedModelMixin, models.Model):
    # PROTECT everywhere: clinical records are never deleted with an account
    # (erasure anonymises instead, docs/decisions.md 2026-10-06).
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="therapy_notes",
    )
    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.PROTECT,
        related_name="therapy_notes",
    )
    # The relationship the note was written in (the pair may have several).
    relationship = models.ForeignKey(
        "relationships.CareRelationship",
        on_delete=models.PROTECT,
        related_name="therapy_notes",
    )
    session = models.ForeignKey(
        "appointments.Session",
        on_delete=models.PROTECT,
        related_name="therapy_notes",
        null=True,
        blank=True,
    )
    observations = _section("Observations")
    interventions = _section("Interventions")
    plan = _section("Plan")
    progress_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(PROGRESS_MIN, message=PROGRESS_MESSAGE),
            MaxValueValidator(PROGRESS_MAX, message=PROGRESS_MESSAGE),
        ],
    )
    # Encrypted: a "high" risk level next to a patient id is sensitive on its own.
    risk_level = EncryptedTextField(choices=RiskLevel.choices, blank=True, default="")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["session"],
                condition=Q(session__isnull=False),
                name="clinical_notes_one_note_per_session",
            )
        ]
        indexes = [
            models.Index(
                fields=["patient", "psychologist", "created_at"],
                name="clinical_notes_pair_created",
            )
        ]

    def __str__(self):
        return f"Therapy note #{self.pk}"

    @property
    def locked_at(self):
        return self.created_at + EDIT_WINDOW

    @property
    def is_locked(self):
        return timezone.now() >= self.locked_at


class NoteVersion(models.Model):
    """A full snapshot of the note after each save (version 1 = as created)."""

    note = models.ForeignKey(
        TherapyNote, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    # JSON of the sections, rating and risk level, encrypted as one value.
    content = EncryptedTextField()
    saved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["version"]
        constraints = [
            models.UniqueConstraint(
                fields=["note", "version"], name="clinical_notes_unique_version"
            )
        ]

    def __str__(self):
        return f"Note #{self.note_id} v{self.version}"


class NoteAddendum(ValidatedModelMixin, models.Model):
    """A later addition to a note. Immutable once written."""

    note = models.ForeignKey(
        TherapyNote, on_delete=models.CASCADE, related_name="addenda"
    )
    text = EncryptedFreeTextField(
        label="Addendum", min_length=SECTION_MIN, rule_max_length=SECTION_MAX
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Addendum #{self.pk} to note #{self.note_id}"


class ProgressSummary(ValidatedModelMixin, models.Model):
    """The one summary a psychologist writes FOR the patient (Q38). The patient
    never sees notes; this is what they see."""

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="progress_summaries",
    )
    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.PROTECT,
        related_name="progress_summaries",
    )
    text = EncryptedFreeTextField(
        label="Summary", min_length=SUMMARY_MIN, rule_max_length=SUMMARY_MAX
    )
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "psychologist"],
                name="clinical_notes_one_summary_per_pair",
            )
        ]

    def __str__(self):
        return f"Progress summary #{self.pk}"
