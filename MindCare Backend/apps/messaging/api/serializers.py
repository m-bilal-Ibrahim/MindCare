"""DRF serializers for the messaging API. No serializer ever puts message text
in a conversation list."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.messaging.models import DELETE_WINDOW, MESSAGE_MAX, Message
from core.serializers import NormalizedCharField, RejectUnknownFieldsMixin
from core.validators import MessageTextValidator, normalize_multiline_text

LENGTH = f"Message must be between 1 and {MESSAGE_MAX} characters."


class OtherPartySerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Patient or psychologist profile id.")
    role = serializers.CharField()
    name = serializers.CharField()


class ConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    other_party = OtherPartySerializer()
    last_message_at = serializers.DateTimeField(allow_null=True)
    unread_count = serializers.IntegerField()
    can_send = serializers.BooleanField(
        help_text="False once care has ended: the conversation is read-only."
    )


class ConversationDetailSerializer(ConversationSerializer):
    safety_notice = serializers.CharField()


class MessageSerializer(serializers.ModelSerializer):
    body = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "body",
            "is_mine",
            "is_deleted",
            "can_delete",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields

    def _user(self):
        return self.context["request"].user

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_body(self, obj):
        return None if obj.is_deleted else obj.body

    def get_is_mine(self, obj) -> bool:
        return obj.sender_id == self._user().pk

    def get_is_deleted(self, obj) -> bool:
        return obj.is_deleted

    def get_can_delete(self, obj) -> bool:
        return (
            obj.sender_id == self._user().pk
            and not obj.is_deleted
            and timezone.now() <= obj.created_at + DELETE_WINDOW
        )


class MessagePageSerializer(serializers.Serializer):
    results = MessageSerializer(many=True)
    next_before = serializers.IntegerField(
        allow_null=True,
        help_text="Pass as ?before= for older messages; null at the start.",
    )


class MessageQuerySerializer(serializers.Serializer):
    before = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=50, required=False)


class SendMessageSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    body = NormalizedCharField(
        normaliser=normalize_multiline_text,
        validators=[MessageTextValidator("Message", MESSAGE_MAX)],
        error_messages={"blank": LENGTH, "required": "Write a message."},
    )


class EmptyBodySerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    pass


class CountSerializer(serializers.Serializer):
    count = serializers.IntegerField()
