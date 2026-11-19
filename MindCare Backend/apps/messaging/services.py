"""Write-path logic for messaging (docs/decisions.md, 2026-11-18).

- Only the two participants write; the patient can't write once care with that
  psychologist has ended (read-only), and a former psychologist can't open it.
- Sending and deleting are audited in the same transaction (fail closed), with
  ids only. Reads aren't audited: both sides are the intended readers, and a
  10-second poll would bury the audit trail.
- The body is NEVER logged, audited, put in a notification or an error.
"""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.messaging import selectors
from apps.messaging.models import DELETE_WINDOW, MESSAGE_MAX, Conversation, Message
from apps.notifications.models import NotificationType
from apps.notifications.services import notify
from core.exceptions import DomainValidationError
from core.validators import (
    MessageTextValidator,
    normalize_multiline_text,
    run_validator,
)

NotFound = selectors.NotFound
READ_ONLY = (
    "This conversation is read-only because care with this psychologist has " "ended."
)
NOT_YOURS = "You can only delete your own messages."
TOO_LATE = "Messages can only be deleted within 5 minutes of sending."
ALREADY_DELETED = "This message was already deleted."


class Forbidden(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def ensure_conversation(*, patient, psychologist):
    """The pair's one conversation, created if missing (called when care is
    accepted, so it exists before the first message)."""
    conversation, _ = Conversation.objects.get_or_create(
        patient=patient, psychologist=psychologist
    )
    return conversation


def _audit(user, action, message, conversation, ip):
    record_access(
        actor=user,
        action=action,
        resource_type=AuditResource.MESSAGE,
        resource_id=message.pk,
        patient_user_id=conversation.patient.user_id,
        ip=ip,
    )


def send_message(*, user, conversation_id, body, ip=None):
    conversation = selectors.get_conversation(
        user=user, conversation_id=conversation_id
    )
    if not selectors.can_send(user=user, conversation=conversation):
        raise Forbidden(READ_ONLY)
    body = normalize_multiline_text(body or "")
    run_validator(MessageTextValidator("Message", MESSAGE_MAX), body, field="body")
    now = timezone.now()
    with transaction.atomic():
        message = Message(
            conversation=conversation, sender=user, body=body, created_at=now
        )
        message.save()
        Conversation.objects.filter(pk=conversation.pk).update(last_message_at=now)
        _audit(user, AuditAction.CREATE, message, conversation, ip)
        recipient = (
            conversation.psychologist.user_id
            if user.role == Role.PATIENT
            else conversation.patient.user_id
        )
        notify(
            recipients=[recipient],
            type=NotificationType.NEW_MESSAGE,
            target_id=conversation.pk,
        )
    return message


def mark_read(*, user, conversation_id):
    """Mark every message from the other side as read. Returns how many."""
    conversation = selectors.get_conversation(
        user=user, conversation_id=conversation_id
    )
    return (
        Message.objects.filter(
            conversation=conversation, read_at__isnull=True, deleted_at__isnull=True
        )
        .exclude(sender=user)
        .update(read_at=timezone.now())
    )


def delete_message(*, user, conversation_id, message_id, ip=None):
    conversation = selectors.get_conversation(
        user=user, conversation_id=conversation_id
    )
    with transaction.atomic():
        message = (
            Message.objects.select_for_update()
            .filter(pk=message_id, conversation=conversation)
            .first()
        )
        if message is None:
            raise NotFound()
        if message.sender_id != user.pk:
            raise Forbidden(NOT_YOURS)
        if message.is_deleted:
            raise DomainValidationError({"non_field_errors": [ALREADY_DELETED]})
        if timezone.now() > message.created_at + DELETE_WINDOW:
            raise DomainValidationError({"non_field_errors": [TOO_LATE]})
        message.deleted_at = timezone.now()
        message.body = ""  # wiped: nobody may read it again
        message.save(update_fields=["deleted_at", "body"])
        _audit(user, AuditAction.DELETE, message, conversation, ip)
    return message
