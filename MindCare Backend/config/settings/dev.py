"""Local development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# A fixed, public, development-only key so local runs work without a .env entry.
# Never used anywhere else: prod has no default and its system check rejects a
# missing key.
if not FIELD_ENCRYPTION_KEY:  # noqa: F405
    FIELD_ENCRYPTION_KEY = "ZGV2LW9ubHktbm90LWEtc2VjcmV0LWtleS0wMDAwMDA="

# Local dev servers, on top of base.py's origins: Vite for MindCare Web, and
# `flutter run -d chrome --web-port 5000` for MindCare App.
CORS_ALLOWED_ORIGINS = [
    *CORS_ALLOWED_ORIGINS,  # noqa: F405
    "http://localhost:5173",
    "http://localhost:5000",
]
