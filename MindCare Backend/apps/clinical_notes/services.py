"""Write-path (and audited read-path) logic for therapy notes (Phase 2 module 5).

docs/decisions.md, 2026-11-18 (Q35-Q39):
- Only the CURRENT assigned psychologist (accepted relationship, approved and
  active) reads or writes a patient's notes, progress ratings and summary.
  Notes span every relationship of that pair. Patients and admins never see
  notes; no endpoint and no Django admin page shows them.
- Editable for 24 hours after creation, then locked; addenda after that. Every
  save stores a full encrypted version.
- Every read and write is audited in its own transaction (fail closed), so if
  the audit row can't be written nothing is returned or saved.
"""

import json

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.appointments.models import Session, SessionStatus
from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.clinical_notes import selectors
from apps.clinical_notes.models import (
    SECTIONS,
    NoteAddendum,
    NoteVersion,
    ProgressSummary,
    TherapyNote,
)
from core.exceptions import DomainValidationError

EMPTY = "Write at least one section or add a progress rating or risk level."
LOCKED = "This note is locked (24 hours after it was written). Add an addendum instead."
BAD_SESSION = "Choose one of this patient's confirmed or past sessions."
SESSION_TAKEN = "This session already has a note. Open it instead."
NOTE_FIELDS = (*SECTIONS, "progress_rating", "risk_level")
NOTE_SESSION_STATUSES = (
    SessionStatus.CONFIRMED,
    SessionStatus.COMPLETED,
    SessionStatus.NO_SHOW,
)


class NotYourPatient(Exception):
    pass


class NotFound(Exception):
    pass


def _current(psychologist_user, relationship_id):
    from apps.relationships.selectors import psychologist_patient

    rel = psychologist_patient(
        psychologist_user=psychologist_user, relationship_id=relationship_id
    )
    if rel is None:
        raise NotYourPatient()
    return rel


def _audit(actor, action, resource, resource_id, rel, ip):
    record_access(
        actor=actor,
        action=action,
        resource_type=resource,
        resource_id=resource_id,
        patient_user_id=rel.patient.user_id,
        ip=ip,
    )


def _note(rel, note_id, *, lock=False):
    qs = TherapyNote.objects.filter(
        pk=note_id, patient=rel.patient, psychologist=rel.psychologist
    )
    if lock:
        qs = qs.select_for_update()
    note = qs.first()
    if note is None:
        raise NotFound()
    return note


def _snapshot(note):
    NoteVersion.objects.create(
        note=note,
        version=note.version,
        content=json.dumps(
            {
                **{f: getattr(note, f) for f in SECTIONS},
                "progress_rating": note.progress_rating,
                "risk_level": note.risk_level or None,
                "session_id": note.session_id,
            }
        ),
    )


def _check_not_empty(note):
    if (
        not any(getattr(note, f) for f in SECTIONS)
        and note.progress_rating is None
        and not note.risk_level
    ):
        raise DomainValidationError({"non_field_errors": [EMPTY]})


def _session_for(rel, session_id):
    if session_id is None:
        return None
    session = Session.objects.filter(
        pk=session_id,
        patient=rel.patient,
        psychologist=rel.psychologist,
        status__in=NOTE_SESSION_STATUSES,
    ).first()
    if session is None:
        raise DomainValidationError({"session": [BAD_SESSION]})
    return session


# --- notes ----------------------------------------------------------------


def list_notes(*, psychologist_user, relationship_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        rows = list(
            selectors.notes_for_pair(patient=rel.patient, psychologist=rel.psychologist)
        )
        _audit(
            psychologist_user, AuditAction.VIEW, AuditResource.THERAPY_NOTE, "", rel, ip
        )
    return rows


def get_note(*, psychologist_user, relationship_id, note_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        note = _note(rel, note_id)
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.THERAPY_NOTE,
            note.pk,
            rel,
            ip,
        )
    return note


def note_versions(*, psychologist_user, relationship_id, note_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        note = _note(rel, note_id)
        versions = [
            {"version": v.version, "saved_at": v.saved_at, **json.loads(v.content)}
            for v in note.versions.all()
        ]
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.THERAPY_NOTE,
            note.pk,
            rel,
            ip,
        )
    return versions


def create_note(*, psychologist_user, relationship_id, session=None, ip=None, **fields):
    rel = _current(psychologist_user, relationship_id)
    note = TherapyNote(
        patient=rel.patient,
        psychologist=rel.psychologist,
        relationship=rel,
        session=_session_for(rel, session),
        **{f: fields[f] for f in NOTE_FIELDS if f in fields and fields[f] is not None},
    )
    _check_not_empty(note)
    try:
        with transaction.atomic():
            note.save()
            _snapshot(note)
            _audit(
                psychologist_user,
                AuditAction.CREATE,
                AuditResource.THERAPY_NOTE,
                note.pk,
                rel,
                ip,
            )
    except IntegrityError as exc:  # one note per session
        raise DomainValidationError({"session": [SESSION_TAKEN]}) from exc
    return note


def update_note(*, psychologist_user, relationship_id, note_id, ip=None, **changes):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        note = _note(rel, note_id, lock=True)
        if note.is_locked:
            raise DomainValidationError({"non_field_errors": [LOCKED]})
        fields = [f for f in NOTE_FIELDS if f in changes]
        for field in fields:
            value = changes[field]
            if field in SECTIONS or field == "risk_level":
                value = value or ""
            setattr(note, field, value)
        if not fields:
            return note
        _check_not_empty(note)
        note.version += 1
        note.save(update_fields=[*fields, "version", "updated_at"])
        _snapshot(note)
        _audit(
            psychologist_user,
            AuditAction.UPDATE,
            AuditResource.THERAPY_NOTE,
            note.pk,
            rel,
            ip,
        )
    return note


def add_addendum(*, psychologist_user, relationship_id, note_id, text, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        note = _note(rel, note_id, lock=True)
        addendum = NoteAddendum.objects.create(note=note, text=text)
        _audit(
            psychologist_user,
            AuditAction.CREATE,
            AuditResource.THERAPY_NOTE,
            note.pk,
            rel,
            ip,
        )
    return addendum


def progress(*, psychologist_user, relationship_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        series = selectors.progress_series(
            patient=rel.patient, psychologist=rel.psychologist
        )
        _audit(
            psychologist_user, AuditAction.VIEW, AuditResource.THERAPY_NOTE, "", rel, ip
        )
    return series


# --- the summary written for the patient ------------------------------------


def get_summary(*, psychologist_user, relationship_id, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        summary = selectors.summary_for_pair(
            patient=rel.patient, psychologist=rel.psychologist
        )
        _audit(
            psychologist_user,
            AuditAction.VIEW,
            AuditResource.PROGRESS_SUMMARY,
            summary.pk if summary else "",
            rel,
            ip,
        )
    return summary


def set_summary(*, psychologist_user, relationship_id, text, ip=None):
    rel = _current(psychologist_user, relationship_id)
    with transaction.atomic():
        summary = (
            ProgressSummary.objects.select_for_update()
            .filter(patient=rel.patient, psychologist=rel.psychologist)
            .first()
        )
        created = summary is None
        if created:
            summary = ProgressSummary(
                patient=rel.patient, psychologist=rel.psychologist
            )
        summary.text = text
        summary.updated_at = timezone.now()
        summary.save()
        _audit(
            psychologist_user,
            AuditAction.CREATE if created else AuditAction.UPDATE,
            AuditResource.PROGRESS_SUMMARY,
            summary.pk,
            rel,
            ip,
        )
    return summary
