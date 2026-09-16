"""Settings used when running the test suite (pytest-django)."""

from .base import *  # noqa: F401,F403

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use LocMemCache for tests to keep them fast and isolated from the real
# Redis instance used in dev/prod (see base.py's CACHES for the rationale).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
