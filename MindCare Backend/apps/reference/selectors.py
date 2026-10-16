"""Read-path query logic for reference data. All public (no PHI)."""

from apps.reference.models import City, Country, Language, Specialization
from core.validators import normalize_display_text


def list_countries():
    return Country.objects.all()


def search_cities(*, country_code, search=None, limit=20):
    qs = City.objects.filter(
        country__code=country_code.upper(), is_verified=True
    ).select_related("country")
    if search:
        qs = qs.filter(name__istartswith=normalize_display_text(search))
    return list(qs.order_by("name")[:limit])


def list_languages():
    return Language.objects.filter(is_active=True)


def list_specializations():
    return list(Specialization.objects.filter(is_active=True))


def admin_cities(*, status=None, country_code=None, search=None):
    """Cities for the admin verification screen. `status`: "unverified"
    (default view, oldest first so the longest-waiting comes first),
    "verified", or None for all. Each row carries `usage_count`."""
    from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce

    from apps.reference.services import city_references

    qs = City.objects.select_related("country")
    if status == "unverified":
        qs = qs.filter(is_verified=False).order_by("id")
    elif status == "verified":
        qs = qs.filter(is_verified=True).order_by("name", "id")
    else:
        qs = qs.order_by("is_verified", "name", "id")
    if country_code:
        qs = qs.filter(country__code=country_code.upper())
    if search:
        qs = qs.filter(name__icontains=normalize_display_text(search))

    usage = Value(0, output_field=IntegerField())
    for model, field in city_references():
        counted = (
            model.objects.filter(**{field: OuterRef("pk")})
            .order_by()
            .values(field)
            .annotate(n=Count("pk"))
            .values("n")
        )
        usage = usage + Coalesce(
            Subquery(counted, output_field=IntegerField()), Value(0)
        )
    return qs.annotate(usage_count=usage)
