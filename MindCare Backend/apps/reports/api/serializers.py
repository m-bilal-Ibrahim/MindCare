"""DRF serializers for 6.14 patient reports (docs/validation-rules.md).

The query serializer validates `period`, `start` and `end`; the rest describe
the response for the OpenAPI schema and serialize the calculated report.
"""

from rest_framework import serializers

from apps.clinical_notes.models import RiskLevel
from apps.emergency.models import SOSStatus
from apps.journals.models import EmotionTag
from apps.recommendations.models import (
    GoalCategory,
    GoalStatus,
    TaskFrequency,
    TaskStatus,
)
from apps.reports.selectors import Granularity, ReportPeriod
from core.serializers import RejectUnknownFieldsMixin


class ReportQuerySerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    period = serializers.ChoiceField(
        choices=ReportPeriod.choices, required=False, default=ReportPeriod.WEEK
    )
    start = serializers.DateField(
        required=False,
        help_text="week / month: any day in it (default: the current one). "
        "custom: the first day (required).",
    )
    end = serializers.DateField(
        required=False, help_text="custom only: the last day (required)."
    )


# --- response ---------------------------------------------------------------


class CountPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.IntegerField()


class NumberPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.FloatField(allow_null=True)


class RiskPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    value = serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)


class PeriodSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ReportPeriod.choices)
    start = serializers.DateField(help_text="First day of the period as asked.")
    end = serializers.DateField(help_text="Last day of the period as asked.")
    data_start = serializers.DateField(
        help_text="First day reported (no earlier than the start of care)."
    )
    data_end = serializers.DateField(
        help_text="Last day reported (no later than today)."
    )
    days = serializers.IntegerField()
    is_partial = serializers.BooleanField(help_text="The period hasn't ended yet.")
    clipped_to_care_start = serializers.BooleanField()
    care_started_on = serializers.DateField()
    timezone = serializers.CharField(help_text="The patient's timezone (local days).")
    granularity = serializers.ChoiceField(choices=Granularity.choices)


class DateRangeSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()


class PatientCancellationsSerializer(serializers.Serializer):
    on_time = serializers.IntegerField()
    late = serializers.IntegerField()


class SessionSeriesSerializer(serializers.Serializer):
    completed = CountPointSerializer(many=True)
    no_show = CountPointSerializer(many=True)


class SessionsSectionSerializer(serializers.Serializer):
    completed = serializers.IntegerField()
    no_show = serializers.IntegerField()
    cancelled_by_patient = PatientCancellationsSerializer()
    cancelled_by_psychologist = serializers.IntegerField()
    cancelled_by_system = serializers.IntegerField()
    expired = serializers.IntegerField()
    attendance_rate = serializers.IntegerField(
        allow_null=True, help_text="completed / (completed + no-show), in percent."
    )
    minutes_attended = serializers.IntegerField()
    next_confirmed_at = serializers.DateTimeField(allow_null=True)
    series = SessionSeriesSerializer()


class ProgressSerializer(serializers.Serializer):
    rated_notes = serializers.IntegerField()
    first = serializers.IntegerField(allow_null=True)
    last = serializers.IntegerField(allow_null=True)
    average = serializers.FloatField(allow_null=True)
    change = serializers.IntegerField(allow_null=True)


class RiskCountsSerializer(serializers.Serializer):
    low = serializers.IntegerField()
    medium = serializers.IntegerField()
    high = serializers.IntegerField()


class RiskSerializer(serializers.Serializer):
    counts = RiskCountsSerializer()
    first = serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)
    latest = serializers.ChoiceField(choices=RiskLevel.choices, allow_null=True)


class NotesSeriesSerializer(serializers.Serializer):
    progress_rating = NumberPointSerializer(many=True)
    risk_level = RiskPointSerializer(many=True)


class NotesSectionSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    progress = ProgressSerializer()
    risk = RiskSerializer()
    series = NotesSeriesSerializer()


class TagCountSerializer(serializers.Serializer):
    tag = serializers.ChoiceField(choices=EmotionTag.choices)
    count = serializers.IntegerField()


class MoodDistributionSerializer(serializers.Serializer):
    def get_fields(self):
        return {str(m): serializers.IntegerField() for m in range(1, 6)}


class MoodSeriesSerializer(serializers.Serializer):
    average_mood = NumberPointSerializer(many=True)


class MoodSectionSerializer(serializers.Serializer):
    check_ins = serializers.IntegerField()
    days_with_check_in_percent = serializers.IntegerField(allow_null=True)
    average_mood = serializers.FloatField(allow_null=True)
    distribution = MoodDistributionSerializer()
    top_tags = TagCountSerializer(many=True)
    longest_streak = serializers.IntegerField()
    series = MoodSeriesSerializer()


class ReportTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    frequency = serializers.ChoiceField(choices=TaskFrequency.choices)
    times_per_week = serializers.IntegerField(allow_null=True)
    status = serializers.ChoiceField(choices=TaskStatus.choices)
    completions = serializers.IntegerField()
    adherence = serializers.IntegerField(
        allow_null=True, help_text="Percent; null if not scheduled in the period."
    )
    done_in_period = serializers.BooleanField(
        allow_null=True, help_text="One-off tasks only."
    )


class ReportGoalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    category = serializers.ChoiceField(choices=GoalCategory.choices)
    status = serializers.ChoiceField(choices=GoalStatus.choices)
    adherence = serializers.IntegerField(allow_null=True)
    tasks = ReportTaskSerializer(many=True)


class CarePlanSeriesSerializer(serializers.Serializer):
    adherence = NumberPointSerializer(many=True)


class CarePlanSectionSerializer(serializers.Serializer):
    has_plan = serializers.BooleanField()
    adherence = serializers.IntegerField(allow_null=True)
    completions = serializers.IntegerField()
    average_difficulty = serializers.FloatField(allow_null=True)
    completion_notes = serializers.IntegerField(
        help_text="How many completions have a note (the text isn't included)."
    )
    goals_achieved = serializers.IntegerField()
    goals_dropped = serializers.IntegerField()
    legacy_items_excluded = serializers.IntegerField(
        help_text="Archived tasks / closed goals from before 2026-11-23 with no "
        "date, left out of adherence."
    )
    goals = ReportGoalSerializer(many=True)
    series = CarePlanSeriesSerializer()


class SOSAlertSerializer(serializers.Serializer):
    date = serializers.DateField()
    status = serializers.ChoiceField(choices=SOSStatus.choices)


class SOSSectionSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    alerts = SOSAlertSerializer(many=True)


class SensorsSectionSerializer(serializers.Serializer):
    available = serializers.BooleanField(help_text="false until 6.5 ships.")


class ComparisonRowSerializer(serializers.Serializer):
    current = serializers.FloatField(allow_null=True)
    previous = serializers.FloatField(allow_null=True)
    change = serializers.FloatField(allow_null=True)


class ComparisonSerializer(serializers.Serializer):
    attendance_rate = ComparisonRowSerializer()
    average_mood = ComparisonRowSerializer()
    adherence = ComparisonRowSerializer()
    average_progress_rating = ComparisonRowSerializer()


class IndicatorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class ReportPatientSerializer(serializers.Serializer):
    display_name = serializers.CharField()


class PatientReportSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    relationship_id = serializers.IntegerField()
    patient = ReportPatientSerializer()
    period = PeriodSerializer()
    previous_period = DateRangeSerializer(allow_null=True)
    sessions = SessionsSectionSerializer()
    therapy_notes = NotesSectionSerializer()
    mood = MoodSectionSerializer()
    care_plan = CarePlanSectionSerializer()
    sos = SOSSectionSerializer()
    sensors = SensorsSectionSerializer()
    comparison = ComparisonSerializer()
    indicators = IndicatorSerializer(many=True)
