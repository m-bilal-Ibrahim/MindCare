"""Mood check-ins (Phase 2 module 3): one compact file (speed mode,
docs/decisions.md 2026-10-28). Happy path per endpoint, permissions, and the
safety rules: one check-in per local day, editable only that day, note encrypted
and never shown to the psychologist, every write and psychologist read audited,
access ends with care."""

from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock

from django.core.cache import cache
from django.db import connection
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.journals import selectors
from apps.journals.models import MoodCheckIn
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.testing import make_patient, make_psychologist

BASE = "/api/v1/journals/"
CHECK_INS = BASE + "check-ins/"


class CheckInTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_patient(date_of_birth=date(1994, 5, 5))
        self.client.force_authenticate(self.patient.user)

    def tearDown(self):
        cache.clear()

    def post(self, **body):
        return self.client.post(CHECK_INS, {"mood": 4, **body}, format="json")


class PatientCheckInTests(CheckInTestCase):
    def test_create_today_list_and_read(self):
        r = self.post(
            tags=["calm", "grateful", "calm"],
            note="  Slept well and went for a walk.  ",
        )
        self.assertEqual(r.status_code, 201, r.json())
        body = r.json()
        self.assertEqual(body["tags"], ["calm", "grateful"])
        self.assertEqual(body["note"], "Slept well and went for a walk.")
        today = self.client.get(CHECK_INS + "today/").json()
        self.assertEqual(today["check_in"]["id"], body["id"])
        self.assertEqual(self.client.get(CHECK_INS).json()["count"], 1)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT note FROM journals_moodcheckin WHERE id = %s", [body["id"]]
            )
            self.assertNotIn("walk", cursor.fetchone()[0])  # encrypted at rest
        self.assertTrue(
            AccessLog.objects.filter(
                resource_type=AuditResource.MOOD_CHECK_IN, action=AuditAction.CREATE
            ).exists()
        )

    def test_one_per_local_day(self):
        self.assertEqual(self.post().status_code, 201)
        r = self.post(mood=2)
        self.assertEqual(
            r.json()["non_field_errors"],
            ["You've already checked in today. Edit today's check-in instead."],
        )

    def test_local_day_follows_patient_timezone(self):
        # 21:00 UTC on 1 Jan is already 2 Jan in Karachi (UTC+5).
        now = datetime(2027, 1, 1, 21, 0, tzinfo=dt_timezone.utc)
        self.assertEqual(
            selectors.patient_today(self.patient, now=now), date(2027, 1, 2)
        )
        self.patient.timezone = "America/New_York"
        self.assertEqual(
            selectors.patient_today(self.patient, now=now), date(2027, 1, 1)
        )

    def test_edit_only_today_delete_any(self):
        pk = self.post().json()["id"]
        r = self.client.patch(
            f"{CHECK_INS}{pk}/", {"mood": 2, "tags": []}, format="json"
        )
        self.assertEqual((r.json()["mood"], r.json()["tags"]), (2, []))
        MoodCheckIn.objects.filter(pk=pk).update(local_date=date(2020, 1, 1))
        r = self.client.patch(f"{CHECK_INS}{pk}/", {"mood": 3}, format="json")
        self.assertEqual(
            r.json()["non_field_errors"],
            ["A check-in can only be edited on the day it was made."],
        )
        self.assertEqual(self.client.delete(f"{CHECK_INS}{pk}/").status_code, 204)
        self.assertEqual(
            AccessLog.objects.filter(resource_type=AuditResource.MOOD_CHECK_IN).count(),
            3,
        )

    def test_validation(self):
        bad = [
            {"mood": 0},
            {"mood": 6},
            {"mood": "great"},
            {"tags": ["joyful"]},
            {"tags": ["calm", "happy", "sad", "tired", "angry", "lonely"]},
            {"note": "short"},
            {"note": "<script>alert(1)</script> hello there"},
            {"note": "1234567890 !!!"},
            {"extra": 1},
        ]
        for body in bad:
            r = self.client.post(CHECK_INS, {"mood": 3, **body}, format="json")
            self.assertEqual(r.status_code, 400, body)
        self.assertEqual(
            self.client.post(CHECK_INS, {"mood": 9}, format="json").json()["mood"],
            ["Mood must be a whole number between 1 and 5."],
        )

    def test_only_your_own_and_only_patients(self):
        pk = self.post().json()["id"]
        self.client.force_authenticate(make_patient().user)
        self.assertEqual(self.client.delete(f"{CHECK_INS}{pk}/").status_code, 404)
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(self.client.get(CHECK_INS).status_code, 403)

    def test_insights(self):
        today = selectors.patient_today(self.patient)
        for days_ago, mood, tags in [
            (0, 5, ["calm"]),
            (1, 3, ["calm", "sad"]),
            (2, 1, []),
            (40, 2, ["sad"]),
        ]:
            MoodCheckIn.objects.create(
                patient=self.patient,
                local_date=today - timedelta(days=days_ago),
                mood=mood,
                tags=tags,
            )
        body = self.client.get(CHECK_INS + "insights/").json()
        self.assertEqual(body["streak"], 3)
        week = body["windows"]["7"]
        self.assertEqual((week["check_ins"], week["average_mood"]), (3, 3.0))
        self.assertEqual(week["distribution"], {"1": 1, "2": 0, "3": 1, "4": 0, "5": 1})
        self.assertEqual(week["top_tags"][0], {"tag": "calm", "count": 2})
        self.assertEqual(body["windows"]["90"]["check_ins"], 4)


class StreakTests(SimpleTestCase):
    def test_streak_survives_until_a_day_is_missed(self):
        today = date(2027, 3, 10)
        days = [today - timedelta(days=n) for n in (1, 2, 3, 5)]
        self.assertEqual(selectors.streak(days, today), 3)  # today not in yet
        self.assertEqual(selectors.streak([*days, today], today), 4)
        self.assertEqual(selectors.streak([today - timedelta(days=2)], today), 0)


class PsychologistMoodTests(CheckInTestCase):
    def setUp(self):
        super().setUp()
        self.psych = make_psychologist()
        self.rel = request_psychologist(
            patient_user=self.patient.user, psychologist_id=self.psych.pk
        )
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)
        self.post(tags=["anxious"], note="Private thoughts nobody else reads.")
        self.url = f"{BASE}psychologist/patients/{self.rel.pk}/moods/"

    def test_current_psychologist_sees_mood_not_note_audited(self):
        self.client.force_authenticate(self.psych.user)
        body = self.client.get(self.url + "?days=7").json()
        self.assertEqual(body["check_ins"][0]["tags"], ["anxious"])
        self.assertNotIn("note", body["check_ins"][0])
        self.assertNotIn("Private", str(body))
        self.assertEqual(body["insights"]["windows"]["7"]["check_ins"], 1)
        self.assertTrue(
            AccessLog.objects.filter(
                actor_id=self.psych.user.pk,
                resource_type=AuditResource.MOOD_CHECK_IN,
                action=AuditAction.VIEW,
            ).exists()
        )
        self.assertEqual(self.client.get(self.url + "?days=5").status_code, 400)

    def test_other_psychologist_and_ended_care_get_404(self):
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        self.client.force_authenticate(self.psych.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_audit_failure_returns_nothing(self):
        self.client.force_authenticate(self.psych.user)
        with mock.patch(
            "apps.journals.services.record_access", side_effect=RuntimeError("down")
        ):
            with self.assertRaises(RuntimeError):
                self.client.get(self.url)
