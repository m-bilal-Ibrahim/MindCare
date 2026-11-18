"""DRF serializers for the clinical_notes API (Phase 2 module 5)."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.clinical_notes.models import (
    PROGRESS_MAX,
    PROGRESS_MIN,
    SECTION_MAX,
    SECTION_MIN,
    SUMMARY_MAX,
    SUMMARY_MIN,
    NoteAddendum,
    RiskLevel,
    TherapyNote,
)
from apps.journals.api.serializers import InsightsSerializer
from core.serializers import (
    RejectUnknownFieldsMixin,
    free_text_field,
    whole_number_field,
)


def _section(label):
    return free_text_field(
        label, SECTION_MIN, SECTION_MAX, required=False, allow_blank=True
    )


class NoteUpdateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    observations = _section("Observations")
    interventions = _section("Interventions")
    plan = _section("Plan")
    progress_rating = whole_number_field(
        "Progress", PROGRESS_MIN, PROGRESS_MAX, required=False, allow_null=True
    )
    risk_level = serializers.ChoiceField(
        choices=RiskLevel.choices, required=False, allow_null=True, allow_blank=True
    )


class NoteCreateSerializer(NoteUpdateSerializer):
    session = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
        help_text="Optional: one of this patient's confirmed or past sessions "
        "with you. One note per session.",
    )


class AddendumSerializer(RejectUnknownFieldsMixin, serializers.ModelSerializer):
    text = free_text_field("Addendum", SECTION_MIN, SECTION_MAX)

    class Meta:
        model = NoteAddendum
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class NoteSerializer(serializers.ModelSerializer):
    session_starts_at = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    locked_at = serializers.DateTimeField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    addenda = AddendumSerializer(many=True, read_only=True)

    class Meta:
        model = TherapyNote
        fields = [
            "id",
            "session_id",
            "session_starts_at",
            "observations",
            "interventions",
            "plan",
            "progress_rating",
            "risk_level",
            "version",
            "created_at",
            "updated_at",
            "locked_at",
            "is_locked",
            "addenda",
        ]
        read_only_fields = fields

    def get_session_starts_at(self, obj) -> str | None:
        if obj.session is None:
            return None
        return serializers.DateTimeField().to_representation(obj.session.starts_at)

    @extend_schema_field(
        serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)
    )
    def get_risk_level(self, obj):
        return obj.risk_level or None


class NoteVersionSerializer(serializers.Serializer):
    version = serializers.IntegerField()
    saved_at = serializers.DateTimeField()
    session_id = serializers.IntegerField(allow_null=True)
    observations = serializers.CharField()
    interventions = serializers.CharField()
    plan = serializers.CharField()
    progress_rating = serializers.IntegerField(allow_null=True)
    risk_level = serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)


class ProgressPointSerializer(serializers.Serializer):
    note_id = serializers.IntegerField()
    date = serializers.DateTimeField(help_text="When the note was written.")
    session_id = serializers.IntegerField(allow_null=True)
    session_starts_at = serializers.DateTimeField(allow_null=True)
    progress_rating = serializers.IntegerField(allow_null=True)
    risk_level = serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)


class SummaryWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    text = free_text_field(
        "Summary",
        SUMMARY_MIN,
        SUMMARY_MAX,
        help_text="Written FOR the patient: they see exactly this text.",
    )


class SummarySerializer(serializers.Serializer):
    text = serializers.CharField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)


class _PsychologistName(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()


class _PatientSummary(serializers.Serializer):
    text = serializers.CharField()
    psychologist = _PsychologistName()
    updated_at = serializers.DateTimeField()


class _SessionCounts(serializers.Serializer):
    completed = serializers.IntegerField()
    upcoming = serializers.IntegerField()


class PatientProgressSerializer(serializers.Serializer):
    sessions = _SessionCounts()
    summary = _PatientSummary(allow_null=True)
    mood = InsightsSerializer()
