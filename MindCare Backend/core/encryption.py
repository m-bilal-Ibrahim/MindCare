"""
Field-level encryption for health data at rest (docs/decisions.md, 2026-10-11).

EncryptedTextField stores Fernet tokens (AES-128-CBC + HMAC-SHA256, from the
`cryptography` package) and decrypts on read. The key comes from the
FIELD_ENCRYPTION_KEY setting; FIELD_ENCRYPTION_PREVIOUS_KEYS still decrypt
during a rotation. Encrypted columns can't be searched, filtered or sorted:
only store text that is read whole, by an audited path.

Losing the key makes the data unreadable for good, so production keeps a copy
of it outside Render (a password manager).
"""

from functools import cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


@cache
def _fernet(primary, previous):
    if not primary:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY is not set; encrypted fields can't be used."
        )
    try:
        return MultiFernet([Fernet(k) for k in (primary, *previous)])
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY (or a previous key) isn't a valid Fernet key."
        ) from exc


def get_fernet():
    return _fernet(
        settings.FIELD_ENCRYPTION_KEY, tuple(settings.FIELD_ENCRYPTION_PREVIOUS_KEYS)
    )


def encrypt_text(value):
    return get_fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_text(token):
    try:
        return get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        # Never include the token or any plaintext in the message.
        raise ImproperlyConfigured(
            "An encrypted value couldn't be decrypted with the configured keys."
        ) from exc


class EncryptedTextField(models.TextField):
    """Plain str in Python, Fernet token in the database. Blank stays blank
    (so 'not given' is still distinguishable without decrypting)."""

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return decrypt_text(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return encrypt_text(value)

    def get_lookup(self, lookup_name):
        # Only isnull makes sense: every encryption produces a different token,
        # so equality or text lookups would silently never match.
        if lookup_name != "isnull":
            return None
        return super().get_lookup(lookup_name)
