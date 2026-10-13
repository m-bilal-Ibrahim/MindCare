"""DRF serializers for the patients API."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.patients.models import (
    MentalHealthHistory,
    PatientProfile,
    YesNo,
    YesNoUnsure,
)
from apps.reference.api.serializers import (
    CitySerializer,
    CountrySerializer,
    LanguageSerializer,
)
from apps.reference.models import Country, Language, Specialization
from core.choices import Gender
from core.serializers import (
    RejectUnknownFieldsMixin,
    free_text_field,
    person_name_field,
    phone_field,
)
from core.validators import validate_iana_timezone

PUBLIC_FLAG_HELP = (
    "If true, other users see your real name instead of your pseudonym. "
    "Going public is a permanent disclosure: people who see your real name while "
    "public may still recognise you later, even if you switch back to private."
)


class PatientRegistrationProfileSerializer(
    RejectUnknownFieldsMixin, serializers.Serializer
):
    """The `profile` object in a patient's register request. `timezone` is read
    from the device by MindCare App; the patient never types it."""

    timezone = serializers.CharField(max_length=64, validators=[validate_iana_timezone])


class PatientProfileUpdateSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    is_profile_public = serializers.BooleanField(
        required=False, help_text=PUBLIC_FLAG_HELP
    )
    country = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Country.objects.all(),
        required=False,
        allow_null=True,
    )
    city = person_name_field("City", required=False, allow_blank=True, allow_null=True)
    timezone = serializers.CharField(
        max_length=64, required=False, validators=[validate_iana_timezone]
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=Gender.choices, required=False, allow_null=True
    )
    # Blank/None skip validators in DRF; the service turns "" into None.
    phone_number = phone_field(required=False, allow_blank=True, allow_null=True)
    preferred_language = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )


# What the one public switch reveals, and what never leaves the patient's
# circle (Q14, docs/decisions.md 2026-10-11). The App shows these lists.
PUBLIC_WHEN_ON = ("full_name", "photo")
ALWAYS_PRIVATE = (
    "date_of_birth",
    "gender",
    "phone_number",
    "mental_health_history",
)


class _PrivacySerializer(serializers.Serializer):
    is_profile_public = serializers.BooleanField()
    shown_when_public = serializers.ListField(child=serializers.CharField())
    always_private = serializers.ListField(child=serializers.CharField())


class _CompletionSerializer(serializers.Serializer):
    missing = serializers.ListField(
        child=serializers.CharField(),
        help_text="Optional profile parts not filled in yet (for the App's "
        "'complete your profile' step).",
    )


class PatientProfileOwnerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    country = CountrySerializer(read_only=True)
    city = CitySerializer(read_only=True)
    preferred_language = LanguageSerializer(read_only=True)
    is_profile_public = serializers.BooleanField(
        read_only=True, help_text=PUBLIC_FLAG_HELP
    )
    photo_url = serializers.SerializerMethodField(
        help_text="Signed link to your photo, valid for a few minutes; null if none."
    )
    privacy = serializers.SerializerMethodField()
    profile_completion = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            "pseudonym",
            "full_name",
            "is_profile_public",
            "photo_url",
            "privacy",
            "profile_completion",
            "country",
            "city",
            "timezone",
            "date_of_birth",
            "gender",
            "phone_number",
            "preferred_language",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_photo_url(self, obj) -> str | None:
        from integrations.storage_client.client import url_or_none

        return url_or_none(obj.photo_key)  # the owner always sees their photo

    @extend_schema_field(_PrivacySerializer)
    def get_privacy(self, obj):
        return {
            "is_profile_public": obj.is_profile_public,
            "shown_when_public": list(PUBLIC_WHEN_ON),
            "always_private": list(ALWAYS_PRIVATE),
        }

    @extend_schema_field(_CompletionSerializer)
    def get_profile_completion(self, obj):
        has_history = MentalHealthHistory.objects.filter(profile=obj).exists()
        present = {
            "date_of_birth": obj.date_of_birth is not None,
            "gender": bool(obj.gender),
            "phone_number": bool(obj.phone_number),
            "city": obj.city_id is not None,
            "preferred_language": obj.preferred_language_id is not None,
            "photo": bool(obj.photo_key),
            "mental_health_history": has_history,
        }
        return {"missing": [name for name, ok in present.items() if not ok]}


class MentalHealthHistoryInputSerializer(
    RejectUnknownFieldsMixin, serializers.Serializer
):
    """PUT /patients/me/history/: the whole history; anything left out is cleared."""

    concerns = serializers.SlugRelatedField(
        slug_field="slug",
        many=True,
        required=False,
        queryset=Specialization.objects.filter(is_active=True),
        help_text="Specialization slugs (GET /reference/specializations/).",
    )
    previous_diagnosis = serializers.ChoiceField(
        choices=YesNoUnsure.choices, required=False, allow_blank=True, allow_null=True
    )
    current_medication = serializers.ChoiceField(
        choices=YesNoUnsure.choices, required=False, allow_blank=True, allow_null=True
    )
    previous_therapy = serializers.ChoiceField(
        choices=YesNo.choices, required=False, allow_blank=True, allow_null=True
    )
    notes = free_text_field(
        "Notes", 10, 1000, required=False, allow_blank=True, allow_null=True
    )


class _ConcernSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()


class MentalHealthHistorySerializer(serializers.Serializer):
    """The history as the patient (or their current psychologist) sees it."""

    concerns = _ConcernSerializer(many=True)
    previous_diagnosis = serializers.CharField(allow_null=True)
    current_medication = serializers.CharField(allow_null=True)
    previous_therapy = serializers.CharField(allow_null=True)
    notes = serializers.CharField()
    is_empty = serializers.BooleanField()
    updated_at = serializers.DateTimeField(allow_null=True)

    @staticmethod
    def data_for(history):
        if history is None:
            return {
                "concerns": [],
                "previous_diagnosis": None,
                "current_medication": None,
                "previous_therapy": None,
                "notes": "",
                "is_empty": True,
                "updated_at": None,
            }
        names = dict(
            Specialization.objects.filter(slug__in=history.concern_slugs).values_list(
                "slug", "name"
            )
        )
        return {
            "concerns": [
                {"slug": slug, "name": names.get(slug, slug)}
                for slug in history.concern_slugs
            ],
            "previous_diagnosis": history.previous_diagnosis or None,
            "current_medication": history.current_medication or None,
            "previous_therapy": history.previous_therapy or None,
            "notes": history.notes,
            "is_empty": history.is_empty,
            "updated_at": history.updated_at,
        }
