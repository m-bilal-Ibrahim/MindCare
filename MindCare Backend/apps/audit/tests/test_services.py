"""The access audit trail: rows written in the caller's transaction, append-only,
fail closed (docs/decisions.md, 2026-10-11)."""

import shutil
import tempfile
from unittest import mock

from django.contrib.admin.sites import site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import RequestFactory, TestCase, override_settings

from apps.accounts.models import Role
from apps.audit.admin import AccessLogAdmin
from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.audit.services import record_access
from apps.patients.selectors import get_patient_display_identity
from core.files import PDF
from core.testing import make_admin, make_patient, make_user
from integrations.storage_client import client as storage


class RecordAccessTests(TestCase):
    def test_writes_ids_and_codes_only(self):
        admin = make_admin()
        with transaction.atomic():
            row = record_access(
                actor=admin,
                action=AuditAction.VIEW,
                resource_type=AuditResource.MENTAL_HEALTH_HISTORY,
                resource_id=12,
                patient_user_id=34,
                ip="203.0.113.7",
            )
        row.refresh_from_db()
        self.assertEqual(
            (row.actor_id, row.actor_role, row.resource_id, row.patient_user_id),
            (admin.pk, Role.ADMIN, "12", 34),
        )

    def test_must_run_inside_the_callers_transaction(self):
        # TestCase wraps each test in a transaction, so simulate "no atomic block".
        with mock.patch("apps.audit.services.transaction.get_connection") as conn:
            conn.return_value.in_atomic_block = False
            with self.assertRaises(RuntimeError):
                record_access(
                    actor=None,
                    action=AuditAction.VIEW,
                    resource_type=AuditResource.MENTAL_HEALTH_HISTORY,
                )

    def test_unknown_codes_refused(self):
        with self.assertRaises(ValueError):
            record_access(actor=None, action="peek", resource_type="patient_identity")
        with self.assertRaises(ValueError):
            record_access(actor=None, action="view", resource_type="diary")

    def test_append_only(self):
        with transaction.atomic():
            row = record_access(
                actor=None,
                action=AuditAction.VIEW,
                resource_type=AuditResource.CREDENTIAL_DOCUMENT,
            )
        row.resource_id = "changed"
        with self.assertRaises(PermissionError):
            row.save()
        with self.assertRaises(PermissionError):
            row.delete()
        with self.assertRaises(PermissionError):
            AccessLog.objects.all().delete()
        with self.assertRaises(PermissionError):
            AccessLog.objects.update(resource_id="x")

    def test_admin_is_read_only_even_for_superusers(self):
        request = RequestFactory().get("/")
        request.user = make_user(role=Role.ADMIN, is_superuser=True, is_staff=True)
        model_admin = AccessLogAdmin(AccessLog, site)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))


class IdentityRevealAuditTests(TestCase):
    def test_admin_reveal_of_a_private_patient_writes_a_row(self):
        patient = make_patient()
        admin = make_admin()
        identity = get_patient_display_identity(patient_profile=patient, viewer=admin)
        self.assertTrue(identity["is_real_name"])
        row = AccessLog.objects.get()
        self.assertEqual(
            (row.action, row.resource_type, row.patient_user_id, row.actor_id),
            (
                AuditAction.IDENTITY_REVEAL,
                AuditResource.PATIENT_IDENTITY,
                patient.user_id,
                admin.pk,
            ),
        )

    def test_fail_closed_no_row_no_name(self):
        patient = make_patient()
        with mock.patch(
            "apps.audit.services.AccessLog.objects.create",
            side_effect=RuntimeError("database down"),
        ):
            with self.assertRaises(RuntimeError):
                get_patient_display_identity(
                    patient_profile=patient, viewer=make_admin()
                )

    def test_public_profile_or_own_view_writes_nothing(self):
        patient = make_patient()
        get_patient_display_identity(patient_profile=patient, viewer=patient.user)
        self.assertFalse(AccessLog.objects.exists())


class StorageClientTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)

    def test_save_signed_url_delete(self):
        f = SimpleUploadedFile("../../etc/passwd.pdf", b"%PDF-1.7\n%%EOF\n")
        key, checked = storage.save_private_file(
            f, folder="credentials/7", label="License", allowed=(PDF,), max_mb=5
        )
        self.assertTrue(key.startswith("credentials/7/"))
        self.assertTrue(key.endswith(".pdf"))
        self.assertNotIn("passwd", key)
        self.assertTrue(storage.exists(key))
        self.assertIn(key, storage.signed_url(key))
        storage.delete_file(key)
        self.assertFalse(storage.exists(key))
        storage.delete_file("")  # no error
