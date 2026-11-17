"""Read-path query logic for clinical_notes (Phase 2 module 5).

Psychologist-facing reads go through services.py, which checks the current
relationship and writes the audit row in the same transaction; these helpers
only build the querysets. Patient-facing reads never touch notes.
"""

from django.utils import timezone

from apps.appointments.models import BLOCKING_STATUSES, Session, SessionStatus
from apps.clinical_notes.models import ProgressSummary, TherapyNote


def notes_for_pair(*, patient, psychologist):
    return (
        TherapyNote.objects.filter(patient=patient, psychologist=psychologist)
        .select_related("session")
        .prefetch_related("addenda")
    )


def progress_series(*, patient, psychologist):
    """Ratings over time, oldest first, for charting: only notes with a
    progress rating or a risk level."""
    rows = notes_for_pair(patient=patient, psychologist=psychologist).order_by(
        "created_at", "id"
    )
    return [
        {
            "note_id": note.pk,
            "date": note.created_at,
            "session_id": note.session_id,
            "session_starts_at": note.session.starts_at if note.session else None,
            "progress_rating": note.progress_rating,
            "risk_level": note.risk_level or None,
        }
        for note in rows
        if note.progress_rating is not None or note.risk_level
    ]


def summary_for_pair(*, patient, psychologist):
    return ProgressSummary.objects.filter(
        patient=patient, psychologist=psychologist
    ).first()


def patient_progress(*, patient_profile, now=None):
    """What the patient sees (Q38): session counts, the latest summary written
    for them, and their mood insights. Never a note."""
    from apps.journals.selectors import insights

    now = now or timezone.now()
    sessions = Session.objects.filter(patient=patient_profile)
    summary = (
        ProgressSummary.objects.filter(patient=patient_profile)
        .select_related("psychologist__user")
        .order_by("-updated_at")
        .first()
    )
    return {
        "sessions": {
            "completed": sessions.filter(status=SessionStatus.COMPLETED).count(),
            "upcoming": sessions.filter(
                status__in=BLOCKING_STATUSES, starts_at__gt=now
            ).count(),
        },
        "summary": None
        if summary is None
        else {
            "text": summary.text,
            "psychologist": {
                "id": summary.psychologist_id,
                "full_name": summary.psychologist.user.full_name,
            },
            "updated_at": summary.updated_at,
        },
        "mood": insights(patient_profile=patient_profile, now=now),
    }
