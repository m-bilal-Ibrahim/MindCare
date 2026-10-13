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

# Uploads: a private Supabase Storage bucket over its S3-compatible API
# (django-storages). Keys are storage-only S3 access keys, not the service_role
# key (docs/decisions.md, 2026-10-11). Files are reachable only via signed URLs.
# Without these variables the default storage stays on local disk, and the
# REQUIRE_OBJECT_STORAGE system check fails the deploy.
REQUIRE_OBJECT_STORAGE = True
if env("SUPABASE_S3_BUCKET", default=""):  # noqa: F405
    STORAGES = {
        **STORAGES,  # noqa: F405
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": env("SUPABASE_S3_BUCKET"),  # noqa: F405
                "endpoint_url": env("SUPABASE_S3_ENDPOINT"),  # noqa: F405
                "region_name": env("SUPABASE_S3_REGION"),  # noqa: F405
                "access_key": env("SUPABASE_S3_ACCESS_KEY_ID"),  # noqa: F405
                "secret_key": env("SUPABASE_S3_SECRET_ACCESS_KEY"),  # noqa: F405
                "default_acl": None,
                "querystring_auth": True,
                "querystring_expire": SIGNED_URL_EXPIRY_SECONDS,  # noqa: F405
                "file_overwrite": False,
                "signature_version": "s3v4",
                "addressing_style": "path",
            },
        },
    }
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

# Pinned explicitly so production only ever allows the real web origin, even if
# base.py's list changes later, plus whatever CORS_EXTRA_ALLOWED_ORIGINS adds on
# Render (unset by default).
CORS_ALLOWED_ORIGINS = [
    "https://mind-care-web-seven.vercel.app",
    *CORS_EXTRA_ALLOWED_ORIGINS,  # noqa: F405
]
