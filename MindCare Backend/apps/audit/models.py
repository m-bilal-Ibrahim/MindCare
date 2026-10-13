"""The database-backed access audit trail (docs/decisions.md, 2026-09-15 and
2026-10-11). Required before any health data is stored.

One row per access to health data, a credential document, or a private
patient's real identity: who, what kind of thing, which record, which patient,
from where, when. IDs and codes only, never content or names. Rows are
append-only: they can't be updated or deleted through the ORM or Django admin.
Ids are plain integers, not foreign keys, so a row survives the deletion or
anonymisation of the people it mentions.
"""

from django.db import models


class AuditAction(models.TextChoices):
    VIEW = "view", "View"
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    DOWNLOAD = "download", "Download"
    IDENTITY_REVEAL = "identity_reveal", "Identity reveal"


class AuditResource(models.TextChoices):
    """Extended as modules add audited data."""

    PATIENT_IDENTITY = "patient_identity", "Patient identity"
    MENTAL_HEALTH_HISTORY = "mental_health_history", "Mental health history"
    CREDENTIAL_DOCUMENT = "credential_document", "Credential document"
    REPORT_DESCRIPTION = "report_description", "Report description"


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise PermissionError("Audit rows are append-only.")

    def delete(self):
        raise PermissionError("Audit rows are append-only.")


class AccessLog(models.Model):
    actor_id = models.BigIntegerField(null=True)  # null: system action
    actor_role = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    resource_type = models.CharField(max_length=40, choices=AuditResource.choices)
    resource_id = models.CharField(max_length=64, blank=True)
    patient_user_id = models.BigIntegerField(null=True)
    ip = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["patient_user_id", "created_at"]),
            models.Index(fields=["actor_id", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("Audit rows are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit rows are append-only.")

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.actor_role} {self.action} {self.resource_type}"
