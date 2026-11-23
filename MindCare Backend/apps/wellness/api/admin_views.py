"""Admin wellness console: CRUD for library items plus cover image and audio
upload. Any admin (not only super-admins), throttle `admin`; uploads also
`wellness_uploads`. Thin views: parse -> service/selector -> serialize."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.accounts.api.admin_views import AdminAPIView
from apps.wellness import selectors, services
from apps.wellness.api.admin_serializers import (
    AdminItemQuerySerializer,
    AdminItemSerializer,
    ItemAudioUploadSerializer,
    ItemImageUploadSerializer,
)
from apps.wellness.models import WellnessItem
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination


class WellnessUploadThrottle(UserRateThrottle):
    scope = "wellness_uploads"


def _errors(exc):
    return ValidationError(exc.errors, code=exc.code)


def _get(pk):
    item = WellnessItem.objects.filter(pk=pk).first()
    if item is None:
        raise Http404
    return item


class AdminItemListView(AdminAPIView):
    @extend_schema(
        parameters=[AdminItemQuerySerializer],
        responses={200: AdminItemSerializer(many=True)},
        description="Every library item, published or hidden, paginated. Admins only.",
    )
    def get(self, request):
        query = AdminItemQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = selectors.admin_items(**query.validated_data)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        return paginator.get_paginated_response(
            AdminItemSerializer(page, many=True).data
        )

    @extend_schema(
        request=AdminItemSerializer,
        responses={201: AdminItemSerializer, 400: OpenApiResponse()},
        description=(
            "Add an item. It stays hidden until `is_published` is true. Articles "
            "need `body`; practices and routines need at least one step."
        ),
    )
    def post(self, request):
        body = AdminItemSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            item = services.create_item(actor=request.user, data=body.validated_data)
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(AdminItemSerializer(item).data, status=status.HTTP_201_CREATED)


class AdminItemDetailView(AdminAPIView):
    @extend_schema(responses={200: AdminItemSerializer, 404: OpenApiResponse()})
    def get(self, request, pk):
        return Response(AdminItemSerializer(_get(pk)).data)

    @extend_schema(
        request=AdminItemSerializer,
        responses={
            200: AdminItemSerializer,
            400: OpenApiResponse(),
            404: OpenApiResponse(),
        },
        description="Edit an item; set is_published=false to hide it.",
    )
    def patch(self, request, pk):
        item = _get(pk)
        body = AdminItemSerializer(item, data=request.data, partial=True)
        body.is_valid(raise_exception=True)
        try:
            item = services.update_item(
                actor=request.user, item=item, data=body.validated_data
            )
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(AdminItemSerializer(item).data)

    @extend_schema(
        responses={
            204: None,
            400: OpenApiResponse(description="Used in a care plan: hide it instead."),
            404: OpenApiResponse(),
        },
        description=(
            "Delete an item (and its media) for good, only if no care-plan task has "
            "ever linked to it."
        ),
    )
    def delete(self, request, pk):
        try:
            services.delete_item(actor=request.user, item=_get(pk))
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class _MediaView(AdminAPIView):
    media = None
    upload_serializer = None
    parser_classes = [MultiPartParser]
    throttle_classes = [*AdminAPIView.throttle_classes, WellnessUploadThrottle]

    def _put(self, request, pk):
        item = _get(pk)
        body = self.upload_serializer(data=request.data)
        body.is_valid(raise_exception=True)
        item = services.set_media(
            item=item,
            media=self.media,
            checked=body.validated_data[self.media],
            actor=request.user,
        )
        return Response(AdminItemSerializer(item).data)

    def _delete(self, request, pk):
        item = _get(pk)
        if not getattr(item, f"{self.media}_key"):
            raise ValidationError({self.media: ["There is nothing to remove."]})
        item = services.remove_media(item=item, media=self.media, actor=request.user)
        return Response(AdminItemSerializer(item).data)


class AdminItemImageView(_MediaView):
    media = "image"
    upload_serializer = ItemImageUploadSerializer

    @extend_schema(
        request={"multipart/form-data": ItemImageUploadSerializer},
        responses={200: AdminItemSerializer, 400: OpenApiResponse(), 404: None},
        description=(
            "Upload or replace the cover image (`image` part): JPG, PNG or WEBP, "
            "5 MB, re-encoded (EXIF removed), shrunk to 1600 px. Only images you "
            "hold the rights to."
        ),
    )
    def put(self, request, pk):
        return self._put(request, pk)

    @extend_schema(
        request=None,
        responses={200: AdminItemSerializer, 400: OpenApiResponse(), 404: None},
        description="Remove the cover image.",
    )
    def delete(self, request, pk):
        return self._delete(request, pk)


class AdminItemAudioView(_MediaView):
    media = "audio"
    upload_serializer = ItemAudioUploadSerializer

    @extend_schema(
        request={"multipart/form-data": ItemAudioUploadSerializer},
        responses={200: AdminItemSerializer, 400: OpenApiResponse(), 404: None},
        description=(
            "Upload or replace the guided audio (`audio` part): MP3, M4A or OGG, "
            "15 MB, checked by content. Only audio you hold the rights to."
        ),
    )
    def put(self, request, pk):
        return self._put(request, pk)

    @extend_schema(
        request=None,
        responses={200: AdminItemSerializer, 400: OpenApiResponse(), 404: None},
        description="Remove the audio.",
    )
    def delete(self, request, pk):
        return self._delete(request, pk)
