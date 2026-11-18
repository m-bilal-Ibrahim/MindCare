"""URL routes for the clinical_notes API, included under /api/v1/clinical-notes/."""

from django.urls import path

from apps.clinical_notes.api import views

app_name = "clinical_notes"

PATIENT = "patients/<int:relationship_id>/"
NOTE = PATIENT + "notes/<int:note_id>/"

urlpatterns = [
    # Psychologists: a CURRENT patient's notes, by relationship id (Phase 2 module 5)
    path(PATIENT + "notes/", views.NotesView.as_view(), name="notes"),
    path(NOTE, views.NoteDetailView.as_view(), name="note-detail"),
    path(NOTE + "versions/", views.NoteVersionsView.as_view(), name="note-versions"),
    path(NOTE + "addenda/", views.AddendumView.as_view(), name="note-addenda"),
    path(PATIENT + "progress/", views.ProgressView.as_view(), name="progress"),
    path(PATIENT + "summary/", views.SummaryView.as_view(), name="summary"),
    # Patients: their own progress (never notes)
    path("me/progress/", views.MyProgressView.as_view(), name="my-progress"),
]
