"""API-layer tests for moderation (6.3 reports and complaints)."""

from datetime import date

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User
from apps.audit.models import AccessLog, AuditAction
from apps.relationships.services import accept_request, request_psychologist
from core.testing import make_admin, make_patient, make_psychologist, make_user

REPORTS = "/api/v1/moderation/reports/"
ADMIN_REPORTS = "/api/v1/moderation/admin/reports/"


class ReportAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psych = make_psychologist()
        self.patient = make_patient(date_of_birth=date(1994, 5, 5))
        self.rel = request_psychologist(
            patient_user=self.patient.user, psychologist_id=self.psych.pk
        )
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)

    def tearDown(self):
        cache.clear()


class SubmitReportAPITests(ReportAPITestCase):
    def test_patient_submits_and_sees_their_report(self):
        self.client.force_authenticate(self.patient.user)
        r = self.client.post(
            REPORTS,
            {
                "psychologist": self.psych.pk,
                "reason": "unprofessional_conduct",
                "description": "  Missed three sessions without telling me.  ",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.json())
        self.assertEqual(
            set(r.json()), {"id", "reason", "status", "created_at", "resolved_at"}
        )
        mine = self.client.get(REPORTS).json()
        self.assertEqual([row["status"] for row in mine], ["open"])

    def test_psychologist_reports_by_relationship(self):
        self.client.force_authenticate(self.psych.user)
        r = self.client.post(
            REPORTS,
            {"relationship": self.rel.pk, "reason": "threats_or_violence"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.json())

    def test_validation(self):
        self.client.force_authenticate(self.patient.user)
        cases = {
            "reason": ({"psychologist": self.psych.pk, "reason": "rude"}, None),
            "description": (
                {
                    "psychologist": self.psych.pk,
                    "reason": "other",
                    "description": "short",
                },
                ["Description must be between 10 and 1000 characters."],
            ),
            "patient_name": (
                {"psychologist": self.psych.pk, "reason": "other", "patient_name": "x"},
                ["This field can't be set."],
            ),
            "psychologist": (
                {"reason": "other"},
                ["This field is required."],
            ),
        }
        for key, (body, message) in cases.items():
            with self.subTest(key=key):
                r = self.client.post(REPORTS, body, format="json")
                self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(key, r.json())
                if message:
                    self.assertEqual(r.json()[key], message)

    def test_only_patients_and_approved_psychologists(self):
        for user in (
            make_user(role=Role.NGO),
            make_admin(),
            make_psychologist(approval_status=ApprovalStatus.PENDING).user,
        ):
            self.client.force_authenticate(user)
            self.assertEqual(
                self.client.post(
                    REPORTS, {"reason": "other"}, format="json"
                ).status_code,
                403,
            )

    def test_throttled_at_ten_a_day(self):
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["reports"], "10/day"
        )
        self.client.force_authenticate(self.patient.user)
        codes = [
            self.client.post(
                REPORTS, {"psychologist": 999999, "reason": "other"}, format="json"
            ).status_code
            for _ in range(11)
        ]
        self.assertEqual(codes[:10], [400] * 10)
        self.assertEqual(codes[10], status.HTTP_429_TOO_MANY_REQUESTS)


class AdminReviewAPITests(ReportAPITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.patient.user)
        self.report_id = self.client.post(
            REPORTS,
            {
                "psychologist": self.psych.pk,
                "reason": "harassment",
                "description": "Sent abusive messages late at night.",
            },
            format="json",
        ).json()["id"]
        self.admin = make_admin()
        self.client.force_authenticate(self.admin)

    def test_list_shows_pseudonyms_and_no_description(self):
        body = self.client.get(ADMIN_REPORTS, {"status": "open"}).json()
        self.assertEqual(body["count"], 1)
        row = body["results"][0]
        self.assertEqual(row["reporter"]["display_name"], self.patient.pseudonym)
        self.assertEqual(
            row["reported_user"]["display_name"], self.psych.user.full_name
        )
        self.assertTrue(row["has_description"])
        self.assertNotIn("description", row)
        reads = AccessLog.objects.filter(action=AuditAction.VIEW).count()
        self.assertEqual(reads, 0)

    def test_detail_reveals_and_audits(self):
        r = self.client.get(f"{ADMIN_REPORTS}{self.report_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual(body["description"], "Sent abusive messages late at night.")
        self.assertEqual(body["reporter"]["display_name"], self.patient.user.full_name)
        actions = set(AccessLog.objects.values_list("action", flat=True))
        self.assertIn(AuditAction.VIEW, actions)  # the description
        self.assertIn(AuditAction.IDENTITY_REVEAL, actions)  # the private patient

    def test_dismiss_and_uphold(self):
        r = self.client.post(f"{ADMIN_REPORTS}{self.report_id}/dismiss/")
        self.assertEqual(r.json()["status"], "dismissed")
        r = self.client.post(f"{ADMIN_REPORTS}{self.report_id}/uphold/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(), {"status": ["This report has already been resolved."]}
        )

    def test_uphold_deactivates_the_reported_account(self):
        r = self.client.post(f"{ADMIN_REPORTS}{self.report_id}/uphold/")
        self.assertEqual(r.json()["status"], "actioned")
        self.assertFalse(User.objects.get(pk=self.psych.user_id).is_active)

    def test_admins_only(self):
        self.client.force_authenticate(self.patient.user)
        self.assertEqual(self.client.get(ADMIN_REPORTS).status_code, 403)
        self.assertEqual(
            self.client.post(f"{ADMIN_REPORTS}{self.report_id}/dismiss/").status_code,
            403,
        )
