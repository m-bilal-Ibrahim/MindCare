"""Read-path query logic for emergency (6.12 SOS).

What a patient sees when they press SOS (docs/decisions.md, 2026-10-28):
helplines for their country (plus ones that work anywhere), hospitals in their
profile city, their current psychologist, and approved NGOs whose service area
covers them. Every list may be empty; the fixed emergency message never is.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import ApprovalStatus
from apps.emergency.models import EmergencyContact, Helpline, Hospital, SOSEvent
from apps.ngo.models import NGOServiceArea
from apps.relationships.models import CareRelationship, RelationshipStatus
from apps.relationships.selectors import get_active_relationship

EMERGENCY_MESSAGE = (
    "If you are in immediate danger, call your local emergency number now."
)
PSYCHOLOGIST_RECENT_DAYS = 30


def helplines_for(*, country):
    qs = Helpline.objects.filter(is_active=True).select_related("country")
    if country is None:
        return qs.filter(country__isnull=True)
    return qs.filter(Q(country=country) | Q(country__isnull=True))


def hospitals_for(*, city):
    if city is None:
        return Hospital.objects.none()
    return Hospital.objects.filter(is_active=True, city=city).select_related("city")


def ngos_for(*, country, city):
    """Approved, active NGOs whose service area covers the city (or the whole
    country). One row per NGO: the most specific matching area."""
    if country is None:
        return []
    covers = Q(country=country, city__isnull=True)
    if city is not None:
        covers |= Q(country=country, city=city)
    areas = (
        NGOServiceArea.objects.filter(covers)
        .filter(
            ngo__user__is_active=True,
            ngo__user__approval_status=ApprovalStatus.APPROVED,
        )
        .select_related("ngo", "country", "city")
        .order_by("ngo__organization_name", "city_id")
    )
    seen, result = set(), []
    for area in areas:
        if area.ngo_id in seen:
            continue
        seen.add(area.ngo_id)
        result.append(area)
    return result


def emergency_resources(*, patient_profile):
    """Everything the SOS screen shows. Never raises for missing data."""
    country, city = patient_profile.country, patient_profile.city
    relationship = get_active_relationship(patient=patient_profile)
    return {
        "message": EMERGENCY_MESSAGE,
        "helplines": list(helplines_for(country=country)),
        "hospitals": list(hospitals_for(city=city)),
        "ngos": ngos_for(country=country, city=city),
        "psychologist": relationship.psychologist if relationship else None,
    }


def contacts_for(*, patient_profile):
    return EmergencyContact.objects.filter(patient=patient_profile)


def events_for_patient(*, patient_profile):
    return SOSEvent.objects.filter(patient=patient_profile)


def events_for_admin(*, status=None):
    """Open alerts oldest first (the longest-waiting is handled first);
    otherwise newest first."""
    qs = SOSEvent.objects.select_related(
        "patient__user", "patient__city", "patient__country", "city", "country"
    )
    if status:
        qs = qs.filter(status=status)
    if status == "open":
        return qs.order_by("created_at", "id")
    return qs.order_by("-created_at", "-id")


def events_for_psychologist(*, psychologist_user, now=None):
    """SOS alerts from the psychologist's CURRENT patients in the last 30 days.
    Object-level: only patients with an accepted relationship with this
    psychologist; access ends when care ends."""
    now = now or timezone.now()
    current = CareRelationship.objects.filter(
        psychologist__user=psychologist_user,
        psychologist__user__is_active=True,
        psychologist__user__approval_status=ApprovalStatus.APPROVED,
        status=RelationshipStatus.ACCEPTED,
    )
    relationship_by_patient = dict(current.values_list("patient_id", "id"))
    events = (
        SOSEvent.objects.filter(
            patient_id__in=relationship_by_patient,
            created_at__gte=now - timedelta(days=PSYCHOLOGIST_RECENT_DAYS),
        )
        .select_related("patient__user")
        .order_by("-created_at", "-id")
    )
    return events, relationship_by_patient
