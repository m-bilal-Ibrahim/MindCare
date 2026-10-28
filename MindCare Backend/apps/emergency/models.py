"""Database models for the emergency app (6.12 SOS, Phase 2 module 2).

docs/decisions.md, 2026-10-28:
- Helplines and hospitals are admin-curated in Django admin. Nothing is seeded:
  only numbers an admin has verified are ever shown.
- Emergency contacts are third parties' personal data, so every field is
  encrypted at rest. The patient confirms each contact agreed to be one.
- An SOS event is never blocked. Device coordinates are optional, rounded to 3
  decimals (~100 m), encrypted, and cleared after 90 days.
"""

from django.conf import settings
from django.db import models

from core.encryption import EncryptedSingleLineField, EncryptedTextField
from core.fields import FreeTextField, OrganisationNameField, ServiceNumberField
from core.models import ValidatedModelMixin


class Helpline(ValidatedModelMixin, models.Model):
    """A verified helpline. country=NULL means it works from any country."""

    country = models.ForeignKey(
        "reference.Country",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        help_text="Leave empty for a helpline that works from any country.",
    )
    name = OrganisationNameField(max_length=150, label="Name")
    number = ServiceNumberField(label="Number")
    description = FreeTextField(
        label="Description", min_length=10, rule_max_length=300, blank=True, default=""
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name", "id"]

    def __str__(self):
        return f"{self.name} ({self.number})"


class Hospital(ValidatedModelMixin, models.Model):
    city = models.ForeignKey(
        "reference.City", on_delete=models.PROTECT, related_name="+"
    )
    name = OrganisationNameField(max_length=150, label="Name")
    phone = ServiceNumberField(label="Phone")
    address = FreeTextField(label="Address", min_length=10, rule_max_length=300)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class ContactRelationship(models.TextChoices):
    PARENT = "parent", "Parent"
    SIBLING = "sibling", "Sibling"
    SPOUSE_PARTNER = "spouse_partner", "Spouse or partner"
    CHILD = "child", "Child"
    RELATIVE = "relative", "Other relative"
    FRIEND = "friend", "Friend"
    OTHER = "other", "Other"


class EmergencyContact(ValidatedModelMixin, models.Model):
    """Up to 3 per patient. Emailed when the patient presses SOS."""

    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    name = EncryptedSingleLineField(kind="person_name", label="Name")
    relationship = models.CharField(max_length=20, choices=ContactRelationship.choices)
    email = EncryptedSingleLineField(kind="email", label="Email")
    phone = EncryptedSingleLineField(
        kind="phone", label="Phone", blank=True, default=""
    )
    consent_confirmed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Emergency contact #{self.pk}"


class SOSStatus(models.TextChoices):
    OPEN = "open", "Open"
    CANCELLED = "cancelled", "Cancelled by the patient"
    FOLLOWED_UP = "followed_up", "Followed up"
    CLOSED = "closed", "Closed"


class SOSOutcome(models.TextChoices):
    PATIENT_SAFE = "patient_safe", "Patient confirmed safe"
    CONTACTED_PATIENT = "contacted_patient", "Contacted the patient"
    REFERRED_EMERGENCY = "referred_emergency_services", "Referred to emergency services"
    FALSE_ALARM = "false_alarm", "False alarm"
    UNREACHABLE = "unreachable", "Couldn't reach the patient"
    OTHER = "other", "Other"


class LocationSource(models.TextChoices):
    DEVICE = "device", "Device location"
    PROFILE_CITY = "profile_city", "Profile city"
    PROFILE_COUNTRY = "profile_country", "Profile country"
    NONE = "none", "No location"


class SOSEvent(models.Model):
    patient = models.ForeignKey(
        "patients.PatientProfile", on_delete=models.PROTECT, related_name="sos_events"
    )
    status = models.CharField(
        max_length=20, choices=SOSStatus.choices, default=SOSStatus.OPEN
    )
    # "lat,lng" rounded to 3 decimals, encrypted; NULL when not sent or purged.
    coordinates = EncryptedTextField(null=True, blank=True, default=None)
    location_source = models.CharField(max_length=20, choices=LocationSource.choices)
    # Snapshots of the profile location at the time (for admins and matching).
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
    contacts_notified = models.PositiveSmallIntegerField(default=0)
    psychologist_notified = models.BooleanField(default=False)
    # Set when this event sent notifications; later events within 30 minutes don't.
    notified_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    followed_up_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    followed_up_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(
        max_length=40, choices=SOSOutcome.choices, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "created_at"])]
        verbose_name = "SOS event"

    def __str__(self):
        return f"SOS #{self.pk} ({self.get_status_display()})"
