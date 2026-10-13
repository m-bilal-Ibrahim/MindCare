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


class EncryptedFreeTextField(EncryptedTextField):
    """Free text that is validated in plain form (normalised, the free-text rule
    in docs/validation-rules.md) and then stored encrypted."""

    def __init__(
        self, *args, label="Text", min_length=1, rule_max_length=1000, **kwargs
    ):
        from core.validators import FreeTextValidator

        self.label = label
        self.min_length = min_length
        self.rule_max_length = rule_max_length
        super().__init__(*args, **kwargs)
        self.validators.append(FreeTextValidator(label, min_length, rule_max_length))

    def to_python(self, value):
        from core.validators import normalize_multiline_text

        value = super().to_python(value)
        if isinstance(value, str):
            value = normalize_multiline_text(value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.update(
            label=self.label,
            min_length=self.min_length,
            rule_max_length=self.rule_max_length,
        )
        return name, path, args, kwargs
