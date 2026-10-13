"""Database models for the patients app.

Phase 2 PatientProfile holds identity, demographics and preferences only — no
health data before the Phase 5 audit trail (docs/decisions.md, 2026-09-26).
"""

import secrets

from django.conf import settings
from django.db import models

from core.choices import Gender
from core.encryption import EncryptedFreeTextField, EncryptedTextField
from core.fields import PhoneField
from core.models import ValidatedModelMixin
from core.validators import validate_iana_timezone

PSEUDONYM_PREFIX = "Patient-"


def generate_pseudonym():
    return f"{PSEUDONYM_PREFIX}{secrets.token_hex(3)}"


class PatientProfile(ValidatedModelMixin, models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    # Immutable, never usable for login. Shown instead of the real name unless
    # is_profile_public (see selectors.get_patient_display_identity).
    pseudonym = models.CharField(max_length=16, unique=True, editable=False)
    is_profile_public = models.BooleanField(default=False)
    country = models.ForeignKey(
        "reference.Country",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    city = models.ForeignKey(
        "reference.City",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    timezone = models.CharField(max_length=64, validators=[validate_iana_timezone])
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, choices=Gender.choices, null=True, blank=True
    )
    # Contact number only — NOT a login identifier. Phone-number login, if built,
    # gets its own unique, verified field on User (docs/decisions.md, 2026-09-26).
    phone_number = PhoneField(max_length=20, null=True, blank=True)
    preferred_language = models.ForeignKey(
        "reference.Language",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    # Private storage key of the profile photo ("" = none). Who may see it:
    # selectors.can_see_patient_photo() (docs/decisions.md, 2026-10-11).
    photo_key = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pseudonym


class YesNoUnsure(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class YesNo(models.TextChoices):
    YES = "yes", "Yes"
    NO = "no", "No"


class MentalHealthHistory(ValidatedModelMixin, models.Model):
    """The optional mental health history a patient shares (6.1).

    Health data: every field is encrypted at rest, it is never logged, the
    patient and their CURRENT assigned psychologist are the only readers (never
    on a pending request, never admins), and every psychologist read and every
    write is in the access audit trail (docs/decisions.md, 2026-10-11).
    Concerns are stored as a comma-separated list of Specialization slugs inside
    the encrypted text, not as a relation, so which conditions a patient has is
    never readable in plain form.
    """

    profile = models.OneToOneField(
        PatientProfile, on_delete=models.CASCADE, related_name="mental_health_history"
    )
    concerns = EncryptedTextField(blank=True, default="")
    previous_diagnosis = EncryptedTextField(
        choices=YesNoUnsure.choices, blank=True, default=""
    )
    current_medication = EncryptedTextField(
        choices=YesNoUnsure.choices, blank=True, default=""
    )
    previous_therapy = EncryptedTextField(choices=YesNo.choices, blank=True, default="")
    notes = EncryptedFreeTextField(
        label="Notes", min_length=10, rule_max_length=1000, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "mental health histories"

    def __str__(self):
        return f"Mental health history #{self.pk}"

    @property
    def concern_slugs(self):
        return [slug for slug in self.concerns.split(",") if slug]

    @property
    def is_empty(self):
        return not any(
            (
                self.concerns,
                self.previous_diagnosis,
                self.current_medication,
                self.previous_therapy,
                self.notes,
            )
        )
