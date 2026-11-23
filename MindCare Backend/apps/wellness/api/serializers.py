"""Serializers for the wellness library API (docs/validation-rules.md)."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.wellness.models import (
    BREATH_MAX,
    DURATION_MAX,
    DURATION_MIN,
    Difficulty,
    WellnessCategory,
    WellnessItem,
    WellnessKind,
)
from apps.wellness.selectors import DISCLAIMER
from core.serializers import search_field, whole_number_field
from integrations.storage_client.client import url_or_none


class ItemQuerySerializer(serializers.Serializer):
    """Query parameters of GET /wellness/items/."""

    category = serializers.ChoiceField(choices=WellnessCategory.choices, required=False)
    kind = serializers.ChoiceField(choices=WellnessKind.choices, required=False)
    difficulty = serializers.ChoiceField(choices=Difficulty.choices, required=False)
    max_duration = whole_number_field(
        "Maximum duration", DURATION_MIN, DURATION_MAX, required=False
    )
    search = search_field(required=False, allow_blank=True)


class _Breathing(serializers.Serializer):
    breath_in_seconds = serializers.IntegerField()
    breath_hold_seconds = serializers.IntegerField()
    breath_out_seconds = serializers.IntegerField()
    breath_hold_after_out_seconds = serializers.IntegerField()


def _null_if_blank(value):
    return value or None


class ItemListSerializer(serializers.ModelSerializer):
    """A card in the library list (no body or steps)."""

    image_url = serializers.SerializerMethodField(
        help_text="Signed link to the cover image (a few minutes); null if none."
    )
    has_audio = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField(
        help_text="Patients: whether they saved it. Psychologists: null."
    )

    class Meta:
        model = WellnessItem
        fields = [
            "id",
            "kind",
            "category",
            "title",
            "summary",
            "duration_minutes",
            "difficulty",
            "image_url",
            "has_audio",
            "is_favourite",
        ]
        read_only_fields = fields

    def get_image_url(self, obj) -> str | None:
        return url_or_none(obj.image_key)

    def get_has_audio(self, obj) -> bool:
        return bool(obj.audio_key)

    def get_is_favourite(self, obj) -> bool | None:
        favourites = self.context.get("favourite_ids")
        if favourites is None:
            return None
        return obj.pk in favourites


class ItemDetailSerializer(ItemListSerializer):
    body = serializers.CharField(help_text="Plain text; keep its line breaks.")
    steps = serializers.ListField(child=serializers.CharField())
    safety_note = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField(
        help_text="YouTube or Vimeo link, opened outside the app; null if none."
    )
    audio_url = serializers.SerializerMethodField(
        help_text="Signed link to the audio (a few minutes); null if none."
    )
    audio_type = serializers.SerializerMethodField()
    breathing = serializers.SerializerMethodField(
        help_text=f"Practices only: seconds per phase (0-{BREATH_MAX}); null if none."
    )
    disclaimer = serializers.SerializerMethodField()

    class Meta(ItemListSerializer.Meta):
        fields = [
            *ItemListSerializer.Meta.fields,
            "body",
            "steps",
            "safety_note",
            "source",
            "video_url",
            "audio_url",
            "audio_type",
            "breathing",
            "updated_at",
            "disclaimer",
        ]
        read_only_fields = fields

    def get_safety_note(self, obj) -> str | None:
        return _null_if_blank(obj.safety_note)

    def get_source(self, obj) -> str | None:
        return _null_if_blank(obj.source)

    def get_video_url(self, obj) -> str | None:
        return _null_if_blank(obj.video_url)

    def get_audio_url(self, obj) -> str | None:
        return url_or_none(obj.audio_key)

    def get_audio_type(self, obj) -> str | None:
        return _null_if_blank(obj.audio_type)

    @extend_schema_field(_Breathing(allow_null=True))
    def get_breathing(self, obj):
        if obj.breath_in_seconds is None:
            return None
        return {
            "breath_in_seconds": obj.breath_in_seconds,
            "breath_hold_seconds": obj.breath_hold_seconds,
            "breath_out_seconds": obj.breath_out_seconds,
            "breath_hold_after_out_seconds": obj.breath_hold_after_out_seconds,
        }

    def get_disclaimer(self, obj) -> str:
        return DISCLAIMER


class FavouriteResultSerializer(serializers.Serializer):
    is_favourite = serializers.BooleanField()


class LinkedContentSerializer(serializers.Serializer):
    """What a care-plan task shows about its linked library item."""

    id = serializers.IntegerField()
    is_available = serializers.BooleanField(
        help_text="false: the item was hidden; show `message` instead."
    )
    kind = serializers.ChoiceField(choices=WellnessKind.choices, allow_null=True)
    category = serializers.ChoiceField(
        choices=WellnessCategory.choices, allow_null=True
    )
    title = serializers.CharField(allow_null=True)
    duration_minutes = serializers.IntegerField(allow_null=True)
    message = serializers.CharField(allow_null=True)
