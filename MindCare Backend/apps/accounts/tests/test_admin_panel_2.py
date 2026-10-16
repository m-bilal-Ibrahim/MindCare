"""admin-panel-2: admin psychologist directory (counts only), overview additions
(recent suspensions / rejections), oldest-first queues."""

from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts import selectors, services
from apps.accounts.models import ApprovalStatus, User
from apps.moderation.models import Report, ReportReason
from apps.moderation.services import submit_report
from apps.relationships.services import accept_request, request_psychologist
from core.testing import make_admin, make_patient, make_psychologist

PSYCHOLOGISTS = "/api/v1/accounts/admin/psychologists/"
OVERVIEW = "/api/v1/accounts/admin/overview/"
REPORTS = "/api/v1/moderation/admin/reports/"


def connect(patient, psychologist):
    relationship = request_psychologist(
        patient_user=patient.user, psychologist_id=psychologist.pk
    )
    return accept_request(
        psychologist_user=psychologist.user, relationship_id=relationship.pk
    )


class AdminPsychologistDirectoryTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_authenticate(make_admin())

    def test_counts_only(self):
        busy = make_psychologist(full_name="Amina Busy")
        connect(make_patient(), busy)
        connect(make_patient(), busy)
        request_psychologist(patient_user=make_patient().user, psychologist_id=busy.pk)
        make_psychologist(full_name="Bilal Idle")

        r = self.client.get(PSYCHOLOGISTS)
        self.assertEqual(r.status_code, 200)
        rows = {row["full_name"]: row for row in r.json()["results"]}
        self.assertEqual(rows["Amina Busy"]["current_patient_count"], 2)
        self.assertEqual(rows["Amina Busy"]["pending_request_count"], 1)
        self.assertEqual(rows["Bilal Idle"]["current_patient_count"], 0)
        row = rows["Amina Busy"]
        self.assertEqual(row["id"], busy.user_id)
        self.assertEqual(row["last_active"], "never")
        # Nothing about who the patients are.
        self.assertFalse({"patients", "relationships"} & set(row))

    def test_expired_requests_not_counted(self):
        psychologist = make_psychologist()
        relationship = request_psychologist(
            patient_user=make_patient().user, psychologist_id=psychologist.pk
        )
        relationship.expires_at = timezone.now() - timedelta(minutes=1)
        relationship.save(update_fields=["expires_at"])
        row = self.client.get(PSYCHOLOGISTS).json()["results"][0]
        self.assertEqual(row["pending_request_count"], 0)

    def test_filters(self):
        make_psychologist(full_name="Open Doctor")
        closed = make_psychologist(full_name="Closed Doctor")
        closed.is_accepting_patients = False
        closed.not_accepting_reason = "fully_booked"
        closed.save(update_fields=["is_accepting_patients", "not_accepting_reason"])
        make_psychologist(
            full_name="Pending Doctor", approval_status=ApprovalStatus.PENDING
        )

        def names(params):
            r = self.client.get(PSYCHOLOGISTS, params)
            self.assertEqual(r.status_code, 200, r.json())
            return {row["full_name"] for row in r.json()["results"]}

        self.assertEqual(names({"accepting": "false"}), {"Closed Doctor"})
        self.assertEqual(names({"status": "pending"}), {"Pending Doctor"})
        self.assertEqual(names({"search": "open"}), {"Open Doctor"})
        for params in ({"status": "nope"}, {"accepting": "maybe"}):
            with self.subTest(params=params):
                self.assertEqual(
                    self.client.get(PSYCHOLOGISTS, params).status_code, 400
                )

    def test_non_admin_refused(self):
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(self.client.get(PSYCHOLOGISTS).status_code, 403)


class RecentAccountActionTests(TestCase):
    def test_deactivations_and_rejections_newest_first_patients_by_pseudonym(self):
        admin = make_admin()
        patient = make_patient()
        rejected = make_psychologist(approval_status=ApprovalStatus.PENDING)
        services.deactivate_account(admin=admin, user_id=patient.user_id)
        services.review_pending_account(
            admin=admin, user_id=rejected.user_id, decision=ApprovalStatus.REJECTED
        )
        old = make_patient()
        services.deactivate_account(admin=admin, user_id=old.user_id)
        User.objects.filter(pk=old.user_id).update(
            deactivated_at=timezone.now() - timedelta(days=31)
        )

        actions = selectors.recent_account_actions()
        self.assertEqual(
            [(user.pk, action) for user, action, _ in actions],
            [(rejected.user_id, "rejected"), (patient.user_id, "deactivated")],
        )

    def test_reactivation_clears_it(self):
        admin = make_admin()
        patient = make_patient()
        services.deactivate_account(admin=admin, user_id=patient.user_id)
        services.reactivate_account(admin=admin, user_id=patient.user_id)
        self.assertEqual(selectors.recent_account_actions(), [])


class OverviewAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = make_admin()
        self.client.force_authenticate(self.admin)

    def test_recent_actions_and_ngo_counts(self):
        patient = make_patient()
        services.deactivate_account(admin=self.admin, user_id=patient.user_id)
        body = self.client.get(OVERVIEW).json()
        self.assertIn("ngo", body["users"])
        self.assertIn("ngo", body["pending_approvals"])
        [action] = body["recent_account_actions"]
        self.assertEqual(action["id"], patient.user_id)
        self.assertEqual(action["action"], "deactivated")
        self.assertEqual(action["display_name"], patient.pseudonym)
        self.assertFalse(action["is_real_name"])
        self.assertNotIn(patient.user.full_name, str(body))


class OpenReportsOldestFirstTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_authenticate(make_admin())

    def test_open_reports_oldest_first_others_newest_first(self):
        psychologist = make_psychologist()
        first, second = make_patient(), make_patient()
        for patient in (first, second):
            connect(patient, psychologist)
            submit_report(
                reporter=patient.user,
                reason=ReportReason.UNPROFESSIONAL,
                psychologist_id=psychologist.pk,
            )
        older, newer = Report.objects.order_by("created_at", "id")
        open_ids = [
            r["id"]
            for r in self.client.get(REPORTS, {"status": "open"}).json()["results"]
        ]
        self.assertEqual(open_ids, [older.pk, newer.pk])
        all_ids = [r["id"] for r in self.client.get(REPORTS).json()["results"]]
        self.assertEqual(all_ids, [newer.pk, older.pk])
