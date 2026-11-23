"""Read-path queries for the wellness library (6.9). Published items only for
patients and psychologists; admins see everything through admin_items()."""

from django.db.models import Q

from apps.wellness.models import WellnessFavourite, WellnessItem

DISCLAIMER = (
    "General wellbeing information, not medical advice. Talk to your "
    "psychologist or doctor before starting something new."
)
UNAVAILABLE = "This resource is no longer available."


def published_items(
    *, category=None, kind=None, difficulty=None, max_duration=None, search=None
):
    qs = WellnessItem.objects.filter(is_published=True)
    if category:
        qs = qs.filter(category=category)
    if kind:
        qs = qs.filter(kind=kind)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)
    if max_duration:
        qs = qs.filter(duration_minutes__lte=max_duration)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(summary__icontains=search))
    return qs


def published_item(*, item_id):
    return WellnessItem.objects.filter(pk=item_id, is_published=True).first()


def favourite_item_ids(*, patient_profile, item_ids):
    return set(
        WellnessFavourite.objects.filter(
            patient=patient_profile, item_id__in=item_ids
        ).values_list("item_id", flat=True)
    )


def patient_favourites(*, patient_profile):
    """The patient's saved items that are still published, newest save first."""
    return WellnessItem.objects.filter(
        favourites__patient=patient_profile, is_published=True
    ).order_by("-favourites__created_at", "-id")


def admin_items(*, is_published=None, category=None, kind=None):
    qs = WellnessItem.objects.all()
    if is_published is not None:
        qs = qs.filter(is_published=is_published)
    if category:
        qs = qs.filter(category=category)
    if kind:
        qs = qs.filter(kind=kind)
    return qs


def content_summary(item):
    """What a care-plan task shows about its linked item (None if no link). A
    hidden item shows only its id and the 'no longer available' message."""
    if item is None:
        return None
    if not item.is_published:
        return {
            "id": item.pk,
            "is_available": False,
            "kind": None,
            "category": None,
            "title": None,
            "duration_minutes": None,
            "message": UNAVAILABLE,
        }
    return {
        "id": item.pk,
        "is_available": True,
        "kind": item.kind,
        "category": item.category,
        "title": item.title,
        "duration_minutes": item.duration_minutes,
        "message": None,
    }
