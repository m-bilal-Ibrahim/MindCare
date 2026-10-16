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


# --- Admin content management (admin-panel-2) ---------------------------------
# The admin console's CRUD for quotes, duas and surahs. Field rules run on the
# model (ValidatedModelMixin), so the API and Django admin enforce the same ones.
# Audit log lines carry only "<kind>:<id>", never the text.


def _log_content(event, actor, content):
    from core.audit import log_admin_event

    ref = f"{content._meta.model_name}:{content.pk}"
    transaction.on_commit(
        lambda: log_admin_event(event=event, actor_id=actor.pk, ref_id=ref)
    )


def _unique_errors(model, exc):
    from django.db import IntegrityError

    if model._meta.model_name == "surah" and isinstance(exc, IntegrityError):
        from core.exceptions import DomainValidationError

        return DomainValidationError(
            {"number": ["A surah with this number already exists."]}
        )
    return None


def create_content(*, actor, model, data):
    from django.db import IntegrityError

    try:
        with transaction.atomic():
            content = model(**data)
            content.save()
            _log_content("content_created", actor, content)
    except IntegrityError as exc:
        error = _unique_errors(model, exc)
        if error is None:
            raise
        raise error from exc
    return content


def update_content(*, actor, content, data):
    from django.db import IntegrityError

    if not data:
        return content
    try:
        with transaction.atomic():
            for field, value in data.items():
                setattr(content, field, value)
            content.save(update_fields=list(data))
            _log_content("content_updated", actor, content)
    except IntegrityError as exc:
        error = _unique_errors(type(content), exc)
        if error is None:
            raise
        raise error from exc
    return content


def delete_content(*, actor, content):
    """Delete a quote, dua or surah. Its recitation file goes after commit.
    To hide content without losing it, set is_active=false instead."""
    audio_key = getattr(content, "audio_key", "")
    with transaction.atomic():
        _log_content("content_deleted", actor, content)
        content.delete()
        if audio_key:
            transaction.on_commit(lambda: storage.delete_file(audio_key))


def set_content_audio_by_admin(*, actor, content, checked):
    with transaction.atomic():
        set_content_audio(content=content, checked=checked)
        _log_content("content_updated", actor, content)
    return content


def remove_content_audio_by_admin(*, actor, content):
    with transaction.atomic():
        remove_content_audio(content=content)
        _log_content("content_updated", actor, content)
    return content
