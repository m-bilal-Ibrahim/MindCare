"""URL routes for the emergency API, included under /api/v1/emergency/."""

from django.urls import path

from apps.emergency.api.views import (
    AdminSOSCloseView,
    AdminSOSDetailView,
    AdminSOSFollowUpView,
    AdminSOSListView,
    CancelSOSView,
    ContactDetailView,
    ContactsView,
    PsychologistAlertsView,
    ResourcesView,
    SOSView,
)

app_name = "emergency"

urlpatterns = [
    # Patients
    path("resources/", ResourcesView.as_view(), name="resources"),
    path("sos/", SOSView.as_view(), name="sos"),
    path("sos/<int:event_id>/cancel/", CancelSOSView.as_view(), name="sos-cancel"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
    path(
        "contacts/<int:contact_id>/", ContactDetailView.as_view(), name="contact-detail"
    ),
    # Psychologists
    path(
        "psychologist/alerts/",
        PsychologistAlertsView.as_view(),
        name="psychologist-alerts",
    ),
    # Admins
    path("admin/sos/", AdminSOSListView.as_view(), name="admin-sos"),
    path(
        "admin/sos/<int:event_id>/",
        AdminSOSDetailView.as_view(),
        name="admin-sos-detail",
    ),
    path(
        "admin/sos/<int:event_id>/follow-up/",
        AdminSOSFollowUpView.as_view(),
        name="admin-sos-follow-up",
    ),
    path(
        "admin/sos/<int:event_id>/close/",
        AdminSOSCloseView.as_view(),
        name="admin-sos-close",
    ),
]
