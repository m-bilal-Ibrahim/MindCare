"""Write-path business logic for emergency (6.12 SOS, Phase 2 module 2).

docs/decisions.md, 2026-10-28:
- SOS is the manual button only. It is never blocked: no throttle on pressing
  it, and the API answers with the emergency message even if something fails.
- Contacts and the current psychologist are emailed at most once per 30
  minutes per patient; later presses are still recorded.
- The patient can cancel within 5 minutes; notified contacts get a "safe" email.
- Device coordinates are rounded to 3 decimals, encrypted, and cleared after
  90 days (`purge_sos_locations`, and opportunistically on every new SOS).
- Contact writes and every psychologist/admin read of an alert are audited
  (fail closed). Nothing here logs names, contacts or coordinates.
"""

import json
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.emergency.models import (
    EmergencyContact,
    LocationSource,
    SOSEvent,
    SOSOutcome,
    SOSStatus,
)
from apps.notifications import emails
from apps.notifications.services import send_email_after_commit
from apps.patients.models import PatientProfile
from apps.relationships.selectors import get_active_relationship
from core.exceptions import DomainValidationError

logger = logging.getLogger("mindcare.emergency")

MAX_CONTACTS = 3
NOTIFY_COOLDOWN = timedelta(minutes=30)
CANCEL_WINDOW = timedelta(minutes=5)
LOCATION_RETENTION = timedelta(days=90)
COORDINATE_DECIMALS = 3

TOO_MANY_CONTACTS = "You can add up to 3 emergency contacts."
CANNOT_CANCEL = "This alert can no longer be cancelled."
ALREADY_CLOSED = "This alert is already closed."


class NotFound(Exception):
    pass


def _local_time(dt, tz_name):
    try:
        tz = ZoneInfo(tz_name or "Asia/Karachi")
    except (ValueError, KeyError):
        tz = ZoneInfo("Asia/Karachi")
    local = dt.astimezone(tz)
    return f"{local:%H:%M} on {local:%d %b %Y} ({tz.key})"


def _round(value):
    return round(float(value), COORDINATE_DECIMALS)


def purge_old_locations(*, now=None):
    """Clear coordinates older than 90 days. Returns how many were cleared."""
    cutoff = (now or timezone.now()) - LOCATION_RETENTION
    # QuerySet.update is fine here: it only blanks a field, nothing user-entered.
    return SOSEvent.objects.filter(
        created_at__lt=cutoff, coordinates__isnull=False
    ).update(coordinates=None)


def _location(profile, latitude, longitude):
    if latitude is not None and longitude is not None:
        return f"{_round(latitude)},{_round(longitude)}", LocationSource.DEVICE
    if profile.city_id:
        return None, LocationSource.PROFILE_CITY
    if profile.country_id:
        return None, LocationSource.PROFILE_COUNTRY
    return None, LocationSource.NONE


def _notify(event, profile, now):
    """Queue the alert emails (after commit). Returns (contacts, psychologist)."""
    patient_name = profile.user.full_name
    when = _local_time(now, profile.timezone)
    contacts = list(EmergencyContact.objects.filter(patient=profile))
    for contact in contacts:
        send_email_after_commit(
            template="sos_contact_alert",
            to=contact.email,
            message=emails.sos_contact_alert(
                contact_name=contact.name, patient_name=patient_name, when=when
            ),
        )
    relationship = get_active_relationship(patient=profile)
    psychologist_notified = False
    if relationship is not None:
        psychologist = relationship.psychologist
        send_email_after_commit(
            template="sos_psychologist_alert",
            to=psychologist.user.email,
            message=emails.sos_psychologist_alert(
                psychologist_name=psychologist.user.full_name,
                pseudonym=profile.pseudonym,
                when=_local_time(now, psychologist.timezone),
            ),
        )
        psychologist_notified = True
    return len(contacts), psychologist_notified


def trigger_sos(*, patient_user, latitude=None, longitude=None):
    """Record an SOS and notify contacts and the current psychologist (unless
    this patient already notified them in the last 30 minutes)."""
    profile = PatientProfile.objects.select_related("user").get(user=patient_user)
    now = timezone.now()
    purge_old_locations(now=now)
    coordinates, source = _location(profile, latitude, longitude)
    with transaction.atomic():
        # Lock the profile so two quick presses can't both send notifications.
        PatientProfile.objects.select_for_update().filter(pk=profile.pk).first()
        recently_notified = SOSEvent.objects.filter(
            patient=profile, notified_at__gte=now - NOTIFY_COOLDOWN
        ).exists()
        event = SOSEvent.objects.create(
            patient=profile,
            coordinates=coordinates,
            location_source=source,
            country_id=profile.country_id,
            city_id=profile.city_id,
        )
        if not recently_notified:
            contacts, psychologist = _notify(event, profile, now)
            event.contacts_notified = contacts
            event.psychologist_notified = psychologist
            event.notified_at = now
            event.save(
                update_fields=[
                    "contacts_notified",
                    "psychologist_notified",
                    "notified_at",
                ]
            )
    return event


def press_sos(*, patient_user, latitude=None, longitude=None):
    """The SOS button. Never raises: if recording or notifying fails, the
    patient still gets the emergency message and whatever resources load.
    Returns (event or None, resources)."""
    from apps.emergency.selectors import EMERGENCY_MESSAGE, emergency_resources

    event = None
    try:
        event = trigger_sos(
            patient_user=patient_user, latitude=latitude, longitude=longitude
        )
    except Exception as exc:  # never block the patient
        logger.error(json.dumps({"event": "sos_failed", "reason": type(exc).__name__}))
    try:
        resources = emergency_resources(patient_profile=patient_user.patient_profile)
    except Exception as exc:
        logger.error(
            json.dumps({"event": "sos_resources_failed", "reason": type(exc).__name__})
        )
        resources = {
            "message": EMERGENCY_MESSAGE,
            "helplines": [],
            "hospitals": [],
            "ngos": [],
            "psychologist": None,
        }
    return event, resources


def cancel_sos(*, patient_user, event_id):
    with transaction.atomic():
        event = (
            SOSEvent.objects.select_for_update()
            .select_related("patient__user")
            .filter(pk=event_id, patient__user=patient_user)
            .first()
        )
        if event is None:
            raise NotFound()
        now = timezone.now()
        if event.status != SOSStatus.OPEN or now > event.created_at + CANCEL_WINDOW:
            raise DomainValidationError({"non_field_errors": [CANNOT_CANCEL]})
        event.status = SOSStatus.CANCELLED
        event.cancelled_at = now
        event.save(update_fields=["status", "cancelled_at"])
        if event.contacts_notified:
            for contact in EmergencyContact.objects.filter(patient=event.patient):
                send_email_after_commit(
                    template="sos_contact_safe",
                    to=contact.email,
                    message=emails.sos_contact_safe(
                        contact_name=contact.name,
                        patient_name=event.patient.user.full_name,
                    ),
                )
    return event


# --- Emergency contacts ------------------------------------------------------


def _audit_contact(patient_user, action, contact_id, ip):
    record_access(
        actor=patient_user,
        action=action,
        resource_type=AuditResource.EMERGENCY_CONTACT,
        resource_id=contact_id,
        patient_user_id=patient_user.pk,
        ip=ip,
    )


def add_contact(*, patient_user, name, relationship, email, phone="", ip=None):
    with transaction.atomic():
        profile = PatientProfile.objects.select_for_update().get(user=patient_user)
        if EmergencyContact.objects.filter(patient=profile).count() >= MAX_CONTACTS:
            raise DomainValidationError({"non_field_errors": [TOO_MANY_CONTACTS]})
        contact = EmergencyContact.objects.create(
            patient=profile,
            name=name,
            relationship=relationship,
            email=email,
            phone=phone or "",
            consent_confirmed_at=timezone.now(),
        )
        _audit_contact(patient_user, AuditAction.CREATE, contact.pk, ip)
    return contact


def _own_contact(patient_user, contact_id):
    contact = (
        EmergencyContact.objects.select_for_update()
        .filter(pk=contact_id, patient__user=patient_user)
        .first()
    )
    if contact is None:
        raise NotFound()
    return contact


EDITABLE_CONTACT_FIELDS = ("name", "relationship", "email", "phone")


def update_contact(*, patient_user, contact_id, ip=None, **changes):
    with transaction.atomic():
        contact = _own_contact(patient_user, contact_id)
        fields = [f for f in EDITABLE_CONTACT_FIELDS if f in changes]
        for field in fields:
            setattr(contact, field, changes[field] or "")
        if fields:
            contact.save(update_fields=[*fields, "updated_at"])
            _audit_contact(patient_user, AuditAction.UPDATE, contact.pk, ip)
    return contact


def delete_contact(*, patient_user, contact_id, ip=None):
    with transaction.atomic():
        contact = _own_contact(patient_user, contact_id)
        _audit_contact(patient_user, AuditAction.DELETE, contact.pk, ip)
        contact.delete()


# --- Psychologist and admin reads/actions -----------------------------------


def _audit_event_view(viewer, event, ip):
    record_access(
        actor=viewer,
        action=AuditAction.VIEW,
        resource_type=AuditResource.SOS_EVENT,
        resource_id=event.pk,
        patient_user_id=event.patient.user_id,
        ip=ip,
    )


def read_events_for_psychologist(*, psychologist_user, ip=None):
    from apps.emergency.selectors import events_for_psychologist

    with transaction.atomic():
        events, relationship_by_patient = events_for_psychologist(
            psychologist_user=psychologist_user
        )
        events = list(events)
        for event in events:
            _audit_event_view(psychologist_user, event, ip)
    return events, relationship_by_patient


def read_event_for_admin(*, admin, event_id, ip=None):
    """The full alert, with decrypted coordinates. Audited (fail closed)."""
    with transaction.atomic():
        event = (
            SOSEvent.objects.select_related(
                "patient__user", "city", "country", "followed_up_by", "closed_by"
            )
            .filter(pk=event_id)
            .first()
        )
        if event is None:
            raise NotFound()
        _audit_event_view(admin, event, ip)
    return event


def _lock_event(event_id):
    event = SOSEvent.objects.select_for_update().filter(pk=event_id).first()
    if event is None:
        raise NotFound()
    if event.status == SOSStatus.CLOSED:
        raise DomainValidationError({"status": [ALREADY_CLOSED]})
    return event


def follow_up_event(*, admin, event_id):
    with transaction.atomic():
        event = _lock_event(event_id)
        event.status = SOSStatus.FOLLOWED_UP
        event.followed_up_by = admin
        event.followed_up_at = timezone.now()
        event.save(update_fields=["status", "followed_up_by", "followed_up_at"])
    return event


def close_event(*, admin, event_id, outcome):
    if outcome not in SOSOutcome.values:
        raise DomainValidationError({"outcome": ["Choose a valid option."]})
    with transaction.atomic():
        event = _lock_event(event_id)
        event.status = SOSStatus.CLOSED
        event.outcome = outcome
        event.closed_by = admin
        event.closed_at = timezone.now()
        event.save(update_fields=["status", "outcome", "closed_by", "closed_at"])
    return event
