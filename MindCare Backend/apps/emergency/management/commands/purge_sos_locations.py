"""Clear SOS device coordinates older than 90 days (docs/decisions.md, 2026-10-28).

Every new SOS also does this, so the command is a backstop for quiet periods:
    python manage.py purge_sos_locations
"""

from django.core.management.base import BaseCommand

from apps.emergency.services import purge_old_locations


class Command(BaseCommand):
    help = "Clear SOS device coordinates older than 90 days."

    def handle(self, *args, **options):
        cleared = purge_old_locations()
        self.stdout.write(f"Cleared coordinates on {cleared} SOS alert(s).")
