"""Read-path queries for the Motivation Corner. Active quotes only: an admin
unticking is_active hides a quote from the next request (no cache)."""

import random

from apps.motivation.models import Quote


def active_quotes(*, category=None):
    qs = Quote.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)
    return qs


def random_active_quote(*, category=None):
    """One random active quote, or None. Count + random offset instead of
    ORDER BY RANDOM(), which sorts the whole table."""
    qs = active_quotes(category=category)
    count = qs.count()
    if not count:
        return None
    return qs[random.randrange(count)]


# --- Religious content (6.10) -------------------------------------------------


def has_opted_in_to_religious_content(*, user):
    from apps.motivation.models import ReligiousContentPreference

    return ReligiousContentPreference.objects.filter(user=user).exists()


def active_duas():
    from apps.motivation.models import Dua

    return Dua.objects.filter(is_active=True)


def active_surahs():
    from apps.motivation.models import Surah

    return Surah.objects.filter(is_active=True)


def admin_content(*, model, is_active=None):
    """Every quote / dua / surah for the admin console, active or not, in the
    model's own order."""
    qs = model.objects.all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs
