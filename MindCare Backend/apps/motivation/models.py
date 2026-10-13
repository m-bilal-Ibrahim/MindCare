"""Motivation Corner content (project-vision §20).

Text quotes (any logged-in user) and, since 6.10, duas and surahs for patients
who opted in. Shared fields live on the abstract MotivationalContent. Religious
content (Dua / Surah, with audio) has its own concrete models and tables, not a
`kind` on Quote: it needs fields quotes don't (audio
reference via integrations/storage_client, source reference, translation), and
it may only be served to patients who opted in, a GDPR Art. 9 preference
(docs/decisions.md, 2026-09-26 and 2026-10-08). A separate table means the
quotes endpoints can never return it by accident.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from core.fields import FreeTextField, OrganisationNameField, PersonNameField
from core.models import ValidatedModelMixin
from core.validators import whole_number_message


class MotivationalContent(ValidatedModelMixin, models.Model):
    is_active = models.BooleanField(
        default=True, help_text="Untick to hide it from the app immediately."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class QuoteCategory(models.TextChoices):
    HOPE = "hope", "Hope"
    RESILIENCE = "resilience", "Resilience"
    CALM = "calm", "Calm"
    SELF_CARE = "self_care", "Self-care"


class Quote(MotivationalContent):
    text = FreeTextField(label="Quote", min_length=10, rule_max_length=500)
    author = PersonNameField(max_length=120, label="Author", blank=True)
    category = models.CharField(
        max_length=20, choices=QuoteCategory.choices, blank=True
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["is_active", "category"])]

    def __str__(self):
        return self.text[:60]


# --- Religious content (6.10) -------------------------------------------------
# Duas and surahs (text + optional audio), served only to patients who opted in.
# Seeded text: Tanzil Quran Text (Simple, CC BY 3.0, verbatim) and Pickthall's
# 1930 public-domain translation (data/religious_content.json). Audio is uploaded
# by admins (rights they hold), stored privately, served via signed URLs.

SOURCE_REFERENCE_VALIDATOR = RegexValidator(
    regex=r"^[\w .:,()'’-]{3,60}$",
    message=(
        "Reference can only contain letters, numbers, spaces and . : , ( ) ' - "
        "(3–60 characters), e.g. Quran 21:87."
    ),
)


class ReligiousContent(MotivationalContent):
    transliteration = FreeTextField(
        label="Transliteration",
        min_length=3,
        rule_max_length=20000,
        blank=True,
        default="",
    )
    # Private storage key of the recitation ("" = none) and its detected type.
    audio_key = models.CharField(max_length=255, blank=True, default="")
    audio_type = models.CharField(max_length=10, blank=True, default="")

    class Meta:
        abstract = True


class Dua(ReligiousContent):
    title = OrganisationNameField(max_length=120, label="Title", rule_max_length=120)
    reference = models.CharField(max_length=60, validators=[SOURCE_REFERENCE_VALIDATOR])
    arabic = FreeTextField(label="Arabic text", min_length=3, rule_max_length=5000)
    translation = FreeTextField(
        label="Translation", min_length=10, rule_max_length=5000
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class Surah(ReligiousContent):
    number = models.PositiveSmallIntegerField(
        unique=True,
        validators=[
            MinValueValidator(1, message=whole_number_message("Surah number", 1, 114)),
            MaxValueValidator(
                114, message=whole_number_message("Surah number", 1, 114)
            ),
        ],
    )
    name_arabic = FreeTextField(label="Arabic name", min_length=3, rule_max_length=100)
    name_english = OrganisationNameField(
        max_length=100, label="English name", rule_max_length=100
    )
    name_meaning = OrganisationNameField(
        max_length=100, label="Meaning", rule_max_length=100
    )
    ayah_count = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message=whole_number_message("Ayah count", 1, 286)),
            MaxValueValidator(286, message=whole_number_message("Ayah count", 1, 286)),
        ]
    )
    arabic = FreeTextField(label="Arabic text", min_length=3, rule_max_length=50000)
    translation = FreeTextField(
        label="Translation", min_length=10, rule_max_length=50000
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.name_english}"


class ReligiousContentPreference(models.Model):
    """A patient opted in to Quran and dua content (project-vision §20).

    Special-category data under GDPR Art. 9 (it reveals religious belief), so it
    is minimal: the row exists only while the patient is opted in, and opting out
    DELETES it. Never logged, never in Django admin, never in profile serializers;
    only apps/motivation reads it (docs/decisions.md, 2026-10-11).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    opted_in_at = models.DateTimeField(auto_now_add=True)
