"""DRF views for the emergency API (6.12 SOS). Thin: parse -> service/selector ->
serialize. Pressing SOS has no throttle and never answers with an error."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.api.admin_views import AdminAPIView
from apps.emergency import selectors, services
from apps.emergency.api.serializers import (
    AdminSOSDetailSerializer,
    AdminSOSListItemSerializer,
    AdminSOSQuerySerializer,
    CloseSOSSerializer,
    EmergencyContactSerializer,
    EmergencyContactUpdateSerializer,
    EmergencyContactWriteSerializer,
    EmergencyResourcesSerializer,
    PsychologistAlertSerializer,
    SOSEventSerializer,
    SOSRequestSerializer,
    SOSResponseSerializer,
)
from apps.patients.selectors import get_patient_display_identity
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _domain(exc):
    return ValidationError(exc.errors, code=exc.code)


class EmergencyContactsThrottle(UserRateThrottle):
    scope = "emergency_contacts"


class PatientView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]


class ResourcesView(PatientView):
    @extend_schema(
        responses={200: EmergencyResourcesSerializer},
        description="What the SOS screen shows, without pressing SOS: the "
        "emergency message, helplines, hospitals in the profile city, the current "
        "psychologist and NGOs serving the patient's area. Lists may be empty.",
    )
    def get(self, request):
        resources = selectors.emergency_resources(
            patient_profile=request.user.patient_profile
        )
        return Response(EmergencyResourcesSerializer(resources).data)


class SOSView(PatientView):
    @extend_schema(
        request=SOSRequestSerializer,
        responses={
            201: SOSResponseSerializer,
            400: OpenApiResponse(description="Only for malformed coordinates."),
        },
        description="Press SOS. Never throttled. Notifies emergency contacts and "
        "the current psychologist by email (at most once per 30 minutes). Always "
        "answers 201 with the emergency message and resources; `alert` is null "
        "only if recording the alert failed.",
    )
    def post(self, request):
        body = SOSRequestSerializer(data=request.data)
        if not body.is_valid():
            # Bad coordinates must not stop an SOS: drop them and carry on.
            data = {}
        else:
            data = body.validated_data
        event, resources = services.press_sos(
            patient_user=request.user,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
        payload = SOSResponseSerializer({**resources, "alert": event}).data
        return Response(payload, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: SOSEventSerializer(many=True)})
    def get(self, request):
        events = selectors.events_for_patient(
            patient_profile=request.user.patient_profile
        )
        return Response(SOSEventSerializer(events, many=True).data)


class CancelSOSView(PatientView):
    @extend_schema(
        request=None,
        responses={
            200: SOSEventSerializer,
            400: OpenApiResponse(description="More than 5 minutes old, or not open."),
            404: OpenApiResponse(),
        },
        description='"I\'m safe": cancel within 5 minutes. Notified contacts get '
        "a follow-up email. The alert stays on record.",
    )
    def post(self, request, event_id):
        try:
            event = services.cancel_sos(patient_user=request.user, event_id=event_id)
        except services.NotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(SOSEventSerializer(event).data)


class ContactsView(PatientView):
    def get_throttles(self):
        return [EmergencyContactsThrottle()] if self.request.method == "POST" else []

    @extend_schema(responses={200: EmergencyContactSerializer(many=True)})
    def get(self, request):
        contacts = selectors.contacts_for(patient_profile=request.user.patient_profile)
        return Response(EmergencyContactSerializer(contacts, many=True).data)

    @extend_schema(
        request=EmergencyContactWriteSerializer,
        responses={
            201: EmergencyContactSerializer,
            400: OpenApiResponse(description="Invalid input or already 3 contacts."),
        },
        description="Add an emergency contact (at most 3). Every field is encrypted "
        "at rest. `consent_confirmed` must be true.",
    )
    def post(self, request):
        body = EmergencyContactWriteSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        try:
            contact = services.add_contact(
                patient_user=request.user,
                name=data["name"],
                relationship=data["relationship"],
                email=data["email"],
                phone=data.get("phone", ""),
                ip=_ip(request),
            )
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(
            EmergencyContactSerializer(contact).data, status=status.HTTP_201_CREATED
        )


class ContactDetailView(PatientView):
    def get_throttles(self):
        return [EmergencyContactsThrottle()] if self.request.method == "PATCH" else []

    @extend_schema(
        request=EmergencyContactUpdateSerializer,
        responses={200: EmergencyContactSerializer, 404: OpenApiResponse()},
    )
    def patch(self, request, contact_id):
        body = EmergencyContactUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            contact = services.update_contact(
                patient_user=request.user,
                contact_id=contact_id,
                ip=_ip(request),
                **body.validated_data,
            )
        except services.NotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(EmergencyContactSerializer(contact).data)

    @extend_schema(responses={204: None, 404: OpenApiResponse()})
    def delete(self, request, contact_id):
        try:
            services.delete_contact(
                patient_user=request.user, contact_id=contact_id, ip=_ip(request)
            )
        except services.NotFound as exc:
            raise Http404 from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class PsychologistAlertsView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    @extend_schema(
        responses={200: PsychologistAlertSerializer(many=True)},
        description="SOS alerts from your current patients in the last 30 days. "
        "Every alert shown is recorded in the access audit trail.",
    )
    def get(self, request):
        events, relationship_by_patient = services.read_events_for_psychologist(
            psychologist_user=request.user, ip=_ip(request)
        )
        rows = [
            {
                "id": event.pk,
                "created_at": event.created_at,
                "status": event.status,
                "relationship_id": relationship_by_patient[event.patient_id],
                "patient_name": get_patient_display_identity(
                    patient_profile=event.patient, viewer=request.user
                )["display_name"],
            }
            for event in events
        ]
        return Response(PsychologistAlertSerializer(rows, many=True).data)


class AdminSOSListView(AdminAPIView):
    @extend_schema(
        parameters=[AdminSOSQuerySerializer],
        responses={200: AdminSOSListItemSerializer(many=True)},
        description="SOS alerts, paginated. `status=open` lists the oldest first. "
        "Private patients appear by pseudonym.",
    )
    def get(self, request):
        query = AdminSOSQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        events = selectors.events_for_admin(status=query.validated_data.get("status"))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(
            AdminSOSListItemSerializer(page, many=True).data
        )


class AdminSOSDetailView(AdminAPIView):
    @extend_schema(
        responses={200: AdminSOSDetailSerializer, 404: OpenApiResponse()},
        description="Opening an alert is audited, and so is revealing a private "
        "patient's identity.",
    )
    def get(self, request, event_id):
        try:
            event = services.read_event_for_admin(
                admin=request.user, event_id=event_id, ip=_ip(request)
            )
        except services.NotFound as exc:
            raise Http404 from exc
        return Response(
            AdminSOSDetailSerializer(event, context={"request": request}).data
        )


class AdminSOSFollowUpView(AdminAPIView):
    @extend_schema(
        request=None,
        responses={
            200: AdminSOSListItemSerializer,
            400: OpenApiResponse(description="Already closed."),
            404: OpenApiResponse(),
        },
    )
    def post(self, request, event_id):
        try:
            event = services.follow_up_event(admin=request.user, event_id=event_id)
        except services.NotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(AdminSOSListItemSerializer(event).data)


class AdminSOSCloseView(AdminAPIView):
    @extend_schema(
        request=CloseSOSSerializer,
        responses={
            200: AdminSOSListItemSerializer,
            400: OpenApiResponse(description="Invalid outcome, or already closed."),
            404: OpenApiResponse(),
        },
    )
    def post(self, request, event_id):
        body = CloseSOSSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            event = services.close_event(
                admin=request.user,
                event_id=event_id,
                outcome=body.validated_data["outcome"],
            )
        except services.NotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain(exc) from exc
        return Response(AdminSOSListItemSerializer(event).data)
