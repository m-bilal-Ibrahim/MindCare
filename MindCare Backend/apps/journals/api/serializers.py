"""DRF serializers for the journals API (mood check-ins)."""

from rest_framework import serializers

from apps.journals.models import (
    ENTRY_BODY_MAX,
    ENTRY_BODY_MIN,
    ENTRY_TITLE_MAX,
    ENTRY_TITLE_MIN,
    MAX_TAGS,
    EmotionTag,
    JournalEntry,
    Mood,
    MoodCheckIn,
)
from core.serializers import (
    NormalizedCharField,
    RejectUnknownFieldsMixin,
    free_text_field,
)
from core.validators import FreeTextValidator, normalize_single_line

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


# --- journal entries (private to the patient) ---------------------------------

DATE_ORDER = "The start date must be on or before the end date."
JOURNAL_SAFETY_NOTICE = (
    "Your journal is private: nobody else, not even your psychologist, can read "
    "it, and nobody is alerted by what you write. If you are in danger or might "
    "harm yourself, press the SOS button or call your local emergency number now."
)


class JournalEntryWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    title = NormalizedCharField(
        normaliser=normalize_single_line,
        validators=[FreeTextValidator("Title", ENTRY_TITLE_MIN, ENTRY_TITLE_MAX)],
        required=False,
        allow_blank=True,
    )
    body = free_text_field(
        "Entry",
        ENTRY_BODY_MIN,
        ENTRY_BODY_MAX,
        error_messages={"required": "Write something in your entry."},
    )
    tags = _tags_field(required=False)
    check_in = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
        help_text="Optional: your mood check-in from the same day.",
    )


class JournalEntryUpdateSerializer(JournalEntryWriteSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.required = False
        return fields


class JournalEntrySerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.ChoiceField(choices=EmotionTag.choices), source="tag_list"
    )
    check_in = serializers.IntegerField(source="check_in_id", allow_null=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "local_date",
            "title",
            "body",
            "tags",
            "check_in",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class JournalEntryQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    tag = serializers.ChoiceField(choices=EmotionTag.choices, required=False)

    def validate(self, attrs):
        start, end = attrs.get("date_from"), attrs.get("date_to")
        if start and end and start > end:
            raise serializers.ValidationError({"date_from": [DATE_ORDER]})
        return attrs
