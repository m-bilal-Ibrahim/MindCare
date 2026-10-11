"""
Client for private file storage (credential documents, profile photos, audio).

Everything goes through Django's storage API (`django.core.files.storage`), so
the backend is chosen in settings: local disk in development and tests, a
private Supabase Storage bucket over its S3-compatible API in production
(django-storages + boto3; see config/settings/prod.py and docs/decisions.md,
2026-10-11). The bucket is private: files are reachable only through
short-lived signed URLs from signed_url(), which callers hand out after their
own permission (and, for sensitive files, audit) checks.

The database stores only the returned key, never file bytes.
"""

from django.conf import settings
from django.core.files.storage import default_storage

from core.files import check_upload


def save_private_file(upload, *, folder, label, allowed, max_mb):
    """Validate an upload (core.files.check_upload) and store it under
    `folder/<uuid>.<ext>`. Returns (key, checked) where `checked` carries the
    detected kind and the stored size. Raises django ValidationError."""
    checked = check_upload(upload, label=label, allowed=allowed, max_mb=max_mb)
    key = default_storage.save(f"{folder}/{checked.storage_name}", checked.content)
    return key, checked


def store_checked(checked, *, folder):
    """Store an upload that has already passed core.files.check_upload (e.g. in a
    serializer, so every file is validated before anything is written)."""
    return default_storage.save(f"{folder}/{checked.storage_name}", checked.content)


def signed_url(key, *, expires=None):
    """A URL that works for `expires` seconds (default SIGNED_URL_EXPIRY_SECONDS).
    On local disk this is just the media URL (development only)."""
    expires = expires or settings.SIGNED_URL_EXPIRY_SECONDS
    try:
        return default_storage.url(key, expire=expires)
    except TypeError:  # FileSystemStorage.url() takes no expiry
        return default_storage.url(key)


def delete_file(key):
    """Remove a stored file; a missing key is not an error."""
    if key:
        default_storage.delete(key)


def exists(key):
    return bool(key) and default_storage.exists(key)
