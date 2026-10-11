"""Read-path query logic for moderation."""

from apps.moderation.models import Report

_PARTIES = (
    "reporter__patient_profile",
    "reporter__psychologist_profile",
    "reported_user__patient_profile",
    "reported_user__psychologist_profile",
)


def reports_by(*, reporter):
    """A reporter's own reports (only status comes back to them)."""
    return Report.objects.filter(reporter=reporter)


def reports_for_admin(*, status=None):
    qs = Report.objects.select_related(*_PARTIES)
    if status:
        qs = qs.filter(status=status)
    return qs
