"""DRF views for the wellness library (6.9). Thin: parse -> service/selector ->
serialize. Patients and approved, active psychologists read published items;
only patients save favourites. Nothing here is audited (no health data)."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.wellness import selectors, services
from apps.wellness.api.serializers import (
    FavouriteResultSerializer,
    ItemDetailSerializer,
    ItemListSerializer,
    ItemQuerySerializer,
)
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsPatient, IsPatientOrApprovedPsychologist


class WellnessRateThrottle(UserRateThrottle):
    scope = "wellness"


class WellnessFavouriteThrottle(UserRateThrottle):
    scope = "wellness_favourites"


def _patient(request):
    if request.user.role == Role.PATIENT:
        return request.user.patient_profile
    return None


def _favourite_ids(request, items):
    patient = _patient(request)
    if patient is None:
        return None
    return selectors.favourite_item_ids(
        patient_profile=patient, item_ids=[item.pk for item in items]
    )


class _LibraryView(APIView):
    permission_classes = [IsAuthenticated, IsPatientOrApprovedPsychologist]
    throttle_classes = [WellnessRateThrottle]


class ItemListView(_LibraryView):
    @extend_schema(
        parameters=[ItemQuerySerializer],
        responses={200: ItemListSerializer(many=True), 403: OpenApiResponse()},
        description=(
            "Published library items, paginated (`sort_order`, then newest). The "
            "page also carries a fixed `disclaimer`. Patients and approved "
            "psychologists."
        ),
    )
    def get(self, request):
        query = ItemQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = selectors.published_items(**query.validated_data)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        data = ItemListSerializer(
            page, many=True, context={"favourite_ids": _favourite_ids(request, page)}
        ).data
        response = paginator.get_paginated_response(data)
        response.data["disclaimer"] = selectors.DISCLAIMER
        return response


class ItemDetailView(_LibraryView):
    @extend_schema(
        responses={200: ItemDetailSerializer, 403: OpenApiResponse(), 404: None},
        description="One published item with its text, steps and media links.",
    )
    def get(self, request, pk):
        item = selectors.published_item(item_id=pk)
        if item is None:
            raise NotFound()
        context = {"favourite_ids": _favourite_ids(request, [item])}
        return Response(ItemDetailSerializer(item, context=context).data)


class FavouriteListView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]
    throttle_classes = [WellnessRateThrottle]

    @extend_schema(
        responses={200: ItemListSerializer(many=True), 403: OpenApiResponse()},
        description="Your saved items that are still published, newest save first.",
    )
    def get(self, request):
        items = selectors.patient_favourites(
            patient_profile=request.user.patient_profile
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(items, request, view=self)
        data = ItemListSerializer(
            page, many=True, context={"favourite_ids": {i.pk for i in page}}
        ).data
        return paginator.get_paginated_response(data)


class FavouriteView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]
    throttle_classes = [WellnessFavouriteThrottle]

    @extend_schema(
        request=None,
        responses={
            200: FavouriteResultSerializer,
            400: OpenApiResponse(description="Already 200 saved items."),
            404: None,
        },
        description="Save a published item. Saving it again changes nothing.",
    )
    def put(self, request, pk):
        try:
            services.add_favourite(
                patient_profile=request.user.patient_profile, item_id=pk
            )
        except services.NotFound as exc:
            raise NotFound() from exc
        except DomainValidationError as exc:
            raise ValidationError(exc.errors, code=exc.code) from exc
        return Response({"is_favourite": True})

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, pk):
        services.remove_favourite(
            patient_profile=request.user.patient_profile, item_id=pk
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
