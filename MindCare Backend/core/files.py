"""Upload checks shared by every app that accepts files (docs/validation-rules.md,
"File uploads").

- The type is detected from the file's first bytes (magic bytes), never from the
  extension or the browser's Content-Type.
- The stored name is a random UUID plus the detected extension; the uploaded
  filename is never used as a path.
- Images are re-encoded with Pillow, which drops EXIF (GPS location, camera
  serial numbers) and anything appended after the image data, and refuses
  decompression bombs.
"""

import io
import uuid
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

MB = 1024 * 1024
# Pillow refuses images above this many pixels (default ~89M); 40M is plenty for
# a profile photo or a scanned certificate and keeps memory use bounded.
MAX_IMAGE_PIXELS = 40_000_000


@dataclass(frozen=True)
class FileKind:
    name: str  # shown to users, e.g. "PDF"
    extension: str
    content_type: str
    is_image: bool = False


PDF = FileKind("PDF", "pdf", "application/pdf")
JPEG = FileKind("JPG", "jpg", "image/jpeg", is_image=True)
PNG = FileKind("PNG", "png", "image/png", is_image=True)
WEBP = FileKind("WEBP", "webp", "image/webp", is_image=True)
MP3 = FileKind("MP3", "mp3", "audio/mpeg")
M4A = FileKind("M4A", "m4a", "audio/mp4")
OGG = FileKind("OGG", "ogg", "audio/ogg")


def detect_kind(head):
    """The FileKind for these leading bytes, or None."""
    if head.startswith(b"%PDF-"):
        return PDF
    if head.startswith(b"\xff\xd8\xff"):
        return JPEG
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return PNG
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return WEBP
    if head.startswith(b"ID3") or (
        len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
    ):
        return MP3
    if head[4:8] == b"ftyp" and head[8:12] in (b"M4A ", b"mp42", b"isom", b"M4B "):
        return M4A
    if head.startswith(b"OggS"):
        return OGG
    return None


@dataclass
class CheckedUpload:
    content: ContentFile  # what to store (images re-encoded)
    kind: FileKind
    size: int

    @property
    def storage_name(self):
        return f"{uuid.uuid4().hex}.{self.kind.extension}"


def check_upload(upload, *, label, allowed, max_mb):
    """Validate an uploaded file and return what to store.

    Raises django ValidationError with the messages in validation-rules.md.
    `allowed` is a sequence of FileKind; `max_mb` the size limit in MB.
    """
    size = getattr(upload, "size", None)
    if not size:
        raise ValidationError(f"{label} is empty.", code="empty")
    if size > max_mb * MB:
        raise ValidationError(
            f"{label} must be {max_mb} MB or smaller.", code="too_big"
        )

    upload.seek(0)
    head = upload.read(16)
    upload.seek(0)
    kind = detect_kind(head)
    if kind not in allowed:
        names = ", ".join(k.name for k in allowed)
        raise ValidationError(f"{label} must be one of: {names}.", code="file_type")

    data = upload.read()
    if kind.is_image:
        data = _reencode_image(data, kind, label=label)
    return CheckedUpload(content=ContentFile(data), kind=kind, size=len(data))


def _reencode_image(data, kind, *, label):
    from PIL import Image, ImageOps

    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    invalid = ValidationError(f"{label} isn't a readable image.", code="bad_image")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()  # structure check; the image must be reopened after
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)  # keep orientation, drop EXIF
            out = io.BytesIO()
            if kind is JPEG:
                image.convert("RGB").save(out, format="JPEG", quality=90)
            elif kind is PNG:
                image.save(out, format="PNG")
            else:
                image.save(out, format="WEBP", quality=90)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError(
            f"{label} is too large in pixels.", code="too_many_pixels"
        ) from exc
    except Exception as exc:  # any Pillow decode error means "not an image"
        raise invalid from exc
    return out.getvalue()
