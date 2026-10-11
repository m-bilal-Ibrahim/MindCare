"""6.2: psychologists upload their license and degree with the registration
request (multipart), validated by content and stored privately
(docs/decisions.md, 2026-10-11)."""

import json
import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User
from apps.psychologists.models import CredentialDocument, DocumentKind
from core.testing import make_psychologist, register_payload

REGISTER_URL = "/api/v1/accounts/register/"
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def pdf(name="file.pdf", data=PDF):
    return SimpleUploadedFile(name, data, content_type="application/pdf")


class CredentialDocumentAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media, ignore_errors=True)
        cache.clear()

    def register(self, files, role=Role.PSYCHOLOGIST, **overrides):
        payload = register_payload(role=role, **overrides)
        return self.client.post(
            REGISTER_URL,
            {"data": json.dumps(payload), **files},
            format="multipart",
        ), payload

    def stored_files(self):
        found = []
        for root, _, names in __import__("os").walk(self.media):
            found += names
        return found

    def test_license_and_degree_are_stored_privately(self):
        r, payload = self.register(
            {
                "license_document": pdf("my licence.pdf"),
                "degree_document": pdf("degree.pdf"),
                "other_documents": [pdf("a.pdf"), pdf("b.pdf")],
            }
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.json())
        user = User.objects.get(email=payload["email"])
        self.assertEqual(user.approval_status, ApprovalStatus.PENDING)
        docs = CredentialDocument.objects.filter(profile=user.psychologist_profile)
        self.assertEqual(
            sorted(docs.values_list("kind", flat=True)),
            [
                DocumentKind.DEGREE,
                DocumentKind.LICENSE,
                DocumentKind.OTHER,
                DocumentKind.OTHER,
            ],
        )
        for doc in docs:
            self.assertTrue(
                doc.storage_key.startswith(
                    f"credentials/{user.psychologist_profile.pk}/"
                )
            )
            self.assertNotIn("licence", doc.storage_key)
            self.assertTrue(default_storage.exists(doc.storage_key))
            self.assertEqual(doc.file_type, "pdf")
        # The response lists the documents without any key or URL.
        listed = r.json()["profile"]["documents"]
        self.assertEqual(len(listed), 4)
        self.assertEqual(
            set(listed[0]), {"id", "kind", "file_type", "size", "uploaded_at"}
        )

    def test_license_and_degree_are_required(self):
        r, payload = self.register({})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "license_document": ["Upload your license document."],
                "degree_document": ["Upload your degree certificate."],
            },
        )
        self.assertFalse(User.objects.filter(email=payload["email"]).exists())

    def test_json_psychologist_registration_needs_the_files(self):
        r = self.client.post(
            REGISTER_URL, register_payload(role=Role.PSYCHOLOGIST), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("license_document", r.json())

    def test_type_is_checked_by_content(self):
        r, payload = self.register(
            {
                "license_document": pdf(
                    "license.pdf", b"<html><script>x</script></html>"
                ),
                "degree_document": pdf(),
            }
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {"license_document": ["License document must be one of: PDF, JPG, PNG."]},
        )
        self.assertFalse(User.objects.filter(email=payload["email"]).exists())
        self.assertEqual(self.stored_files(), [])

    def test_size_limit_and_empty_file(self):
        big = pdf("big.pdf", PDF + b"0" * (5 * 1024 * 1024))
        r, _ = self.register({"license_document": big, "degree_document": pdf()})
        self.assertEqual(
            r.json(),
            {"license_document": ["License document must be 5 MB or smaller."]},
        )
        r, _ = self.register(
            {"license_document": pdf(), "degree_document": pdf("empty.pdf", b"")}
        )
        self.assertEqual(
            r.json(), {"degree_document": ["Degree certificate is empty."]}
        )

    def test_at_most_three_other_documents(self):
        r, _ = self.register(
            {
                "license_document": pdf(),
                "degree_document": pdf(),
                "other_documents": [pdf() for _ in range(4)],
            }
        )
        self.assertEqual(
            r.json(), {"other_documents": ["Upload at most 3 other documents."]}
        )

    def test_files_are_refused_for_other_roles(self):
        r, _ = self.register({"license_document": pdf()}, role=Role.PATIENT)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"license_document": ["This field can't be set."]})

    def test_unknown_file_field_refused(self):
        r, _ = self.register(
            {"license_document": pdf(), "degree_document": pdf(), "selfie": pdf()}
        )
        self.assertEqual(r.json(), {"selfie": ["This field can't be set."]})

    def test_malformed_data_part(self):
        r = self.client.post(
            REGISTER_URL,
            {"data": "{not json", "license_document": pdf()},
            format="multipart",
        )
        self.assertEqual(
            r.json(),
            {"data": ["Send the registration details as JSON in the 'data' field."]},
        )

    def test_files_are_removed_when_registration_fails_later(self):
        make_psychologist(license_number="PMDC-12345")  # same license as the payload
        r, payload = self.register(
            {"license_document": pdf(), "degree_document": pdf()}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("license_number", r.json()["profile"])
        self.assertFalse(User.objects.filter(email=payload["email"]).exists())
        self.assertEqual(self.stored_files(), [])

    def test_owner_sees_their_documents_on_me(self):
        r, payload = self.register(
            {"license_document": pdf(), "degree_document": pdf()}
        )
        user = User.objects.get(email=payload["email"])
        self.client.force_authenticate(user)
        me = self.client.get("/api/v1/psychologists/me/").json()
        self.assertEqual(
            sorted(d["kind"] for d in me["documents"]), ["degree", "license"]
        )
        self.assertNotIn("storage_key", json.dumps(me))
