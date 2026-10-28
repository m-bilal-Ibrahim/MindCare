"""
Base settings shared by all environments.

dev.py, prod.py and test.py each `from .base import *` and override
whatever they need. Every secret/config value is read from the
environment (via django-environ, backed by a .env file) — nothing
sensitive is hardcoded here.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

AUTH_USER_MODEL = "accounts.User"

LOCAL_APPS = [
    "apps.accounts",
    "apps.reference",
    "apps.stats",
    "apps.ai",
    "apps.motivation",
    "apps.patients",
    "apps.psychologists",
    "apps.relationships",
    "apps.appointments",
    "apps.clinical_notes",
    "apps.journals",
    "apps.recommendations",
    "apps.wearables",
    "apps.reports",
    "apps.payments",
    "apps.notifications",
    "apps.communities",
    "apps.moderation",
    "apps.ngo",
    "apps.rewards",
    "apps.emergency",
    "apps.audit",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
]

DJANGO_APPS = [
    "config.apps.MindCareAdminConfig",  # django.contrib.admin with MindCare's site
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Must sit above CommonMiddleware so CORS headers are added to every response,
    # including CommonMiddleware's own redirects.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded files (credential documents, photos, audio). Local disk by default;
# the SUPABASE_S3_* variables switch to a private Supabase Storage bucket. The
# database stores only keys; files are served through short-lived signed URLs
# from integrations/storage_client (docs/decisions.md, 2026-10-11).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
SIGNED_URL_EXPIRY_SECONDS = 300
# Psychologist registration: are the license and degree files required? Off by
# default so the live therapist signup (JSON, no files) keeps working; turn on
# with REQUIRE_CREDENTIAL_DOCS=true once the Web sends the files
# (docs/decisions.md, 2026-10-11).
REQUIRE_CREDENTIAL_DOCS = env.bool("REQUIRE_CREDENTIAL_DOCS", default=False)

# Uploads: a private Supabase Storage bucket over its S3-compatible API
# (django-storages). Keys are storage-only S3 access keys, not the service_role
# key (docs/decisions.md, 2026-10-11). Files are reachable only via signed URLs.
# Turned on by the SUPABASE_S3_* variables, in any environment (so `seed_demo` run
# locally against production writes demo files to the real bucket).
if env("SUPABASE_S3_BUCKET", default=""):
    STORAGES = {
        **STORAGES,
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": env("SUPABASE_S3_BUCKET"),
                "endpoint_url": env("SUPABASE_S3_ENDPOINT"),
                "region_name": env("SUPABASE_S3_REGION"),
                "access_key": env("SUPABASE_S3_ACCESS_KEY_ID"),
                "secret_key": env("SUPABASE_S3_SECRET_ACCESS_KEY"),
                "default_acl": None,
                "querystring_auth": True,
                "querystring_expire": SIGNED_URL_EXPIRY_SECONDS,
                "file_overwrite": False,
                "signature_version": "s3v4",
                "addressing_style": "path",
            },
        },
    }

# prod.py sets this: a deploy fails its system check if uploads would land on
# Render's temporary disk.
REQUIRE_OBJECT_STORAGE = False

# Field-level encryption for health data at rest (core/encryption.py). A Fernet
# key; never committed. Previous keys (comma-separated) still decrypt during a
# rotation. Production refuses to start without a valid key.
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default="")
FIELD_ENCRYPTION_PREVIOUS_KEYS = env.list("FIELD_ENCRYPTION_PREVIOUS_KEYS", default=[])

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.ActivityTrackingJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
        "register": "10/hour",
        "reference": "120/min",
        "public_stats": "60/min",
        "directory": "60/min",
        "relationship_requests": "10/hour",
        "ai_prediction": "20/min",
        "motivation": "60/min",
        "admin": "120/min",
        "reports": "10/day",
        "uploads": "20/hour",
        "password_change": "10/hour",
        "emergency_contacts": "30/hour",
        "check_ins": "30/hour",
        "password_reset": "5/hour",
        "password_reset_confirm": "20/hour",
    },
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0),
}

# MindCare AI inference service (FastAPI on Render). Base URL only; the client
# appends /predict. Empty means "not configured": the AI endpoint answers 503.
AI_SERVICE_URL = env("AI_SERVICE_URL", default="")

# Email (integrations/email_client; docs/decisions.md, 2026-10-19). Sent over the
# provider's HTTPS API, because Render's free plan blocks outbound SMTP. Switching
# provider is a settings change: EMAIL_PROVIDER plus its API key.
#   brevo | resend : the provider's API (needs EMAIL_PROVIDER_API_KEY)
#   console        : Django's default mailer (MAILERS; console here, in-memory in tests)
#   disabled       : send nothing (prod.py's default until a provider is set)
EMAIL_PROVIDER = env("EMAIL_PROVIDER", default="console")
EMAIL_PROVIDER_API_KEY = env("EMAIL_PROVIDER_API_KEY", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@mindcare.local")
DEFAULT_FROM_NAME = env("DEFAULT_FROM_NAME", default="MindCare")
# Shown in emails as the address to contact (e.g. after a rejection).
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="")
EMAIL_TIMEOUT_SECONDS = 10
# Emails are sent after the transaction commits, on a background thread, so a
# slow provider never delays (or reveals anything through) the response.
EMAIL_SEND_IN_BACKGROUND = True
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}

# django-cors-headers: lets MindCare Web call this API from a browser.
# Only the deployed web origin here; dev.py adds the local Vite dev server.
# Extra origins (e.g. a local Flutter web build during a demo) come only from the
# CORS_EXTRA_ALLOWED_ORIGINS env var, comma-separated; never hardcoded here.
CORS_EXTRA_ALLOWED_ORIGINS = env.list("CORS_EXTRA_ALLOWED_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = [
    "https://mind-care-web-seven.vercel.app",
    *CORS_EXTRA_ALLOWED_ORIGINS,
]
# Auth is JWT bearer tokens in the Authorization header, not cookies, so
# cross-origin requests never need credentials.
CORS_ALLOW_CREDENTIALS = False

# djangorestframework-simplejwt
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "MindCare API",
    "DESCRIPTION": "Unified backend serving MindCare Web and MindCare App.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Several request bodies have a `reason` field with different choice sets;
    # name each enum explicitly so the schema has no naming collisions.
    "ENUM_NAME_OVERRIDES": {
        "DeclineReasonEnum": "apps.relationships.models.DeclineReason",
        "NotAcceptingReasonEnum": "apps.psychologists.models.NotAcceptingReason",
        "PsychologistEndReasonEnum": [
            "other",
            "referred_elsewhere",
            "treatment_completed",
        ],
        "ReportReasonEnum": "apps.moderation.models.ReportReason",
        "ReportStatusEnum": "apps.moderation.models.ReportStatus",
        "RejectReasonEnum": "apps.accounts.services.RejectReason.CHOICES",
        "DeactivateReasonEnum": "apps.accounts.services.DeactivateReason.CHOICES",
        "RelationshipStatusEnum": "apps.relationships.models.RelationshipStatus",
        "YesNoUnsureEnum": "apps.patients.models.YesNoUnsure",
        "YesNoEnum": "apps.patients.models.YesNo",
        "SOSStatusEnum": "apps.emergency.models.SOSStatus",
        "SOSOutcomeEnum": "apps.emergency.models.SOSOutcome",
        "LocationSourceEnum": "apps.emergency.models.LocationSource",
        "ContactRelationshipEnum": "apps.emergency.models.ContactRelationship",
        "MoodEnum": "apps.journals.models.Mood",
        "EmotionTagEnum": "apps.journals.models.EmotionTag",
    },
}

# Cache (also backs DRF throttling — must be shared across worker processes)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

# Celery
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Third-party service credentials (used by integrations/)
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
ZOOM_API_KEY = env("ZOOM_API_KEY", default="")
ZOOM_API_SECRET = env("ZOOM_API_SECRET", default="")
FCM_SERVER_KEY = env("FCM_SERVER_KEY", default="")
FCM_CREDENTIALS_FILE = env("FCM_CREDENTIALS_FILE", default="")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "mindcare.audit": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Template name and failure kind only: never addresses or bodies.
        "mindcare.email": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
