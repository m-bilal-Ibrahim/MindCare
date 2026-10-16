"""Write-path business logic for reference data.

Cities are created only as a side effect of a profile write — there is no
public city-create endpoint (spec §3.4).
"""

from django.db import IntegrityError, transaction

from apps.reference.models import City
from core.exceptions import DomainValidationError
from core.validators import normalize_display_text

CITY_NAME_MAX_LENGTH = 120


def resolve_city(*, country, name):
    cleaned = normalize_display_text(name or "")
    if not cleaned:
        raise DomainValidationError({"city": ["City name can't be empty."]})
    if len(cleaned) > CITY_NAME_MAX_LENGTH:
        raise DomainValidationError({"city": ["City name is too long."]})

    existing = City.objects.filter(country=country, name__iexact=cleaned).first()
    if existing is not None:
        return existing
    try:
        with transaction.atomic():
            return City.objects.create(country=country, name=cleaned)
    except IntegrityError:
        # Another request created the same city between our lookup and insert.
        return City.objects.get(country=country, name__iexact=cleaned)


def resolve_location_fields(*, current_country, current_city, fields, city_required):
    """Validate/resolve `country` + `city` in a profile write. `fields["city"]`
    comes in as a name (str) and leaves as a City or None. Mutates `fields`."""
    if (
        "country" in fields
        and fields["country"] is None
        and current_country is not None
    ):
        raise DomainValidationError({"country": ["Country can't be removed once set."]})
    country = fields.get("country", current_country)

    if "city" in fields:
        name = fields["city"]
        if not name:
            if city_required:
                raise DomainValidationError({"city": ["City is required."]})
            fields["city"] = None
        else:
            if country is None:
                raise DomainValidationError(
                    {"city": ["Choose a country before a city."]}
                )
            fields["city"] = resolve_city(country=country, name=name)
    elif (
        "country" in fields
        and current_city is not None
        and current_city.country_id != country.pk
    ):
        if city_required:
            raise DomainValidationError(
                {"city": ["Changing country needs a city in the new country."]}
            )
        fields["city"] = None
    return fields


def ensure_active_choices(*, items, field):
    if not items:
        raise DomainValidationError({field: ["Choose at least one."]})
    inactive = [str(item) for item in items if not item.is_active]
    if inactive:
        raise DomainValidationError(
            {field: [f"No longer available: {', '.join(inactive)}."]}
        )


# --- Admin city verification (admin-panel-2) ----------------------------------
# A city typed at registration starts unverified and stays out of the public
# dropdown until an admin verifies it (docs/decisions.md, 2026-09-29). Admins can
# also merge a misspelt duplicate into the right city, or reject an unused one.


def city_references():
    """(model, field) for every foreign key to City. Profiles point at cities
    with related_name="+", so they are listed here rather than discovered."""
    from apps.ngo.models import NGOProfile, NGOServiceArea
    from apps.patients.models import PatientProfile
    from apps.psychologists.models import PsychologistProfile

    return [
        (PatientProfile, "city"),
        (PsychologistProfile, "city"),
        (NGOProfile, "city"),
        (NGOServiceArea, "city"),
    ]


def city_usage_count(city):
    return sum(
        model.objects.filter(**{field: city}).count()
        for model, field in city_references()
    )


class CityNotFound(Exception):
    """No city with that id (404)."""


def _lock_city(city_id):
    city = City.objects.select_for_update().filter(pk=city_id).first()
    if city is None:
        raise CityNotFound()
    return city


def _log(event, actor, ref_id):
    from core.audit import log_admin_event

    transaction.on_commit(
        lambda: log_admin_event(event=event, actor_id=actor.pk, ref_id=ref_id)
    )


def verify_city(*, actor, city_id):
    """Show a city in the public dropdown."""
    with transaction.atomic():
        city = _lock_city(city_id)
        if city.is_verified:
            raise DomainValidationError({"city": ["This city is already verified."]})
        city.is_verified = True
        city.save(update_fields=["is_verified"])
        _log("city_verified", actor, f"city:{city.pk}")
    return city


def merge_city(*, actor, city_id, into_id):
    """Move every profile and service area from an unverified city to another
    city in the same country, then delete it. An NGO that already serves the
    target city keeps one service area, not two."""
    from apps.ngo.models import NGOServiceArea

    if int(city_id) == int(into_id):
        raise DomainValidationError({"into": ["Choose a different city."]})
    with transaction.atomic():
        source = _lock_city(city_id)
        target = City.objects.select_for_update().filter(pk=into_id).first()
        if target is None:
            raise DomainValidationError({"into": ["That city doesn't exist."]})
        if source.is_verified:
            raise DomainValidationError(
                {"city": ["Only an unverified city can be merged away."]}
            )
        if target.country_id != source.country_id:
            raise DomainValidationError(
                {"into": ["Choose a city in the same country."]}
            )
        already_served = NGOServiceArea.objects.filter(city=target).values("ngo_id")
        NGOServiceArea.objects.filter(city=source, ngo_id__in=already_served).delete()
        for model, field in city_references():
            model.objects.filter(**{field: source}).update(**{field: target})
        source.delete()
        _log("city_merged", actor, f"city:{city_id}->city:{target.pk}")
    return target


def reject_city(*, actor, city_id):
    """Delete an unverified city nobody uses (e.g. spam typed at registration).
    A city in use must be merged into the right one instead."""
    with transaction.atomic():
        city = _lock_city(city_id)
        if city.is_verified:
            raise DomainValidationError(
                {"city": ["A verified city can't be rejected."]}
            )
        used = city_usage_count(city)
        if used:
            raise DomainValidationError(
                {
                    "city": [
                        f"This city is used by {used} profile(s) or service "
                        "area(s). Merge it into the right city instead."
                    ]
                }
            )
        city.delete()
        _log("city_rejected", actor, f"city:{city_id}")
