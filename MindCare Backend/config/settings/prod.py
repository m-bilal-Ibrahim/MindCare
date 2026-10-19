"""Production settings (Render deployment)."""

from .base import *  # noqa: F401,F403

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS: one day first; raise to one year (31536000) after a week without problems
# (docs/decisions.md, 2026-10-10). No includeSubDomains: the host is a subdomain
# of onrender.com, which this app doesn't control.
SECURE_HSTS_SECONDS = 86400

# Uploads must go to the private bucket (configured in base.py from the
# SUPABASE_S3_* variables). Without them the REQUIRE_OBJECT_STORAGE system check
# fails the deploy, so files can never land on Render's temporary disk.
REQUIRE_OBJECT_STORAGE = True

# No email goes out until a provider is configured on Render. Never "console" in
# production: it would print one-time codes into the logs (mindcare.E003).
EMAIL_PROVIDER = env("EMAIL_PROVIDER", default="disabled")  # noqa: F405

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

# Pinned explicitly so production only ever allows the real web origin, even if
# base.py's list changes later, plus whatever CORS_EXTRA_ALLOWED_ORIGINS adds on
# Render (unset by default).
CORS_ALLOWED_ORIGINS = [
    "https://mind-care-web-seven.vercel.app",
    *CORS_EXTRA_ALLOWED_ORIGINS,  # noqa: F405
]
