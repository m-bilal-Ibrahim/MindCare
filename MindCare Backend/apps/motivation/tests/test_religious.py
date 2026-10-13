"""6.10: duas and surahs (text + audio) in their own tables, patients only,
behind an opt-in that is deleted on opt-out (docs/decisions.md, 2026-10-11)."""

import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.motivation import services
from apps.motivation.admin import ReligiousContentForm
from apps.motivation.models import Dua, ReligiousContentPreference, Surah
from apps.motivation.permissions import OPT_IN_MESSAGE
from core.files import check_audio
from core.testing import make_admin, make_patient, make_psychologist

PREF = "/api/v1/motivation/religious/preference/"
DUAS = "/api/v1/motivation/duas/"
SURAHS = "/api/v1/motivation/surahs/"
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


class SeedTests(TestCase):
    def test_seeded_text_is_complete_and_valid(self):
        self.assertEqual(Dua.objects.count(), 10)
        self.assertEqual(
            list(Surah.objects.values_list("number", flat=True)),
            [1, 108, 112, 113, 114],
        )
        fatiha = Surah.objects.get(number=1)
        self.assertEqual(fatiha.ayah_count, 7)
        self.assertEqual(len(fatiha.arabic.split("\n")), 7)
        self.assertEqual(len(fatiha.translation.split("\n")), 7)
        for row in [*Dua.objects.all(), *Surah.objects.all()]:
            with self.subTest(row=str(row)):
                row.full_clean(validate_unique=False, validate_constraints=False)
        self.assertTrue(Dua.objects.filter(reference="Quran 20:25-28").exists())


class PreferenceTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_patient()
        self.client.force_authenticate(self.patient.user)

    def tearDown(self):
        cache.clear()

    def test_off_by_default_on_then_off_deletes_the_record(self):
        self.assertEqual(self.client.get(PREF).json(), {"opted_in": False})
        r = self.client.put(PREF, {"opted_in": True}, format="json")
        self.assertEqual(r.json(), {"opted_in": True})
        self.assertTrue(
            ReligiousContentPreference.objects.filter(user=self.patient.user).exists()
        )
        r = self.client.put(PREF, {"opted_in": False}, format="json")
        self.assertEqual(r.json(), {"opted_in": False})
        self.assertFalse(ReligiousContentPreference.objects.exists())

    def test_validation_and_roles(self):
        self.assertEqual(
            self.client.put(PREF, {"opted_in": "maybe"}, format="json").status_code, 400
        )
        self.assertEqual(
            self.client.put(
                PREF, {"opted_in": True, "faith": "x"}, format="json"
            ).json(),
            {"faith": ["This field can't be set."]},
        )
        for user in (make_psychologist().user, make_admin()):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(PREF).status_code, 403)

    def test_never_logged(self):
        with self.assertNoLogs("mindcare", "INFO"):
            self.client.put(PREF, {"opted_in": True}, format="json")


class ContentAccessTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.patient = make_patient()
        self.client.force_authenticate(self.patient.user)

    def tearDown(self):
        cache.clear()

    def test_refused_until_opted_in(self):
        for url in (DUAS, SURAHS, f"{SURAHS}1/"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(r.json(), {"detail": OPT_IN_MESSAGE})

    def test_opted_in_patient_reads_duas_and_surahs(self):
        services.set_religious_opt_in(user=self.patient.user, opted_in=True)
        duas = self.client.get(DUAS).json()
        self.assertEqual(len(duas), 10)
        self.assertEqual(
            set(duas[0]),
            {
                "id",
                "title",
                "reference",
                "arabic",
                "transliteration",
                "translation",
                "audio_url",
            },
        )
        self.assertIsNone(duas[0]["audio_url"])
        detail = self.client.get(f"{DUAS}{duas[0]['id']}/").json()
        self.assertEqual(detail["id"], duas[0]["id"])
        surahs = self.client.get(SURAHS).json()
        self.assertEqual([s["number"] for s in surahs], [1, 108, 112, 113, 114])
        self.assertNotIn("arabic", surahs[0])
        fatiha = self.client.get(f"{SURAHS}1/").json()
        self.assertEqual(fatiha["name_english"], "Al-Faatiha")
        self.assertEqual(self.client.get(f"{SURAHS}2/").status_code, 404)

    def test_hidden_items_are_not_served(self):
        services.set_religious_opt_in(user=self.patient.user, opted_in=True)
        Surah.objects.filter(number=112).update(is_active=False)
        self.assertEqual(self.client.get(f"{SURAHS}112/").status_code, 404)
        self.assertNotIn(112, [s["number"] for s in self.client.get(SURAHS).json()])

    def test_psychologists_never(self):
        psych = make_psychologist()
        self.client.force_authenticate(psych.user)
        self.assertEqual(self.client.get(DUAS).status_code, 403)

    def test_quotes_endpoints_never_return_religious_content(self):
        services.set_religious_opt_in(user=self.patient.user, opted_in=True)
        quotes = self.client.get("/api/v1/motivation/quotes/?page_size=50").json()
        texts = {q["text"] for q in quotes["results"]}
        self.assertFalse(texts & set(Dua.objects.values_list("translation", flat=True)))


class AudioTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)
        cache.clear()

    def test_audio_is_served_with_a_signed_link(self):
        surah = Surah.objects.get(number=112)
        services.set_content_audio(
            content=surah, checked=check_audio(SimpleUploadedFile("r.mp3", MP3))
        )
        surah.refresh_from_db()
        self.assertEqual(surah.audio_type, "mp3")
        patient = make_patient()
        services.set_religious_opt_in(user=patient.user, opted_in=True)
        self.client.force_authenticate(patient.user)
        body = self.client.get(f"{SURAHS}112/").json()
        self.assertIn(surah.audio_key, body["audio_url"])
        self.assertTrue(
            [s for s in self.client.get(SURAHS).json() if s["number"] == 112][0][
                "has_audio"
            ]
        )

    def test_admin_form_checks_the_audio_by_content(self):
        from django.forms import modelform_factory

        dua = Dua.objects.first()
        form_class = modelform_factory(
            Dua, form=ReligiousContentForm, exclude=["audio_key", "audio_type"]
        )
        form = form_class(
            data={
                "title": dua.title,
                "reference": dua.reference,
                "arabic": dua.arabic,
                "translation": dua.translation,
                "sort_order": 1,
                "is_active": True,
            },
            files={"audio_upload": SimpleUploadedFile("r.mp3", b"%PDF-1.7\n%%EOF\n")},
            instance=dua,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["audio_upload"], ["Recitation must be one of: MP3, M4A, OGG."]
        )
