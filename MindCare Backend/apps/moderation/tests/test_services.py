"""6.3 reports and complaints: standing, encryption, audit, admin decisions."""

from datetime import date
from unittest import mock

from django.db import connection
from django.test import TestCase

from apps.accounts.models import Role
from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.moderation import services
from apps.moderation.models import Report, ReportReason, ReportStatus
from apps.relationships.models import RelationshipStatus
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.exceptions import DomainValidationError
from core.testing import make_admin, make_patient, make_psychologist, make_user


def care_pair(accepted=True):
    psych = make_psychologist()
    patient = make_patient(date_of_birth=date(1994, 5, 5))
    rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
    if accepted:
        accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
        rel.refresh_from_db()
    return patient, psych, rel


class SubmitReportTests(TestCase):
    def test_patient_reports_their_psychologist(self):
        patient, psych, rel = care_pair()
        report = services.submit_report(
            reporter=patient.user,
            reason=ReportReason.UNPROFESSIONAL,
            description="Turned up late and shared my details with others.",
            psychologist_id=psych.pk,
        )
        self.assertEqual(report.reported_user, psych.user)
        self.assertEqual(report.relationship, rel)
        self.assertEqual(report.status, ReportStatus.OPEN)

    def test_description_is_encrypted_at_rest_and_audited(self):
        patient, psych, _ = care_pair()
        report = services.submit_report(
            reporter=patient.user,
            reason=ReportReason.PRIVACY,
            description="Told my employer about my anxiety diagnosis.",
            psychologist_id=psych.pk,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT description FROM moderation_report WHERE id = %s", [report.pk]
            )
            stored = cursor.fetchone()[0]
        self.assertNotIn("anxiety", stored)
        report.refresh_from_db()
        self.assertEqual(
            report.description, "Told my employer about my anxiety diagnosis."
        )
        row = AccessLog.objects.get()
        self.assertEqual(
            (row.action, row.resource_type, row.patient_user_id),
            (AuditAction.CREATE, AuditResource.REPORT_DESCRIPTION, patient.user_id),
        )

    def test_former_psychologist_can_be_reported(self):
        patient, psych, rel = care_pair()
        patient_end_relationship(patient_user=patient.user, confirm=True)
        report = services.submit_report(
            reporter=patient.user,
            reason=ReportReason.HARASSMENT,
            psychologist_id=psych.pk,
        )
        self.assertEqual(report.relationship_id, rel.pk)

    def test_no_standing_without_accepted_care(self):
        patient, psych, _ = care_pair(accepted=False)  # only a pending request
        with self.assertRaises(DomainValidationError) as ctx:
            services.submit_report(
                reporter=patient.user,
                reason=ReportReason.OTHER,
                psychologist_id=psych.pk,
            )
        self.assertEqual(
            ctx.exception.errors,
            {"psychologist": [services.PATIENT_STANDING_MESSAGE]},
        )
        stranger = make_psychologist()
        with self.assertRaises(DomainValidationError):
            services.submit_report(
                reporter=patient.user,
                reason=ReportReason.OTHER,
                psychologist_id=stranger.pk,
            )

    def test_psychologist_reports_a_patient_by_relationship(self):
        patient, psych, rel = care_pair()
        report = services.submit_report(
            reporter=psych.user, reason=ReportReason.THREATS, relationship_id=rel.pk
        )
        self.assertEqual(report.reported_user, patient.user)
        other_psych = make_psychologist()
        with self.assertRaises(DomainValidationError) as ctx:
            services.submit_report(
                reporter=other_psych.user,
                reason=ReportReason.THREATS,
                relationship_id=rel.pk,
            )
        self.assertEqual(
            ctx.exception.errors,
            {"relationship": [services.PSYCHOLOGIST_STANDING_MESSAGE]},
        )

    def test_one_open_report_per_relationship(self):
        patient, psych, _ = care_pair()
        services.submit_report(
            reporter=patient.user, reason=ReportReason.OTHER, psychologist_id=psych.pk
        )
        with self.assertRaises(DomainValidationError) as ctx:
            services.submit_report(
                reporter=patient.user,
                reason=ReportReason.OTHER,
                psychologist_id=psych.pk,
            )
        self.assertEqual(
            ctx.exception.errors, {"non_field_errors": [services.DUPLICATE_MESSAGE]}
        )

    def test_description_rules_apply_on_the_model_too(self):
        patient, psych, _ = care_pair()
        with self.assertRaises(DomainValidationError) as ctx:
            services.submit_report(
                reporter=patient.user,
                reason=ReportReason.OTHER,
                description="<script>alert(1)</script> and some more words",
                psychologist_id=psych.pk,
            )
        self.assertEqual(
            ctx.exception.errors,
            {"description": ["Description can't contain HTML tags."]},
        )
        self.assertFalse(Report.objects.exists())


class AdminDecisionTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.patient, self.psych, self.rel = care_pair()
        self.report = services.submit_report(
            reporter=self.patient.user,
            reason=ReportReason.HARASSMENT,
            description="Sent me abusive messages at night, repeatedly.",
            psychologist_id=self.psych.pk,
        )

    def test_reading_the_description_is_audited_and_fails_closed(self):
        audit_before = AccessLog.objects.count()
        report = services.read_report_for_admin(
            admin=self.admin, report_id=self.report.pk
        )
        self.assertIn("abusive", report.description)
        self.assertEqual(AccessLog.objects.count(), audit_before + 1)
        with mock.patch(
            "apps.audit.services.AccessLog.objects.create",
            side_effect=RuntimeError("database down"),
        ):
            with self.assertRaises(RuntimeError):
                services.read_report_for_admin(
                    admin=self.admin, report_id=self.report.pk
                )

    def test_dismiss(self):
        report = services.dismiss_report(admin=self.admin, report_id=self.report.pk)
        self.assertEqual(report.status, ReportStatus.DISMISSED)
        self.assertEqual(report.resolved_by, self.admin)
        with self.assertRaises(DomainValidationError):
            services.dismiss_report(admin=self.admin, report_id=self.report.pk)

    def test_uphold_deactivates_ends_care_and_closes_all_open_reports(self):
        other_patient = make_patient(date_of_birth=date(1990, 1, 1))
        rel2 = request_psychologist(
            patient_user=other_patient.user, psychologist_id=self.psych.pk
        )
        accept_request(psychologist_user=self.psych.user, relationship_id=rel2.pk)
        second = services.submit_report(
            reporter=other_patient.user,
            reason=ReportReason.HARASSMENT,
            psychologist_id=self.psych.pk,
        )
        report = services.uphold_report(admin=self.admin, report_id=self.report.pk)
        self.assertEqual(report.status, ReportStatus.ACTIONED)
        second.refresh_from_db()
        self.assertEqual(second.status, ReportStatus.ACTIONED)
        self.psych.user.refresh_from_db()
        self.assertFalse(self.psych.user.is_active)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.status, RelationshipStatus.ENDED)

    def test_missing_report(self):
        with self.assertRaises(services.ReportNotFound):
            services.dismiss_report(admin=self.admin, report_id=999999)


class StandingByRoleTests(TestCase):
    def test_ngo_cannot_report(self):
        with self.assertRaises(PermissionError):
            services.submit_report(
                reporter=make_user(role=Role.NGO), reason=ReportReason.OTHER
            )
