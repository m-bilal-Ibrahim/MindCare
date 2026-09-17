"""Read-path query logic for accounts.

Views call into these functions to fetch data. Object-level ownership
filtering (e.g. scoping a psychologist's queries to their own patients)
belongs here, not just in permission classes.
"""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


def get_user_from_refresh_token(refresh_token):
    """Decode a refresh token and look up its owning user, or None if invalid."""
    try:
        token = RefreshToken(refresh_token)
    except TokenError:
        return None
    return User.objects.filter(pk=token["user_id"]).first()
