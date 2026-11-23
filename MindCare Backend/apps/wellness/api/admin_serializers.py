"""Serializers for the admin wellness console. Each field uses the same rule and
message as the model (docs/validation-rules.md); the model checks again on save,
including the kind rules (article text, steps, breathing pattern)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.wellness.models import (
    BODY_MAX,
    BODY_MIN,
    BREATH_MAX,
    DURATION_MAX,
    DURATION_MIN,
    MAX_STEPS,
    SAFETY_MAX,
    SAFETY_MIN,
    SORT_MAX,
    SOURCE_MAX,
    SOURCE_MIN,
    STEP_MAX,
    STEP_MIN,
    SUMMARY_MAX,
    SUMMARY_MIN,
    TITLE_MAX,
    TITLE_MIN,
    TOO_MANY_STEPS,
    VIDEO_DOMAINS,
    Difficulty,
    WellnessCategory,
    WellnessItem,
    WellnessKind,
)
from core.files import PHOTO_KINDS, check_audio, check_upload
from core.serializers import (
    NormalizedCharField,
    RejectUnknownFieldsMixin,
    free_text_field,
    https_url_field,
    whole_number_field,
)
from core.validators import FreeTextValidator, normalize_single_line
from integrations.storage_client.client import url_or_none

COVER_MAX_MB = 5
COVER_MAX_SIDE = 1600


class AdminItemQuerySerializer(serializers.Serializer):
    is_published = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )
    category = serializers.ChoiceField(choices=WellnessCategory.choices, required=False)
    kind = serializers.ChoiceField(choices=WellnessKind.choices, required=False)


def _single_line(label, minimum, maximum, **kwargs):
    return NormalizedCharField(
        normaliser=normalize_single_line,
        validators=[FreeTextValidator(label, minimum, maximum)],
        **kwargs,
    )


def _breath(label, minimum):
    return whole_number_field(
        label, minimum, BREATH_MAX, required=False, allow_null=True
    )


class AdminItemSerializer(RejectUnknownFieldsMixin, serializers.ModelSerializer):
    kind = serializers.ChoiceField(choices=WellnessKind.choices)
    category = serializers.ChoiceField(choices=WellnessCategory.choices)
    title = _single_line("Title", TITLE_MIN, TITLE_MAX)
    summary = free_text_field("Summary", SUMMARY_MIN, SUMMARY_MAX)
    body = free_text_field("Body", BODY_MIN, BODY_MAX, required=False, allow_blank=True)
    steps = serializers.ListField(
        child=_single_line("Step", STEP_MIN, STEP_MAX),
        max_length=MAX_STEPS,
        required=False,
        error_messages={"max_length": TOO_MANY_STEPS},
    )
    duration_minutes = whole_number_field("Duration", DURATION_MIN, DURATION_MAX)
    difficulty = serializers.ChoiceField(choices=Difficulty.choices, required=False)
    safety_note = free_text_field(
        "Safety note", SAFETY_MIN, SAFETY_MAX, required=False, allow_blank=True
    )
    source = _single_line(
        "Source", SOURCE_MIN, SOURCE_MAX, required=False, allow_blank=True
    )
    video_url = https_url_field(
        "Video link", VIDEO_DOMAINS, required=False, allow_blank=True
    )
    breath_in_seconds = _breath("Breath in", 1)
    breath_hold_seconds = _breath("Hold", 0)
    breath_out_seconds = _breath("Breath out", 1)
    breath_hold_after_out_seconds = _breath("Hold after breathing out", 0)
    sort_order = whole_number_field("Sort order", 0, SORT_MAX, required=False)
    is_published = serializers.BooleanField(required=False)
    image_url = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = WellnessItem
        fields = [
            "id",
            "kind",
            "category",
            "title",
            "summary",
            "body",
            "steps",
            "duration_minutes",
            "difficulty",
            "safety_note",
            "source",
            "video_url",
            "breath_in_seconds",
            "breath_hold_seconds",
            "breath_out_seconds",
            "breath_hold_after_out_seconds",
            "sort_order",
            "is_published",
            "ever_linked",
            "image_type",
            "image_url",
            "audio_type",
            "audio_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "ever_linked",
            "image_type",
            "image_url",
            "audio_type",
            "audio_url",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj) -> str | None:
        return url_or_none(obj.image_key)

    def get_audio_url(self, obj) -> str | None:
        return url_or_none(obj.audio_key)


def _checked(check, value):
    try:
        return check(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages) from exc


def check_cover(upload):
    """A cover image: JPG, PNG or WEBP, 5 MB, re-encoded (EXIF removed) and
    shrunk to at most 1600 px."""
    return check_upload(
        upload,
        label="Cover image",
        allowed=PHOTO_KINDS,
        max_mb=COVER_MAX_MB,
        max_image_side=COVER_MAX_SIDE,
    )


def check_item_audio(upload):
    return check_audio(upload, label="Audio")


class ItemImageUploadSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    image = serializers.FileField(
        help_text="JPG, PNG or WEBP, max 5 MB, checked by content.",
        error_messages={"required": "Choose an image to upload."},
    )

    def validate_image(self, value):
        return _checked(check_cover, value)


class ItemAudioUploadSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    audio = serializers.FileField(
        help_text="MP3, M4A or OGG, max 15 MB, checked by content.",
        error_messages={"required": "Choose an audio file to upload."},
    )

    def validate_audio(self, value):
        return _checked(check_item_audio, value)
