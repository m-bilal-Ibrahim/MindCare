"""Delete in-app notifications older than 90 days (docs/decisions.md, 2026-11-18).

Every new notification also does this, so the command is a backstop for quiet
periods:
    python manage.py purge_notifications
"""

from django.core.management.base import BaseCommand

from apps.notifications.services import purge_old_notifications


class Command(BaseCommand):
    help = "Delete in-app notifications older than 90 days."

    def handle(self, *args, **options):
        deleted = purge_old_notifications()
        self.stdout.write(f"Deleted {deleted} notification(s).")
