"""URL routes for the reports API, included under /api/v1/reports/.

6.14 patient reports (docs/decisions.md, 2026-11-23).
"""

from django.urls import path

from apps.reports.api import views

app_name = "reports"

urlpatterns = [
    # Psychologists: a report on a CURRENT patient, by relationship id
    path(
        "psychologist/patients/<int:relationship_id>/report/",
        views.PatientReportView.as_view(),
        name="patient-report",
    ),
]
