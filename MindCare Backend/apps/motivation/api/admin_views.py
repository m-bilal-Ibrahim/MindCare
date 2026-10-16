"""Admin content console (admin-panel-2): CRUD for quotes, duas and surahs, and
recitation upload. Any admin (not only super-admins), throttle `admin`. Thin
views: parse -> service/selector -> serialize."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.accounts.api.admin_views import AdminAPIView
from apps.motivation import selectors, services
from apps.motivation.api.admin_serializers import (
    AdminContentQuerySerializer,
    AdminDuaSerializer,
    AdminQuoteSerializer,
    AdminSurahSerializer,
    AudioUploadSerializer,
)
from apps.motivation.models import Dua, Quote, Surah
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination


def _errors(exc):
    return ValidationError(exc.errors, code=exc.code)


class _ContentListView(AdminAPIView):
    model = None
    serializer_class = None

    def get(self, request):
        query = AdminContentQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = selectors.admin_content(
            model=self.model, is_active=query.validated_data.get("is_active")
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        return paginator.get_paginated_response(
            self.serializer_class(page, many=True).data
        )

    def post(self, request):
        body = self.serializer_class(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            content = services.create_content(
                actor=request.user, model=self.model, data=body.validated_data
            )
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(
            self.serializer_class(content).data, status=status.HTTP_201_CREATED
        )


class _ContentDetailView(AdminAPIView):
    model = None
    serializer_class = None

    def _get(self, pk):
        content = self.model.objects.filter(pk=pk).first()
        if content is None:
            raise Http404
        return content

    def get(self, request, pk):
        return Response(self.serializer_class(self._get(pk)).data)

    def patch(self, request, pk):
        content = self._get(pk)
        body = self.serializer_class(content, data=request.data, partial=True)
        body.is_valid(raise_exception=True)
        try:
            content = services.update_content(
                actor=request.user, content=content, data=body.validated_data
            )
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(self.serializer_class(content).data)

    def delete(self, request, pk):
        services.delete_content(actor=request.user, content=self._get(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)


class _ContentAudioView(AdminAPIView):
    model = None
    serializer_class = None
    parser_classes = [MultiPartParser]

    def _get(self, pk):
        content = self.model.objects.filter(pk=pk).first()
        if content is None:
            raise Http404
        return content

    def put(self, request, pk):
        content = self._get(pk)
        body = AudioUploadSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        content = services.set_content_audio_by_admin(
            actor=request.user, content=content, checked=body.validated_data["audio"]
        )
        return Response(self.serializer_class(content).data)

    def delete(self, request, pk):
        content = self._get(pk)
        if not content.audio_key:
            raise ValidationError({"audio": ["There is no recitation to remove."]})
        content = services.remove_content_audio_by_admin(
            actor=request.user, content=content
        )
        return Response(self.serializer_class(content).data)


def _own(method):
    """A fresh function per class, so extend_schema doesn't tag the shared one."""

    def wrapper(self, *args, **kwargs):
        return method(self, *args, **kwargs)

    wrapper.__name__ = method.__name__
    return wrapper


def _list_view(name, model, serializer):
    doc = extend_schema(
        parameters=[AdminContentQuerySerializer],
        responses={200: serializer(many=True)},
        description=f"Every {name}, active or hidden, paginated. Admins only.",
    )
    create_doc = extend_schema(
        request=serializer,
        responses={201: serializer, 400: OpenApiResponse()},
        description=f"Add a {name}. It shows in the app at once if is_active.",
    )
    attrs = {
        "model": model,
        "serializer_class": serializer,
        "get": doc(_own(_ContentListView.get)),
        "post": create_doc(_own(_ContentListView.post)),
    }
    return type(f"Admin{model.__name__}ListView", (_ContentListView,), attrs)


def _detail_view(name, model, serializer):
    attrs = {
        "model": model,
        "serializer_class": serializer,
        "get": extend_schema(responses={200: serializer, 404: OpenApiResponse()})(
            _own(_ContentDetailView.get)
        ),
        "patch": extend_schema(
            request=serializer,
            responses={200: serializer, 400: OpenApiResponse(), 404: OpenApiResponse()},
            description=f"Edit a {name}; set is_active=false to hide it.",
        )(_own(_ContentDetailView.patch)),
        "delete": extend_schema(
            responses={204: None, 404: OpenApiResponse()},
            description=(
                f"Delete a {name} for good (its recitation too). Prefer "
                "is_active=false to hide it."
            ),
        )(_own(_ContentDetailView.delete)),
    }
    return type(f"Admin{model.__name__}DetailView", (_ContentDetailView,), attrs)


def _audio_view(name, model, serializer):
    attrs = {
        "model": model,
        "serializer_class": serializer,
        "put": extend_schema(
            request={"multipart/form-data": AudioUploadSerializer},
            responses={200: serializer, 400: OpenApiResponse(), 404: OpenApiResponse()},
            description=(
                f"Upload or replace the {name}'s recitation (`audio` part): MP3, "
                "M4A or OGG, 15 MB, checked by content. Only audio you hold the "
                "rights to."
            ),
        )(_own(_ContentAudioView.put)),
        "delete": extend_schema(
            request=None,
            responses={200: serializer, 400: OpenApiResponse(), 404: OpenApiResponse()},
            description=f"Remove the {name}'s recitation.",
        )(_own(_ContentAudioView.delete)),
    }
    return type(f"Admin{model.__name__}AudioView", (_ContentAudioView,), attrs)


AdminQuoteListView = _list_view("quote", Quote, AdminQuoteSerializer)
AdminQuoteDetailView = _detail_view("quote", Quote, AdminQuoteSerializer)
AdminDuaListView = _list_view("dua", Dua, AdminDuaSerializer)
AdminDuaDetailView = _detail_view("dua", Dua, AdminDuaSerializer)
AdminDuaAudioView = _audio_view("dua", Dua, AdminDuaSerializer)
AdminSurahListView = _list_view("surah", Surah, AdminSurahSerializer)
AdminSurahDetailView = _detail_view("surah", Surah, AdminSurahSerializer)
AdminSurahAudioView = _audio_view("surah", Surah, AdminSurahSerializer)
