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
