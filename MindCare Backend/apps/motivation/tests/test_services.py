"""Service-layer tests for the Motivation Corner (6.10)."""

import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.motivation import services
from apps.motivation.models import ReligiousContentPreference, Surah
from core.files import check_audio
from core.testing import make_patient, make_psychologist

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


class OptInTests(TestCase):
    def test_opt_in_creates_and_opt_out_deletes(self):
        user = make_patient().user
        services.set_religious_opt_in(user=user, opted_in=True)
        services.set_religious_opt_in(user=user, opted_in=True)  # idempotent
        self.assertEqual(
            ReligiousContentPreference.objects.filter(user=user).count(), 1
        )
        services.set_religious_opt_in(user=user, opted_in=False)
        self.assertFalse(ReligiousContentPreference.objects.filter(user=user).exists())

    def test_only_patients(self):
        with self.assertRaises(PermissionError):
            services.set_religious_opt_in(user=make_psychologist().user, opted_in=True)


class AudioServiceTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)

    def files(self):
        return [n for _, _, names in os.walk(self.media) for n in names]

    def test_replace_then_remove(self):
        surah = Surah.objects.get(number=1)
        with self.captureOnCommitCallbacks(execute=True):
            services.set_content_audio(
                content=surah, checked=check_audio(SimpleUploadedFile("a.mp3", MP3))
            )
        with self.captureOnCommitCallbacks(execute=True):
            services.set_content_audio(
                content=surah, checked=check_audio(SimpleUploadedFile("b.mp3", MP3))
            )
        self.assertEqual(len(self.files()), 1)  # the old recitation was deleted
        with self.captureOnCommitCallbacks(execute=True):
            services.remove_content_audio(content=surah)
        surah.refresh_from_db()
        self.assertEqual((surah.audio_key, surah.audio_type), ("", ""))
        self.assertEqual(self.files(), [])
