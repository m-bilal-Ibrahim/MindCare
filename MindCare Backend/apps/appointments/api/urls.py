"""URL routes for the appointments API, included under /api/v1/appointments/."""

from django.urls import path

from apps.appointments.api import views

app_name = "appointments"

urlpatterns = [
    # Psychologists: set-up and their sessions (Phase 2 module 4)
    path(
        "psychologist/settings/",
        views.BookingSettingsView.as_view(),
        name="psychologist-settings",
    ),
    path(
        "psychologist/working-hours/",
        views.WorkingHoursView.as_view(),
        name="psychologist-working-hours",
    ),
    path(
        "psychologist/days-off/",
        views.DaysOffView.as_view(),
        name="psychologist-days-off",
    ),
    path(
        "psychologist/days-off/<int:day_off_id>/",
        views.DayOffDetailView.as_view(),
        name="psychologist-day-off",
    ),
    path(
        "psychologist/slots/",
        views.PsychologistSlotsView.as_view(),
        name="psychologist-slots",
    ),
    path(
        "psychologist/sessions/",
        views.PsychologistSessionsView.as_view(),
        name="psychologist-sessions",
    ),
    path(
        "psychologist/sessions/<int:session_id>/confirm/",
        views.ConfirmSessionView.as_view(),
        name="psychologist-session-confirm",
    ),
    path(
        "psychologist/sessions/<int:session_id>/propose/",
        views.ProposeSessionView.as_view(),
        name="psychologist-session-propose",
    ),
    path(
        "psychologist/sessions/<int:session_id>/cancel/",
        views.PsychologistCancelSessionView.as_view(),
        name="psychologist-session-cancel",
    ),
    path(
        "psychologist/sessions/<int:session_id>/outcome/",
        views.SessionOutcomeView.as_view(),
        name="psychologist-session-outcome",
    ),
    # Patients: slots with their current psychologist, and their sessions
    path("slots/", views.SlotsView.as_view(), name="slots"),
    path("sessions/", views.PatientSessionsView.as_view(), name="sessions"),
    path(
        "sessions/<int:session_id>/accept/",
        views.AcceptProposalView.as_view(),
        name="session-accept",
    ),
    path(
        "sessions/<int:session_id>/cancel/",
        views.PatientCancelSessionView.as_view(),
        name="session-cancel",
    ),
]
