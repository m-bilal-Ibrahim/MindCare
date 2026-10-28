"""DRF serializers for the appointments API (Phase 2 module 4)."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.appointments.models import (
    MAX_FEE_PKR,
    MIN_FEE_PKR,
    VIDEO_DOMAINS,
    BookingSettings,
    DayOff,
    Session,
    SessionLength,
    SessionStatus,
    Weekday,
    WorkingWindow,
)
from apps.appointments.selectors import FREE_CANCELLATION, PSYCHOLOGIST_VIEWS
from apps.appointments.services import OUTCOMES
from apps.patients.selectors import get_patient_display_identity
from core.serializers import (
    RejectUnknownFieldsMixin,
    https_url_field,
    whole_number_field,
)

MAX_WINDOWS = 21
TOO_MANY_WINDOWS = f"You can set at most {MAX_WINDOWS} windows."


class BookingSettingsWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    session_minutes = serializers.ChoiceField(
        choices=SessionLength.choices, required=False
    )
    fee_pkr = whole_number_field(
        "Session fee", MIN_FEE_PKR, MAX_FEE_PKR, required=False
    )
    video_link = https_url_field(
        "Video link",
        VIDEO_DOMAINS,
        required=False,
        allow_blank=True,
        help_text="Your personal Zoom or Google Meet link (https). Patients see it "
        "only on confirmed sessions.",
    )


class BookingSettingsSerializer(serializers.ModelSerializer):
    is_bookable = serializers.SerializerMethodField()
    not_bookable_reason = serializers.SerializerMethodField(
        help_text="null when bookable, else no_fee / no_video_link / no_working_hours."
    )

    class Meta:
        model = BookingSettings
        fields = [
            "session_minutes",
            "fee_pkr",
            "video_link",
            "is_bookable",
            "not_bookable_reason",
        ]
        read_only_fields = fields

    def get_not_bookable_reason(self, obj) -> str | None:
        return self.context["reason"]

    def get_is_bookable(self, obj) -> bool:
        return self.context["reason"] is None


class WindowSerializer(RejectUnknownFieldsMixin, serializers.ModelSerializer):
    weekday = serializers.ChoiceField(
        choices=Weekday.choices, help_text="0 = Monday … 6 = Sunday."
    )
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = WorkingWindow
        fields = ["weekday", "start_time", "end_time"]


class WorkingHoursSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    windows = serializers.ListField(
        child=WindowSerializer(),
        allow_empty=True,
        max_length=MAX_WINDOWS,
        error_messages={"max_length": TOO_MANY_WINDOWS},
        help_text="Wall-clock times in your profile timezone, quarter hours.",
    )
    timezone = serializers.CharField(read_only=True)


class DayOffWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    date = serializers.DateField(help_text="A day in your timezone.")


class DayOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOff
        fields = ["id", "date"]
        read_only_fields = fields


class StartsAtSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    starts_at = serializers.DateTimeField(
        help_text="One of the slot times from GET /slots/ (ISO 8601 with offset)."
    )


class OutcomeSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    outcome = serializers.ChoiceField(choices=[(o.value, o.label) for o in OUTCOMES])


class FreeSlotsSerializer(serializers.Serializer):
    slots = serializers.ListField(child=serializers.DateTimeField())


class SlotsSerializer(serializers.Serializer):
    bookable = serializers.BooleanField()
    not_bookable_reason = serializers.CharField(allow_null=True)
    psychologist_timezone = serializers.CharField()
    session_minutes = serializers.IntegerField(allow_null=True)
    fee_pkr = serializers.IntegerField(allow_null=True)
    upcoming_sessions = serializers.IntegerField()
    max_upcoming_sessions = serializers.IntegerField()
    slots = serializers.ListField(child=serializers.DateTimeField())


_SESSION_FIELDS = [
    "id",
    "status",
    "starts_at",
    "ends_at",
    "duration_minutes",
    "fee_pkr",
    "requested_starts_at",
    "confirmed_at",
    "cancelled_at",
    "cancelled_by",
    "is_late_cancellation",
    "created_at",
]


class _SessionBase(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=SessionStatus.choices,
        source="effective_status",
        read_only=True,
        help_text="A request or proposal past its start reads as expired.",
    )


class PatientSessionSerializer(_SessionBase):
    psychologist = serializers.SerializerMethodField()
    video_link = serializers.SerializerMethodField(
        help_text="Only on confirmed sessions; null otherwise."
    )
    free_cancellation_until = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            *_SESSION_FIELDS,
            "psychologist",
            "video_link",
            "free_cancellation_until",
        ]
        read_only_fields = fields

    @extend_schema_field(
        {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "full_name": {"type": "string"}},
        }
    )
    def get_psychologist(self, obj):
        return {"id": obj.psychologist_id, "full_name": obj.psychologist.user.full_name}

    def get_video_link(self, obj) -> str | None:
        if obj.effective_status != SessionStatus.CONFIRMED:
            return None
        settings = getattr(obj.psychologist, "booking_settings", None)
        return (settings.video_link or None) if settings else None

    def get_free_cancellation_until(self, obj) -> str | None:
        if obj.effective_status != SessionStatus.CONFIRMED:
            return None
        return serializers.DateTimeField().to_representation(
            obj.starts_at - FREE_CANCELLATION
        )


class PsychologistSessionSerializer(_SessionBase):
    relationship_id = serializers.IntegerField(read_only=True)
    patient = serializers.SerializerMethodField(
        help_text="Real name while the patient is yours, else the pseudonym."
    )

    class Meta:
        model = Session
        fields = [*_SESSION_FIELDS, "relationship_id", "patient", "outcome_marked_at"]
        read_only_fields = fields

    @extend_schema_field(
        {
            "type": "object",
            "properties": {
                "display_name": {"type": "string"},
                "is_real_name": {"type": "boolean"},
            },
        }
    )
    def get_patient(self, obj):
        return get_patient_display_identity(
            patient_profile=obj.patient, viewer=self.context["request"].user
        )


class PsychologistSessionQuerySerializer(serializers.Serializer):
    view = serializers.ChoiceField(
        choices=PSYCHOLOGIST_VIEWS, required=False, default="upcoming"
    )
