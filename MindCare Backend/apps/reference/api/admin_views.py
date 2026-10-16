"""Admin city verification (admin-panel-2). Admins only (any admin, not just
super-admins), throttle `admin`. Thin views: parse -> service/selector -> serialize."""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.api.admin_views import AdminAPIView
from apps.reference import selectors, services
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.serializers import RejectUnknownFieldsMixin, search_field
from core.validators import COUNTRY_CODE_VALIDATOR


class AdminCityQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["unverified", "verified", "all"], required=False, default="unverified"
    )
    country = serializers.CharField(
        max_length=2, required=False, validators=[COUNTRY_CODE_VALIDATOR]
    )
    search = search_field(required=False, allow_blank=True)


class AdminCitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = serializers.CharField(source="country.code")
    country_name = serializers.CharField(source="country.name")
    is_verified = serializers.BooleanField()
    usage_count = serializers.IntegerField(
        help_text="Profiles and NGO service areas using this city."
    )


class MergeCitySerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    into = serializers.IntegerField(
        min_value=1, help_text="The city (same country) to move everything to."
    )


def _errors(exc):
    return ValidationError(exc.errors, code=exc.code)


class AdminCitiesView(AdminAPIView):
    @extend_schema(
        parameters=[AdminCityQuerySerializer],
        responses={200: AdminCitySerializer(many=True)},
        description=(
            "Cities for verification, paginated. Default `status=unverified`, "
            "oldest first."
        ),
    )
    def get(self, request):
        query = AdminCityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        cities = selectors.admin_cities(
            status=None if data["status"] == "all" else data["status"],
            country_code=data.get("country"),
            search=data.get("search") or None,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(cities, request, view=self)
        return paginator.get_paginated_response(
            AdminCitySerializer(page, many=True).data
        )


_ACTION_RESPONSES = {
    400: OpenApiResponse(description="The rule this action would break."),
    404: OpenApiResponse(description="No such city."),
}


class VerifyCityView(AdminAPIView):
    @extend_schema(
        request=None,
        responses={200: AdminCitySerializer, **_ACTION_RESPONSES},
        description="Shows the city in the public dropdown.",
    )
    def post(self, request, city_id):
        try:
            services.verify_city(actor=request.user, city_id=city_id)
        except services.CityNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        city = selectors.admin_cities().get(pk=city_id)
        return Response(AdminCitySerializer(city).data)


class MergeCityView(AdminAPIView):
    @extend_schema(
        request=MergeCitySerializer,
        responses={200: AdminCitySerializer, **_ACTION_RESPONSES},
        description=(
            "Moves every profile and NGO service area from this unverified city "
            "to `into` (same country), then deletes this city. Returns `into`."
        ),
    )
    def post(self, request, city_id):
        body = MergeCitySerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            target = services.merge_city(
                actor=request.user, city_id=city_id, into_id=body.validated_data["into"]
            )
        except services.CityNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(
            AdminCitySerializer(selectors.admin_cities().get(pk=target.pk)).data
        )


class RejectCityView(AdminAPIView):
    @extend_schema(
        request=None,
        responses={204: None, **_ACTION_RESPONSES},
        description="Deletes an unverified city that nothing uses.",
    )
    def post(self, request, city_id):
        try:
            services.reject_city(actor=request.user, city_id=city_id)
        except services.CityNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _errors(exc) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)
