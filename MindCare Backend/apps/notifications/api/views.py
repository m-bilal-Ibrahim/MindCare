"""DRF views for the in-app notifications API. Thin: parse -> service/selector ->
serialize. Every user sees only their own notifications; anyone else's id is a
404."""

from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.notifications import selectors, services
from apps.notifications.api.serializers import (
    EmptyBodySerializer,
    NotificationQuerySerializer,
    NotificationSerializer,
    ReadAllSerializer,
    ReminderPreferenceSerializer,
    UnreadCountSerializer,
)
from apps.notifications.models import NotificationType
from core.pagination import StandardPagination


class NotificationsThrottle(UserRateThrottle):
    scope = "notifications"


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [NotificationsThrottle]


def _empty_body(request):
    EmptyBodySerializer(data=request.data or {}).is_valid(raise_exception=True)


class NotificationListView(NotificationView):
    @extend_schema(
        parameters=[
            OpenApiParameter("unread", bool, description="true: unread only."),
            OpenApiParameter("type", str, enum=NotificationType.values),
        ],
        responses={200: NotificationSerializer(many=True)},
        description="Your notifications, newest first, paginated.",
    )
    def get(self, request):
        query = NotificationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = selectors.notifications_for(
            user=request.user,
            unread=query.validated_data.get("unread"),
            type=query.validated_data.get("type"),
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(
            NotificationSerializer(page, many=True).data
        )


class UnreadCountView(NotificationView):
    @extend_schema(
        responses={200: UnreadCountSerializer},
        description="How many of your notifications are unread (poll every 60 s).",
    )
    def get(self, request):
        count = selectors.unread_count(user=request.user)
        return Response(UnreadCountSerializer({"count": count}).data)


class NotificationReadView(NotificationView):
    @extend_schema(
        request=None,
        responses={200: NotificationSerializer, 404: OpenApiResponse()},
        description="Mark one of your notifications as read.",
    )
    def post(self, request, notification_id):
        _empty_body(request)
        try:
            row = services.mark_read(user=request.user, notification_id=notification_id)
        except services.NotFound as exc:
            raise Http404 from exc
        return Response(NotificationSerializer(row).data)


class ReadAllView(NotificationView):
    @extend_schema(
        request=None,
        responses={200: ReadAllSerializer},
        description="Mark all your notifications as read.",
    )
    def post(self, request):
        _empty_body(request)
        updated = services.mark_all_read(user=request.user)
        return Response(ReadAllSerializer({"updated": updated}).data)


class ReminderPreferenceView(NotificationView):
    @extend_schema(
        responses={200: ReminderPreferenceSerializer},
        description=(
            "Your reminder switches (all on by default). check_in_reminders and "
            "care_plan_reminders apply to patients; session_reminder_emails to "
            "patients and psychologists. In-app session and care-request "
            "reminders can't be turned off."
        ),
    )
    def get(self, request):
        row = selectors.reminder_preferences_for(user=request.user)
        return Response(ReminderPreferenceSerializer(row).data)

    @extend_schema(
        request=ReminderPreferenceSerializer,
        responses={200: ReminderPreferenceSerializer},
        description="Change any of your reminder switches.",
    )
    def patch(self, request):
        body = ReminderPreferenceSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        row = services.update_reminder_preferences(
            user=request.user, **body.validated_data
        )
        return Response(ReminderPreferenceSerializer(row).data)


class NotificationDetailView(NotificationView):
    @extend_schema(responses={204: None, 404: OpenApiResponse()})
    def delete(self, request, notification_id):
        try:
            services.delete_notification(
                user=request.user,
                notification_id=notification_id,
                ip=request.META.get("REMOTE_ADDR"),
            )
        except services.NotFound as exc:
            raise Http404 from exc
        return Response(status=status.HTTP_204_NO_CONTENT)
