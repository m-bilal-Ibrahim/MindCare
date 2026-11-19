"""Secure patient <-> psychologist messaging (docs/decisions.md, 2026-11-18).

- One conversation per patient-psychologist PAIR (like therapy notes), so a
  returning patient continues the same thread. Created when care is accepted
  (or on first use).
- The body is encrypted at rest and never logged. Text only: no attachments,
  no editing. A sender can delete their own message within 5 minutes; the row
  stays as "Message deleted" and the text is wiped (nobody, admins included,
  could ever read it again, so there is nothing to keep it for).
- Admins never see messages: no admin endpoint, not registered in Django admin.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.encryption import EncryptedMessageTextField
from core.models import ValidatedModelMixin

MESSAGE_MAX = 2000
DELETE_WINDOW = timedelta(minutes=5)


class Conversation(models.Model):
    # PROTECT: communication records don't disappear with an account (erasure
    # anonymises, docs/decisions.md 2026-10-06); test-data SQL in deployment.md.
    patient = models.ForeignKey(
        "patients.PatientProfile",
        on_delete=models.PROTECT,
        related_name="conversations",
    )
    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.PROTECT,
        related_name="conversations",
    )
    created_at = models.DateTimeField(default=timezone.now)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "psychologist"],
                name="messaging_one_conversation_per_pair",
            )
        ]

    def __str__(self):
        return f"Conversation #{self.pk}"


class Message(ValidatedModelMixin, models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
    )
    # Blank only once deleted (the service always validates a new body).
    body = EncryptedMessageTextField(
        label="Message", rule_max_length=MESSAGE_MAX, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["conversation", "-id"], name="messaging_conv_recent"),
            models.Index(
                fields=["conversation", "read_at"], name="messaging_conv_unread"
            ),
        ]

    def __str__(self):  # never the body
        return f"Message #{self.pk}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None
