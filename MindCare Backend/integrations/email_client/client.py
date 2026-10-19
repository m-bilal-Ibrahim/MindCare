"""
Outbound email over each provider's HTTPS API (docs/decisions.md, 2026-10-19).

Render's free plan blocks outbound SMTP, so mail goes through the provider's
HTTP API with the standard library (no new package). `EMAIL_PROVIDER` picks the
provider, so moving from Brevo to Resend is a settings change only:

- `brevo`   POST https://api.brevo.com/v3/smtp/email   (header `api-key`)
- `resend`  POST https://api.resend.com/emails          (header `Authorization: Bearer`)
- `console` Django's default mailer (`MAILERS`): the console in
  development, the in-memory outbox in tests
- `disabled` nothing is sent (the production default until a provider is set)

Callers get `EmailNotSent` on any failure. Nothing here logs the API key, the
recipient or the body (bodies can hold one-time codes); callers log only the
template name and the failure kind.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

PROVIDERS = {"brevo", "resend", "console", "disabled"}

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
RESEND_URL = "https://api.resend.com/emails"


class EmailNotSent(Exception):
    """The provider refused or couldn't be reached. `reason` is safe to log:
    a status code or an exception type, never the address or the content."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _sender():
    return settings.DEFAULT_FROM_EMAIL, getattr(settings, "DEFAULT_FROM_NAME", "")


def _post_json(url, payload, headers):
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.EMAIL_TIMEOUT_SECONDS) as response:
            response.read()
    except HTTPError as exc:
        status = exc.code
        exc.close()  # an HTTPError holds the open response
        raise EmailNotSent(f"http_{status}") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise EmailNotSent(type(exc).__name__) from None


def _send_brevo(*, to, subject, text, html):
    address, name = _sender()
    sender = {"email": address, **({"name": name} if name else {})}
    payload = {
        "sender": sender,
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
    }
    if html:
        payload["htmlContent"] = html
    _post_json(BREVO_URL, payload, {"api-key": settings.EMAIL_PROVIDER_API_KEY})


def _send_resend(*, to, subject, text, html):
    address, name = _sender()
    payload = {
        "from": f"{name} <{address}>" if name else address,
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html:
        payload["html"] = html
    _post_json(
        RESEND_URL,
        payload,
        {"Authorization": f"Bearer {settings.EMAIL_PROVIDER_API_KEY}"},
    )


def _send_console(*, to, subject, text, html):
    from django.core.mail import EmailMultiAlternatives

    address, name = _sender()
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=f"{name} <{address}>" if name else address,
        to=[to],
    )
    if html:
        message.attach_alternative(html, "text/html")
    try:
        message.send()
    except Exception as exc:  # the backend's own failure
        raise EmailNotSent(type(exc).__name__) from None


def send_email(*, to, subject, text, html=None):
    """Send one email now. Raises EmailNotSent. With `disabled`, does nothing."""
    provider = settings.EMAIL_PROVIDER
    if provider == "disabled":
        return
    if provider in {"brevo", "resend"} and not settings.EMAIL_PROVIDER_API_KEY:
        raise EmailNotSent("missing_api_key")
    sender = {
        "brevo": _send_brevo,
        "resend": _send_resend,
        "console": _send_console,
    }.get(provider)
    if sender is None:
        raise EmailNotSent("unknown_provider")
    sender(to=to, subject=subject, text=text, html=html)
