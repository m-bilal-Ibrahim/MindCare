"""admin-panel-2: admin CRUD for quotes, duas and surahs, with recitation upload
checked by content (the same check as Django admin)."""

import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.motivation import services
from apps.motivation.models import Dua, Quote, Surah
from core.exceptions import DomainValidationError
from core.testing import make_admin, make_patient, make_psychologist

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64
BASE = "/api/v1/motivation/admin/"

DUA = {
    "title": "Dua for ease",
    "reference": "Quran 20:25-26",
    "arabic": "رَبِّ اشْرَحْ لِي صَدْرِي",
    "translation": "My Lord! Relieve my mind and ease my task for me.",
}
SURAH = {
    "number": 103,
    "name_arabic": "العصر",
    "name_english": "Al-Asr",
    "name_meaning": "The Declining Day",
    "ayah_count": 3,
    "arabic": "وَالْعَصْرِ\nإِنَّ الْإِنْسَانَ لَفِي خُسْرٍ",
    "translation": "By the declining day,\nLo! man is in a state of loss,",
}


class ContentServiceTests(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_create_update_delete_quote(self):
        quote = services.create_content(
            actor=self.admin,
            model=Quote,
            data={"text": "Small steps every day add up."},
        )
        services.update_content(
            actor=self.admin, content=quote, data={"is_active": False}
        )
        quote.refresh_from_db()
        self.assertFalse(quote.is_active)
        services.delete_content(actor=self.admin, content=quote)
        self.assertFalse(Quote.objects.filter(pk=quote.pk).exists())

    def test_model_rules_apply(self):
        with self.assertRaises(DomainValidationError):
            services.create_content(
                actor=self.admin, model=Quote, data={"text": "short"}
            )

    def test_duplicate_surah_number(self):
        existing = Surah.objects.first()
        with self.assertRaises(DomainValidationError) as ctx:
            services.create_content(
                actor=self.admin, model=Surah, data={**SURAH, "number": existing.number}
            )
        self.assertEqual(
            ctx.exception.errors,
            {"number": ["A surah with this number already exists."]},
        )


class AdminContentAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.client.force_authenticate(make_admin())

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)

    def test_quote_crud_includes_hidden(self):
        r = self.client.post(
            f"{BASE}quotes/",
            {
                "text": "  Rest is   part of the work.  ",
                "author": "",
                "category": "calm",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.json())
        quote_id = r.json()["id"]
        self.assertEqual(r.json()["text"], "Rest is part of the work.")
        self.assertTrue(r.json()["is_active"])

        r = self.client.patch(
            f"{BASE}quotes/{quote_id}/", {"is_active": False}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["is_active"])

        hidden = self.client.get(f"{BASE}quotes/", {"is_active": "false"}).json()
        self.assertIn(quote_id, [q["id"] for q in hidden["results"]])
        public = self.client.get("/api/v1/motivation/quotes/").json()
        self.assertNotIn(quote_id, [q["id"] for q in public["results"]])

        self.assertEqual(
            self.client.delete(f"{BASE}quotes/{quote_id}/").status_code, 204
        )
        self.assertEqual(self.client.get(f"{BASE}quotes/{quote_id}/").status_code, 404)

    def test_quote_validation(self):
        cases = [
            ({"text": "too short"}, "text"),
            ({"text": "<script>alert(1)</script> hello there"}, "text"),
            ({"text": "            "}, "text"),
            ({"text": "1234567890 !!!"}, "text"),
            ({"text": "A fine quote to keep.", "author": "R2D2"}, "author"),
            ({"text": "A fine quote to keep.", "category": "joy"}, "category"),
            ({"text": "A fine quote to keep.", "unknown": 1}, "unknown"),
        ]
        for body, field in cases:
            with self.subTest(body=body):
                r = self.client.post(f"{BASE}quotes/", body, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())

    def test_dua_crud_and_validation(self):
        r = self.client.post(f"{BASE}duas/", DUA, format="json")
        self.assertEqual(r.status_code, 201, r.json())
        self.assertFalse(r.json()["has_audio"])
        dua_id = r.json()["id"]
        r = self.client.patch(f"{BASE}duas/{dua_id}/", {"sort_order": 3}, format="json")
        self.assertEqual(r.json()["sort_order"], 3)
        cases = [
            ({**DUA, "title": "X"}, "title"),
            ({**DUA, "reference": "<b>"}, "reference"),
            ({**DUA, "translation": "short"}, "translation"),
            ({**DUA, "sort_order": -1}, "sort_order"),
            ({**DUA, "transliteration": "<i>x</i> words here"}, "transliteration"),
            ({k: v for k, v in DUA.items() if k != "arabic"}, "arabic"),
        ]
        for body, field in cases:
            with self.subTest(field=field):
                r = self.client.post(f"{BASE}duas/", body, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())

    def test_surah_crud_and_validation(self):
        Surah.objects.filter(number=103).delete()
        r = self.client.post(f"{BASE}surahs/", SURAH, format="json")
        self.assertEqual(r.status_code, 201, r.json())
        self.assertIn("\n", r.json()["arabic"])
        r = self.client.post(f"{BASE}surahs/", SURAH, format="json")
        self.assertEqual(
            r.json(), {"number": ["A surah with this number already exists."]}
        )
        for body, field in [
            ({**SURAH, "number": 115}, "number"),
            ({**SURAH, "number": 0}, "number"),
            ({**SURAH, "ayah_count": 287}, "ayah_count"),
            ({**SURAH, "name_english": "!!"}, "name_english"),
        ]:
            with self.subTest(field=field):
                r = self.client.post(f"{BASE}surahs/", body, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())

    def test_audio_upload_replace_and_remove(self):
        dua = Dua.objects.first()
        url = f"{BASE}duas/{dua.pk}/audio/"
        r = self.client.put(
            url, {"audio": SimpleUploadedFile("r.mp3", MP3)}, format="multipart"
        )
        self.assertEqual(r.status_code, 200, r.json())
        self.assertTrue(r.json()["has_audio"])
        self.assertEqual(r.json()["audio_type"], "mp3")
        self.assertIsNotNone(r.json()["audio_url"])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["has_audio"])
        self.assertEqual(self.client.delete(url).status_code, 400)

    def test_audio_checked_by_content(self):
        surah = Surah.objects.first()
        url = f"{BASE}surahs/{surah.pk}/audio/"
        for upload in (
            SimpleUploadedFile("fake.mp3", b"%PDF-1.4 not audio"),
            SimpleUploadedFile("empty.mp3", b""),
        ):
            with self.subTest(name=upload.name):
                r = self.client.put(url, {"audio": upload}, format="multipart")
                self.assertEqual(r.status_code, 400)
                self.assertIn("audio", r.json())
        r = self.client.put(url, {}, format="multipart")
        self.assertEqual(r.json(), {"audio": ["Choose an audio file to upload."]})

    def test_non_admins_refused(self):
        for user in (make_patient().user, make_psychologist().user):
            self.client.force_authenticate(user)
            for path in ("quotes/", "duas/", "surahs/"):
                self.assertEqual(self.client.get(f"{BASE}{path}").status_code, 403)
