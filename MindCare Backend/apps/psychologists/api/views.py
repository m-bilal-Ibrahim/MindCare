"""DRF views for the psychologists API.

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from apps.psychologists import selectors, services
from apps.psychologists.api.serializers import (
    AvailabilitySerializer,
    DirectoryCardSerializer,
    DirectoryQuerySerializer,
    PsychologistProfileOwnerSerializer,
    PsychologistRegistrationProfileSerializer,
)
from apps.relationships import services as relationship_services
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.serializers import PhotoUploadSerializer
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist


class MyPsychologistProfileView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist]

    def _profile(self, request):
        profile = selectors.get_psychologist_profile_for_user(user=request.user)
        if profile is None:
            raise NotFound("Profile not found.")
        return profile

    @extend_schema(responses=PsychologistProfileOwnerSerializer)
    def get(self, request):
        return Response(PsychologistProfileOwnerSerializer(self._profile(request)).data)

    @extend_schema(
        request=PsychologistRegistrationProfileSerializer,
        responses=PsychologistProfileOwnerSerializer,
    )
    def patch(self, request):
        profile = self._profile(request)
        serializer = PsychologistRegistrationProfileSerializer(
            data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        try:
            profile = services.update_psychologist_profile(
                profile=profile, **serializer.validated_data
            )
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        profile = selectors.get_psychologist_profile_for_user(user=request.user)
        return Response(PsychologistProfileOwnerSerializer(profile).data)


class DirectoryRateThrottle(UserRateThrottle):
    scope = "directory"


class DirectoryListView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]
    throttle_classes = [DirectoryRateThrottle]

    @extend_schema(
        parameters=[DirectoryQuerySerializer],
        responses=DirectoryCardSerializer(many=True),
    )
    def get(self, request):
        query = DirectoryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        qs = selectors.list_directory(**query.validated_data)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            DirectoryCardSerializer(page, many=True).data
        )


class DirectoryDetailView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]
    throttle_classes = [DirectoryRateThrottle]

    @extend_schema(responses=DirectoryCardSerializer)
    def get(self, request, pk):
        profile = selectors.get_directory_entry(profile_id=pk)
        if profile is None:
            raise NotFound()
        return Response(DirectoryCardSerializer(profile).data)


class AvailabilityView(APIView):
    """The psychologist's "accepting new patients" switch. Approved, active
    psychologists only (unlike /me/, which a pending psychologist still needs)."""

    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    @staticmethod
    def _payload(profile):
        return {
            "accepting": profile.is_accepting_patients,
            "reason": profile.not_accepting_reason,
        }

    @extend_schema(responses=AvailabilitySerializer)
    def get(self, request):
        profile = selectors.get_psychologist_profile_for_user(user=request.user)
        if profile is None:
            raise NotFound("Profile not found.")
        return Response(self._payload(profile))

    @extend_schema(request=AvailabilitySerializer, responses=AvailabilitySerializer)
    def put(self, request):
        body = AvailabilitySerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            profile = relationship_services.set_accepting_status(
                psychologist_user=request.user,
                accepting=body.validated_data["accepting"],
                reason=body.validated_data.get("reason"),
            )
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response(self._payload(profile))


class UploadRateThrottle(UserRateThrottle):
    scope = "uploads"


class MyPsychologistPhotoView(MyPsychologistProfileView):
    """PUT the photo patients see in the directory (multipart, field `photo`),
    or DELETE it. Pending psychologists may set it too, like /me/."""

    http_method_names = ["put", "delete", "options"]
    parser_classes = [MultiPartParser]

    def get_throttles(self):
        return [UploadRateThrottle()] if self.request.method == "PUT" else []

    @extend_schema(
        request={"multipart/form-data": PhotoUploadSerializer},
        responses={200: PsychologistProfileOwnerSerializer},
        description=(
            "JPG, PNG or WEBP, max 5 MB. Re-encoded on the server (EXIF removed) "
            "and shrunk to at most 1024 px."
        ),
    )
    def put(self, request):
        profile = self._profile(request)
        body = PhotoUploadSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        profile = services.set_psychologist_photo(
            profile=profile, checked=body.validated_data["photo"]
        )
        return Response(PsychologistProfileOwnerSerializer(profile).data)

    @extend_schema(request=None, responses={200: PsychologistProfileOwnerSerializer})
    def delete(self, request):
        profile = services.remove_psychologist_photo(profile=self._profile(request))
        return Response(PsychologistProfileOwnerSerializer(profile).data)
