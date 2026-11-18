"""Read-path query logic for in-app notifications. Every query is scoped to the
requesting user: nobody ever reads another user's notifications."""

from apps.notifications.models import Notification


def notifications_for(*, user, unread=None, type=None):
    rows = Notification.objects.filter(recipient=user)
    if unread is True:
        rows = rows.filter(is_read=False)
    elif unread is False:
        rows = rows.filter(is_read=True)
    if type:
        rows = rows.filter(type=type)
    return rows.order_by("-created_at", "-id")


def unread_count(*, user):
    return Notification.objects.filter(recipient=user, is_read=False).count()
