"""CORS origins: the deployed web origin always, extra origins only from the
CORS_EXTRA_ALLOWED_ORIGINS env var (never hardcoded for production)."""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BACKEND = Path(__file__).resolve().parents[2]
VERCEL = "https://mind-care-web-seven.vercel.app"


def _origins(module, extra=None):
    env = {**os.environ, "SECRET_KEY": os.environ.get("SECRET_KEY", "x")}
    env.pop("CORS_EXTRA_ALLOWED_ORIGINS", None)
    if extra is not None:
        env["CORS_EXTRA_ALLOWED_ORIGINS"] = extra
    code = f"import {module} as s; print('|'.join(s.CORS_ALLOWED_ORIGINS))"
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip().split("|")


class CorsSettingsTests(SimpleTestCase):
    def test_prod_defaults_to_the_vercel_origin_only(self):
        self.assertEqual(_origins("config.settings.prod"), [VERCEL])

    def test_prod_adds_env_origins_and_keeps_vercel(self):
        self.assertEqual(
            _origins(
                "config.settings.prod", "http://localhost:5000,http://127.0.0.1:5000"
            ),
            [VERCEL, "http://localhost:5000", "http://127.0.0.1:5000"],
        )

    def test_dev_allows_the_local_web_and_flutter_web_servers(self):
        origins = _origins("config.settings.dev")
        self.assertIn("http://localhost:5173", origins)
        self.assertIn("http://localhost:5000", origins)
