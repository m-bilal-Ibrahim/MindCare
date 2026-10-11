"""Field encryption (core/encryption.py) and the deployment guards (core/checks.py)."""

import os
import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from core import checks
from core.encryption import (
    EncryptedTextField,
    _fernet,
    decrypt_text,
    encrypt_text,
)

BACKEND = Path(__file__).resolve().parents[2]
OTHER_KEY = Fernet.generate_key().decode()


class EncryptionTests(SimpleTestCase):
    def setUp(self):
        _fernet.cache_clear()

    def tearDown(self):
        _fernet.cache_clear()

    def test_round_trip_and_ciphertext_differs_each_time(self):
        a, b = (
            encrypt_text("Diagnosed with GAD in 2021"),
            encrypt_text("Diagnosed with GAD in 2021"),
        )
        self.assertNotEqual(a, b)
        self.assertNotIn("GAD", a)
        self.assertEqual(decrypt_text(a), "Diagnosed with GAD in 2021")

    def test_field_encrypts_on_write_and_decrypts_on_read(self):
        field = EncryptedTextField()
        token = field.get_prep_value("نوٹس: بے چینی")
        self.assertNotIn("بے", token)
        self.assertEqual(field.from_db_value(token, None, None), "نوٹس: بے چینی")
        self.assertEqual(field.get_prep_value(""), "")
        self.assertIsNone(field.from_db_value(None, None, None))

    def test_only_isnull_lookup_allowed(self):
        field = EncryptedTextField()
        self.assertIsNotNone(field.get_lookup("isnull"))
        for name in ("exact", "icontains", "startswith"):
            self.assertIsNone(field.get_lookup(name))

    def test_rotation_previous_key_still_decrypts(self):
        with override_settings(FIELD_ENCRYPTION_KEY=OTHER_KEY):
            _fernet.cache_clear()
            old_token = encrypt_text("written with the old key")
        new_key = Fernet.generate_key().decode()
        with override_settings(
            FIELD_ENCRYPTION_KEY=new_key, FIELD_ENCRYPTION_PREVIOUS_KEYS=[OTHER_KEY]
        ):
            _fernet.cache_clear()
            self.assertEqual(decrypt_text(old_token), "written with the old key")

    def test_wrong_key_fails_without_leaking(self):
        token = encrypt_text("secret history")
        with override_settings(FIELD_ENCRYPTION_KEY=OTHER_KEY):
            _fernet.cache_clear()
            with self.assertRaises(ImproperlyConfigured) as ctx:
                decrypt_text(token)
        self.assertNotIn("secret", str(ctx.exception))
        self.assertNotIn(token, str(ctx.exception))

    def test_missing_or_bad_key(self):
        for key in ("", "not-a-key"):
            with override_settings(FIELD_ENCRYPTION_KEY=key):
                _fernet.cache_clear()
                with self.assertRaises(ImproperlyConfigured):
                    encrypt_text("x")


class DeploymentCheckTests(SimpleTestCase):
    def setUp(self):
        _fernet.cache_clear()

    def tearDown(self):
        _fernet.cache_clear()

    def test_missing_key_fails_the_check_outside_debug(self):
        with override_settings(DEBUG=False, FIELD_ENCRYPTION_KEY=""):
            errors = checks.check_field_encryption_key(None)
        self.assertEqual([e.id for e in errors], ["mindcare.E001"])
        with override_settings(DEBUG=False):
            _fernet.cache_clear()
            self.assertEqual(checks.check_field_encryption_key(None), [])

    def test_local_disk_fails_the_check_when_object_storage_is_required(self):
        with override_settings(REQUIRE_OBJECT_STORAGE=True):
            errors = checks.check_object_storage(None)
        self.assertEqual([e.id for e in errors], ["mindcare.E002"])
        self.assertEqual(checks.check_object_storage(None), [])


def _prod_default_storage(extra_env):
    env = {**os.environ, "SECRET_KEY": "x", **extra_env}
    for name in list(env):
        if name.startswith("SUPABASE_S3_") and name not in extra_env:
            env.pop(name)
    code = (
        "import config.settings.prod as s; "
        "d = s.STORAGES['default']; "
        "print(d['BACKEND'], d.get('OPTIONS', {}).get('querystring_auth'), "
        "d.get('OPTIONS', {}).get('default_acl'))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


class ProdStorageSettingsTests(SimpleTestCase):
    def test_private_s3_bucket_when_configured(self):
        out = _prod_default_storage(
            {
                "SUPABASE_S3_BUCKET": "mindcare-private",
                "SUPABASE_S3_ENDPOINT": "https://x.supabase.co/storage/v1/s3",
                "SUPABASE_S3_REGION": "ap-south-1",
                "SUPABASE_S3_ACCESS_KEY_ID": "id",
                "SUPABASE_S3_SECRET_ACCESS_KEY": "secret",
            }
        )
        self.assertEqual(out, "storages.backends.s3.S3Storage True None")

    def test_local_disk_without_the_variables(self):
        out = _prod_default_storage({})
        self.assertTrue(out.startswith("django.core.files.storage.FileSystemStorage"))
