"""Deployment guards, registered by apps.audit (core is not a Django app).

`migrate` runs system checks, and Render's build runs `migrate`, so an Error
here fails the build and Render keeps serving the previous version instead of
starting a production service that would lose uploads or can't encrypt.
"""

from django.conf import settings
from django.core.checks import Error, register


@register()
def check_field_encryption_key(app_configs, **kwargs):
    from django.core.exceptions import ImproperlyConfigured

    from core.encryption import get_fernet

    if settings.DEBUG:
        return []
    try:
        get_fernet()
    except ImproperlyConfigured as exc:
        return [
            Error(
                str(exc),
                hint=(
                    'Generate one with: python -c "from cryptography.fernet import '
                    'Fernet; print(Fernet.generate_key().decode())" and set it as '
                    "FIELD_ENCRYPTION_KEY. Keep a copy in a password manager."
                ),
                id="mindcare.E001",
            )
        ]
    return []


@register()
def check_object_storage(app_configs, **kwargs):
    if not getattr(settings, "REQUIRE_OBJECT_STORAGE", False):
        return []
    backend = settings.STORAGES["default"]["BACKEND"]
    if backend.endswith("FileSystemStorage"):
        return [
            Error(
                "Uploads would be stored on the server's temporary disk.",
                hint=(
                    "Set SUPABASE_S3_BUCKET, SUPABASE_S3_ENDPOINT, SUPABASE_S3_REGION, "
                    "SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY."
                ),
                id="mindcare.E002",
            )
        ]
    return []
