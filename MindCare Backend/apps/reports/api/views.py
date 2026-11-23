"""DRF views for 6.14 patient reports. Thin: parse -> service -> serialize.

The psychologist endpoint takes the relationship id of a CURRENT patient (404
otherwise, the same as the care plan and therapy notes).
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.reports import services
from apps.reports.api.serializers import PatientReportSerializer, ReportQuerySerializer
from core.exceptions import DomainValidationError
from core.permissions import IsApprovedPsychologist, IsPsychologist


class PatientReportThrottle(UserRateThrottle):
    scope = "patient_reports"


class PatientReportView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]
    throttle_classes = [PatientReportThrottle]

    @extend_schema(
        parameters=[ReportQuerySerializer],
        responses={
            200: PatientReportSerializer,
            400: OpenApiResponse(description="Invalid period."),
            404: OpenApiResponse(description="Not your current patient."),
        },
        description="A report on a current patient for one period of the "
        "patient's local days: `week` (Monday to Sunday), `month`, or `custom` "
        "(up to 183 days). Never before this pair's care started; never past "
        "today. Sessions, therapy-note ratings and risk levels, mood, care-plan "
        "adherence, SOS alerts, a comparison with the previous period and "
        "factual indicators. Never note, check-in or journal text. Calculated "
        "on every request, never stored. Audited.",
    )
    def get(self, request, relationship_id):
        query = ReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            report = services.generate_report(
                psychologist_user=request.user,
                relationship_id=relationship_id,
                ip=request.META.get("REMOTE_ADDR"),
                **query.validated_data,
            )
        except services.NotYourPatient as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(PatientReportSerializer(report).data)
