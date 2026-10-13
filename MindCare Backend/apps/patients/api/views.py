"""DRF views for the patients API.

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.patients import selectors, services
from apps.patients.api.serializers import (
    MentalHealthHistoryInputSerializer,
    MentalHealthHistorySerializer,
    PatientProfileOwnerSerializer,
    PatientProfileUpdateSerializer,
)
from core.exceptions import DomainValidationError
from core.permissions import IsPatient
from core.serializers import PhotoUploadSerializer


class MyPatientProfileView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def _profile(self, request):
        profile = selectors.get_patient_profile_for_user(user=request.user)
        if profile is None:
            raise NotFound("Profile not found.")
        return profile

    @extend_schema(responses=PatientProfileOwnerSerializer)
    def get(self, request):
        return Response(PatientProfileOwnerSerializer(self._profile(request)).data)

    @extend_schema(
        request=PatientProfileUpdateSerializer,
        responses=PatientProfileOwnerSerializer,
    )
    def patch(self, request):
        profile = self._profile(request)
        serializer = PatientProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            profile = services.update_patient_profile(
                profile=profile, **serializer.validated_data
            )
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(PatientProfileOwnerSerializer(profile).data)


class UploadRateThrottle(UserRateThrottle):
    scope = "uploads"


class MyPatientPhotoView(MyPatientProfileView):
    """PUT a profile photo (multipart, field `photo`), or DELETE it."""

    http_method_names = ["put", "delete", "options"]
    parser_classes = [MultiPartParser]
    throttle_classes = [UploadRateThrottle]

    def get_throttles(self):
        return super().get_throttles() if self.request.method == "PUT" else []

    @extend_schema(
        request={"multipart/form-data": PhotoUploadSerializer},
        responses={200: PatientProfileOwnerSerializer},
        description=(
            "JPG, PNG or WEBP, max 5 MB. Re-encoded on the server (EXIF such as GPS "
            "location removed) and shrunk to at most 1024 px."
        ),
    )
    def put(self, request):
        profile = self._profile(request)
        body = PhotoUploadSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        profile = services.set_patient_photo(
            profile=profile, checked=body.validated_data["photo"]
        )
        return Response(PatientProfileOwnerSerializer(profile).data)

    @extend_schema(request=None, responses={200: PatientProfileOwnerSerializer})
    def delete(self, request):
        profile = services.remove_patient_photo(profile=self._profile(request))
        return Response(PatientProfileOwnerSerializer(profile).data)


class MyMentalHealthHistoryView(MyPatientProfileView):
    """The patient's optional mental health history (6.1). Encrypted at rest;
    writes are audited; only the patient and their current psychologist read it."""

    http_method_names = ["get", "put", "delete", "options"]

    @extend_schema(responses={200: MentalHealthHistorySerializer})
    def get(self, request):
        history = selectors.get_mental_health_history(
            patient_profile=self._profile(request)
        )
        return Response(MentalHealthHistorySerializer.data_for(history))

    @extend_schema(
        request=MentalHealthHistoryInputSerializer,
        responses={200: MentalHealthHistorySerializer},
        description="Replaces the whole history; anything not sent is cleared.",
    )
    def put(self, request):
        profile = self._profile(request)
        body = MentalHealthHistoryInputSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = body.validated_data
        try:
            history = services.save_mental_health_history(
                profile=profile,
                actor=request.user,
                concerns=data.get("concerns", []),
                previous_diagnosis=data.get("previous_diagnosis") or "",
                current_medication=data.get("current_medication") or "",
                previous_therapy=data.get("previous_therapy") or "",
                notes=data.get("notes") or "",
                ip=request.META.get("REMOTE_ADDR"),
            )
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(MentalHealthHistorySerializer.data_for(history))

    @extend_schema(request=None, responses={204: None})
    def delete(self, request):
        services.delete_mental_health_history(
            profile=self._profile(request),
            actor=request.user,
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
