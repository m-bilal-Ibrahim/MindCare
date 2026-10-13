"""DRF views for the Motivation Corner. Thin: parse -> selector -> serialize."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.motivation import selectors, services
from apps.motivation.api.serializers import (
    DuaSerializer,
    QuoteQuerySerializer,
    QuoteSerializer,
    ReligiousPreferenceSerializer,
    SurahListSerializer,
    SurahSerializer,
)
from apps.motivation.permissions import HasReligiousOptIn
from core.permissions import IsPatient
from core.pagination import StandardPagination


class MotivationRateThrottle(UserRateThrottle):
    scope = "motivation"


class _QuoteView(APIView):
    """Any logged-in user (patients and psychologists)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [MotivationRateThrottle]

    def _category(self, request):
        query = QuoteQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return query.validated_data.get("category")


class QuoteListView(_QuoteView):
    @extend_schema(
        parameters=[QuoteQuerySerializer], responses=QuoteSerializer(many=True)
    )
    def get(self, request):
        qs = selectors.active_quotes(category=self._category(request))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(QuoteSerializer(page, many=True).data)


class RandomQuoteView(_QuoteView):
    @extend_schema(
        parameters=[QuoteQuerySerializer],
        responses={
            200: QuoteSerializer,
            404: OpenApiResponse(description="No active quote (in that category)."),
        },
    )
    def get(self, request):
        quote = selectors.random_active_quote(category=self._category(request))
        if quote is None:
            raise NotFound("No quotes available.")
        return Response(QuoteSerializer(quote).data)


# --- Religious content (6.10): patients only, and only after opting in --------


class ReligiousPreferenceView(APIView):
    """The patient's opt-in to Quran and dua content. Off by default; opting out
    deletes the record (docs/decisions.md, 2026-10-11)."""

    permission_classes = [IsAuthenticated, IsPatient]
    throttle_classes = [MotivationRateThrottle]

    @extend_schema(responses={200: ReligiousPreferenceSerializer})
    def get(self, request):
        opted_in = selectors.has_opted_in_to_religious_content(user=request.user)
        return Response({"opted_in": opted_in})

    @extend_schema(
        request=ReligiousPreferenceSerializer,
        responses={200: ReligiousPreferenceSerializer},
    )
    def put(self, request):
        body = ReligiousPreferenceSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        opted_in = services.set_religious_opt_in(
            user=request.user, opted_in=body.validated_data["opted_in"]
        )
        return Response({"opted_in": opted_in})


class _ReligiousView(APIView):
    permission_classes = [IsAuthenticated, IsPatient, HasReligiousOptIn]
    throttle_classes = [MotivationRateThrottle]


class DuaListView(_ReligiousView):
    @extend_schema(
        responses={200: DuaSerializer(many=True), 403: OpenApiResponse()},
        description="Active duas in their set order. Patients who opted in only.",
    )
    def get(self, request):
        return Response(DuaSerializer(selectors.active_duas(), many=True).data)


class DuaDetailView(_ReligiousView):
    @extend_schema(responses={200: DuaSerializer, 403: OpenApiResponse(), 404: None})
    def get(self, request, pk):
        dua = selectors.active_duas().filter(pk=pk).first()
        if dua is None:
            raise NotFound()
        return Response(DuaSerializer(dua).data)


class SurahListView(_ReligiousView):
    @extend_schema(
        responses={200: SurahListSerializer(many=True), 403: OpenApiResponse()},
        description="Active surahs by number (names only; open one for its text).",
    )
    def get(self, request):
        return Response(SurahListSerializer(selectors.active_surahs(), many=True).data)


class SurahDetailView(_ReligiousView):
    @extend_schema(responses={200: SurahSerializer, 403: OpenApiResponse(), 404: None})
    def get(self, request, number):
        surah = selectors.active_surahs().filter(number=number).first()
        if surah is None:
            raise NotFound()
        return Response(SurahSerializer(surah).data)
