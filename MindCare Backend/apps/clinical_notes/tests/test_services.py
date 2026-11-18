"""Therapy notes (Phase 2 module 5): one compact file (speed mode,
docs/decisions.md 2026-10-28). Happy path per endpoint, permissions (other
psychologists, the patient, admins and former psychologists all refused),
encryption at rest, every read and write audited, the 24-hour lock with
versions and addenda, and what the patient sees instead of notes."""

from datetime import timedelta

from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus
from apps.appointments import services as booking_services
from apps.appointments.models import Session, SessionStatus
from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.clinical_notes import services
from apps.clinical_notes.models import NoteVersion, TherapyNote
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.testing import make_admin, make_patient, make_psychologist

BASE = "/api/v1/clinical-notes/"
OBS = "Patient reports sleeping poorly before exams."


def in_care(psych, patient=None):
    patient = patient or make_patient()
    rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
    accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
    return patient, rel


class NotesTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psych = make_psychologist()
        self.patient, self.rel = in_care(self.psych)
        self.client.force_authenticate(self.psych.user)

    def tearDown(self):
        cache.clear()

    def url(self, suffix="notes/", rel=None):
        return f"{BASE}patients/{(rel or self.rel).pk}/{suffix}"

    def create(self, **body):
        body.setdefault("observations", OBS)
        return self.client.post(self.url(), body, format="json")

    def session(self, *, patient=None, psych=None, status=SessionStatus.COMPLETED):
        patient = patient or self.patient
        psych = psych or self.psych
        rel = patient.care_relationships.filter(psychologist=psych).first() or self.rel
        session = Session(
            relationship=rel,
            patient=patient,
            psychologist=psych,
            status=status,
            fee_pkr=3000,
            requested_starts_at=timezone.now() - timedelta(days=1),
        )
        booking_services._set_times(session, timezone.now() - timedelta(days=1), 50)
        session.save()
        return session


class NoteFlowTests(NotesTestCase):
    def test_create_list_detail_encrypted_and_audited(self):
        session = self.session()
        r = self.create(
            session=session.pk,
            plan="  Keep a sleep diary for two weeks.  ",
            progress_rating=4,
            risk_level="medium",
        )
        self.assertEqual(r.status_code, 201, r.json())
        note = r.json()
        self.assertEqual(note["plan"], "Keep a sleep diary for two weeks.")
        self.assertEqual(note["session_id"], session.pk)
        self.assertEqual(note["version"], 1)
        self.assertFalse(note["is_locked"])
        self.assertEqual(self.client.get(self.url()).json()["count"], 1)
        self.assertEqual(
            self.client.get(self.url(f"notes/{note['id']}/")).json()["risk_level"],
            "medium",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT observations, plan, risk_level FROM clinical_notes_therapynote"
            )
            row = cursor.fetchone()
            cursor.execute("SELECT content FROM clinical_notes_noteversion")
            version = cursor.fetchone()[0]
        self.assertNotIn("exams", row[0])
        self.assertNotIn("diary", row[1])
        self.assertNotEqual(row[2], "medium")
        self.assertNotIn("exams", version)
        logs = AccessLog.objects.filter(resource_type=AuditResource.THERAPY_NOTE)
        self.assertEqual(logs.filter(action=AuditAction.CREATE).count(), 1)
        self.assertEqual(logs.filter(action=AuditAction.VIEW).count(), 2)
        self.assertTrue(
            logs.filter(patient_user_id=self.patient.user_id).count() == logs.count()
        )

    def test_validation(self):
        cases = [
            ({"observations": ""}, "non_field_errors", services.EMPTY),
            ({"observations": "short"}, "observations", None),
            ({"plan": "<script>alert(1)</script> and more"}, "plan", None),
            ({"progress_rating": 11}, "progress_rating", None),
            ({"risk_level": "extreme"}, "risk_level", None),
            ({"colour": "red"}, "colour", None),
        ]
        for body, key, message in cases:
            r = self.create(**body)
            self.assertEqual(r.status_code, 400, body)
            self.assertIn(key, r.json(), body)
            if message:
                self.assertEqual(r.json()[key], [message])
        rating_only = self.client.post(
            self.url(), {"progress_rating": 7}, format="json"
        )
        self.assertEqual(rating_only.status_code, 201)

    def test_session_link_rules(self):
        session = self.session()
        self.assertEqual(self.create(session=session.pk).status_code, 201)
        self.assertEqual(
            self.create(session=session.pk).json(),
            {"session": [services.SESSION_TAKEN]},
        )
        other_patient, _ = in_care(make_psychologist())
        stranger = self.session(
            patient=other_patient,
            psych=other_patient.care_relationships.get().psychologist,
        )
        cancelled = self.session(status=SessionStatus.CANCELLED)
        for bad in (stranger.pk, cancelled.pk, 999999):
            self.assertEqual(
                self.create(session=bad).json(), {"session": [services.BAD_SESSION]}
            )

    def test_edit_window_versions_lock_and_addenda(self):
        note_id = self.create().json()["id"]
        detail = self.url(f"notes/{note_id}/")
        r = self.client.patch(
            detail, {"plan": "Weekly sessions for a month."}, format="json"
        )
        self.assertEqual(r.json()["version"], 2)
        versions = self.client.get(detail + "versions/").json()
        self.assertEqual([v["version"] for v in versions], [1, 2])
        self.assertEqual(versions[0]["plan"], "")
        self.assertEqual(versions[1]["plan"], "Weekly sessions for a month.")
        self.assertEqual(
            self.client.patch(detail, {"observations": ""}, format="json").status_code,
            200,  # the plan still keeps it non-empty
        )

        TherapyNote.objects.filter(pk=note_id).update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        r = self.client.patch(
            detail, {"plan": "Changed after the window."}, format="json"
        )
        self.assertEqual(r.json(), {"non_field_errors": [services.LOCKED]})
        r = self.client.post(
            detail + "addenda/", {"text": "Patient called; exams moved to June."}
        )
        self.assertEqual(r.status_code, 201, r.json())
        note = self.client.get(detail).json()
        self.assertTrue(note["is_locked"])
        self.assertEqual(
            note["addenda"][0]["text"], "Patient called; exams moved to June."
        )
        self.assertEqual(note["plan"], "Weekly sessions for a month.")
        self.assertEqual(NoteVersion.objects.filter(note_id=note_id).count(), 3)
        self.assertEqual(self.client.delete(detail).status_code, 405)

    def test_progress_series(self):
        self.create(progress_rating=3, risk_level="high")
        self.create()  # no ratings: not a chart point
        self.create(progress_rating=6)
        points = self.client.get(self.url("progress/")).json()
        self.assertEqual([p["progress_rating"] for p in points], [3, 6])
        self.assertEqual([p["risk_level"] for p in points], ["high", None])

    def test_summary_and_what_the_patient_sees(self):
        self.assertIsNone(self.client.get(self.url("summary/")).json()["text"])
        text = "You are sleeping better. Keep the diary going."
        r = self.client.put(self.url("summary/"), {"text": text})
        self.assertEqual(r.json()["text"], text)
        self.create(progress_rating=5, risk_level="high")
        self.session()

        self.client.force_authenticate(self.patient.user)
        body = self.client.get(BASE + "me/progress/").json()
        self.assertEqual(body["summary"]["text"], text)
        self.assertEqual(body["summary"]["psychologist"]["id"], self.psych.pk)
        self.assertEqual(body["sessions"], {"completed": 1, "upcoming": 0})
        self.assertIn("streak", body["mood"])
        self.assertNotIn("high", str(body))
        self.assertNotIn(OBS, str(body))


class NotePermissionTests(NotesTestCase):
    def test_nobody_else_gets_in(self):
        note_id = self.create().json()["id"]
        urls = [
            self.url(),
            self.url(f"notes/{note_id}/"),
            self.url(f"notes/{note_id}/versions/"),
            self.url("progress/"),
            self.url("summary/"),
        ]
        # Another psychologist: not their patient.
        self.client.force_authenticate(make_psychologist().user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        # The patient and an admin: wrong role.
        for user in (self.patient.user, make_admin()):
            self.client.force_authenticate(user)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 403, url)
        self.client.force_authenticate(self.psych.user)
        self.assertEqual(self.client.get(BASE + "me/progress/").status_code, 403)
        # A paused (pending) psychologist.
        self.psych.user.approval_status = ApprovalStatus.PENDING
        self.psych.user.save(update_fields=["approval_status"])
        self.assertEqual(self.client.get(urls[0]).status_code, 403)

    def test_access_ends_with_care_and_returns_with_it(self):
        self.create()
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.create().status_code, 404)
        _, new_rel = in_care(self.psych, self.patient)
        listed = self.client.get(self.url(rel=new_rel)).json()
        self.assertEqual(listed["count"], 1)  # the pair's notes continue
