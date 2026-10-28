"""DRF views for the appointments API (Phase 2 module 4: booking and fees).

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.appointments import selectors, services
from apps.appointments.api.serializers import (
    BookingSettingsSerializer,
    BookingSettingsWriteSerializer,
    DayOffSerializer,
    DayOffWriteSerializer,
    FreeSlotsSerializer,
    OutcomeSerializer,
    PatientSessionSerializer,
    PsychologistSessionQuerySerializer,
    PsychologistSessionSerializer,
    SlotsSerializer,
    StartsAtSerializer,
    WorkingHoursSerializer,
)
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist

ERRORS = {
    400: OpenApiResponse(description="Invalid input or not allowed now."),
    404: OpenApiResponse(),
}


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _run(fn, **kwargs):
    try:
        return fn(**kwargs)
    except services.NotFound as exc:
        raise Http404 from exc
    except DomainValidationError as exc:
        raise ValidationError(exc.errors, code=exc.code) from exc


class BookingWriteThrottle(UserRateThrottle):
    scope = "bookings"


class _WriteThrottled(APIView):
    def get_throttles(self):
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [BookingWriteThrottle()]
        return []


def _paginate(view, request, rows, serializer_cls):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(rows, request, view=view)
    data = serializer_cls(page, many=True, context={"request": request}).data
    return paginator.get_paginated_response(data)


# --- psychologist -------------------------------------------------------------


class PsychologistView(_WriteThrottled):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    def profile(self):
        return self.request.user.psychologist_profile


def _settings_response(profile):
    settings = selectors.booking_settings_for(profile)
    reason = selectors.not_bookable_reason(
        settings, selectors.windows_for(profile).exists()
    )
    return Response(
        BookingSettingsSerializer(settings, context={"reason": reason}).data
    )


class BookingSettingsView(PsychologistView):
    @extend_schema(responses={200: BookingSettingsSerializer})
    def get(self, request):
        return _settings_response(self.profile())

    @extend_schema(
        request=BookingSettingsWriteSerializer,
        responses={200: BookingSettingsSerializer, 400: ERRORS[400]},
        description="Any of session_minutes (30/50/60), fee_pkr (PKR, 100-100000) "
        "and video_link (https, zoom.us or meet.google.com).",
    )
    def patch(self, request):
        body = BookingSettingsWriteSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        _run(
            services.update_booking_settings,
            psychologist_profile=self.profile(),
            **body.validated_data,
        )
        return _settings_response(self.profile())


class WorkingHoursView(PsychologistView):
    def _payload(self):
        profile = self.profile()
        return WorkingHoursSerializer(
            {"windows": selectors.windows_for(profile), "timezone": profile.timezone}
        ).data

    @extend_schema(responses={200: WorkingHoursSerializer})
    def get(self, request):
        return Response(self._payload())

    @extend_schema(
        request=WorkingHoursSerializer,
        responses={200: WorkingHoursSerializer, 400: ERRORS[400]},
        description="Replaces every weekly window. Existing sessions are kept.",
    )
    def put(self, request):
        body = WorkingHoursSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        _run(
            services.replace_working_windows,
            psychologist_profile=self.profile(),
            windows=body.validated_data["windows"],
        )
        return Response(self._payload())


class DaysOffView(PsychologistView):
    @extend_schema(responses={200: DayOffSerializer(many=True)})
    def get(self, request):
        rows = selectors.days_off_for(self.profile())
        return Response(DayOffSerializer(rows, many=True).data)

    @extend_schema(
        request=DayOffWriteSerializer,
        responses={201: DayOffSerializer, 400: ERRORS[400]},
    )
    def post(self, request):
        body = DayOffWriteSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        day = _run(
            services.add_day_off,
            psychologist_profile=self.profile(),
            date=body.validated_data["date"],
        )
        return Response(DayOffSerializer(day).data, status=status.HTTP_201_CREATED)


class DayOffDetailView(PsychologistView):
    @extend_schema(responses={204: None, 404: ERRORS[404]})
    def delete(self, request, day_off_id):
        _run(
            services.remove_day_off,
            psychologist_profile=self.profile(),
            day_off_id=day_off_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PsychologistSlotsView(PsychologistView):
    @extend_schema(
        responses={200: FreeSlotsSerializer},
        description="Your own free slots (UTC), 12 hours to 30 days ahead: the "
        "times you can propose.",
    )
    def get(self, request):
        return Response(
            FreeSlotsSerializer({"slots": selectors.free_slots(self.profile())}).data
        )


class PsychologistSessionsView(PsychologistView):
    @extend_schema(
        parameters=[PsychologistSessionQuerySerializer],
        responses={200: PsychologistSessionSerializer(many=True)},
        description="`view=requests` (awaiting your answer or the patient's), "
        "`upcoming` (confirmed, default) or `past`. Paginated.",
    )
    def get(self, request):
        query = PsychologistSessionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = selectors.psychologist_sessions(
            psychologist_profile=self.profile(), view=query.validated_data["view"]
        )
        return _paginate(self, request, rows, PsychologistSessionSerializer)


class _PsychologistSessionAction(PsychologistView):
    def respond(self, session):
        return Response(
            PsychologistSessionSerializer(
                session, context={"request": self.request}
            ).data
        )


class ConfirmSessionView(_PsychologistSessionAction):
    @extend_schema(
        request=None, responses={200: PsychologistSessionSerializer, **ERRORS}
    )
    def post(self, request, session_id):
        session = _run(
            services.confirm_session,
            psychologist_profile=self.profile(),
            session_id=session_id,
            ip=_ip(request),
        )
        return self.respond(session)


class ProposeSessionView(_PsychologistSessionAction):
    @extend_schema(
        request=StartsAtSerializer,
        responses={200: PsychologistSessionSerializer, **ERRORS},
        description="Move a request to another of your free slots; the patient "
        "accepts or cancels.",
    )
    def post(self, request, session_id):
        body = StartsAtSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        session = _run(
            services.propose_time,
            psychologist_profile=self.profile(),
            session_id=session_id,
            starts_at=body.validated_data["starts_at"],
            ip=_ip(request),
        )
        return self.respond(session)


class PsychologistCancelSessionView(_PsychologistSessionAction):
    @extend_schema(
        request=None, responses={200: PsychologistSessionSerializer, **ERRORS}
    )
    def post(self, request, session_id):
        session = _run(
            services.psychologist_cancel_session,
            psychologist_profile=self.profile(),
            session_id=session_id,
            ip=_ip(request),
        )
        return self.respond(session)


class SessionOutcomeView(_PsychologistSessionAction):
    @extend_schema(
        request=OutcomeSerializer,
        responses={200: PsychologistSessionSerializer, **ERRORS},
        description="After a confirmed session has ended: completed or no_show.",
    )
    def post(self, request, session_id):
        body = OutcomeSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        session = _run(
            services.mark_outcome,
            psychologist_profile=self.profile(),
            session_id=session_id,
            outcome=body.validated_data["outcome"],
            ip=_ip(request),
        )
        return self.respond(session)


# --- patient --------------------------------------------------------------


class PatientView(_WriteThrottled):
    permission_classes = [IsAuthenticated, IsPatient]

    def profile(self):
        return self.request.user.patient_profile


class SlotsView(PatientView):
    @extend_schema(
        responses={200: SlotsSerializer, 400: ERRORS[400]},
        description="Free slots (UTC) with your current psychologist, from 12 hours "
        "to 30 days ahead.",
    )
    def get(self, request):
        data = selectors.slots_for_patient(patient_profile=self.profile())
        if data is None:
            raise ValidationError({"relationship": [services.NO_PSYCHOLOGIST]})
        return Response(SlotsSerializer(data).data)


class PatientSessionsView(PatientView):
    @extend_schema(
        responses={200: PatientSessionSerializer(many=True)},
        description="Your sessions, newest first, paginated.",
    )
    def get(self, request):
        rows = selectors.patient_sessions(patient_profile=self.profile())
        return _paginate(self, request, rows, PatientSessionSerializer)

    @extend_schema(
        request=StartsAtSerializer,
        responses={201: PatientSessionSerializer, 400: ERRORS[400]},
        description="Request one of the free slots. Your psychologist confirms it or "
        "proposes another time.",
    )
    def post(self, request):
        body = StartsAtSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        session = _run(
            services.book_session,
            patient_user=request.user,
            starts_at=body.validated_data["starts_at"],
            ip=_ip(request),
        )
        return Response(
            PatientSessionSerializer(session).data, status=status.HTTP_201_CREATED
        )


class AcceptProposalView(PatientView):
    @extend_schema(request=None, responses={200: PatientSessionSerializer, **ERRORS})
    def post(self, request, session_id):
        session = _run(
            services.accept_proposal,
            patient_user=request.user,
            session_id=session_id,
            ip=_ip(request),
        )
        return Response(PatientSessionSerializer(session).data)


class PatientCancelSessionView(PatientView):
    @extend_schema(
        request=None,
        responses={200: PatientSessionSerializer, **ERRORS},
        description="Free up to 24 h before a confirmed session; later it is "
        "recorded as a late cancellation.",
    )
    def post(self, request, session_id):
        session = _run(
            services.patient_cancel_session,
            patient_user=request.user,
            session_id=session_id,
            ip=_ip(request),
        )
        return Response(PatientSessionSerializer(session).data)
