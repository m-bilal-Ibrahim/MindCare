"""Database models for the moderation app.

6.3: reports and complaints between people in a care relationship, in both
directions (patient → psychologist, psychologist → patient), reviewed by admins
(docs/decisions.md, 2026-10-06 and 2026-10-11). Community content reports come
with 6.8.
"""

from django.conf import settings
from django.db import models

from core.encryption import EncryptedFreeTextField
from core.models import ValidatedModelMixin


class ReportReason(models.TextChoices):
    HARASSMENT = "harassment", "Harassment or bullying"
    THREATS = "threats_or_violence", "Threats or violence"
    INAPPROPRIATE_CONTENT = "inappropriate_content", "Inappropriate messages or content"
    UNPROFESSIONAL = "unprofessional_conduct", "Unprofessional conduct"
    PRIVACY = "privacy_breach", "Shared my private information"
    OTHER = "other", "Something else"


class ReportStatus(models.TextChoices):
    OPEN = "open", "Open"
    DISMISSED = "dismissed", "Dismissed (no violation found)"
    ACTIONED = "actioned", "Actioned (account deactivated)"


class Report(ValidatedModelMixin, models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reports_made"
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports_received",
    )
    # The care relationship that gives the reporter standing (and the admin context).
    relationship = models.ForeignKey(
        "relationships.CareRelationship", on_delete=models.PROTECT, related_name="+"
    )
    reason = models.CharField(max_length=40, choices=ReportReason.choices)
    # Optional. Encrypted at rest; shown only to admins, every read audited;
    # never logged.
    description = EncryptedFreeTextField(
        label="Description", min_length=10, rule_max_length=1000, blank=True, default=""
    )
    status = models.CharField(
        max_length=20, choices=ReportStatus.choices, default=ReportStatus.OPEN
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            # One open report per reporter per relationship: no pile-on spam.
            models.UniqueConstraint(
                fields=["reporter", "relationship"],
                condition=models.Q(status="open"),
                name="moderation_one_open_report_per_relationship",
            )
        ]

    def __str__(self):
        return f"Report #{self.pk} ({self.get_status_display()})"
