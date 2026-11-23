"""Send the scheduled reminders (docs/decisions.md, 2026-11-23).

Run every 15 minutes by .github/workflows/backend-scheduler-reminders.yml:
    python manage.py send_reminders [--dry-run] [--only sessions,care_requests,care_plan,check_in]
"""

from apps.notifications.management.commands._scheduler import SchedulerCommand
from apps.notifications.services import REMINDER_JOBS, send_reminders


class Command(SchedulerCommand):
    help = "Send session, care-request, care-plan and check-in reminders."
    lock_name = "reminders"
    jobs = REMINDER_JOBS

    def run(self, *, only):
        return send_reminders(only=only)
