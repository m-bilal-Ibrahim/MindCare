"""Write-path logic for the Motivation Corner.

6.10 religious content (docs/decisions.md, 2026-10-11): the opt-in is special-
category data (GDPR Art. 9), so it is stored only while true and deleted on
opt-out, and it is never logged. Audio is admin-uploaded, checked by content and
stored privately.
"""

from django.db import transaction

from apps.accounts.models import Role
from apps.motivation.models import ReligiousContentPreference
from integrations.storage_client import client as storage


def set_religious_opt_in(*, user, opted_in):
    """Opt a patient in or out. Opting out deletes the record."""
    if user.role != Role.PATIENT:
        raise PermissionError("Only patients can opt in to religious content.")
    if opted_in:
        ReligiousContentPreference.objects.get_or_create(user=user)
    else:
        ReligiousContentPreference.objects.filter(user=user).delete()
    return opted_in


def set_content_audio(*, content, checked):
    """Replace a dua's or surah's recitation with an upload already checked by
    core.files.check_audio. The old file is deleted after commit."""
    with transaction.atomic():
        key = storage.replace_file(
            old_key=content.audio_key,
            checked=checked,
            folder=f"audio/{content._meta.model_name}/{content.pk}",
        )
        try:
            content.audio_key = key
            content.audio_type = checked.kind.extension
            content.save(update_fields=["audio_key", "audio_type"])
        except Exception:
            storage.delete_file(key)
            raise
    return content


def remove_content_audio(*, content):
    old_key = content.audio_key
    with transaction.atomic():
        content.audio_key = ""
        content.audio_type = ""
        content.save(update_fields=["audio_key", "audio_type"])
        if old_key:
            transaction.on_commit(lambda: storage.delete_file(old_key))
    return content
