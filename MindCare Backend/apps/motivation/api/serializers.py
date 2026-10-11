"""Serializers for the Motivation Corner API."""

from rest_framework import serializers

from apps.motivation.models import Dua, Quote, QuoteCategory, Surah
from core.serializers import RejectUnknownFieldsMixin
from integrations.storage_client.client import url_or_none


class QuoteQuerySerializer(serializers.Serializer):
    """Query parameters of GET /motivation/quotes/ and /quotes/random/."""

    category = serializers.ChoiceField(choices=QuoteCategory.choices, required=False)


class QuoteSerializer(serializers.ModelSerializer):
    # Blank author/category come back as null, so the App can hide them.
    author = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = ["id", "text", "author", "category"]
        read_only_fields = fields

    def get_author(self, obj) -> str | None:
        return obj.author or None

    def get_category(self, obj) -> str | None:
        return obj.category or None


# --- Religious content (6.10) -------------------------------------------------


class ReligiousPreferenceSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    opted_in = serializers.BooleanField(
        help_text="true to see Quran and dua content; false deletes the opt-in."
    )


class _AudioMixin(serializers.Serializer):
    audio_url = serializers.SerializerMethodField(
        help_text="Signed link to the recitation (a few minutes); null if none."
    )
    transliteration = serializers.SerializerMethodField()

    def get_audio_url(self, obj) -> str | None:
        return url_or_none(obj.audio_key)

    def get_transliteration(self, obj) -> str | None:
        return obj.transliteration or None


class DuaSerializer(_AudioMixin, serializers.ModelSerializer):
    class Meta:
        model = Dua
        fields = [
            "id",
            "title",
            "reference",
            "arabic",
            "transliteration",
            "translation",
            "audio_url",
        ]
        read_only_fields = fields


class SurahListSerializer(serializers.ModelSerializer):
    has_audio = serializers.SerializerMethodField()

    class Meta:
        model = Surah
        fields = [
            "number",
            "name_arabic",
            "name_english",
            "name_meaning",
            "ayah_count",
            "has_audio",
        ]
        read_only_fields = fields

    def get_has_audio(self, obj) -> bool:
        return bool(obj.audio_key)


class SurahSerializer(_AudioMixin, serializers.ModelSerializer):
    class Meta:
        model = Surah
        fields = [
            "number",
            "name_arabic",
            "name_english",
            "name_meaning",
            "ayah_count",
            "arabic",
            "transliteration",
            "translation",
            "audio_url",
        ]
        read_only_fields = fields
