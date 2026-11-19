"""URL routes for the messaging API, included under /api/v1/messaging/."""

from django.urls import path

from apps.messaging.api import views

app_name = "messaging"

CONV = "conversations/<int:conversation_id>/"

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="conversations"),
    path(CONV, views.ConversationDetailView.as_view(), name="conversation"),
    path(CONV + "messages/", views.MessagesView.as_view(), name="messages"),
    path(
        CONV + "messages/<int:message_id>/",
        views.MessageDetailView.as_view(),
        name="message",
    ),
    path(CONV + "read/", views.MarkReadView.as_view(), name="read"),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread-count"),
]
