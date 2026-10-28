"""DRF serializers for the journals API (mood check-ins)."""

from rest_framework import serializers

from apps.journals.models import MAX_TAGS, EmotionTag, Mood, MoodCheckIn
from core.serializers import RejectUnknownFieldsMixin, free_text_field

TOO_MANY_TAGS = f"Choose at most {MAX_TAGS} feelings."
MOOD_MESSAGE = "Mood must be a whole number between 1 and 5."


def _mood_field(**kwargs):
    return serializers.ChoiceField(
        choices=Mood.choices,
        error_messages={"invalid_choice": MOOD_MESSAGE},
        **kwargs,
    )


def _tags_field(**kwargs):
    return serializers.ListField(
        child=serializers.ChoiceField(choices=EmotionTag.choices),
        max_length=MAX_TAGS,
        error_messages={"max_length": TOO_MANY_TAGS},
        **kwargs,
    )


class CheckInWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    mood = _mood_field()
    tags = _tags_field(required=False)
    note = free_text_field(
        "Note",
        10,
        500,
        required=False,
        allow_blank=True,
        help_text="Optional. Encrypted; only the patient ever sees it.",
    )


class CheckInUpdateSerializer(CheckInWriteSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.required = False
        return fields


class CheckInSerializer(serializers.ModelSerializer):
    """The patient's own view, note included."""

    class Meta:
        model = MoodCheckIn
        fields = [
            "id",
            "local_date",
            "mood",
            "tags",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TodaySerializer(serializers.Serializer):
    local_date = serializers.DateField()
    check_in = CheckInSerializer(allow_null=True)


class PsychologistCheckInSerializer(serializers.ModelSerializer):
    """Mood and tags only: the note is private to the patient."""

    class Meta:
        model = MoodCheckIn
        fields = ["id", "local_date", "mood", "tags"]
        read_only_fields = fields


class _TagCount(serializers.Serializer):
    tag = serializers.ChoiceField(choices=EmotionTag.choices)
    count = serializers.IntegerField()


class _Window(serializers.Serializer):
    check_ins = serializers.IntegerField()
    average_mood = serializers.FloatField(allow_null=True)
    distribution = serializers.DictField(
        child=serializers.IntegerField(), help_text="Mood value '1'..'5' -> count."
    )
    top_tags = _TagCount(many=True)


class InsightsSerializer(serializers.Serializer):
    today = serializers.DateField(help_text="The patient's local date.")
    streak = serializers.IntegerField(
        help_text="Consecutive local days with a check-in, ending today (or "
        "yesterday if today's isn't in yet)."
    )
    windows = serializers.DictField(
        child=_Window(), help_text="Keys '7', '30', '90' (days, today included)."
    )


class PsychologistMoodSerializer(serializers.Serializer):
    check_ins = PsychologistCheckInSerializer(many=True)
    insights = InsightsSerializer()


class PsychologistMoodQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(choices=[7, 30, 90], required=False, default=30)
