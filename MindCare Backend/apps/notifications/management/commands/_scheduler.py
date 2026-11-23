"""Shared runner for the scheduler commands (docs/decisions.md, 2026-11-23).

Both commands are run by GitHub Actions cron jobs, whose logs are PUBLIC: they
print one JSON line of counts and nothing else (no names, emails or ids).

- `--dry-run` does the whole run inside a transaction and rolls it back, so the
  counts are real but nothing is written and, because notifications and emails
  are queued with on_commit, nothing is sent.
- A Postgres advisory lock keeps two runs of one command from overlapping (the
  workflow's concurrency group is the first guard).
- System checks are skipped: the scheduler runs with a narrow set of
  variables (config/settings/scheduler.py), without the encryption key or the
  storage keys the production checks require.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.notifications.services import advisory_lock


class SchedulerCommand(BaseCommand):
    requires_system_checks = []
    lock_name = ""
    jobs = ()

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Count what would happen, then roll back. Nothing is sent.",
        )
        parser.add_argument(
            "--only",
            default="all",
            help=f"Comma-separated subset of: {', '.join(self.jobs)} (default all).",
        )

    def run(self, *, only):
        raise NotImplementedError

    def handle(self, *args, **options):
        only = self._parse_only(options["only"])
        # A command's process exits right after handle(): a background email
        # thread would be killed, so email is delivered synchronously here.
        settings.EMAIL_SEND_IN_BACKGROUND = False
        dry_run = options["dry_run"]
        with advisory_lock(self.lock_name) as acquired:
            if not acquired:
                self._print({"skipped": "another run is in progress"})
                return
            if dry_run:
                with transaction.atomic():
                    counts = self.run(only=only)
                    transaction.set_rollback(True)
            else:
                counts = self.run(only=only)
        self._print({"dry_run": dry_run, **counts})

    def _parse_only(self, value):
        if value in ("", "all"):
            return None
        names = [part.strip() for part in value.split(",") if part.strip()]
        unknown = sorted(set(names) - set(self.jobs))
        if unknown:
            raise CommandError(
                f"Unknown job(s): {', '.join(unknown)}. Choose from: "
                f"{', '.join(self.jobs)}."
            )
        return names

    def _print(self, payload):
        self.stdout.write(json.dumps({"command": self.lock_name, **payload}))
