"""DRF views for the moderation API (6.3). Thin: parse -> service/selector ->
serialize."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.api.admin_views import AdminAPIView
from apps.moderation import selectors, services
from apps.moderation.api.serializers import (
    AdminReportDetailSerializer,
    AdminReportListItemSerializer,
    AdminReportsQuerySerializer,
    MyReportSerializer,
    ReportCreateSerializer,
)
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsPatientOrApprovedPsychologist


class ReportRateThrottle(UserRateThrottle):
    scope = "reports"


class ReportCreateView(APIView):
    permission_classes = [IsAuthenticated, IsPatientOrApprovedPsychologist]

    def get_throttles(self):
        # Only submitting is limited (10/day); listing your own reports isn't.
        return [ReportRateThrottle()] if self.request.method == "POST" else []

    @extend_schema(
        request=ReportCreateSerializer,
        responses={
            201: MyReportSerializer,
            400: OpenApiResponse(
                description="Invalid input, no standing to report this person, or "
                "an open report about them already exists."
            ),
        },
        description=(
            "Report a psychologist you have been in care with (patients send "
            "`psychologist`) or a current or former patient (psychologists send "
            "`relationship`). Admins review it."
        ),
    )
    def post(self, request):
        body = ReportCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        try:
            report = services.submit_report(
                reporter=request.user,
                reason=data["reason"],
                description=data.get("description", ""),
                psychologist_id=data.get("psychologist"),
                relationship_id=data.get("relationship"),
                ip=request.META.get("REMOTE_ADDR"),
            )
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(MyReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: MyReportSerializer(many=True)})
    def get(self, request):
        return Response(
            MyReportSerializer(
                selectors.reports_by(reporter=request.user), many=True
            ).data
        )


class AdminReportsView(AdminAPIView):
    @extend_schema(
        parameters=[AdminReportsQuerySerializer],
        responses={200: AdminReportListItemSerializer(many=True)},
        description=(
            "Reports and complaints, paginated. `status=open` lists the "
            "longest-waiting first; otherwise newest first."
        ),
    )
    def get(self, request):
        query = AdminReportsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        reports = selectors.reports_for_admin(status=query.validated_data.get("status"))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(reports, request, view=self)
        return paginator.get_paginated_response(
            AdminReportListItemSerializer(page, many=True).data
        )


class AdminReportDetailView(AdminAPIView):
    @extend_schema(
        responses={200: AdminReportDetailSerializer, 404: OpenApiResponse()},
        description="Reading the description is recorded in the access audit trail.",
    )
    def get(self, request, report_id):
        try:
            report = services.read_report_for_admin(
                admin=request.user,
                report_id=report_id,
                ip=request.META.get("REMOTE_ADDR"),
            )
        except services.ReportNotFound as exc:
            raise Http404 from exc
        return Response(
            AdminReportDetailSerializer(report, context={"request": request}).data
        )


class _ResolveReportView(AdminAPIView):
    resolve = None  # the moderation service to call (not `action`: DRF uses that)

    @extend_schema(
        request=None,
        responses={
            200: AdminReportListItemSerializer,
            400: OpenApiResponse(description="Already resolved."),
            404: OpenApiResponse(),
        },
    )
    def post(self, request, report_id):
        try:
            report = self.resolve(admin=request.user, report_id=report_id)
        except services.ReportNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(AdminReportListItemSerializer(report).data)


class DismissReportView(_ResolveReportView):
    """No violation found."""

    resolve = staticmethod(services.dismiss_report)


class UpholdReportView(_ResolveReportView):
    """Deactivate the reported account (ending their care relationships) and
    close every open report about them."""

    resolve = staticmethod(services.uphold_report)
