"""In-app notifications: one compact file (speed mode, docs/decisions.md
2026-11-18). Every trigger group, own-only access, no sensitive text in any
template, read / read-all / unread-count, delete audit, and the 90-day purge."""

import re
from datetime import timedelta
from io import StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.db import transaction
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role
from apps.accounts.services import (
    change_password,
    register_user,
    review_pending_account,
)
from apps.appointments import selectors as booking_selectors
from apps.appointments import services as booking
from apps.appointments.models import SessionStatus
from apps.appointments.tests.test_services import open_bookings
from apps.audit.models import AccessLog, AuditResource
from apps.clinical_notes.services import set_summary
from apps.emergency import services as sos
from apps.notifications import services
from apps.notifications.models import Notification, NotificationType, TargetType
from apps.notifications.templates import TEMPLATES, render
from apps.relationships.services import (
    accept_request,
    decline_request,
    patient_end_relationship,
    psychologist_end_relationship,
    request_psychologist,
)
from core.testing import (
    make_admin,
    make_patient,
    make_psychologist,
    psychologist_profile_data,
)

BASE = "/api/v1/notifications/"
T = NotificationType


def types_for(user):
    return list(
        Notification.objects.filter(recipient=user)
        .order_by("id")
        .values_list("type", flat=True)
    )


class TemplateTests(SimpleTestCase):
    def test_every_type_has_a_safe_template(self):
        self.assertEqual(set(TEMPLATES), set(NotificationType.values))
        for type, (title, body, target_type) in TEMPLATES.items():
            placeholders = set(re.findall(r"\{(\w+)\}", title + body))
            self.assertLessEqual(placeholders, {"when"}, type)
            self.assertLessEqual(len(title), 120)
            self.assertLessEqual(len(body.format(when="x" * 40)), 300)
            self.assertIn(target_type, ["", *TargetType.values])
            lowered = (title + body).lower()
            for word in ("mood", "note:", "diagnos", "latitude", "location", "@"):
                self.assertNotIn(word, lowered, type)

    def test_when_is_required_exactly_where_used(self):
        with self.assertRaises(ValueError):
            render(T.SESSION_CONFIRMED)
        with self.assertRaises(ValueError):
            render(T.CARE_ACCEPTED, when="Mon 01 Dec")
        self.assertIn("Mon 01 Dec", render(T.SESSION_CONFIRMED, when="Mon 01 Dec")[1])


class TriggerTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psych = make_psychologist()
        self.patient = make_patient()

    def tearDown(self):
        cache.clear()

    def in_care(self, patient=None):
        patient = patient or self.patient
        with self.captureOnCommitCallbacks(execute=True):
            rel = request_psychologist(
                patient_user=patient.user, psychologist_id=self.psych.pk
            )
            accept_request(psychologist_user=self.psych.user, relationship_id=rel.pk)
        return rel


class RelationshipTriggerTests(TriggerTestCase):
    def test_request_accept_end(self):
        rel = self.in_care()
        self.assertEqual(types_for(self.psych.user), [T.CARE_REQUESTED])
        self.assertEqual(types_for(self.patient.user), [T.CARE_ACCEPTED])
        n = Notification.objects.get(recipient=self.patient.user)
        self.assertEqual((n.target_type, n.target_id), ("care_relationship", rel.pk))
        with self.captureOnCommitCallbacks(execute=True):
            psychologist_end_relationship(
                psychologist_user=self.psych.user,
                relationship_id=rel.pk,
                reason="treatment_completed",
            )
        self.assertEqual(types_for(self.patient.user), [T.CARE_ACCEPTED, T.CARE_ENDED])

    def test_decline_and_patient_ending_themselves(self):
        other = make_patient()
        with self.captureOnCommitCallbacks(execute=True):
            rel = request_psychologist(
                patient_user=other.user, psychologist_id=self.psych.pk
            )
            decline_request(psychologist_user=self.psych.user, relationship_id=rel.pk)
        self.assertEqual(types_for(other.user), [T.CARE_DECLINED])
        self.in_care()
        with self.captureOnCommitCallbacks(execute=True):
            patient_end_relationship(patient_user=self.patient.user, confirm=True)
        self.assertNotIn(T.CARE_ENDED, types_for(self.patient.user))

    def test_rolled_back_action_notifies_nobody(self):
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    request_psychologist(
                        patient_user=self.patient.user, psychologist_id=self.psych.pk
                    )
                    raise RuntimeError
            except RuntimeError:
                pass
        self.assertEqual(Notification.objects.count(), 0)


class BookingTriggerTests(TriggerTestCase):
    def setUp(self):
        super().setUp()
        open_bookings(self.psych)
        self.in_care()
        Notification.objects.all().delete()
        self.slots = booking_selectors.free_slots(self.psych)

    def test_request_confirm_cancel(self):
        with self.captureOnCommitCallbacks(execute=True):
            s = booking.book_session(
                patient_user=self.patient.user, starts_at=self.slots[0]
            )
            booking.confirm_session(psychologist_profile=self.psych, session_id=s.pk)
            booking.psychologist_cancel_session(
                psychologist_profile=self.psych, session_id=s.pk
            )
        self.assertEqual(types_for(self.psych.user), [T.SESSION_REQUESTED])
        self.assertEqual(
            types_for(self.patient.user), [T.SESSION_CONFIRMED, T.SESSION_CANCELLED]
        )
        n = Notification.objects.filter(recipient=self.psych.user).get()
        self.assertEqual((n.target_type, n.target_id), ("session", s.pk))
        self.assertIn("Asia/Karachi", n.body)  # the recipient's timezone
        self.assertNotIn(self.patient.user.full_name, n.body)

    def test_propose_accept_patient_cancel_and_decline(self):
        with self.captureOnCommitCallbacks(execute=True):
            s = booking.book_session(
                patient_user=self.patient.user, starts_at=self.slots[0]
            )
            booking.propose_time(
                psychologist_profile=self.psych,
                session_id=s.pk,
                starts_at=self.slots[3],
            )
            booking.accept_proposal(patient_user=self.patient.user, session_id=s.pk)
            booking.patient_cancel_session(
                patient_user=self.patient.user, session_id=s.pk
            )
            s2 = booking.book_session(
                patient_user=self.patient.user, starts_at=self.slots[6]
            )
            booking.psychologist_cancel_session(
                psychologist_profile=self.psych, session_id=s2.pk
            )
        self.assertEqual(
            types_for(self.psych.user),
            [
                T.SESSION_REQUESTED,
                T.SESSION_PROPOSAL_ACCEPTED,
                T.SESSION_CANCELLED,
                T.SESSION_REQUESTED,
            ],
        )
        self.assertEqual(
            types_for(self.patient.user), [T.SESSION_PROPOSED, T.SESSION_DECLINED]
        )

    def test_outcome(self):
        from apps.appointments.models import Session

        rel = self.patient.care_relationships.get(status="accepted")
        past = timezone.now() - timedelta(hours=3)
        s = Session(
            relationship=rel,
            patient=self.patient,
            psychologist=self.psych,
            status=SessionStatus.CONFIRMED,
            fee_pkr=3000,
            requested_starts_at=past,
        )
        booking._set_times(s, past, 50)
        s.save()
        with self.captureOnCommitCallbacks(execute=True):
            booking.mark_outcome(
                psychologist_profile=self.psych,
                session_id=s.pk,
                outcome=SessionStatus.NO_SHOW,
            )
        self.assertEqual(types_for(self.patient.user), [T.SESSION_NO_SHOW])


class OtherTriggerTests(TriggerTestCase):
    def test_sos_alert_and_cancel(self):
        admin = make_admin()
        self.in_care()
        with self.captureOnCommitCallbacks(execute=True):
            event, _ = sos.press_sos(patient_user=self.patient.user)
        self.assertEqual(types_for(admin), [T.SOS_ALERT])
        self.assertEqual(types_for(self.psych.user), [T.CARE_REQUESTED, T.SOS_ALERT])
        with self.captureOnCommitCallbacks(execute=True):
            sos.cancel_sos(patient_user=self.patient.user, event_id=event.pk)
        self.assertEqual(types_for(admin), [T.SOS_ALERT, T.SOS_CANCELLED])
        self.assertEqual(types_for(self.psych.user)[-1], T.SOS_CANCELLED)
        self.assertEqual(
            set(
                Notification.objects.filter(type=T.SOS_ALERT).values_list(
                    "target_id", flat=True
                )
            ),
            {event.pk},
        )

    def test_application_review_and_password(self):
        admin = make_admin()
        with self.captureOnCommitCallbacks(execute=True):
            applicant = register_user(
                email="applicant@example.com",
                password="Correct-Horse-91",
                full_name="Ayesha Khan",
                role=Role.PSYCHOLOGIST,
                is_adult_confirmed=True,
                profile_data=psychologist_profile_data(license_number="LIC-NOTIF-1"),
            )
        n = Notification.objects.get(recipient=admin)
        self.assertEqual((n.type, n.target_id), (T.APPLICATION_SUBMITTED, applicant.pk))
        with self.captureOnCommitCallbacks(execute=True):
            review_pending_account(
                admin=admin, user_id=applicant.pk, decision=ApprovalStatus.APPROVED
            )
            change_password(
                user=applicant,
                current_password="Correct-Horse-91",
                new_password="Another-Horse-92",
            )
        self.assertEqual(types_for(applicant), [T.ACCOUNT_APPROVED, T.PASSWORD_CHANGED])

    def test_progress_summary(self):
        rel = self.in_care()
        with self.captureOnCommitCallbacks(execute=True):
            summary = set_summary(
                psychologist_user=self.psych.user,
                relationship_id=rel.pk,
                text="You are sleeping better and practising the exercises.",
            )
        n = Notification.objects.get(
            recipient=self.patient.user, type=T.PROGRESS_SUMMARY_UPDATED
        )
        self.assertEqual(n.target_id, summary.pk)
        self.assertNotIn("sleeping", n.body)


class ApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_patient()
        self.other = make_patient()
        self.mine = [self._make(self.patient.user, T.CARE_ACCEPTED) for _ in range(3)]
        self.mine.append(self._make(self.patient.user, T.CARE_ENDED))
        self.theirs = self._make(self.other.user, T.CARE_ACCEPTED)
        self.client.force_authenticate(self.patient.user)

    def tearDown(self):
        cache.clear()

    def _make(self, user, type, **extra):
        title, body, target_type = render(type)
        return Notification.objects.create(
            recipient=user,
            type=type,
            title=title,
            body=body,
            target_type=target_type,
            target_id=1,
            **extra,
        )

    def test_list_filters_and_count(self):
        body = self.client.get(BASE).json()
        self.assertEqual(body["count"], 4)
        self.assertEqual(body["results"][0]["id"], self.mine[-1].pk)  # newest first
        self.assertNotIn(self.theirs.pk, [r["id"] for r in body["results"]])
        self.assertEqual(
            self.client.get(BASE, {"type": "care_ended"}).json()["count"], 1
        )
        self.assertEqual(self.client.get(BASE, {"type": "nope"}).status_code, 400)
        self.assertEqual(self.client.get(BASE, {"unread": "maybe"}).status_code, 400)
        self.assertEqual(self.client.get(BASE + "unread-count/").json(), {"count": 4})

    def test_read_and_read_all(self):
        r = self.client.post(f"{BASE}{self.mine[0].pk}/read/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_read"])
        self.assertEqual(self.client.get(BASE, {"unread": "true"}).json()["count"], 3)
        self.assertEqual(
            self.client.post(f"{BASE}{self.theirs.pk}/read/").status_code, 404
        )
        self.assertEqual(
            self.client.post(BASE + "read-all/", {"x": 1}).status_code, 400
        )
        self.assertEqual(self.client.post(BASE + "read-all/").json(), {"updated": 3})
        self.assertEqual(self.client.get(BASE + "unread-count/").json()["count"], 0)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_read)

    def test_delete_own_only_and_audited(self):
        self.assertEqual(
            self.client.delete(f"{BASE}{self.theirs.pk}/").status_code, 404
        )
        self.assertTrue(Notification.objects.filter(pk=self.theirs.pk).exists())
        self.assertEqual(
            self.client.delete(f"{BASE}{self.mine[0].pk}/").status_code, 204
        )
        self.assertFalse(Notification.objects.filter(pk=self.mine[0].pk).exists())
        log = AccessLog.objects.get(resource_type=AuditResource.NOTIFICATION)
        self.assertEqual(
            (log.actor_id, log.action, log.patient_user_id),
            (self.patient.user.pk, "delete", self.patient.user.pk),
        )

    def test_any_role_and_anonymous(self):
        psych = make_psychologist()
        self.client.force_authenticate(psych.user)
        self.assertEqual(self.client.get(BASE).json()["count"], 0)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(BASE).status_code, 401)

    def test_purge_on_create_and_command(self):
        old = self._make(
            self.patient.user,
            T.CARE_ACCEPTED,
            created_at=timezone.now() - timedelta(days=91),
        )
        recent = self._make(
            self.patient.user,
            T.CARE_ACCEPTED,
            created_at=timezone.now() - timedelta(days=89),
        )
        with self.captureOnCommitCallbacks(execute=True):
            services.notify(recipients=[self.other.user], type=T.CARE_DECLINED)
        self.assertFalse(Notification.objects.filter(pk=old.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=recent.pk).exists())
        self._make(
            self.patient.user,
            T.CARE_ACCEPTED,
            created_at=timezone.now() - timedelta(days=100),
        )
        out = StringIO()
        call_command("purge_notifications", stdout=out)
        self.assertIn("Deleted 1", out.getvalue())
