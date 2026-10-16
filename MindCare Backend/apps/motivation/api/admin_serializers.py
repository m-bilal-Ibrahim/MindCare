"""Serializers for the admin content console (admin-panel-2): quotes, duas and
surahs, active or not. Each field uses the same rule and message as the model
(docs/validation-rules.md); the model checks again on save."""

from rest_framework import serializers

from apps.motivation.models import (
    SOURCE_REFERENCE_VALIDATOR,
    Dua,
    Quote,
    QuoteCategory,
    Surah,
)
from core.serializers import (
    NormalizedCharField,
    RejectUnknownFieldsMixin,
    free_text_field,
    organisation_name_field,
    person_name_field,
    whole_number_field,
)
from integrations.storage_client.client import url_or_none


class AdminContentQuerySerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False, allow_null=True, default=None)


class _AdminContentSerializer(RejectUnknownFieldsMixin, serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False)


class AdminQuoteSerializer(_AdminContentSerializer):
    text = free_text_field("Quote", 10, 500)
    author = person_name_field("Author", required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=QuoteCategory.choices, required=False, allow_blank=True
    )

    class Meta:
        model = Quote
        fields = ["id", "text", "author", "category", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class _AdminReligiousSerializer(_AdminContentSerializer):
    transliteration = free_text_field(
        "Transliteration", 3, 20000, required=False, allow_blank=True
    )
    has_audio = serializers.SerializerMethodField()
    audio_type = serializers.CharField(read_only=True)
    audio_url = serializers.SerializerMethodField(
        help_text="Signed link to the recitation (a few minutes); null if none."
    )

    def get_has_audio(self, obj) -> bool:
        return bool(obj.audio_key)

    def get_audio_url(self, obj) -> str | None:
        return url_or_none(obj.audio_key)


_RELIGIOUS_READ_ONLY = ["id", "has_audio", "audio_type", "audio_url", "created_at"]


class AdminDuaSerializer(_AdminReligiousSerializer):
    title = organisation_name_field("Title", max_length=120)
    reference = NormalizedCharField(
        max_length=60, validators=[SOURCE_REFERENCE_VALIDATOR]
    )
    arabic = free_text_field("Arabic text", 3, 5000)
    translation = free_text_field("Translation", 10, 5000)
    sort_order = whole_number_field("Sort order", 0, 32767, required=False)

    class Meta:
        model = Dua
        fields = [
            "id",
            "title",
            "reference",
            "arabic",
            "transliteration",
            "translation",
            "sort_order",
            "is_active",
            "has_audio",
            "audio_type",
            "audio_url",
            "created_at",
        ]
        read_only_fields = _RELIGIOUS_READ_ONLY


class AdminSurahSerializer(_AdminReligiousSerializer):
    number = whole_number_field("Surah number", 1, 114)
    name_arabic = free_text_field("Arabic name", 3, 100)
    name_english = organisation_name_field("English name", max_length=100)
    name_meaning = organisation_name_field("Meaning", max_length=100)
    ayah_count = whole_number_field("Ayah count", 1, 286)
    arabic = free_text_field("Arabic text", 3, 50000)
    translation = free_text_field("Translation", 10, 50000)

    class Meta:
        model = Surah
        fields = [
            "id",
            "number",
            "name_arabic",
            "name_english",
            "name_meaning",
            "ayah_count",
            "arabic",
            "transliteration",
            "translation",
            "is_active",
            "has_audio",
            "audio_type",
            "audio_url",
            "created_at",
        ]
        read_only_fields = _RELIGIOUS_READ_ONLY
        # Uniqueness is answered by the service with the field's own message.
        extra_kwargs = {"number": {"validators": []}}


class AudioUploadSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    audio = serializers.FileField(
        help_text="MP3, M4A or OGG, max 15 MB, checked by content.",
        error_messages={"required": "Choose an audio file to upload."},
    )

    def validate_audio(self, value):
        from django.core.exceptions import ValidationError as DjangoValidationError

        from core.files import check_audio

        try:
            return check_audio(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
