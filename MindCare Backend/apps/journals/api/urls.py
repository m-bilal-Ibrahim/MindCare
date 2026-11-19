"""URL routes for the journals API, included under /api/v1/journals/."""

from django.urls import path

from apps.journals.api.views import (
    CheckInDetailView,
    CheckInsView,
    InsightsView,
    JournalEntriesView,
    JournalEntryDetailView,
    PsychologistMoodsView,
    TodayView,
)

app_name = "journals"

urlpatterns = [
    # Patients: mood check-ins (Phase 2 module 3)
    path("check-ins/", CheckInsView.as_view(), name="check-ins"),
    path("check-ins/today/", TodayView.as_view(), name="check-in-today"),
    path("check-ins/insights/", InsightsView.as_view(), name="check-in-insights"),
    path(
        "check-ins/<int:check_in_id>/",
        CheckInDetailView.as_view(),
        name="check-in-detail",
    ),
    # Patients: the private journal (no psychologist or admin route exists)
    path("entries/", JournalEntriesView.as_view(), name="entries"),
    path(
        "entries/<int:entry_id>/",
        JournalEntryDetailView.as_view(),
        name="entry-detail",
    ),
    # Psychologists: a current patient's moods (by relationship id)
    path(
        "psychologist/patients/<int:relationship_id>/moods/",
        PsychologistMoodsView.as_view(),
        name="psychologist-moods",
    ),
]
