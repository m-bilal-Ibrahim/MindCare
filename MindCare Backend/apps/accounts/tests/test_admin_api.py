"""6.3 admin console API: approvals exactly per
MindCare Web/docs/admin-approvals-api-contract.md, audited credential document
links, platform monitoring, deactivation."""

import json
import shutil
import tempfile
from datetime import date
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User
from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.relationships.models import CareRelationship, RelationshipStatus
from apps.relationships.services import accept_request, request_psychologist
from core.testing import (
    make_admin,
    make_patient,
    make_psychologist,
    make_user,
    ngo_profile_data,
    post_register,
    register_payload,
)

PENDING = "/api/v1/accounts/admin/pending/"


def approve_url(user_id):
    return f"/api/v1/accounts/admin/{user_id}/approve/"


def reject_url(user_id):
    return f"/api/v1/accounts/admin/{user_id}/reject/"


class AdminTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.admin = make_admin()
        self.client.force_authenticate(self.admin)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)
        cache.clear()

    def register_applicant(self, license_number=None, **overrides):
        self.client.force_authenticate(None)
        payload = register_payload(role=Role.PSYCHOLOGIST, **overrides)
        if license_number:
            payload["profile"]["license_number"] = license_number
        r = post_register(self.client, payload)
        assert r.status_code == 201, r.json()
        self.client.force_authenticate(self.admin)
        return User.objects.get(email=payload["email"])


class PendingListTests(AdminTestCase):
    def test_lists_pending_psychologists_oldest_first_with_profile_and_documents(self):
        first = self.register_applicant(license_number="PMDC-1")
        second = self.register_applicant(license_number="PMDC-2")
        make_psychologist()  # approved: not listed
        r = self.client.get(PENDING, {"role": "psychologist"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual([row["id"] for row in body], [first.pk, second.pk])
        row = body[0]
        self.assertEqual(
            set(row),
            {
                "id",
                "email",
                "full_name",
                "role",
                "approval_status",
                "created_at",
                "psychologist_profile",
                "ngo_profile",
            },
        )
        self.assertEqual(row["approval_status"], "pending")
        self.assertIsNone(row["ngo_profile"])
        profile = row["psychologist_profile"]
        self.assertEqual(profile["license_number"], "PMDC-1")
        self.assertEqual(profile["license_issuing_country"]["code"], "PK")
        self.assertEqual(
            sorted(d["kind"] for d in profile["documents"]), ["degree", "license"]
        )

    def test_ngo_rows_carry_the_ngo_profile(self):
        from apps.ngo.services import create_ngo_profile

        user = make_user(role=Role.NGO, approval_status=ApprovalStatus.PENDING)
        create_ngo_profile(user=user, **ngo_profile_data())
        body = self.client.get(PENDING, {"role": "ngo"}).json()
        self.assertEqual(len(body), 1)
        self.assertIsNone(body[0]["psychologist_profile"])
        self.assertEqual(
            body[0]["ngo_profile"]["organization_name"], "Helping Hands Foundation"
        )

    def test_role_is_required_and_checked(self):
        self.assertEqual(self.client.get(PENDING).status_code, 400)
        r = self.client.get(PENDING, {"role": "patient"})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", r.json())

    def test_admins_only(self):
        for user in (make_patient().user, make_psychologist().user):
            self.client.force_authenticate(user)
            self.assertEqual(
                self.client.get(PENDING, {"role": "psychologist"}).status_code, 403
            )
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.get(PENDING, {"role": "psychologist"}).status_code, 401
        )


class ApproveRejectTests(AdminTestCase):
    def test_approve(self):
        applicant = self.register_applicant()
        with self.assertLogs("mindcare.audit", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                r = self.client.post(approve_url(applicant.pk))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["approval_status"], "approved")
        self.assertEqual(r.json()["id"], applicant.pk)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, ApprovalStatus.APPROVED)
        line = json.loads(logs.records[-1].getMessage())
        self.assertEqual(
            (line["event"], line["actor_id"], line["target_user_id"]),
            ("account_approved", self.admin.pk, applicant.pk),
        )
        # The approved psychologist can now sign in.
        self.client.force_authenticate(None)
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"email": applicant.email, "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_not_pending_is_400(self):
        approved = make_psychologist().user
        r = self.client.post(approve_url(approved.pk))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"approval_status": ["This account isn't pending."]})

    def test_deactivated_pending_account_is_400(self):
        applicant = self.register_applicant()
        User.objects.filter(pk=applicant.pk).update(is_active=False)
        r = self.client.post(approve_url(applicant.pk))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "approval_status": [
                    "This account is deactivated. Reactivate it before reviewing it."
                ]
            },
        )

    def test_404_for_missing_or_non_reviewable_user(self):
        self.assertEqual(self.client.post(approve_url(999999)).status_code, 404)
        patient = make_patient().user
        self.assertEqual(self.client.post(approve_url(patient.pk)).status_code, 404)
        self.assertEqual(self.client.post(reject_url(self.admin.pk)).status_code, 404)

    def test_reject_with_reason_and_logs_it(self):
        applicant = self.register_applicant()
        with self.assertLogs("mindcare.audit", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                r = self.client.post(
                    reject_url(applicant.pk),
                    {"reason": "license_unverified"},
                    format="json",
                )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["approval_status"], "rejected")
        line = json.loads(logs.records[-1].getMessage())
        self.assertEqual(
            (line["event"], line["reason"]), ("account_rejected", "license_unverified")
        )

    def test_reject_without_reason_and_bad_bodies(self):
        applicant = self.register_applicant()
        self.assertEqual(
            self.client.post(
                reject_url(applicant.pk), {"why": "x"}, format="json"
            ).json(),
            {"why": ["This field can't be set."]},
        )
        self.assertEqual(
            self.client.post(
                reject_url(applicant.pk), {"reason": "vibes"}, format="json"
            ).status_code,
            400,
        )
        r = self.client.post(reject_url(applicant.pk), {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_reject_ends_relationships(self):
        # A psychologist moved back to pending (re-review) keeps the relationship
        # paused; rejecting them ends it.
        psych = make_psychologist()
        patient = make_patient(date_of_birth=date(1995, 1, 1))
        rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
        accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
        User.objects.filter(pk=psych.user_id).update(
            approval_status=ApprovalStatus.PENDING
        )
        self.client.post(reject_url(psych.user_id))
        rel.refresh_from_db()
        self.assertEqual(rel.status, RelationshipStatus.ENDED)


class CredentialDocumentLinkTests(AdminTestCase):
    def test_admin_gets_a_signed_link_and_the_access_is_audited(self):
        applicant = self.register_applicant()
        doc = applicant.psychologist_profile.documents.get(kind="license")
        r = self.client.get(f"/api/v1/accounts/admin/documents/{doc.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual(body["kind"], "license")
        self.assertIn(doc.storage_key, body["url"])
        self.assertEqual(body["expires_in"], 300)
        row = AccessLog.objects.get()
        self.assertEqual(
            (row.action, row.resource_type, row.resource_id, row.actor_id),
            (
                AuditAction.DOWNLOAD,
                AuditResource.CREDENTIAL_DOCUMENT,
                str(doc.pk),
                self.admin.pk,
            ),
        )

    def test_fail_closed_no_audit_row_no_link(self):
        applicant = self.register_applicant()
        doc = applicant.psychologist_profile.documents.first()
        with mock.patch(
            "apps.audit.services.AccessLog.objects.create",
            side_effect=RuntimeError("database down"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.get(f"/api/v1/accounts/admin/documents/{doc.pk}/")

    def test_non_admin_and_missing(self):
        applicant = self.register_applicant()
        doc = applicant.psychologist_profile.documents.first()
        self.assertEqual(
            self.client.get("/api/v1/accounts/admin/documents/999999/").status_code, 404
        )
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(
            self.client.get(f"/api/v1/accounts/admin/documents/{doc.pk}/").status_code,
            403,
        )
        self.assertFalse(AccessLog.objects.exists())


class MonitoringTests(AdminTestCase):
    def test_overview_counts(self):
        make_patient()
        make_psychologist()
        self.register_applicant()
        body = self.client.get("/api/v1/accounts/admin/overview/").json()
        self.assertEqual(body["users"]["patient"]["total"], 1)
        self.assertEqual(body["users"]["psychologist"]["total"], 2)
        self.assertEqual(body["pending_approvals"], {"psychologist": 1, "ngo": 0})
        self.assertEqual(body["open_reports"], 0)
        self.assertEqual(sum(w["psychologist"] for w in body["weekly_signups"]), 2)

    def test_users_list_hides_private_patients(self):
        private = make_patient()
        public = make_patient()
        public.is_profile_public = True
        public.save(update_fields=["is_profile_public"])
        psych = make_psychologist()
        body = self.client.get("/api/v1/accounts/admin/users/").json()
        rows = {row["id"]: row for row in body["results"]}
        self.assertEqual(rows[private.user_id]["display_name"], private.pseudonym)
        self.assertIsNone(rows[private.user_id]["email"])
        self.assertEqual(rows[public.user_id]["display_name"], public.user.full_name)
        self.assertEqual(rows[psych.user_id]["email"], psych.user.email)
        self.assertNotIn(self.admin.pk, rows)
        self.assertFalse(AccessLog.objects.exists())  # a list never reveals

    def test_search_never_matches_a_patients_real_name(self):
        private = make_patient(full_name="Zarmeena Quraishi")
        r = self.client.get("/api/v1/accounts/admin/users/", {"search": "Zarmeena"})
        self.assertEqual(r.json()["count"], 0)
        r = self.client.get(
            "/api/v1/accounts/admin/users/", {"search": private.pseudonym}
        )
        self.assertEqual([row["id"] for row in r.json()["results"]], [private.user_id])

    def test_filters(self):
        make_patient()
        applicant = self.register_applicant()
        r = self.client.get(
            "/api/v1/accounts/admin/users/",
            {"role": "psychologist", "status": "pending"},
        )
        self.assertEqual([row["id"] for row in r.json()["results"]], [applicant.pk])
        self.assertEqual(
            self.client.get(
                "/api/v1/accounts/admin/users/", {"status": "x"}
            ).status_code,
            400,
        )

    def test_opening_a_private_patient_reveals_and_audits(self):
        private = make_patient()
        r = self.client.get(f"/api/v1/accounts/admin/users/{private.user_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual(body["identity"]["display_name"], private.user.full_name)
        self.assertEqual(body["email"], private.user.email)
        self.assertNotIn("date_of_birth", json.dumps(body))
        row = AccessLog.objects.get()
        self.assertEqual(row.action, AuditAction.IDENTITY_REVEAL)
        self.assertEqual(row.patient_user_id, private.user_id)

    def test_admin_accounts_are_not_listed_or_opened(self):
        self.assertEqual(
            self.client.get(
                f"/api/v1/accounts/admin/users/{self.admin.pk}/"
            ).status_code,
            404,
        )


class DeactivationTests(AdminTestCase):
    def test_deactivate_ends_care_and_blocks_login_then_reactivate(self):
        psych = make_psychologist()
        patient = make_patient(date_of_birth=date(1995, 1, 1))
        rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
        accept_request(psychologist_user=psych.user, relationship_id=rel.pk)

        r = self.client.post(
            f"/api/v1/accounts/admin/users/{patient.user_id}/deactivate/",
            {"reason": "policy_violation"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.json()["is_active"])
        rel.refresh_from_db()
        self.assertEqual(rel.status, RelationshipStatus.ENDED)
        self.client.force_authenticate(None)
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"email": patient.user.email, "password": "strongpass123"},
            format="json",
        )
        self.assertNotEqual(login.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.admin)
        r = self.client.post(
            f"/api/v1/accounts/admin/users/{patient.user_id}/reactivate/"
        )
        self.assertTrue(r.json()["is_active"])
        rel.refresh_from_db()
        self.assertEqual(rel.status, RelationshipStatus.ENDED)  # stays ended

    def test_twice_and_admin_targets(self):
        patient = make_patient()
        url = f"/api/v1/accounts/admin/users/{patient.user_id}/"
        self.client.post(url + "deactivate/")
        r = self.client.post(url + "deactivate/")
        self.assertEqual(
            r.json(), {"is_active": ["This account is already deactivated."]}
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/accounts/admin/users/{self.admin.pk}/deactivate/"
            ).status_code,
            404,
        )
        self.assertEqual(CareRelationship.objects.count(), 0)
