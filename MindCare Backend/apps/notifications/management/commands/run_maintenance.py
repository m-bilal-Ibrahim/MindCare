"""Daily clean-up and Supabase heartbeat (docs/decisions.md, 2026-11-23).

Run at 03:17 Asia/Karachi by .github/workflows/backend-scheduler-maintenance.yml:
    python manage.py run_maintenance [--dry-run] [--only notifications,sos_locations,reset_codes,sent_reminders]

Deletes notifications older than 90 days, clears SOS coordinates older than 90
days, deletes reset codes older than a day and sent-reminder records older than
30 days. Fails if the database can't be reached.
"""

from apps.notifications.management.commands._scheduler import SchedulerCommand
from apps.notifications.services import MAINTENANCE_JOBS, run_maintenance


class Command(SchedulerCommand):
    help = "Daily clean-up of old notifications, SOS coordinates and codes."
    lock_name = "maintenance"
    jobs = MAINTENANCE_JOBS

    def run(self, *, only):
        return run_maintenance(only=only)
