"""DRF views for the Motivation Corner. Thin: parse -> selector -> serialize."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.motivation import selectors
from apps.motivation.api.serializers import QuoteQuerySerializer, QuoteSerializer
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
