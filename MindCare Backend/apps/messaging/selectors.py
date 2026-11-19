"""Read-path query logic for messaging (incl. ownership filtering).

Who may open a conversation (docs/decisions.md, 2026-11-18):
- the patient: always (read-only once care with that psychologist has ended);
- the psychologist: only while they are the patient's CURRENT assigned
  psychologist (accepted relationship, approved and active). A former
  psychologist loses access entirely, like therapy notes.
Everyone else, admins included, gets a 404.
"""

from django.db.models import Count, Q

from apps.accounts.models import Role
from apps.messaging.models import Conversation, Message
from apps.relationships.selectors import (
    get_active_relationship,
    is_assigned_psychologist,
)

PAGE_SIZE = 30
MAX_PAGE_SIZE = 50
SAFETY_NOTICE = (
    "Messages are not for emergencies and may not be read straight away. If you "
    "are in danger or might harm yourself, press the SOS button or call your "
    "local emergency number now."
)


class NotFound(Exception):
    pass


def _unread_filter(user):
    return Q(messages__read_at__isnull=True, messages__deleted_at__isnull=True) & ~Q(
        messages__sender=user
    )


def visible_conversations(*, user):
    """Every conversation the user may open, with `unread` annotated."""
    base = Conversation.objects.select_related("patient__user", "psychologist__user")
    if user.role == Role.PATIENT:
        qs = base.filter(patient__user=user)
    elif user.role == Role.PSYCHOLOGIST and user.is_active:
        # Current patients only; the relationships selector re-checks approval.
        from apps.relationships.selectors import psychologist_patients

        current = psychologist_patients(psychologist_user=user).values("patient_id")
        qs = base.filter(psychologist__user=user, patient_id__in=current)
    else:
        return Conversation.objects.none()
    return qs.annotate(unread=Count("messages", filter=_unread_filter(user)))


def can_send(*, user, conversation):
    if user.role == Role.PATIENT:
        rel = get_active_relationship(patient=conversation.patient)
        return rel is not None and rel.psychologist_id == conversation.psychologist_id
    return is_assigned_psychologist(viewer=user, patient_profile=conversation.patient)


def get_conversation(*, user, conversation_id):
    """The conversation, or NotFound if the user isn't allowed to open it."""
    conversation = visible_conversations(user=user).filter(pk=conversation_id).first()
    if conversation is None:
        raise NotFound()
    return conversation


def other_party(*, user, conversation):
    if user.role == Role.PATIENT:
        psych = conversation.psychologist
        return {"id": psych.pk, "role": Role.PSYCHOLOGIST, "name": psych.user.full_name}
    from apps.patients.selectors import get_patient_display_identity

    identity = get_patient_display_identity(
        patient_profile=conversation.patient, viewer=user
    )
    return {
        "id": conversation.patient_id,
        "role": Role.PATIENT,
        "name": identity["display_name"],
    }


def conversation_summary(*, user, conversation, detail=False):
    """What the list shows. Never the text of any message."""
    data = {
        "id": conversation.pk,
        "other_party": other_party(user=user, conversation=conversation),
        "last_message_at": conversation.last_message_at,
        "unread_count": getattr(conversation, "unread", 0),
        "can_send": can_send(user=user, conversation=conversation),
    }
    if detail:
        data["safety_notice"] = SAFETY_NOTICE
    return data


def messages_page(*, conversation, before=None, limit=PAGE_SIZE):
    """Newest first. `before` is a message id (exclusive); returns
    (rows, next_before), next_before None when there is nothing older."""
    limit = max(1, min(limit or PAGE_SIZE, MAX_PAGE_SIZE))
    qs = Message.objects.filter(conversation=conversation).order_by("-id")
    if before is not None:
        qs = qs.filter(pk__lt=before)
    rows = list(qs[: limit + 1])
    has_more = len(rows) > limit
    rows = rows[:limit]
    return rows, (rows[-1].pk if has_more else None)


def total_unread(*, user):
    ids = visible_conversations(user=user).values("pk")
    return (
        Message.objects.filter(
            conversation_id__in=ids, read_at__isnull=True, deleted_at__isnull=True
        )
        .exclude(sender=user)
        .count()
    )
