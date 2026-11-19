"""The fixed wording of every in-app notification (docs/decisions.md, 2026-11-18).

Never put sensitive data here: no names (patient or psychologist), note or
summary text, mood, feelings, SOS location, contact details or diagnosis. The
only value filled in is `{when}`, a session time in the recipient's timezone.
A test checks every template against a list of forbidden placeholders.
"""

from apps.notifications.models import NotificationType as T
from apps.notifications.models import TargetType

# type -> (title, body, target_type or "")
TEMPLATES = {
    T.SESSION_REQUESTED: (
        "New session request",
        "One of your patients asked for a session on {when}. Confirm it or "
        "propose another time.",
        TargetType.SESSION,
    ),
    T.SESSION_CONFIRMED: (
        "Session confirmed",
        "Your session on {when} was confirmed. The video link is on the session.",
        TargetType.SESSION,
    ),
    T.SESSION_PROPOSED: (
        "New time proposed",
        "Your psychologist proposed {when} for your session. Accept it or cancel.",
        TargetType.SESSION,
    ),
    T.SESSION_DECLINED: (
        "Session request declined",
        "Your session request for {when} wasn't accepted. You can pick another "
        "time.",
        TargetType.SESSION,
    ),
    T.SESSION_CANCELLED: (
        "Session cancelled",
        "The session on {when} was cancelled. The time is free again.",
        TargetType.SESSION,
    ),
    T.SESSION_PROPOSAL_ACCEPTED: (
        "Proposed time accepted",
        "Your patient accepted {when}. The session is confirmed.",
        TargetType.SESSION,
    ),
    T.SESSION_COMPLETED: (
        "Session completed",
        "Your session on {when} was marked as completed.",
        TargetType.SESSION,
    ),
    T.SESSION_NO_SHOW: (
        "Session missed",
        "Your session on {when} was marked as missed. You can book another time.",
        TargetType.SESSION,
    ),
    T.CARE_REQUESTED: (
        "New care request",
        "A patient asked you to be their psychologist. It expires after 3 days.",
        TargetType.CARE_RELATIONSHIP,
    ),
    T.CARE_ACCEPTED: (
        "Care request accepted",
        "Your psychologist accepted your request. You can book a session now.",
        TargetType.CARE_RELATIONSHIP,
    ),
    T.CARE_DECLINED: (
        "Care request declined",
        "Your care request wasn't accepted. You can choose another psychologist.",
        TargetType.CARE_RELATIONSHIP,
    ),
    T.CARE_ENDED: (
        "Care ended",
        "Your care relationship has ended. You can choose another psychologist.",
        TargetType.CARE_RELATIONSHIP,
    ),
    T.SOS_ALERT: (
        "SOS alert",
        "A patient pressed the SOS button. Open the alert to follow up.",
        TargetType.SOS_EVENT,
    ),
    T.SOS_CANCELLED: (
        "SOS cancelled",
        "A patient cancelled their SOS alert and says they're safe.",
        TargetType.SOS_EVENT,
    ),
    T.ACCOUNT_APPROVED: (
        "Account approved",
        "Your account has been approved. Welcome to MindCare.",
        "",
    ),
    T.ACCOUNT_REJECTED: (
        "Application not approved",
        "Your application wasn't approved. Check your email for details.",
        "",
    ),
    T.APPLICATION_SUBMITTED: (
        "New application",
        "A new account is waiting for approval.",
        TargetType.PENDING_APPLICATION,
    ),
    T.PASSWORD_CHANGED: (
        "Password changed",
        "Your password was changed and your other devices were signed out. If "
        "this wasn't you, reset your password now.",
        "",
    ),
    T.PROGRESS_SUMMARY_UPDATED: (
        "Progress summary updated",
        "Your psychologist updated your progress summary.",
        TargetType.PROGRESS_SUMMARY,
    ),
    # Never the message text or a preview, and never who sent it.
    T.NEW_MESSAGE: (
        "New message",
        "You have a new message.",
        TargetType.CONVERSATION,
    ),
    # Never what changed: no goal or task text.
    T.CARE_PLAN_UPDATED: (
        "Care plan updated",
        "Your psychologist updated your care plan.",
        TargetType.CARE_PLAN,
    ),
}

ALLOWED_PLACEHOLDERS = {"when"}


def render(type, *, when=""):
    """Return (title, body, target_type) for a type. `when` is required exactly
    when the body uses it."""
    title, body, target_type = TEMPLATES[type]
    needs_when = "{when}" in body
    if needs_when and not when:
        raise ValueError(f"Notification {type!r} needs `when`.")
    if not needs_when and when:
        raise ValueError(f"Notification {type!r} takes no `when`.")
    return title, body.format(when=when) if needs_when else body, target_type
