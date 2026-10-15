"""Serializers for the admin console API (6.3). Admin-only endpoints; patients'
real identities appear only where an admin opens one record, through
get_patient_display_identity() (audited for private profiles)."""

from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.accounts.services import DeactivateReason, RejectReason
from apps.ngo.api.serializers import NGOProfileOwnerSerializer
from apps.patients.selectors import (
    get_patient_display_identity,
    list_display_identity,
)
from apps.psychologists.api.serializers import PsychologistProfileOwnerSerializer
from core.serializers import (
    RejectUnknownFieldsMixin,
    person_name_field,
    search_field,
)


class PendingAccountSerializer(serializers.ModelSerializer):
    """One pending application (contract: MindCare Web/docs/admin-approvals-api-contract.md)."""

    psychologist_profile = serializers.SerializerMethodField()
    ngo_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "approval_status",
            "created_at",
            "submitted_at",
            "psychologist_profile",
            "ngo_profile",
        ]
        read_only_fields = fields

    submitted_at = serializers.DateTimeField(
        source="created_at",
        read_only=True,
        help_text="Waiting since: when the application was submitted (oldest first).",
    )

    def get_psychologist_profile(self, obj) -> PsychologistProfileOwnerSerializer:
        if obj.role != Role.PSYCHOLOGIST:
            return None
        return PsychologistProfileOwnerSerializer(obj.psychologist_profile).data

    def get_ngo_profile(self, obj) -> NGOProfileOwnerSerializer:
        if obj.role != Role.NGO:
            return None
        return NGOProfileOwnerSerializer(obj.ngo_profile).data


class PendingQuerySerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[Role.PSYCHOLOGIST, Role.NGO])


class RejectSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=RejectReason.CHOICES, required=False, allow_null=True
    )


class DeactivateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=DeactivateReason.CHOICES, required=False, allow_null=True
    )


class ReviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "approval_status", "is_active"]
        read_only_fields = fields


class DocumentLinkSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    kind = serializers.CharField()
    file_type = serializers.CharField()
    url = serializers.CharField(
        help_text="Signed; works only for `expires_in` seconds."
    )
    expires_in = serializers.IntegerField()


def party_summary(user, *, reveal_for=None):
    """{id, role, display_name, is_real_name} for a user. Patients show their
    list identity, unless `reveal_for` (an admin) opened this one record."""
    if user.role == Role.PATIENT:
        profile = user.patient_profile
        identity = (
            get_patient_display_identity(patient_profile=profile, viewer=reveal_for)
            if reveal_for is not None
            else list_display_identity(patient_profile=profile)
        )
        return {"id": user.pk, "role": user.role, **identity}
    return {
        "id": user.pk,
        "role": user.role,
        "display_name": user.full_name,
        "is_real_name": True,
    }


class PartySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.CharField()
    display_name = serializers.CharField()
    is_real_name = serializers.BooleanField()


class AdminUserListItemSerializer(serializers.ModelSerializer):
    """A row on the admin Users page. A private patient shows only their
    pseudonym and no email."""

    display_name = serializers.SerializerMethodField()
    is_real_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "role",
            "display_name",
            "is_real_name",
            "email",
            "approval_status",
            "is_active",
            "created_at",
            "last_login",
        ]
        read_only_fields = fields

    def _summary(self, obj):
        cache = self.context.setdefault("_summaries", {})
        if obj.pk not in cache:
            cache[obj.pk] = party_summary(obj)
        return cache[obj.pk]

    def get_display_name(self, obj) -> str:
        return self._summary(obj)["display_name"]

    def get_is_real_name(self, obj) -> bool:
        return self._summary(obj)["is_real_name"]

    def get_email(self, obj) -> str | None:
        if obj.role == Role.PATIENT and not self._summary(obj)["is_real_name"]:
            return None
        return obj.email


class AdminUsersQuerySerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=[Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO], required=False
    )
    status = serializers.ChoiceField(
        choices=["active", "pending", "rejected", "deactivated"], required=False
    )
    search = serializers.CharField(max_length=120, required=False, allow_blank=True)


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """One account opened by an admin. For a private patient this reveals the real
    name and email, and the reveal is audited (get_patient_display_identity).
    Never health data: no date of birth, gender or phone for patients."""

    identity = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    psychologist_profile = serializers.SerializerMethodField()
    ngo_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "role",
            "identity",
            "email",
            "approval_status",
            "is_active",
            "created_at",
            "last_login",
            "patient",
            "psychologist_profile",
            "ngo_profile",
        ]
        read_only_fields = fields

    def _identity(self, obj):
        if "_identity" not in self.context:
            self.context["_identity"] = party_summary(
                obj, reveal_for=self.context["request"].user
            )
        return self.context["_identity"]

    def get_identity(self, obj) -> PartySerializer:
        return self._identity(obj)

    def get_email(self, obj) -> str:
        self._identity(obj)  # a patient's email is shown only after the audited reveal
        return obj.email

    def get_patient(self, obj) -> dict | None:
        if obj.role != Role.PATIENT:
            return None
        from integrations.storage_client.client import url_or_none

        profile = obj.patient_profile
        self._identity(obj)  # the photo identifies them too: after the audited reveal
        return {
            "pseudonym": profile.pseudonym,
            "is_profile_public": profile.is_profile_public,
            "country": profile.country.code if profile.country_id else None,
            "photo_url": url_or_none(profile.photo_key),
        }

    def get_psychologist_profile(self, obj) -> PsychologistProfileOwnerSerializer:
        if obj.role != Role.PSYCHOLOGIST:
            return None
        return PsychologistProfileOwnerSerializer(obj.psychologist_profile).data

    def get_ngo_profile(self, obj) -> NGOProfileOwnerSerializer:
        if obj.role != Role.NGO:
            return None
        return NGOProfileOwnerSerializer(obj.ngo_profile).data


class _RoleCounts(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    pending = serializers.IntegerField()
    rejected = serializers.IntegerField()
    deactivated = serializers.IntegerField()


class _UsersByRole(serializers.Serializer):
    patient = _RoleCounts()
    psychologist = _RoleCounts()
    ngo = _RoleCounts()


class _PendingApprovals(serializers.Serializer):
    psychologist = serializers.IntegerField()
    ngo = serializers.IntegerField()


class _WeeklySignups(serializers.Serializer):
    week_start = serializers.DateField()
    patient = serializers.IntegerField()
    psychologist = serializers.IntegerField()
    ngo = serializers.IntegerField()


class _RecentAction(PartySerializer):
    action = serializers.ChoiceField(choices=["deactivated", "rejected"])
    at = serializers.DateTimeField()


class OverviewSerializer(serializers.Serializer):
    users = _UsersByRole()
    pending_approvals = _PendingApprovals()
    relationships = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count per relationship status (pending, accepted, ended, ...).",
    )
    open_reports = serializers.IntegerField()
    weekly_signups = _WeeklySignups(many=True, help_text="Last 12 weeks.")
    recent_account_actions = serializers.SerializerMethodField(
        help_text=(
            "Accounts deactivated or rejected in the last 30 days, newest first "
            "(max 10). Private patients appear by pseudonym."
        )
    )

    def get_recent_account_actions(self, obj) -> _RecentAction(many=True):
        return [
            {**party_summary(user), "action": action, "at": at}
            for user, action, at in obj["recent_account_actions"]
        ]


# --- Super-admin workflow -----------------------------------------------------


class AdminAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_super_admin",
            "is_active",
            "must_change_password",
            "created_at",
            "last_login",
        ]
        read_only_fields = fields


class CreateAdminSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    full_name = person_name_field("Full name")

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class CreatedAdminSerializer(AdminAccountSerializer):
    temporary_password = serializers.CharField(
        help_text=(
            "Shown once and never again. Give it to the new admin privately; "
            "they must change it before using the admin console."
        )
    )

    class Meta(AdminAccountSerializer.Meta):
        fields = [*AdminAccountSerializer.Meta.fields, "temporary_password"]
        read_only_fields = fields


# --- Psychologist directory (admin) -------------------------------------------


class AdminPsychologistsQuerySerializer(serializers.Serializer):
    accepting = serializers.BooleanField(required=False, allow_null=True, default=None)
    status = serializers.ChoiceField(
        choices=["active", "pending", "rejected", "deactivated"], required=False
    )
    search = search_field(required=False, allow_blank=True)


class AdminPsychologistSerializer(serializers.Serializer):
    """Counts only: never which patients a psychologist has."""

    id = serializers.IntegerField(source="user_id", help_text="The user id.")
    full_name = serializers.CharField(source="user.full_name")
    email = serializers.EmailField(source="user.email")
    approval_status = serializers.CharField(source="user.approval_status")
    is_active = serializers.BooleanField(source="user.is_active")
    is_accepting_patients = serializers.BooleanField()
    not_accepting_reason = serializers.CharField(allow_null=True)
    current_patient_count = serializers.IntegerField()
    pending_request_count = serializers.IntegerField(
        help_text="Open (unexpired) requests waiting for an answer."
    )
    last_active = serializers.SerializerMethodField(
        help_text="today, this_week, this_month, over_a_month or never."
    )
    country = serializers.CharField(source="country.code")
    city = serializers.CharField(source="city.name")
    years_of_experience = serializers.IntegerField()
    created_at = serializers.DateTimeField(source="user.created_at")

    def get_last_active(self, obj) -> str:
        from apps.relationships.selectors import last_active_band

        return last_active_band(obj.user.last_active_at)
