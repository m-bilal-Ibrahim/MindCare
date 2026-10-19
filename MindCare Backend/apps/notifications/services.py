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
