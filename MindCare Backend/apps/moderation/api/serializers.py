"""DRF serializers for the moderation API (6.3 reports and complaints)."""

from rest_framework import serializers

from apps.accounts.api.admin_serializers import PartySerializer, party_summary
from apps.moderation.models import Report, ReportReason, ReportStatus
from core.serializers import RejectUnknownFieldsMixin, free_text_field


class ReportCreateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    """A patient sends `psychologist` (the directory id); a psychologist sends
    `relationship` (the patient's relationship id)."""

    psychologist = serializers.IntegerField(min_value=1, required=False)
    relationship = serializers.IntegerField(min_value=1, required=False)
    reason = serializers.ChoiceField(choices=ReportReason.choices)
    description = free_text_field(
        "Description",
        10,
        1000,
        required=False,
        allow_blank=True,
        help_text="Optional. Encrypted; only admins read it.",
    )


class MyReportSerializer(serializers.ModelSerializer):
    """What a reporter sees back: never the other person's details or the outcome
    beyond the status."""

    class Meta:
        model = Report
        fields = ["id", "reason", "status", "created_at", "resolved_at"]
        read_only_fields = fields


class AdminReportListItemSerializer(serializers.ModelSerializer):
    reporter = serializers.SerializerMethodField()
    reported_user = serializers.SerializerMethodField()
    has_description = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "reason",
            "status",
            "created_at",
            "resolved_at",
            "reporter",
            "reported_user",
            "has_description",
        ]
        read_only_fields = fields

    def get_reporter(self, obj) -> PartySerializer:
        return party_summary(obj.reporter)

    def get_reported_user(self, obj) -> PartySerializer:
        return party_summary(obj.reported_user)

    def get_has_description(self, obj) -> bool:
        return bool(obj.description)


class AdminReportDetailSerializer(AdminReportListItemSerializer):
    """Opening a report: the description (audited read) and both people's real
    identities (a private patient's reveal is audited)."""

    description = serializers.CharField(read_only=True)
    relationship_id = serializers.IntegerField(read_only=True)
    resolved_by_id = serializers.IntegerField(read_only=True, allow_null=True)
    reported_user_is_active = serializers.BooleanField(
        source="reported_user.is_active", read_only=True
    )

    class Meta(AdminReportListItemSerializer.Meta):
        fields = [
            *AdminReportListItemSerializer.Meta.fields,
            "description",
            "relationship_id",
            "resolved_by_id",
            "reported_user_is_active",
        ]
        read_only_fields = fields

    def get_reporter(self, obj) -> PartySerializer:
        return party_summary(obj.reporter, reveal_for=self.context["request"].user)

    def get_reported_user(self, obj) -> PartySerializer:
        return party_summary(obj.reported_user, reveal_for=self.context["request"].user)


class AdminReportsQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReportStatus.choices, required=False)
