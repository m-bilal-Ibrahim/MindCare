"""Local development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Local dev servers, on top of base.py's origins: Vite for MindCare Web, and
# `flutter run -d chrome --web-port 5000` for MindCare App.
CORS_ALLOWED_ORIGINS = [
    *CORS_ALLOWED_ORIGINS,  # noqa: F405
    "http://localhost:5173",
    "http://localhost:5000",
]
