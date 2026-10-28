"""DRF views for the journals API (mood check-ins). Thin: parse ->
service/selector -> serialize."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.journals import selectors, services
from apps.journals.api.serializers import (
    CheckInSerializer,
    CheckInUpdateSerializer,
    CheckInWriteSerializer,
    InsightsSerializer,
    PsychologistCheckInSerializer,
    PsychologistMoodQuerySerializer,
    PsychologistMoodSerializer,
    TodaySerializer,
)
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _domain(exc):
    return ValidationError(exc.errors, code=exc.code)


class CheckInWriteThrottle(UserRateThrottle):
    scope = "check_ins"


class PatientView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get_throttles(self):
        if self.request.method in ("POST", "PATCH"):
            return [CheckInWriteThrottle()]
        return []


class CheckInsView(PatientView):
    @extend_schema(
        responses={200: CheckInSerializer(many=True)},
        description="Your check-ins, newest first, paginated.",
    )
    def get(self, request):
        rows = selectors.check_ins_for(patient_profile=request.user.patient_profile)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(CheckInSerializer(page, many=True).data)

    @extend_schema(
        request=CheckInWriteSerializer,
        responses={
            201: CheckInSerializer,
            400: OpenApiResponse(
                description="Invalid input, or already checked in today."
            ),
        },
        description="Today's check-in (your local day). One per day.",
    )
    def post(self, request):
        body = CheckInWriteSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            check_in = services.create_check_in(
                patient_profile=request.user.patient_profile,
                ip=_ip(request),
                **body.validated_data,
            )
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(
            CheckInSerializer(check_in).data, status=status.HTTP_201_CREATED
        )


class TodayView(PatientView):
    @extend_schema(
        responses={200: TodaySerializer},
        description="Your local date and today's check-in (null if none yet).",
    )
    def get(self, request):
        today, check_in = selectors.today_check_in(
            patient_profile=request.user.patient_profile
        )
        return Response(
            TodaySerializer({"local_date": today, "check_in": check_in}).data
        )


class CheckInDetailView(PatientView):
    @extend_schema(
        request=CheckInUpdateSerializer,
        responses={
            200: CheckInSerializer,
            400: OpenApiResponse(description="Invalid input, or not today's check-in."),
            404: OpenApiResponse(),
        },
    )
    def patch(self, request, check_in_id):
        body = CheckInUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            check_in = services.update_check_in(
                patient_profile=request.user.patient_profile,
                check_in_id=check_in_id,
                ip=_ip(request),
                **body.validated_data,
            )
        except services.NotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(CheckInSerializer(check_in).data)

    @extend_schema(responses={204: None, 404: OpenApiResponse()})
    def delete(self, request, check_in_id):
        try:
            services.delete_check_in(
                patient_profile=request.user.patient_profile,
                check_in_id=check_in_id,
                ip=_ip(request),
            )
        except services.NotFound as exc:
            raise Http404 from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class InsightsView(PatientView):
    @extend_schema(
        responses={200: InsightsSerializer},
        description="Averages, mood distribution and top feelings for the last 7, "
        "30 and 90 days, plus your streak. Calculated, not AI.",
    )
    def get(self, request):
        data = selectors.insights(patient_profile=request.user.patient_profile)
        return Response(InsightsSerializer(data).data)


class PsychologistMoodsView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    @extend_schema(
        parameters=[PsychologistMoodQuerySerializer],
        responses={200: PsychologistMoodSerializer, 404: OpenApiResponse()},
        description="A CURRENT patient's moods and feelings (never their notes) for "
        "the last `days` (7, 30 or 90; default 30), with insights. Audited.",
    )
    def get(self, request, relationship_id):
        query = PsychologistMoodQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            rows, summary = services.read_moods_for_psychologist(
                psychologist_user=request.user,
                relationship_id=relationship_id,
                days=int(query.validated_data["days"]),
                ip=_ip(request),
            )
        except services.NotYourPatient as exc:
            raise Http404 from exc
        return Response(
            {
                "check_ins": PsychologistCheckInSerializer(rows, many=True).data,
                "insights": InsightsSerializer(summary).data,
            }
        )
