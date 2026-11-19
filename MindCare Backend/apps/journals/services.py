"""Write-path business logic for journals (mood check-ins, Phase 2 module 3).

docs/decisions.md, 2026-10-28:
- One check-in per patient per local day, editable only on that day.
- The patient can delete any check-in (hard delete).
- Every write and every psychologist read is audited (fail closed); the
  patient's own reads aren't (the same rule as the mental health history).
- Nothing reacts to a low mood automatically: no thresholds are invented. The
  App shows the helplines link on the check-in screen.
"""

from django.db import IntegrityError, transaction

from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.journals.models import MAX_ENTRIES_PER_DAY, JournalEntry, MoodCheckIn
from apps.journals.selectors import (
    insights,
    mood_history_for_psychologist,
    patient_today,
)
from core.exceptions import DomainValidationError

ALREADY_TODAY = "You've already checked in today. Edit today's check-in instead."
NOT_TODAY = "A check-in can only be edited on the day it was made."
EDITABLE_FIELDS = ("mood", "tags", "note")


class NotFound(Exception):
    pass


class NotYourPatient(Exception):
    pass


def _audit(actor, action, check_in_id, patient_user_id, ip):
    record_access(
        actor=actor,
        action=action,
        resource_type=AuditResource.MOOD_CHECK_IN,
        resource_id=check_in_id,
        patient_user_id=patient_user_id,
        ip=ip,
    )


def create_check_in(*, patient_profile, mood, tags=(), note="", ip=None, now=None):
    today = patient_today(patient_profile, now=now)
    try:
        with transaction.atomic():
            check_in = MoodCheckIn.objects.create(
                patient=patient_profile,
                local_date=today,
                mood=mood,
                tags=sorted(set(tags or ())),
                note=note or "",
            )
            _audit(
                patient_profile.user,
                AuditAction.CREATE,
                check_in.pk,
                patient_profile.user_id,
                ip,
            )
    except IntegrityError as exc:  # the one-per-day constraint
        raise DomainValidationError({"non_field_errors": [ALREADY_TODAY]}) from exc
    return check_in


def _own(patient_profile, check_in_id):
    check_in = (
        MoodCheckIn.objects.select_for_update()
        .filter(pk=check_in_id, patient=patient_profile)
        .first()
    )
    if check_in is None:
        raise NotFound()
    return check_in


def update_check_in(*, patient_profile, check_in_id, ip=None, now=None, **changes):
    with transaction.atomic():
        check_in = _own(patient_profile, check_in_id)
        if check_in.local_date != patient_today(patient_profile, now=now):
            raise DomainValidationError({"non_field_errors": [NOT_TODAY]})
        fields = [f for f in EDITABLE_FIELDS if f in changes]
        for field in fields:
            value = changes[field]
            if field == "tags":
                value = sorted(set(value or ()))
            elif field == "note":
                value = value or ""
            setattr(check_in, field, value)
        if fields:
            check_in.save(update_fields=[*fields, "updated_at"])
            _audit(
                patient_profile.user,
                AuditAction.UPDATE,
                check_in.pk,
                patient_profile.user_id,
                ip,
            )
    return check_in


def delete_check_in(*, patient_profile, check_in_id, ip=None):
    with transaction.atomic():
        check_in = _own(patient_profile, check_in_id)
        _audit(
            patient_profile.user,
            AuditAction.DELETE,
            check_in.pk,
            patient_profile.user_id,
            ip,
        )
        check_in.delete()


# --- journal entries (docs/decisions.md, 2026-11-19) --------------------------
# Strictly private to the patient: no psychologist or admin path exists. Writes
# and deletes are audited (ids only, fail closed); the patient's own reads aren't.

TOO_MANY_ENTRIES = f"You can write at most {MAX_ENTRIES_PER_DAY} journal entries a day."
BAD_CHECK_IN = "Choose your mood check-in from the same day as this entry."
ENTRY_FIELDS = ("title", "body", "tags", "check_in")


def _entry_audit(patient_profile, action, entry_id, ip):
    record_access(
        actor=patient_profile.user,
        action=action,
        resource_type=AuditResource.JOURNAL_ENTRY,
        resource_id=entry_id,
        patient_user_id=patient_profile.user_id,
        ip=ip,
    )


def _check_in_for(patient_profile, check_in_id, local_date):
    if check_in_id is None:
        return None
    check_in = MoodCheckIn.objects.filter(
        pk=check_in_id, patient=patient_profile, local_date=local_date
    ).first()
    if check_in is None:
        raise DomainValidationError({"check_in": [BAD_CHECK_IN]})
    return check_in


def _tags_value(tags):
    return ",".join(sorted(set(tags or ())))


def create_entry(
    *, patient_profile, body, title="", tags=(), check_in=None, ip=None, now=None
):
    today = patient_today(patient_profile, now=now)
    with transaction.atomic():
        # Lock the profile row so two parallel writes can't both pass the cap.
        type(patient_profile).objects.select_for_update().filter(
            pk=patient_profile.pk
        ).first()
        if (
            JournalEntry.objects.filter(
                patient=patient_profile, local_date=today
            ).count()
            >= MAX_ENTRIES_PER_DAY
        ):
            raise DomainValidationError({"non_field_errors": [TOO_MANY_ENTRIES]})
        entry = JournalEntry.objects.create(
            patient=patient_profile,
            local_date=today,
            title=title or "",
            body=body,
            tags=_tags_value(tags),
            check_in=_check_in_for(patient_profile, check_in, today),
        )
        _entry_audit(patient_profile, AuditAction.CREATE, entry.pk, ip)
    return entry


def _own_entry(patient_profile, entry_id):
    entry = (
        JournalEntry.objects.select_for_update()
        .filter(pk=entry_id, patient=patient_profile)
        .first()
    )
    if entry is None:
        raise NotFound()
    return entry


def update_entry(*, patient_profile, entry_id, ip=None, **changes):
    """Editable at any time; no version history (it's the patient's own)."""
    with transaction.atomic():
        entry = _own_entry(patient_profile, entry_id)
        fields = [f for f in ENTRY_FIELDS if f in changes]
        for field in fields:
            value = changes[field]
            if field == "tags":
                value = _tags_value(value)
            elif field == "title":
                value = value or ""
            elif field == "check_in":
                value = _check_in_for(patient_profile, value, entry.local_date)
            setattr(entry, field, value)
        if fields:
            entry.save(update_fields=[*fields, "updated_at"])
            _entry_audit(patient_profile, AuditAction.UPDATE, entry.pk, ip)
    return entry


def delete_entry(*, patient_profile, entry_id, ip=None):
    """Hard delete: the journal is the patient's own."""
    with transaction.atomic():
        entry = _own_entry(patient_profile, entry_id)
        _entry_audit(patient_profile, AuditAction.DELETE, entry.pk, ip)
        entry.delete()


def read_moods_for_psychologist(*, psychologist_user, relationship_id, days, ip=None):
    """Mood + tags (never notes) and insights for the CURRENT assigned
    psychologist only. Audited in the same transaction (fail closed)."""
    from apps.relationships.selectors import psychologist_patient

    relationship = psychologist_patient(
        psychologist_user=psychologist_user, relationship_id=relationship_id
    )
    if relationship is None:
        raise NotYourPatient()
    profile = relationship.patient
    with transaction.atomic():
        rows = list(mood_history_for_psychologist(patient_profile=profile, days=days))
        summary = insights(patient_profile=profile)
        _audit(psychologist_user, AuditAction.VIEW, "", profile.user_id, ip)
    return rows, summary
