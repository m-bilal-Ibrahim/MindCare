"""Write-path business logic for moderation.

6.3 reports and complaints (docs/decisions.md, 2026-10-11):
- Only people who are or were in care together can report each other: a patient
  reports a psychologist they had an accepted relationship with; a psychologist
  reports a current or former patient (by relationship id). Object-level check,
  not just the role.
- The optional description is encrypted at rest, never logged, shown only to
  admins, and every write and admin read is audited (fail closed).
- Admins dismiss a report, or uphold it by deactivating the reported account
  (accounts.services.deactivate_account, which ends their relationships).
  Time-limited bans belong to community moderation (6.8).
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.models import AuditAction, AuditResource
from apps.audit.services import record_access
from apps.moderation.models import Report, ReportStatus
from apps.relationships.models import CareRelationship, RelationshipStatus
from core.audit import log_admin_event
from core.exceptions import DomainValidationError

# A relationship gives standing to report only once care actually started.
REPORTABLE_STATUSES = (RelationshipStatus.ACCEPTED, RelationshipStatus.ENDED)
DUPLICATE_MESSAGE = "You already have an open report about this person."
PATIENT_STANDING_MESSAGE = (
    "You can only report a psychologist you have been in care with."
)
PSYCHOLOGIST_STANDING_MESSAGE = (
    "You can only report your own current or former patients."
)


class ReportNotFound(Exception):
    pass


def _relationship_for(reporter, *, psychologist_id, relationship_id):
    if reporter.role == Role.PATIENT:
        if not psychologist_id:
            raise DomainValidationError({"psychologist": ["This field is required."]})
        rel = (
            CareRelationship.objects.filter(
                patient__user=reporter,
                psychologist_id=psychologist_id,
                status__in=REPORTABLE_STATUSES,
            )
            .select_related("psychologist__user", "patient")
            .order_by("-requested_at", "-id")
            .first()
        )
        if rel is None:
            raise DomainValidationError({"psychologist": [PATIENT_STANDING_MESSAGE]})
        return rel, rel.psychologist.user
    if reporter.role == Role.PSYCHOLOGIST:
        if not relationship_id:
            raise DomainValidationError({"relationship": ["This field is required."]})
        rel = (
            CareRelationship.objects.filter(
                pk=relationship_id,
                psychologist__user=reporter,
                status__in=REPORTABLE_STATUSES,
            )
            .select_related("patient__user")
            .first()
        )
        if rel is None:
            raise DomainValidationError(
                {"relationship": [PSYCHOLOGIST_STANDING_MESSAGE]}
            )
        return rel, rel.patient.user
    raise PermissionError("Only patients and psychologists can submit reports.")


def submit_report(
    *,
    reporter,
    reason,
    description="",
    psychologist_id=None,
    relationship_id=None,
    ip=None,
):
    relationship, reported_user = _relationship_for(
        reporter, psychologist_id=psychologist_id, relationship_id=relationship_id
    )
    if Report.objects.filter(
        reporter=reporter, relationship=relationship, status=ReportStatus.OPEN
    ).exists():
        raise DomainValidationError({"non_field_errors": [DUPLICATE_MESSAGE]})
    try:
        with transaction.atomic():
            report = Report.objects.create(
                reporter=reporter,
                reported_user=reported_user,
                relationship=relationship,
                reason=reason,
                description=description or "",
            )
            if report.description:
                record_access(
                    actor=reporter,
                    action=AuditAction.CREATE,
                    resource_type=AuditResource.REPORT_DESCRIPTION,
                    resource_id=report.pk,
                    patient_user_id=relationship.patient.user_id,
                    ip=ip,
                )
            transaction.on_commit(
                lambda: log_admin_event(
                    event="report_submitted",
                    actor_id=reporter.pk,
                    target_user_id=reported_user.pk,
                    reason=reason,
                    ref_id=report.pk,
                )
            )
    except IntegrityError as exc:  # a concurrent duplicate hit the constraint
        raise DomainValidationError({"non_field_errors": [DUPLICATE_MESSAGE]}) from exc
    return report


def read_report_for_admin(*, admin, report_id, ip=None):
    """The full report for an admin. Reading a description is audited in the
    same transaction (fail closed)."""
    with transaction.atomic():
        report = (
            Report.objects.select_related(
                "reporter__patient_profile",
                "reporter__psychologist_profile",
                "reported_user__patient_profile",
                "reported_user__psychologist_profile",
                "relationship__patient",
            )
            .filter(pk=report_id)
            .first()
        )
        if report is None:
            raise ReportNotFound()
        if report.description:
            record_access(
                actor=admin,
                action=AuditAction.VIEW,
                resource_type=AuditResource.REPORT_DESCRIPTION,
                resource_id=report.pk,
                patient_user_id=report.relationship.patient.user_id,
                ip=ip,
            )
    return report


def _lock_open_report(report_id):
    report = Report.objects.select_for_update().filter(pk=report_id).first()
    if report is None:
        raise ReportNotFound()
    if report.status != ReportStatus.OPEN:
        raise DomainValidationError(
            {"status": ["This report has already been resolved."]}
        )
    return report


def _resolve(report, *, admin, status, when):
    report.status = status
    report.resolved_by = admin
    report.resolved_at = when
    report.save(update_fields=["status", "resolved_by", "resolved_at"])


def dismiss_report(*, admin, report_id):
    with transaction.atomic():
        report = _lock_open_report(report_id)
        _resolve(
            report, admin=admin, status=ReportStatus.DISMISSED, when=timezone.now()
        )
        transaction.on_commit(
            lambda: log_admin_event(
                event="report_dismissed",
                actor_id=admin.pk,
                target_user_id=report.reported_user_id,
                ref_id=report.pk,
            )
        )
    return report


def uphold_report(*, admin, report_id):
    """Deactivate the reported account (ending their relationships) and close
    every open report about them."""
    from apps.accounts.services import DeactivateReason, deactivate_account

    with transaction.atomic():
        report = _lock_open_report(report_id)
        target = report.reported_user
        if target.is_active:
            deactivate_account(
                admin=admin, user_id=target.pk, reason=DeactivateReason.REPORT_UPHELD
            )
        now = timezone.now()
        for open_report in Report.objects.select_for_update().filter(
            reported_user=target, status=ReportStatus.OPEN
        ):
            _resolve(open_report, admin=admin, status=ReportStatus.ACTIONED, when=now)
        transaction.on_commit(
            lambda: log_admin_event(
                event="report_actioned",
                actor_id=admin.pk,
                target_user_id=target.pk,
                ref_id=report.pk,
            )
        )
    report.refresh_from_db()
    return report
