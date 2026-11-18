"""DRF serializers for the in-app notifications API."""

from rest_framework import serializers

from apps.notifications.models import Notification, NotificationType
from core.serializers import RejectUnknownFieldsMixin


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "body",
            "target_type",
            "target_id",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields


class NotificationQuerySerializer(serializers.Serializer):
    """Query parameters for the list (page / page_size are the paginator's)."""

    unread = serializers.BooleanField(required=False, allow_null=True, default=None)
    type = serializers.ChoiceField(choices=NotificationType.choices, required=False)


class EmptyBodySerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    """The read / read-all actions take no body; any key is refused."""


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class ReadAllSerializer(serializers.Serializer):
    updated = serializers.IntegerField()
