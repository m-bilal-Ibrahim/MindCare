"""Serializers for the Motivation Corner API."""

from rest_framework import serializers

from apps.motivation.models import Quote, QuoteCategory


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
