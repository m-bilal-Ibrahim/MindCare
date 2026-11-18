"""Write-path business logic for notifications.

Email delivery (docs/decisions.md, 2026-10-19): `send_email_after_commit()` is the
only way the rest of the backend sends mail. It waits for the caller's
transaction to commit (so a rolled-back action never emails anyone), then sends
on a background thread (so a slow provider never delays the response, and the
response time can't reveal whether an account exists). Failures are caught and
logged with the template name and the failure kind only, never the address or
the body, and never raised into the request.
"""

import json
import logging
import threading

from django.conf import settings
from django.db import transaction

from integrations.email_client.client import EmailNotSent, send_email

logger = logging.getLogger("mindcare.email")


def _deliver(*, template, to, subject, text, html):
    try:
        send_email(to=to, subject=subject, text=text, html=html)
    except EmailNotSent as exc:
        logger.warning(
            json.dumps(
                {"event": "email_failed", "template": template, "reason": exc.reason}
            )
        )
        return False
    except Exception as exc:  # never let email break anything
        logger.warning(
            json.dumps(
                {
                    "event": "email_failed",
                    "template": template,
                    "reason": type(exc).__name__,
                }
            )
        )
        return False
    logger.info(json.dumps({"event": "email_sent", "template": template}))
    return True


def send_email_after_commit(*, template, to, message):
    """Queue one email. `message` is (subject, text, html) from
    apps.notifications.emails. Outside a transaction it is sent at once (still in
    the background)."""
    subject, text, html = message

    def start():
        kwargs = {
            "template": template,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
        }
        if settings.EMAIL_SEND_IN_BACKGROUND:
            threading.Thread(target=_deliver, kwargs=kwargs, daemon=True).start()
        else:
            _deliver(**kwargs)

    transaction.on_commit(start)


# --- In-app notifications (docs/decisions.md, 2026-11-18) ----------------------
# Created after the caller's transaction commits (a rolled-back action notifies
# nobody), synchronously, and `robust`: a failure here is logged by Django and
# never breaks the action that caused it (an SOS above all).


class NotFound(Exception):
    pass


def purge_old_notifications(*, now=None):
    """Delete notifications older than 90 days. Returns how many were deleted."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.notifications.models import RETENTION_DAYS, Notification

    cutoff = (now or timezone.now()) - timedelta(days=RETENTION_DAYS)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    return deleted


def _create(user_ids, type, target_id, when):
    from apps.notifications.models import Notification
    from apps.notifications.templates import render

    title, body, target_type = render(type, when=when)
    user_ids = list(dict.fromkeys(uid for uid in user_ids if uid))
    if not user_ids:
        return
    purge_old_notifications()
    # bulk_create is fine: every field is server-built, nothing user-entered.
    Notification.objects.bulk_create(
        [
            Notification(
                recipient_id=uid,
                type=type,
                title=title,
                body=body,
                target_type=target_type,
                target_id=target_id if target_type else None,
            )
            for uid in user_ids
        ]
    )


def notify(*, recipients, type, target_id=None, when=""):
    """Queue one notification per recipient (users or user ids). The wording
    comes from apps/notifications/templates.py; it is rendered now so a bad
    call fails in tests, not silently after commit."""
    from apps.notifications.templates import render

    render(type, when=when)
    user_ids = [getattr(r, "pk", r) for r in recipients]
    transaction.on_commit(lambda: _create(user_ids, type, target_id, when), robust=True)


def notify_admins(*, type, target_id=None):
    """Notify every active admin (resolved after commit)."""
    from apps.accounts.models import Role, User
    from apps.notifications.templates import render

    render(type)

    def create():
        ids = User.objects.filter(role=Role.ADMIN, is_active=True).values_list(
            "pk", flat=True
        )
        _create(list(ids), type, target_id, "")

    transaction.on_commit(create, robust=True)


def _own(user, notification_id):
    from apps.notifications.models import Notification

    row = (
        Notification.objects.select_for_update()
        .filter(pk=notification_id, recipient=user)
        .first()
    )
    if row is None:
        raise NotFound()
    return row


def mark_read(*, user, notification_id):
    from django.utils import timezone

    with transaction.atomic():
        row = _own(user, notification_id)
        if not row.is_read:
            row.is_read = True
            row.read_at = timezone.now()
            row.save(update_fields=["is_read", "read_at"])
    return row


def mark_all_read(*, user):
    """Returns how many were marked."""
    from django.utils import timezone

    from apps.notifications.models import Notification

    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def delete_notification(*, user, notification_id, ip=None):
    """Delete one of your own notifications. Audited (fail closed)."""
    from apps.accounts.models import Role
    from apps.audit.models import AuditAction, AuditResource
    from apps.audit.services import record_access

    with transaction.atomic():
        row = _own(user, notification_id)
        record_access(
            actor=user,
            action=AuditAction.DELETE,
            resource_type=AuditResource.NOTIFICATION,
            resource_id=row.pk,
            patient_user_id=user.pk if user.role == Role.PATIENT else None,
            ip=ip,
        )
        row.delete()
