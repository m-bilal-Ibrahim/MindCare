"""URL routes for the moderation API, included under /api/v1/moderation/."""

from django.urls import path

from apps.moderation.api.views import (
    AdminReportDetailView,
    AdminReportsView,
    DismissReportView,
    ReportCreateView,
    UpholdReportView,
)

app_name = "moderation"

urlpatterns = [
    path("reports/", ReportCreateView.as_view(), name="reports"),
    # Admin review (6.3): admins only.
    path("admin/reports/", AdminReportsView.as_view(), name="admin-reports"),
    path(
        "admin/reports/<int:report_id>/",
        AdminReportDetailView.as_view(),
        name="admin-report",
    ),
    path(
        "admin/reports/<int:report_id>/dismiss/",
        DismissReportView.as_view(),
        name="admin-report-dismiss",
    ),
    path(
        "admin/reports/<int:report_id>/uphold/",
        UpholdReportView.as_view(),
        name="admin-report-uphold",
    ),
]
