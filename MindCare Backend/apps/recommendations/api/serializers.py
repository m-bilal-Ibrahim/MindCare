"""DRF serializers for the care plan API (docs/validation-rules.md)."""

from rest_framework import serializers

from apps.recommendations.models import (
    COMPLETION_NOTE_MAX,
    COMPLETION_NOTE_MIN,
    DESCRIPTION_MAX,
    DESCRIPTION_MIN,
    DIFFICULTY_MAX,
    DIFFICULTY_MIN,
    TIMES_PER_WEEK_MAX,
    TIMES_PER_WEEK_MIN,
    TITLE_MAX,
    TITLE_MIN,
    GoalCategory,
    GoalStatus,
    TaskCompletion,
    TaskFrequency,
    TaskStatus,
)
from core.serializers import (
    NormalizedCharField,
    RejectUnknownFieldsMixin,
    free_text_field,
    whole_number_field,
)
from core.validators import FreeTextValidator, normalize_single_line


def title_field(**kwargs):
    """Single line, free-text rule 3-120."""
    return NormalizedCharField(
        normaliser=normalize_single_line,
        validators=[FreeTextValidator("Title", TITLE_MIN, TITLE_MAX)],
        **kwargs,
    )


class _Partial:
    """Every field optional (PATCH)."""

    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.required = False
        return fields


# --- psychologist input ------------------------------------------------------


class GoalCreateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    title = title_field()
    description = free_text_field(
        "Description",
        DESCRIPTION_MIN,
        DESCRIPTION_MAX,
        required=False,
        allow_blank=True,
    )
    category = serializers.ChoiceField(choices=GoalCategory.choices)
    target_date = serializers.DateField(required=False, allow_null=True)


class GoalUpdateSerializer(_Partial, GoalCreateSerializer):
    status = serializers.ChoiceField(choices=GoalStatus.choices)


class TaskCreateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    title = title_field()
    instructions = free_text_field(
        "Instructions",
        DESCRIPTION_MIN,
        DESCRIPTION_MAX,
        required=False,
        allow_blank=True,
    )
    frequency = serializers.ChoiceField(choices=TaskFrequency.choices)
    times_per_week = whole_number_field(
        "Times per week",
        TIMES_PER_WEEK_MIN,
        TIMES_PER_WEEK_MAX,
        required=False,
        allow_null=True,
    )
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)


class TaskUpdateSerializer(_Partial, TaskCreateSerializer):
    status = serializers.ChoiceField(choices=TaskStatus.choices)


class DaysQuerySerializer(serializers.Serializer):
    days = serializers.ChoiceField(choices=[7, 30, 90], required=False, default=30)


# --- patient input -------------------------------------------------------------


class CompletionCreateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    local_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Today or yesterday in your timezone; default today.",
    )
    note = free_text_field(
        "Note",
        COMPLETION_NOTE_MIN,
        COMPLETION_NOTE_MAX,
        required=False,
        allow_blank=True,
        help_text="Optional. Encrypted; your current psychologist reads it.",
    )
    difficulty = whole_number_field(
        "Difficulty",
        DIFFICULTY_MIN,
        DIFFICULTY_MAX,
        required=False,
        allow_null=True,
        help_text="How hard was it? 1 (easy) to 5 (very hard).",
    )


# --- output ----------------------------------------------------------------------


def _windows_field():
    return serializers.DictField(
        child=serializers.IntegerField(allow_null=True),
        help_text="Adherence % (0-100) for keys '7', '30', '90' (days, today "
        "included); null when nothing recurring was scheduled.",
    )


class _Person(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    instructions = serializers.CharField()
    frequency = serializers.ChoiceField(choices=TaskFrequency.choices)
    times_per_week = serializers.IntegerField(allow_null=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    status = serializers.ChoiceField(choices=TaskStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    done_today = serializers.BooleanField()
    last_completed_on = serializers.DateField(allow_null=True)
    is_done = serializers.BooleanField(
        allow_null=True, help_text="One-off tasks only; null for recurring tasks."
    )
    adherence = _windows_field()


class GoalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=GoalCategory.choices)
    target_date = serializers.DateField(allow_null=True)
    status = serializers.ChoiceField(choices=GoalStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    adherence = _windows_field()
    tasks = TaskSerializer(many=True)


class CarePlanSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True, help_text="Null: no plan yet.")
    version = serializers.IntegerField()
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
    can_track = serializers.BooleanField(
        help_text="Whether the patient can log completions now."
    )
    today = serializers.DateField(help_text="The patient's local date.")
    psychologist = _Person(allow_null=True)
    adherence = _windows_field()
    goals = GoalSerializer(many=True)


class CarePlanListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    psychologist = _Person()
    can_track = serializers.BooleanField()
    active_goals = serializers.IntegerField()
    updated_at = serializers.DateTimeField()


class GoalWriteResultSerializer(serializers.Serializer):
    """What a goal create/update returns (the plan has the full picture)."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=GoalCategory.choices)
    target_date = serializers.DateField(allow_null=True)
    status = serializers.ChoiceField(choices=GoalStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class TaskWriteResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    goal = serializers.IntegerField(source="goal_id")
    title = serializers.CharField()
    instructions = serializers.CharField()
    frequency = serializers.ChoiceField(choices=TaskFrequency.choices)
    times_per_week = serializers.IntegerField(allow_null=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    status = serializers.ChoiceField(choices=TaskStatus.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class CompletionSerializer(serializers.ModelSerializer):
    goal = serializers.IntegerField(source="task.goal_id", read_only=True)

    class Meta:
        model = TaskCompletion
        fields = [
            "id",
            "task",
            "goal",
            "local_date",
            "note",
            "difficulty",
            "created_at",
        ]
        read_only_fields = fields


class _VersionTask(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    instructions = serializers.CharField()
    frequency = serializers.CharField()
    times_per_week = serializers.IntegerField(allow_null=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()


class _VersionGoal(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    target_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    tasks = _VersionTask(many=True)


class CarePlanVersionSerializer(serializers.Serializer):
    version = serializers.IntegerField()
    saved_at = serializers.DateTimeField()
    goals = _VersionGoal(many=True)
