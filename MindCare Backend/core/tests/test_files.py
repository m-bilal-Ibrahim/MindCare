"""Upload checks (core/files.py): type by magic bytes, size, EXIF removal."""

import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from core.files import JPEG, MP3, PDF, PNG, check_upload, detect_kind

PDF_BYTES = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def jpeg_with_gps():
    image = Image.new("RGB", (40, 30), "red")
    exif = Image.Exif()
    exif[0x8825] = {2: (33.0, 41.0, 0.0), 4: (73.0, 3.0, 0.0)}  # GPSInfo
    exif[0x010F] = "PhoneMaker"  # camera make
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def png_bytes():
    out = io.BytesIO()
    Image.new("RGB", (10, 10), "blue").save(out, format="PNG")
    return out.getvalue()


def upload(name, data, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, data, content_type=content_type)


class DetectKindTests(SimpleTestCase):
    def test_signatures(self):
        self.assertIs(detect_kind(PDF_BYTES[:16]), PDF)
        self.assertIs(detect_kind(png_bytes()[:16]), PNG)
        self.assertIs(detect_kind(jpeg_with_gps()[:16]), JPEG)
        self.assertIs(detect_kind(b"ID3\x04\x00" + b"\x00" * 11), MP3)
        self.assertIsNone(detect_kind(b"<html><body>hi"))
        self.assertIsNone(detect_kind(b"MZ\x90\x00"))  # a Windows executable


class CheckUploadTests(SimpleTestCase):
    def check(self, f, allowed=(PDF, JPEG, PNG), max_mb=5):
        return check_upload(f, label="License", allowed=allowed, max_mb=max_mb)

    def test_valid_pdf(self):
        checked = self.check(upload("licence.pdf", PDF_BYTES))
        self.assertIs(checked.kind, PDF)
        self.assertTrue(checked.storage_name.endswith(".pdf"))
        self.assertNotIn("licence", checked.storage_name)

    def test_type_comes_from_content_not_extension(self):
        # A PDF named .png with an image content type is still a PDF...
        checked = self.check(upload("photo.png", PDF_BYTES, "image/png"))
        self.assertIs(checked.kind, PDF)
        # ...and an HTML page named .pdf is refused.
        with self.assertRaises(ValidationError) as ctx:
            self.check(
                upload("licence.pdf", b"<html><script>x</script>", "application/pdf")
            )
        self.assertEqual(
            ctx.exception.messages, ["License must be one of: PDF, JPG, PNG."]
        )

    def test_wrong_type_for_this_field(self):
        with self.assertRaises(ValidationError) as ctx:
            self.check(upload("x.pdf", PDF_BYTES), allowed=(JPEG, PNG))
        self.assertEqual(ctx.exception.messages, ["License must be one of: JPG, PNG."])

    def test_too_big_and_empty(self):
        with self.assertRaises(ValidationError) as ctx:
            self.check(upload("big.pdf", PDF_BYTES + b"0" * (1024 * 1024)), max_mb=1)
        self.assertEqual(ctx.exception.messages, ["License must be 1 MB or smaller."])
        with self.assertRaises(ValidationError) as ctx:
            self.check(upload("empty.pdf", b""))
        self.assertEqual(ctx.exception.messages, ["License is empty."])

    def test_jpeg_exif_and_gps_are_removed(self):
        original = jpeg_with_gps()
        self.assertIn(0x8825, Image.open(io.BytesIO(original)).getexif())
        checked = self.check(upload("me.jpg", original))
        cleaned = Image.open(io.BytesIO(checked.content.read()))
        self.assertEqual(dict(cleaned.getexif()), {})
        self.assertEqual(cleaned.size, (40, 30))

    def test_corrupt_image_refused(self):
        with self.assertRaises(ValidationError) as ctx:
            self.check(upload("x.jpg", b"\xff\xd8\xff\xe0" + b"garbage" * 10))
        self.assertEqual(ctx.exception.messages, ["License isn't a readable image."])

    def test_data_appended_after_an_image_is_dropped(self):
        payload = png_bytes() + b"<?php system($_GET['c']); ?>"
        checked = self.check(upload("x.png", payload))
        self.assertNotIn(b"<?php", checked.content.read())
