"""Booking and fees (Phase 2 module 4): one compact file (speed mode,
docs/decisions.md 2026-10-28). Happy path per endpoint, permissions, no double
booking (sequential, at the database, and concurrent), and the notice /
horizon / limit / cancellation rules."""

import threading
from datetime import time, timedelta

from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus
from apps.appointments import selectors, services
from apps.appointments.models import CancelledBy, Session, SessionStatus
from apps.audit.models import AccessLog, AuditResource
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.exceptions import DomainValidationError
from core.testing import (
    ReferenceDataTransactionTestCase,
    make_patient,
    make_psychologist,
)

BASE = "/api/v1/appointments/"
PSY = BASE + "psychologist/"
LINK = "https://us02web.zoom.us/j/1234567890"


def open_bookings(psych, *, fee=3000, minutes=50):
    services.update_booking_settings(
        psychologist_profile=psych,
        fee_pkr=fee,
        session_minutes=minutes,
        video_link=LINK,
    )
    services.replace_working_windows(
        psychologist_profile=psych,
        windows=[
            {"weekday": d, "start_time": time(9), "end_time": time(17)}
            for d in range(7)
        ],
    )


def in_care(psych):
    patient = make_patient()
    rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
    accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
    return patient


def iso(dt):
    return dt.isoformat()


class BookingTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psych = make_psychologist()
        open_bookings(self.psych)
        self.patient = in_care(self.psych)
        self.slots = selectors.free_slots(self.psych)

    def tearDown(self):
        cache.clear()

    def as_patient(self, patient=None):
        self.client.force_authenticate((patient or self.patient).user)

    def as_psych(self, psych=None):
        self.client.force_authenticate((psych or self.psych).user)

    def book(self, slot, patient=None):
        self.as_patient(patient)
        return self.client.post(BASE + "sessions/", {"starts_at": iso(slot)})

    def make_session(self, *, starts_at, status=SessionStatus.CONFIRMED):
        rel = self.patient.care_relationships.get(status="accepted")
        session = Session(
            relationship=rel,
            patient=self.patient,
            psychologist=self.psych,
            status=status,
            fee_pkr=3000,
            requested_starts_at=starts_at,
        )
        services._set_times(session, starts_at, 50)
        session.save()
        return session


class PsychologistSetupTests(BookingTestCase):
    def test_settings_validation_and_bookable_flag(self):
        other = make_psychologist()
        self.as_psych(other)
        body = self.client.get(PSY + "settings/").json()
        self.assertFalse(body["is_bookable"])
        self.assertEqual(body["not_bookable_reason"], "no_fee")
        for bad in (
            {"fee_pkr": 0},
            {"fee_pkr": 100001},
            {"session_minutes": 45},
            {"video_link": "http://zoom.us/j/1"},
            {"video_link": "https://evil.example.com/j/1"},
            {"colour": "red"},
        ):
            self.assertEqual(
                self.client.patch(PSY + "settings/", bad, format="json").status_code,
                400,
                bad,
            )
        r = self.client.patch(
            PSY + "settings/",
            {
                "fee_pkr": 2500,
                "session_minutes": 30,
                "video_link": "https://meet.google.com/abc-defg-hij",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.json())
        self.assertEqual(r.json()["not_bookable_reason"], "no_working_hours")

    def test_working_hours_rules(self):
        self.as_psych()
        url = PSY + "working-hours/"

        def put(*windows):
            return self.client.put(
                url,
                {
                    "windows": [
                        dict(zip(("weekday", "start_time", "end_time"), w, strict=True))
                        for w in windows
                    ]
                },
                format="json",
            )

        self.assertEqual(
            put((0, "09:00", "12:00"), (0, "13:00", "17:00")).status_code, 200
        )
        self.assertEqual(len(self.client.get(url).json()["windows"]), 2)
        cases = {
            services.WINDOW_OVERLAP: [(1, "09:00", "12:00"), (1, "11:00", "14:00")],
            services.WINDOW_QUARTER: [(1, "09:10", "12:00")],
            services.WINDOW_ORDER: [(1, "12:00", "09:00")],
            services.WINDOW_TOO_SHORT: [(1, "09:00", "09:30")],
        }
        for message, windows in cases.items():
            r = put(*windows)
            self.assertEqual(r.json(), {"windows": [message]})

    def test_days_off(self):
        self.as_psych()
        tomorrow = (timezone.localdate() + timedelta(days=5)).isoformat()
        r = self.client.post(PSY + "days-off/", {"date": tomorrow})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(
            self.client.post(PSY + "days-off/", {"date": tomorrow}).status_code, 400
        )
        past = (timezone.localdate() - timedelta(days=2)).isoformat()
        self.assertEqual(
            self.client.post(PSY + "days-off/", {"date": past}).json(),
            {"date": [services.DAY_OFF_PAST]},
        )
        self.assertEqual(len(self.client.get(PSY + "days-off/").json()), 1)
        self.assertEqual(
            self.client.delete(PSY + f"days-off/{r.json()['id']}/").status_code, 204
        )

    def test_day_off_removes_slots_and_refuses_busy_days(self):
        slot = self.slots[0]
        self.assertEqual(self.book(slot).status_code, 201)
        local_day = slot.astimezone(selectors._tz(self.psych.timezone)).date()
        with self.assertRaises(DomainValidationError):
            services.add_day_off(psychologist_profile=self.psych, date=local_day)
        free_day = local_day + timedelta(days=3)
        services.add_day_off(psychologist_profile=self.psych, date=free_day)
        tz = selectors._tz(self.psych.timezone)
        self.assertFalse(
            any(
                s.astimezone(tz).date() == free_day
                for s in selectors.free_slots(self.psych)
            )
        )

    def test_directory_shows_fee(self):
        self.as_patient()
        card = self.client.get(
            f"/api/v1/psychologists/directory/{self.psych.pk}/"
        ).json()
        self.assertEqual(card["session_fee_pkr"], 3000)
        self.assertEqual(card["session_minutes"], 50)


class SlotTests(BookingTestCase):
    def test_slots_follow_the_rules(self):
        self.as_patient()
        body = self.client.get(BASE + "slots/").json()
        self.assertTrue(body["bookable"])
        self.assertEqual(body["fee_pkr"], 3000)
        now = timezone.now()
        self.assertTrue(self.slots)
        self.assertGreaterEqual(self.slots[0], now + timedelta(hours=12))
        self.assertLessEqual(self.slots[-1], now + timedelta(days=30))
        tz = selectors._tz(self.psych.timezone)
        for slot in self.slots:  # on the 50 + 10 minute grid from 09:00 local
            local = slot.astimezone(tz)
            self.assertEqual(local.minute, 0)
            self.assertTrue(9 <= local.hour <= 16)

    def test_no_relationship_no_slots(self):
        self.as_patient(make_patient())
        r = self.client.get(BASE + "slots/")
        self.assertEqual(r.json(), {"relationship": [services.NO_PSYCHOLOGIST]})
        self.assertEqual(self.book(self.slots[0], make_patient()).status_code, 400)


class BookingFlowTests(BookingTestCase):
    def test_book_confirm_and_link_visibility(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.book(self.slots[0])
        self.assertEqual(r.status_code, 201, r.json())
        session = r.json()
        self.assertEqual(session["status"], "requested")
        self.assertEqual(session["fee_pkr"], 3000)
        self.assertIsNone(session["video_link"])
        self.assertEqual(mail.outbox[-1].to, [self.psych.user.email])
        self.assertNotIn(self.patient.user.full_name, mail.outbox[-1].body)
        self.assertNotIn(self.slots[0], selectors.free_slots(self.psych))

        self.as_psych()
        listed = self.client.get(PSY + "sessions/?view=requests").json()
        self.assertEqual(
            listed["results"][0]["patient"]["display_name"], self.patient.user.full_name
        )
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(PSY + f"sessions/{session['id']}/confirm/")
        self.assertEqual(r.json()["status"], "confirmed")
        self.assertEqual(mail.outbox[-1].to, [self.patient.user.email])
        self.as_patient()
        mine = self.client.get(BASE + "sessions/").json()["results"][0]
        self.assertEqual(mine["video_link"], LINK)
        self.assertIsNotNone(mine["free_cancellation_until"])
        self.assertEqual(
            AccessLog.objects.filter(resource_type=AuditResource.APPOINTMENT).count(), 2
        )

    def test_fee_is_a_snapshot(self):
        session_id = self.book(self.slots[0]).json()["id"]
        services.update_booking_settings(psychologist_profile=self.psych, fee_pkr=9000)
        self.assertEqual(Session.objects.get(pk=session_id).fee_pkr, 3000)

    def test_propose_then_accept(self):
        session_id = self.book(self.slots[0]).json()["id"]
        self.as_psych()
        offered = self.client.get(PSY + "slots/").json()["slots"]
        self.assertNotIn(iso(self.slots[0]).replace("+00:00", "Z"), offered)
        r = self.client.post(
            PSY + f"sessions/{session_id}/propose/", {"starts_at": offered[2]}
        )
        self.assertEqual(r.json()["status"], "proposed", r.json())
        self.assertIn(self.slots[0], selectors.free_slots(self.psych))  # old slot freed
        self.as_patient()
        r = self.client.post(BASE + f"sessions/{session_id}/accept/")
        self.assertEqual(r.json()["status"], "confirmed")
        self.assertEqual(r.json()["starts_at"], offered[2])

    def test_psychologist_cancel_and_outcome(self):
        session_id = self.book(self.slots[0]).json()["id"]
        self.as_psych()
        r = self.client.post(PSY + f"sessions/{session_id}/cancel/")
        self.assertEqual(r.json()["cancelled_by"], "psychologist")
        self.assertFalse(r.json()["is_late_cancellation"])

        past = self.make_session(starts_at=timezone.now() - timedelta(hours=2))
        future = self.make_session(
            starts_at=timezone.now() + timedelta(days=2, hours=1, minutes=7)
        )
        outcome = PSY + "sessions/{}/outcome/"
        self.assertEqual(
            self.client.post(
                outcome.format(future.pk), {"outcome": "completed"}
            ).json(),
            {"session": [services.NOT_ENDED]},
        )
        r = self.client.post(outcome.format(past.pk), {"outcome": "no_show"})
        self.assertEqual(r.json()["status"], "no_show")
        self.assertEqual(
            self.client.get(PSY + "sessions/?view=past").json()["count"], 2
        )

    def test_patient_cancellation_free_or_late(self):
        free = self.book(self.slots[-1]).json()["id"]
        self.as_patient()
        r = self.client.post(BASE + f"sessions/{free}/cancel/")
        self.assertFalse(r.json()["is_late_cancellation"])
        soon = self.make_session(
            starts_at=timezone.now() + timedelta(hours=5, minutes=3)
        )
        r = self.client.post(BASE + f"sessions/{soon.pk}/cancel/")
        self.assertTrue(r.json()["is_late_cancellation"])
        self.assertEqual(
            self.client.post(BASE + f"sessions/{soon.pk}/cancel/").json(),
            {"session": [services.NOT_CANCELLABLE]},
        )

    def test_unconfirmed_request_expires_at_its_start(self):
        stale = self.make_session(
            starts_at=timezone.now() - timedelta(minutes=5),
            status=SessionStatus.REQUESTED,
        )
        self.as_psych()
        r = self.client.post(PSY + f"sessions/{stale.pk}/confirm/")
        self.assertEqual(r.json(), {"session": [services.NOT_REQUESTED]})
        stale.refresh_from_db()
        self.assertEqual(stale.status, SessionStatus.EXPIRED)

    def test_ending_care_cancels_future_sessions(self):
        session_id = self.book(self.slots[0]).json()["id"]
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        session = Session.objects.get(pk=session_id)
        self.assertEqual(session.status, SessionStatus.CANCELLED)
        self.assertEqual(session.cancelled_by, CancelledBy.SYSTEM)


class BookingRuleTests(BookingTestCase):
    def test_notice_horizon_grid_and_limit(self):
        now = timezone.now()
        self.assertEqual(
            self.book(now + timedelta(hours=2)).json(), {"starts_at": [services.NOTICE]}
        )
        self.assertEqual(
            self.book(now + timedelta(days=31)).json(),
            {"starts_at": [services.HORIZON]},
        )
        off_grid = self.slots[0] + timedelta(minutes=20)
        self.assertEqual(
            self.book(off_grid).json(), {"starts_at": [services.SLOT_UNAVAILABLE]}
        )
        self.assertEqual(self.book(self.slots[0]).status_code, 201)
        self.assertEqual(self.book(self.slots[1]).status_code, 201)
        self.assertEqual(
            self.book(self.slots[2]).json(), {"non_field_errors": [services.LIMIT]}
        )

    def test_confirm_needs_video_link(self):
        session_id = self.book(self.slots[0]).json()["id"]
        services.update_booking_settings(psychologist_profile=self.psych, video_link="")
        self.as_psych()
        r = self.client.post(PSY + f"sessions/{session_id}/confirm/")
        self.assertEqual(r.json(), {"video_link": [services.NEED_LINK]})

    def test_sequential_double_booking_refused(self):
        other = in_care(self.psych)
        self.assertEqual(self.book(self.slots[0]).status_code, 201)
        self.assertEqual(
            self.book(self.slots[0], other).json(),
            {"starts_at": [services.SLOT_UNAVAILABLE]},
        )

    def test_database_refuses_overlap(self):
        self.make_session(starts_at=self.slots[0])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_session(starts_at=self.slots[0] + timedelta(minutes=55))
        # A cancelled session no longer holds its slot.
        Session.objects.filter(starts_at=self.slots[0]).update(
            status=SessionStatus.CANCELLED
        )
        self.make_session(starts_at=self.slots[0])


class PermissionTests(BookingTestCase):
    def test_roles_and_ownership(self):
        session_id = self.book(self.slots[0]).json()["id"]
        self.as_patient()
        self.assertEqual(self.client.get(PSY + "sessions/").status_code, 403)
        self.assertEqual(self.client.get(PSY + "settings/").status_code, 403)
        self.as_psych()
        self.assertEqual(self.client.get(BASE + "slots/").status_code, 403)
        self.assertEqual(self.client.post(BASE + "sessions/", {}).status_code, 403)
        # Another psychologist can't see or act on this session.
        stranger = make_psychologist()
        self.as_psych(stranger)
        self.assertEqual(
            self.client.get(PSY + "sessions/?view=requests").json()["count"], 0
        )
        self.assertEqual(
            self.client.post(PSY + f"sessions/{session_id}/confirm/").status_code, 404
        )
        # Another patient can't cancel it.
        self.as_patient(make_patient())
        self.assertEqual(
            self.client.post(BASE + f"sessions/{session_id}/cancel/").status_code, 404
        )
        # A paused (pending) psychologist is refused, and their patient can't book.
        self.psych.user.approval_status = ApprovalStatus.PENDING
        self.psych.user.save(update_fields=["approval_status"])
        self.as_psych()
        self.assertEqual(self.client.get(PSY + "sessions/").status_code, 403)
        self.assertEqual(
            self.book(self.slots[1]).json(),
            {"relationship": [services.NO_PSYCHOLOGIST]},
        )
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(BASE + "slots/").status_code, 401)


class ConcurrentBookingTests(ReferenceDataTransactionTestCase):
    def test_two_patients_same_slot_one_wins(self):
        psych = make_psychologist()
        open_bookings(psych)
        patients = [in_care(psych), in_care(psych)]
        slot = selectors.free_slots(psych)[0]
        barrier = threading.Barrier(2)
        results = [None, None]

        def run(i):
            try:
                barrier.wait()
                services.book_session(patient_user=patients[i].user, starts_at=slot)
                results[i] = "ok"
            except DomainValidationError:
                results[i] = "rejected"
            finally:
                connection.close()

        threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), ["ok", "rejected"])
        self.assertEqual(Session.objects.filter(starts_at=slot).count(), 1)
