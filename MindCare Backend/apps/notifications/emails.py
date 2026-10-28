"""The emails MindCare sends. Each builder returns (subject, text, html).

Plain wording, no tracking, nothing about health. Values that came from users
(names) are HTML-escaped in the HTML part. Builders never log anything: the
bodies of reset emails hold one-time codes.
"""

from django.conf import settings
from django.utils.html import escape

PRODUCT = "MindCare"


def _html(paragraphs):
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;'
        f'line-height:1.5;color:#1f2933;max-width:560px">{body}</div>'
    )


def _support_line():
    support = getattr(settings, "SUPPORT_EMAIL", "")
    if not support:
        return None
    return f"Questions? Contact us at {support}."


def _finish(subject, lines, html_lines):
    support = _support_line()
    if support:
        lines = [*lines, support]
        html_lines = [*html_lines, escape(support)]
    lines = [*lines, f"— The {PRODUCT} team"]
    html_lines = [*html_lines, f"— The {PRODUCT} team"]
    return subject, "\n\n".join(lines), _html(html_lines)


def password_reset_code(*, full_name, code, minutes):
    greeting = f"Hi {full_name},"
    intro = f"Use this code to reset your {PRODUCT} password:"
    expiry = (
        f"It works for {minutes} minutes and only once. If you didn't ask for "
        "this, ignore this email: your password stays the same."
    )
    return _finish(
        f"Your {PRODUCT} password reset code",
        [greeting, intro, code, expiry],
        [
            escape(greeting),
            intro,
            f'<strong style="font-size:24px;letter-spacing:4px">{code}</strong>',
            expiry,
        ],
    )


def password_changed(*, full_name):
    greeting = f"Hi {full_name},"
    body = (
        f"Your {PRODUCT} password was just changed, and you've been signed out "
        "on your other devices."
    )
    warning = (
        "If this wasn't you, reset your password from the sign-in screen now "
        "and contact us."
    )
    return _finish(
        f"Your {PRODUCT} password was changed",
        [greeting, body, warning],
        [escape(greeting), body, warning],
    )


ROLE_LABELS = {"psychologist": "psychologist", "ngo": "NGO"}


def account_approved(*, full_name, role):
    greeting = f"Hi {full_name},"
    body = (
        f"Good news: your {PRODUCT} {ROLE_LABELS.get(role, '')} account has been "
        "approved. You can sign in now."
    )
    return _finish(
        f"Your {PRODUCT} account is approved",
        [greeting, body],
        [escape(greeting), body],
    )


def account_rejected(*, full_name, role, reason_label):
    greeting = f"Hi {full_name},"
    body = (
        f"We're sorry: your {PRODUCT} {ROLE_LABELS.get(role, '')} application "
        "wasn't approved."
    )
    lines = [greeting, body]
    html_lines = [escape(greeting), body]
    if reason_label:
        reason = f"Reason: {reason_label}."
        lines.append(reason)
        html_lines.append(escape(reason))
    return _finish(f"Your {PRODUCT} application", lines, html_lines)


# --- SOS (6.12). No health details, no location: only that SOS was pressed. ---

EMERGENCY_LINE = (
    "If you think they are in immediate danger, call your local emergency number."
)


def sos_contact_alert(*, contact_name, patient_name, when):
    greeting = f"Hi {contact_name},"
    body = (
        f"{patient_name} pressed the SOS button in {PRODUCT} at {when} and listed "
        "you as an emergency contact. Please try to reach them now."
    )
    return _finish(
        f"{patient_name} needs you: SOS alert from {PRODUCT}",
        [greeting, body, EMERGENCY_LINE],
        [escape(greeting), escape(body), EMERGENCY_LINE],
    )


def sos_contact_safe(*, contact_name, patient_name):
    greeting = f"Hi {contact_name},"
    body = (
        f"{patient_name} has cancelled their SOS alert and says they're safe. "
        "It may still help to check in with them."
    )
    return _finish(
        f"Update: {patient_name} cancelled their SOS alert",
        [greeting, body],
        [escape(greeting), escape(body)],
    )


def sos_psychologist_alert(*, psychologist_name, pseudonym, when):
    greeting = f"Hi {psychologist_name},"
    body = (
        f"Your patient {pseudonym} pressed the SOS button at {when}. Open "
        f"{PRODUCT} to see who it is and check on them."
    )
    return _finish(
        f"SOS alert from one of your patients ({PRODUCT})",
        [greeting, body, EMERGENCY_LINE],
        [escape(greeting), escape(body), EMERGENCY_LINE],
    )
