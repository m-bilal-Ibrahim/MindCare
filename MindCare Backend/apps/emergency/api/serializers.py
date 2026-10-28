"""DRF serializers for the emergency API (6.12 SOS)."""

from rest_framework import serializers

from apps.accounts.api.admin_serializers import PartySerializer, party_summary
from apps.emergency.models import (
    ContactRelationship,
    EmergencyContact,
    SOSEvent,
    SOSOutcome,
    SOSStatus,
)
from apps.emergency.services import CANCEL_WINDOW
from core.serializers import (
    RejectUnknownFieldsMixin,
    StrictTrueField,
    number_field,
    person_name_field,
    phone_field,
)

COORDINATES_PAIR = "Send both latitude and longitude, or neither."
CONSENT_MESSAGE = "Confirm this person agreed to be your emergency contact."


# --- Resources shown on the SOS screen ---------------------------------------


class HelplineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    number = serializers.CharField()
    description = serializers.CharField()
    country = serializers.CharField(
        source="country.code", allow_null=True, default=None
    )


class HospitalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField(source="city.name")


class ServiceAreaSerializer(serializers.Serializer):
    country = serializers.CharField(source="country.name")
    city = serializers.CharField(source="city.name", allow_null=True, default=None)


class NGOResourceSerializer(serializers.Serializer):
    """Built from the matching NGOServiceArea. The official email stays
    admin-only (Q17)."""

    organization_name = serializers.CharField(source="ngo.organization_name")
    official_phone = serializers.CharField(source="ngo.official_phone")
    website = serializers.CharField(source="ngo.website")
    service_area = serializers.SerializerMethodField()

    def get_service_area(self, obj) -> ServiceAreaSerializer:
        return ServiceAreaSerializer(obj).data


class CurrentPsychologistSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(source="user.full_name")


class EmergencyResourcesSerializer(serializers.Serializer):
    message = serializers.CharField()
    helplines = HelplineSerializer(many=True)
    hospitals = HospitalSerializer(many=True)
    ngos = NGOResourceSerializer(many=True)
    psychologist = CurrentPsychologistSerializer(allow_null=True)


# --- Pressing SOS --------------------------------------------------------------


class SOSRequestSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    latitude = number_field("Latitude", -90, 90, required=False, allow_null=True)
    longitude = number_field("Longitude", -180, 180, required=False, allow_null=True)

    def validate(self, attrs):
        has_lat = attrs.get("latitude") is not None
        has_lng = attrs.get("longitude") is not None
        if has_lat != has_lng:
            raise serializers.ValidationError({"latitude": [COORDINATES_PAIR]})
        return attrs


class SOSEventSerializer(serializers.ModelSerializer):
    """The patient's own view of an alert."""

    cancel_until = serializers.SerializerMethodField()

    class Meta:
        model = SOSEvent
        fields = [
            "id",
            "status",
            "created_at",
            "cancel_until",
            "location_source",
            "contacts_notified",
            "psychologist_notified",
        ]
        read_only_fields = fields

    def get_cancel_until(self, obj) -> str:
        return (obj.created_at + CANCEL_WINDOW).isoformat()


class SOSResponseSerializer(EmergencyResourcesSerializer):
    """`alert` is null only if recording the alert failed; the message and
    resources still come back (SOS never blocks the patient)."""

    alert = SOSEventSerializer(allow_null=True)


# --- Emergency contacts ------------------------------------------------------


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["id", "name", "relationship", "email", "phone", "created_at"]
        read_only_fields = fields


class EmergencyContactWriteSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    name = person_name_field("Name")
    relationship = serializers.ChoiceField(choices=ContactRelationship.choices)
    email = serializers.EmailField(max_length=254)
    phone = phone_field(required=False, allow_blank=True)
    consent_confirmed = StrictTrueField(
        error_messages={"invalid": CONSENT_MESSAGE, "required": CONSENT_MESSAGE},
        help_text="Must be true: the patient confirms this person agreed.",
    )

    def validate_email(self, value):
        return value.strip().lower()


class EmergencyContactUpdateSerializer(EmergencyContactWriteSerializer):
    """PATCH: any field may be sent; consent was confirmed when it was added."""

    def get_fields(self):
        fields = super().get_fields()
        fields.pop("consent_confirmed")
        for field in fields.values():
            field.required = False
        return fields


# --- Psychologist ------------------------------------------------------------


class PsychologistAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=SOSStatus.choices)
    relationship_id = serializers.IntegerField()
    patient_name = serializers.CharField()


# --- Admin -------------------------------------------------------------------


class AdminSOSQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SOSStatus.choices, required=False)


class AdminSOSListItemSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    city = serializers.CharField(source="city.name", allow_null=True, default=None)
    country = serializers.CharField(
        source="country.name", allow_null=True, default=None
    )
    has_coordinates = serializers.SerializerMethodField()

    class Meta:
        model = SOSEvent
        fields = [
            "id",
            "status",
            "outcome",
            "created_at",
            "cancelled_at",
            "followed_up_at",
            "closed_at",
            "patient",
            "city",
            "country",
            "location_source",
            "has_coordinates",
            "contacts_notified",
            "psychologist_notified",
        ]
        read_only_fields = fields

    def get_patient(self, obj) -> PartySerializer:
        return party_summary(obj.patient.user)

    def get_has_coordinates(self, obj) -> bool:
        return bool(obj.coordinates)


class AdminSOSDetailSerializer(AdminSOSListItemSerializer):
    """Opening an alert reveals the patient (audited) and their contact details
    for follow-up, plus the rounded device coordinates if any."""

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    patient_email = serializers.EmailField(source="patient.user.email")
    patient_phone = serializers.CharField(
        source="patient.phone_number", allow_null=True
    )
    followed_up_by_id = serializers.IntegerField(allow_null=True)
    closed_by_id = serializers.IntegerField(allow_null=True)

    class Meta(AdminSOSListItemSerializer.Meta):
        fields = [
            *AdminSOSListItemSerializer.Meta.fields,
            "latitude",
            "longitude",
            "patient_email",
            "patient_phone",
            "followed_up_by_id",
            "closed_by_id",
        ]
        read_only_fields = fields

    def get_patient(self, obj) -> PartySerializer:
        return party_summary(obj.patient.user, reveal_for=self.context["request"].user)

    def _coordinate(self, obj, index):
        if not obj.coordinates:
            return None
        return float(obj.coordinates.split(",")[index])

    def get_latitude(self, obj) -> float | None:
        return self._coordinate(obj, 0)

    def get_longitude(self, obj) -> float | None:
        return self._coordinate(obj, 1)


class CloseSOSSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    outcome = serializers.ChoiceField(choices=SOSOutcome.choices)
