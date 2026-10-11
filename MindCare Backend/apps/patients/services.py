"""Write-path business logic for patients.

Views call into these functions instead of touching the ORM or enforcing
business rules themselves. Anything that mutates state belongs here.
"""

from django.db import IntegrityError, transaction

from apps.accounts.models import Role
from apps.patients.models import PatientProfile, generate_pseudonym
from apps.reference.services import resolve_location_fields
from core.choices import Gender
from core.exceptions import DomainValidationError
from integrations.storage_client import client as storage
from core.validators import (
    E164_VALIDATOR,
    run_validator,
    validate_adult_date_of_birth,
    validate_iana_timezone,
)

MAX_PSEUDONYM_ATTEMPTS = 5
DOB_CANNOT_CLEAR = "Your date of birth can't be removed once set."

UPDATABLE_FIELDS = {
    "is_profile_public",
    "country",
    "city",
    "timezone",
    "date_of_birth",
    "gender",
    "phone_number",
    "preferred_language",
}


class PseudonymGenerationError(Exception):
    """Could not generate a unique pseudonym after MAX_PSEUDONYM_ATTEMPTS."""


def create_patient_profile(*, user, timezone):
    if user.role != Role.PATIENT:
        raise ValueError("Patient profiles can only be created for patient users.")
    run_validator(validate_iana_timezone, timezone, field="timezone")

    for _ in range(MAX_PSEUDONYM_ATTEMPTS):
        try:
            with transaction.atomic():
                return PatientProfile.objects.create(
                    user=user, pseudonym=generate_pseudonym(), timezone=timezone
                )
        except IntegrityError:
            if PatientProfile.objects.filter(user=user).exists():
                raise
            # Otherwise it was a pseudonym collision: try a fresh one.
    raise PseudonymGenerationError("Could not generate a unique pseudonym.")


def update_patient_profile(*, profile, **fields):
    unknown = sorted(set(fields) - UPDATABLE_FIELDS)
    if unknown:
        raise DomainValidationError(
            {name: ["This field can't be updated."] for name in unknown}
        )

    if fields.get("timezone") is not None:
        run_validator(validate_iana_timezone, fields["timezone"], field="timezone")
    if fields.get("phone_number"):
        run_validator(E164_VALIDATOR, fields["phone_number"], field="phone_number")
    elif "phone_number" in fields:
        fields["phone_number"] = None
    if (
        "date_of_birth" in fields
        and not fields["date_of_birth"]
        and profile.date_of_birth is not None
    ):
        # Phase 3: required to request a psychologist, so never removable once set.
        raise DomainValidationError({"date_of_birth": [DOB_CANNOT_CLEAR]})
    if fields.get("date_of_birth") is not None:
        run_validator(
            validate_adult_date_of_birth, fields["date_of_birth"], field="date_of_birth"
        )
    if fields.get("gender") is not None and fields["gender"] not in Gender.values:
        raise DomainValidationError({"gender": ["Choose a valid option."]})

    resolve_location_fields(
        current_country=profile.country,
        current_city=profile.city,
        fields=fields,
        city_required=False,
    )

    for name, value in fields.items():
        setattr(profile, name, value)
    profile.save()
    return profile


# --- Profile photo (6.1) ------------------------------------------------------


def set_patient_photo(*, profile, checked):
    """Replace the profile photo with an upload already checked by
    core.files.check_photo. The old file is deleted after commit."""
    with transaction.atomic():
        key = storage.replace_file(
            old_key=profile.photo_key,
            checked=checked,
            folder=f"photos/patients/{profile.pk}",
        )
        try:
            profile.photo_key = key
            profile.save(update_fields=["photo_key", "updated_at"])
        except Exception:
            storage.delete_file(key)
            raise
    return profile


def remove_patient_photo(*, profile):
    old_key = profile.photo_key
    with transaction.atomic():
        profile.photo_key = ""
        profile.save(update_fields=["photo_key", "updated_at"])
        if old_key:
            transaction.on_commit(lambda: storage.delete_file(old_key))
    return profile


# --- Mental health history (6.1) ---------------------------------------------
# Health data: encrypted at rest, every write and every psychologist read is in
# the access audit trail, in the same transaction (fail closed). The patient's
# own reads are not audited: reading your own record is not a privacy event.


def save_mental_health_history(
    *,
    profile,
    actor,
    concerns=(),
    previous_diagnosis="",
    current_medication="",
    previous_therapy="",
    notes="",
    ip=None,
):
    """Replace the whole history (PUT semantics: anything not sent is cleared).
    `concerns` are active Specialization rows."""
    from apps.audit.models import AuditAction, AuditResource
    from apps.audit.services import record_access
    from apps.patients.models import MentalHealthHistory
    from apps.reference.services import ensure_active_choices

    concerns = list(concerns)
    if concerns:  # an empty list is fine: the history is optional
        ensure_active_choices(items=concerns, field="concerns")
    values = {
        "concerns": ",".join(sorted(s.slug for s in concerns)),
        "previous_diagnosis": previous_diagnosis or "",
        "current_medication": current_medication or "",
        "previous_therapy": previous_therapy or "",
        "notes": notes or "",
    }
    with transaction.atomic():
        history = (
            MentalHealthHistory.objects.select_for_update()
            .filter(profile=profile)
            .first()
        )
        action = AuditAction.UPDATE if history else AuditAction.CREATE
        if history is None:
            history = MentalHealthHistory(profile=profile)
        for name, value in values.items():
            setattr(history, name, value)
        history.save()
        record_access(
            actor=actor,
            action=action,
            resource_type=AuditResource.MENTAL_HEALTH_HISTORY,
            resource_id=history.pk,
            patient_user_id=profile.user_id,
            ip=ip,
        )
    return history


def delete_mental_health_history(*, profile, actor, ip=None):
    from apps.audit.models import AuditAction, AuditResource
    from apps.audit.services import record_access
    from apps.patients.models import MentalHealthHistory

    with transaction.atomic():
        history = (
            MentalHealthHistory.objects.select_for_update()
            .filter(profile=profile)
            .first()
        )
        if history is None:
            return False
        history_id = history.pk
        history.delete()
        record_access(
            actor=actor,
            action=AuditAction.DELETE,
            resource_type=AuditResource.MENTAL_HEALTH_HISTORY,
            resource_id=history_id,
            patient_user_id=profile.user_id,
            ip=ip,
        )
    return True


class NotYourPatient(Exception):
    """No accepted relationship between this psychologist and that row."""


def read_history_for_psychologist(*, psychologist_user, relationship_id, ip=None):
    """The patient's history for their CURRENT assigned psychologist only
    (accepted relationship; psychologist approved and active). Audited in the
    same transaction (fail closed). Returns (relationship, history or None)."""
    from apps.audit.models import AuditAction, AuditResource
    from apps.audit.services import record_access
    from apps.patients.models import MentalHealthHistory
    from apps.relationships.selectors import psychologist_patient

    relationship = psychologist_patient(
        psychologist_user=psychologist_user, relationship_id=relationship_id
    )
    if relationship is None:
        raise NotYourPatient()
    with transaction.atomic():
        history = MentalHealthHistory.objects.filter(
            profile_id=relationship.patient_id
        ).first()
        record_access(
            actor=psychologist_user,
            action=AuditAction.VIEW,
            resource_type=AuditResource.MENTAL_HEALTH_HISTORY,
            resource_id=history.pk if history else "",
            patient_user_id=relationship.patient.user_id,
            ip=ip,
        )
    return relationship, history
