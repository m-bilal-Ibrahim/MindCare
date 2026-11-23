"""Settings for the scheduled jobs run by GitHub Actions (docs/decisions.md,
2026-11-23). Used only by `manage.py run_maintenance` and `send_reminders`.

Narrow on purpose: the runner gets a low-privilege database role
(`mindcare_scheduler`, see docs/deployment.md), its own SECRET_KEY, and the email
variables. It never gets FIELD_ENCRYPTION_KEY, the storage keys or Redis: the
jobs read no encrypted column, upload nothing and throttle nothing. The commands
skip system checks for the same reason.

base.py reads REDIS_URL without a default, so the workflow sets a placeholder;
it is never used because the cache below is in memory.
"""

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = []

# One short-lived process per run: no persistent connections, TLS required.
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
DATABASES["default"].setdefault("OPTIONS", {}).setdefault(  # noqa: F405
    "sslmode",
    env("SCHEDULER_DB_SSLMODE", default="require"),  # noqa: F405
)

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Off unless the workflow configures a provider; never "console" (it would print
# reminder emails into public logs).
# An unset GitHub variable arrives as an empty string, hence the `or`.
EMAIL_PROVIDER = env("EMAIL_PROVIDER", default="") or "disabled"  # noqa: F405
if EMAIL_PROVIDER == "console":
    EMAIL_PROVIDER = "disabled"
DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL or "no-reply@mindcare.local"  # noqa: F405
DEFAULT_FROM_NAME = DEFAULT_FROM_NAME or "MindCare"  # noqa: F405
# The process exits after the run: send synchronously, not on a thread.
EMAIL_SEND_IN_BACKGROUND = False
