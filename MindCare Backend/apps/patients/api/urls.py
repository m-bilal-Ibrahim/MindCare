"""URL routes for the patients API, included under /api/v1/patients/."""

from django.urls import path

from apps.patients.api.views import (
    MyMentalHealthHistoryView,
    MyPatientPhotoView,
    MyPatientProfileView,
)

app_name = "patients"

urlpatterns = [
    path("me/", MyPatientProfileView.as_view(), name="me"),
    path("me/photo/", MyPatientPhotoView.as_view(), name="me-photo"),
    path("me/history/", MyMentalHealthHistoryView.as_view(), name="me-history"),
]
