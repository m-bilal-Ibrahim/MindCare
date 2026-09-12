"""Celery application. Broker/result backend point at Redis via
CELERY_BROKER_URL/CELERY_RESULT_BACKEND in settings."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
