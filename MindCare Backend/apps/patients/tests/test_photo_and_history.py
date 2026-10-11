"""6.1: profile photos (patients and psychologists), privacy info, the
'complete your profile' hint, and the encrypted, audited mental health history."""

import io
import os
import shutil
import tempfile
from datetime import date
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.patients.models import MentalHealthHistory
from apps.patients.selectors import can_see_patient_photo
from apps.reference.models import Specialization
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.testing import make_admin, make_patient, make_psychologist

ME = "/api/v1/patients/me/"
PHOTO = "/api/v1/patients/me/photo/"
HISTORY = "/api/v1/patients/me/history/"


def jpeg(size=(2000, 1000), gps=True):
    image = Image.new("RGB", size, "teal")
    exif = Image.Exif()
    if gps:
        exif[0x8825] = {2: (33.0, 41.0, 0.0), 4: (73.0, 3.0, 0.0)}
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    return SimpleUploadedFile("me.jpg", out.getvalue(), content_type="image/jpeg")


class MediaTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)
        cache.clear()

    def files(self):
        return [n for _, _, names in os.walk(self.media) for n in names]


class PatientPhotoTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.profile = make_patient()
        self.client.force_authenticate(self.profile.user)

    def test_upload_strips_exif_and_shrinks(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.put(PHOTO, {"photo": jpeg()}, format="multipart")
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.json())
        self.assertIsNotNone(r.json()["photo_url"])
        self.profile.refresh_from_db()
        with default_storage.open(self.profile.photo_key) as f:
            stored = Image.open(io.BytesIO(f.read()))
        self.assertEqual(dict(stored.getexif()), {})
        self.assertEqual(max(stored.size), 1024)

    def test_replace_deletes_the_old_file_and_delete_removes_it(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.put(PHOTO, {"photo": jpeg()}, format="multipart")
        with self.captureOnCommitCallbacks(execute=True):
            self.client.put(PHOTO, {"photo": jpeg(size=(300, 300))}, format="multipart")
        self.assertEqual(len(self.files()), 1)
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.delete(PHOTO)
        self.assertIsNone(r.json()["photo_url"])
        self.assertEqual(self.files(), [])

    def test_validation(self):
        r = self.client.put(
            PHOTO,
            {"photo": SimpleUploadedFile("x.jpg", b"%PDF-1.7\n%%EOF\n")},
            format="multipart",
        )
        self.assertEqual(r.json(), {"photo": ["Photo must be one of: JPG, PNG, WEBP."]})
        r = self.client.put(PHOTO, {}, format="multipart")
        self.assertEqual(r.json(), {"photo": ["Choose a photo to upload."]})
        r = self.client.put(
            PHOTO,
            {"photo": SimpleUploadedFile("x.jpg", b"\xff\xd8\xff\xe0garbage" * 4)},
            format="multipart",
        )
        self.assertEqual(r.json(), {"photo": ["Photo isn't a readable image."]})

    def test_only_patients_and_methods(self):
        self.assertEqual(self.client.get(PHOTO).status_code, 405)
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(
            self.client.put(PHOTO, {"photo": jpeg()}, format="multipart").status_code,
            403,
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["uploads"], "20/hour"
        )


class PhotoVisibilityTests(MediaTestCase):
    def test_who_sees_a_private_patients_photo(self):
        patient = make_patient(date_of_birth=date(1995, 1, 1))
        psych = make_psychologist()
        stranger_psych = make_psychologist()
        other_patient = make_patient()
        rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)

        def sees(viewer):
            return can_see_patient_photo(patient_profile=patient, viewer=viewer)

        self.assertTrue(sees(patient.user))
        self.assertTrue(sees(make_admin()))
        self.assertFalse(sees(psych.user))  # pending request only
        accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
        self.assertTrue(sees(psych.user))
        self.assertFalse(sees(stranger_psych.user))
        self.assertFalse(sees(other_patient.user))
        patient.is_profile_public = True
        self.assertTrue(sees(other_patient.user))

    def test_assigned_psychologist_sees_the_photo_in_patient_detail(self):
        patient = make_patient(date_of_birth=date(1995, 1, 1))
        self.client.force_authenticate(patient.user)
        self.client.put(PHOTO, {"photo": jpeg()}, format="multipart")
        psych = make_psychologist()
        rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
        accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
        self.client.force_authenticate(psych.user)
        body = self.client.get(f"/api/v1/relationships/patients/{rel.pk}/").json()
        self.assertIsNotNone(body["photo_url"])


class PsychologistPhotoTests(MediaTestCase):
    def test_photo_shows_in_the_directory(self):
        psych = make_psychologist()
        self.client.force_authenticate(psych.user)
        r = self.client.put(
            "/api/v1/psychologists/me/photo/", {"photo": jpeg()}, format="multipart"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.json())
        self.assertIsNotNone(r.json()["photo_url"])
        self.client.force_authenticate(make_patient().user)
        card = self.client.get(f"/api/v1/psychologists/directory/{psych.pk}/").json()
        self.assertIsNotNone(card["photo_url"])


class ProfileInfoTests(APITestCase):
    def test_privacy_and_completion(self):
        profile = make_patient()
        self.client.force_authenticate(profile.user)
        body = self.client.get(ME).json()
        self.assertEqual(
            body["privacy"],
            {
                "is_profile_public": False,
                "shown_when_public": ["full_name", "photo"],
                "always_private": [
                    "date_of_birth",
                    "gender",
                    "phone_number",
                    "mental_health_history",
                ],
            },
        )
        self.assertIn("gender", body["profile_completion"]["missing"])
        self.assertIn("mental_health_history", body["profile_completion"]["missing"])
        self.client.patch(ME, {"gender": "female"}, format="json")
        body = self.client.get(ME).json()
        self.assertNotIn("gender", body["profile_completion"]["missing"])


class HistoryTests(APITestCase):
    def setUp(self):
        self.profile = make_patient()
        self.client.force_authenticate(self.profile.user)
        self.full = {
            "concerns": ["anxiety", "sleep-issues"],
            "previous_diagnosis": "yes",
            "current_medication": "prefer_not_to_say",
            "previous_therapy": "no",
            "notes": "Panic attacks before exams since 2019.",
        }

    def test_empty_by_default(self):
        body = self.client.get(HISTORY).json()
        self.assertTrue(body["is_empty"])
        self.assertEqual(body["concerns"], [])

    def test_save_read_and_encrypted_at_rest(self):
        r = self.client.put(HISTORY, self.full, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK, r.json())
        body = self.client.get(HISTORY).json()
        self.assertEqual(
            body["concerns"],
            [
                {"slug": "anxiety", "name": "Anxiety"},
                {"slug": "sleep-issues", "name": "Sleep issues"},
            ],
        )
        self.assertEqual(body["previous_diagnosis"], "yes")
        self.assertFalse(body["is_empty"])
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT concerns, previous_diagnosis, notes FROM "
                "patients_mentalhealthhistory WHERE profile_id = %s",
                [self.profile.pk],
            )
            raw = " ".join(cursor.fetchone())
        for plain in ("anxiety", "yes", "Panic"):
            self.assertNotIn(plain, raw)

    def test_put_replaces_the_whole_history(self):
        self.client.put(HISTORY, self.full, format="json")
        body = self.client.put(
            HISTORY, {"previous_therapy": "yes"}, format="json"
        ).json()
        self.assertEqual(body["concerns"], [])
        self.assertIsNone(body["previous_diagnosis"])
        self.assertEqual(body["previous_therapy"], "yes")

    def test_validation(self):
        cases = {
            "previous_diagnosis": ({"previous_diagnosis": "maybe"}, None),
            "concerns": ({"concerns": ["astrology"]}, None),
            "notes": (
                {"notes": "<b>bold</b> notes about my panic attacks"},
                ["Notes can't contain HTML tags."],
            ),
            "diagnosis_name": ({"diagnosis_name": "GAD"}, ["This field can't be set."]),
        }
        for key, (body, message) in cases.items():
            with self.subTest(key=key):
                r = self.client.put(HISTORY, body, format="json")
                self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(key, r.json())
                if message:
                    self.assertEqual(r.json()[key], message)

    def test_retired_specialization_refused(self):
        Specialization.objects.filter(slug="grief").update(is_active=False)
        r = self.client.put(HISTORY, {"concerns": ["grief"]}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_writes_are_audited_and_own_reads_are_not(self):
        self.client.put(HISTORY, self.full, format="json")
        self.client.put(HISTORY, self.full, format="json")
        self.client.get(HISTORY)
        self.assertEqual(self.client.delete(HISTORY).status_code, 204)
        actions = list(
            AccessLog.objects.filter(
                resource_type=AuditResource.MENTAL_HEALTH_HISTORY
            ).values_list("action", flat=True)
        )
        self.assertEqual(
            sorted(actions),
            sorted([AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]),
        )
        self.assertFalse(MentalHealthHistory.objects.exists())


class PsychologistHistoryAccessTests(APITestCase):
    def setUp(self):
        self.patient = make_patient(date_of_birth=date(1995, 1, 1))
        self.psych = make_psychologist()
        self.client.force_authenticate(self.patient.user)
        self.client.put(
            HISTORY,
            {"concerns": ["anxiety"], "notes": "Worse in winter, better with walks."},
            format="json",
        )
        self.rel = request_psychologist(
            patient_user=self.patient.user, psychologist_id=self.psych.pk
        )

    def url(self):
        return f"/api/v1/relationships/patients/{self.rel.pk}/history/"

    def views(self):
        return AccessLog.objects.filter(action=AuditAction.VIEW).count()

    def test_not_on_a_pending_request(self):
        self.client.force_authenticate(self.psych.user)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.views(), 0)

    def test_current_psychologist_reads_and_it_is_audited(self):
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)
        self.client.force_authenticate(self.psych.user)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["notes"], "Worse in winter, better with walks.")
        row = AccessLog.objects.get(action=AuditAction.VIEW)
        self.assertEqual(
            (row.actor_id, row.patient_user_id),
            (self.psych.user_id, self.patient.user_id),
        )

    def test_access_ends_when_care_ends(self):
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        self.client.force_authenticate(self.psych.user)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_other_psychologists_and_admins_never(self):
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_authenticate(make_admin())
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(self.views(), 0)

    def test_fail_closed(self):
        accept_request(psychologist_user=self.psych.user, relationship_id=self.rel.pk)
        self.client.force_authenticate(self.psych.user)
        with mock.patch(
            "apps.audit.services.AccessLog.objects.create",
            side_effect=RuntimeError("database down"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.get(self.url())
