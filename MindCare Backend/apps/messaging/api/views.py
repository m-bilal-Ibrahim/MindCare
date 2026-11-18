"""DRF views for messaging. Thin: parse -> service/selector -> serialize.

Every conversation endpoint answers 404 to anyone who isn't allowed to open it
(admins, other psychologists, a former psychologist), and 403 when a patient
tries to write in a read-only conversation.
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.messaging import selectors, services
from apps.messaging.api.serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    CountSerializer,
    EmptyBodySerializer,
    MessagePageSerializer,
    MessageQuerySerializer,
    MessageSerializer,
    SendMessageSerializer,
)
from core.exceptions import DomainValidationError

NOT_FOUND = OpenApiResponse(description="Not a conversation you can open.")


class MessagingThrottle(UserRateThrottle):
    scope = "messaging"


class MessageSendThrottle(UserRateThrottle):
    """30 messages per user per 10 minutes. DRF only reads the unit's first
    letter, so "30/10m" is parsed here as a multiple of that unit."""

    scope = "messages"

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split("/")
        digits = "".join(ch for ch in period if ch.isdigit())
        unit = period[len(digits)]
        seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return (int(num), int(digits or 1) * seconds)


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _run(fn, **kwargs):
    try:
        return fn(**kwargs)
    except services.NotFound as exc:
        raise Http404 from exc
    except services.Forbidden as exc:
        raise PermissionDenied(exc.message) from exc
    except DomainValidationError as exc:
        raise ValidationError(exc.errors, code=exc.code) from exc


class MessagingView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MessagingThrottle]


class ConversationListView(MessagingView):
    @extend_schema(
        responses={200: ConversationSerializer(many=True)},
        description="Your conversations, most recent first: the other party's "
        "name, last message time and unread count. Never any message text.",
    )
    def get(self, request):
        user = request.user
        rows = [
            selectors.conversation_summary(user=user, conversation=c)
            for c in selectors.visible_conversations(user=user)
        ]
        return Response(ConversationSerializer(rows, many=True).data)


class ConversationDetailView(MessagingView):
    @extend_schema(
        responses={200: ConversationDetailSerializer, 404: NOT_FOUND},
        description="One conversation, with the fixed `safety_notice` (messages "
        "aren't for emergencies; use SOS).",
    )
    def get(self, request, conversation_id):
        conversation = _run(
            selectors.get_conversation,
            user=request.user,
            conversation_id=conversation_id,
        )
        data = selectors.conversation_summary(
            user=request.user, conversation=conversation, detail=True
        )
        return Response(ConversationDetailSerializer(data).data)


class MessagesView(MessagingView):
    def get_throttles(self):
        if self.request.method == "POST":
            return [MessageSendThrottle(), MessagingThrottle()]
        return super().get_throttles()

    @extend_schema(
        parameters=[
            OpenApiParameter("before", int, description="Message id: older only."),
            OpenApiParameter("limit", int, description="1-50, default 30."),
        ],
        responses={200: MessagePageSerializer, 404: NOT_FOUND},
        description="Messages, newest first. Deleted ones have `body: null`.",
    )
    def get(self, request, conversation_id):
        query = MessageQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        conversation = _run(
            selectors.get_conversation,
            user=request.user,
            conversation_id=conversation_id,
        )
        rows, next_before = selectors.messages_page(
            conversation=conversation,
            before=query.validated_data.get("before"),
            limit=query.validated_data.get("limit"),
        )
        data = {
            "results": MessageSerializer(
                rows, many=True, context={"request": request}
            ).data,
            "next_before": next_before,
        }
        return Response(data)

    @extend_schema(
        request=SendMessageSerializer,
        responses={
            201: MessageSerializer,
            400: OpenApiResponse(description="Invalid message."),
            403: OpenApiResponse(description="Read-only: care has ended."),
            404: NOT_FOUND,
            429: OpenApiResponse(description="More than 30 messages in 10 minutes."),
        },
        description="Send a text message (1-2000 characters). The other side "
        "gets a notification without the text.",
    )
    def post(self, request, conversation_id):
        body = SendMessageSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        message = _run(
            services.send_message,
            user=request.user,
            conversation_id=conversation_id,
            body=body.validated_data["body"],
            ip=_ip(request),
        )
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MessageDetailView(MessagingView):
    @extend_schema(
        responses={
            204: None,
            400: OpenApiResponse(description="Older than 5 minutes, or deleted."),
            403: OpenApiResponse(description="Not your message."),
            404: NOT_FOUND,
        },
        description="Delete your own message within 5 minutes. It shows as "
        "'Message deleted'. Audited.",
    )
    def delete(self, request, conversation_id, message_id):
        _run(
            services.delete_message,
            user=request.user,
            conversation_id=conversation_id,
            message_id=message_id,
            ip=_ip(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkReadView(MessagingView):
    @extend_schema(
        request=None,
        responses={200: CountSerializer, 404: NOT_FOUND},
        description="Mark every message from the other side as read. Returns how "
        "many were marked.",
    )
    def post(self, request, conversation_id):
        EmptyBodySerializer(data=request.data or {}).is_valid(raise_exception=True)
        count = _run(
            services.mark_read, user=request.user, conversation_id=conversation_id
        )
        return Response({"count": count})


class UnreadCountView(MessagingView):
    @extend_schema(
        responses={200: CountSerializer},
        description="Unread messages across all your conversations.",
    )
    def get(self, request):
        return Response({"count": selectors.total_unread(user=request.user)})
