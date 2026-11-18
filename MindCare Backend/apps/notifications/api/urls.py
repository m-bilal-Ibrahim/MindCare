"""URL routes for the notifications API, included under /api/v1/notifications/."""

from django.urls import path

from apps.notifications.api.views import (
    NotificationDetailView,
    NotificationListView,
    NotificationReadView,
    ReadAllView,
    UnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path("read-all/", ReadAllView.as_view(), name="read-all"),
    path("<int:notification_id>/read/", NotificationReadView.as_view(), name="read"),
    path("<int:notification_id>/", NotificationDetailView.as_view(), name="detail"),
]
