"""Write-path logic for the wellness library (6.9; docs/decisions.md,
2026-11-23).

Admins manage items (the API and Django admin share these rules through the
model). Field rules run on save() without update_fields, so the kind-specific
checks in WellnessItem.clean() always apply. Admin changes are logged as
structured lines with "wellnessitem:<id>" only, never the text, like quotes.
Favourites are private to the patient and not audited.
"""

from django.db import IntegrityError, transaction

from apps.wellness.models import MAX_FAVOURITES, WellnessFavourite, WellnessItem
from core.exceptions import DomainValidationError
from integrations.storage_client import client as storage

LINKED_CANT_DELETE = "This item has been used in a care plan. Hide it instead."
TOO_MANY_FAVOURITES = f"You can save up to {MAX_FAVOURITES} items."
NOT_PUBLISHED = "Choose a published item from the wellness library."


class NotFound(Exception):
    pass


def _log(event, actor, item):
    from core.audit import log_admin_event

    ref = f"wellnessitem:{item.pk}"
    transaction.on_commit(
        lambda: log_admin_event(event=event, actor_id=actor.pk, ref_id=ref)
    )


# --- admin: items ------------------------------------------------------------


def create_item(*, actor, data):
    with transaction.atomic():
        item = WellnessItem(**data)
        item.save()
        _log("content_created", actor, item)
    return item


def update_item(*, actor, item, data):
    if not data:
        return item
    with transaction.atomic():
        item = WellnessItem.objects.select_for_update().get(pk=item.pk)
        for field, value in data.items():
            setattr(item, field, value)
        item.save()  # full validation, including the kind rules
        _log("content_updated", actor, item)
    return item


def delete_item(*, actor, item):
    """Delete an item that no care-plan task has ever linked to. Its image and
    audio go after commit. Otherwise hide it (is_published=false)."""
    with transaction.atomic():
        item = WellnessItem.objects.select_for_update().get(pk=item.pk)
        if item.ever_linked or item.care_plan_tasks.exists():
            raise DomainValidationError({"non_field_errors": [LINKED_CANT_DELETE]})
        keys = [k for k in (item.image_key, item.audio_key) if k]
        _log("content_deleted", actor, item)
        item.delete()
        for key in keys:
            transaction.on_commit(lambda key=key: storage.delete_file(key))


def set_media(*, item, media, checked, actor=None):
    """Replace the item's image or audio ('image' / 'audio') with an upload
    already checked by core.files. The old file is deleted after commit."""
    key_field, type_field = f"{media}_key", f"{media}_type"
    with transaction.atomic():
        key = storage.replace_file(
            old_key=getattr(item, key_field),
            checked=checked,
            folder=f"wellness/{media}/{item.pk}",
        )
        try:
            setattr(item, key_field, key)
            setattr(item, type_field, checked.kind.extension)
            item.save(update_fields=[key_field, type_field, "updated_at"])
        except Exception:
            storage.delete_file(key)
            raise
        if actor is not None:
            _log("content_updated", actor, item)
    return item


def remove_media(*, item, media, actor=None):
    key_field, type_field = f"{media}_key", f"{media}_type"
    old_key = getattr(item, key_field)
    with transaction.atomic():
        setattr(item, key_field, "")
        setattr(item, type_field, "")
        item.save(update_fields=[key_field, type_field, "updated_at"])
        if old_key:
            transaction.on_commit(lambda: storage.delete_file(old_key))
        if actor is not None:
            _log("content_updated", actor, item)
    return item


# --- patient: favourites -----------------------------------------------------


def add_favourite(*, patient_profile, item_id):
    """Save a published item. Saving it again changes nothing."""
    with transaction.atomic():
        item = WellnessItem.objects.filter(pk=item_id, is_published=True).first()
        if item is None:
            raise NotFound()
        if WellnessFavourite.objects.filter(
            patient=patient_profile, item=item
        ).exists():
            return item
        # Lock the patient's row so two parallel saves can't pass the limit.
        type(patient_profile).objects.select_for_update().filter(
            pk=patient_profile.pk
        ).first()
        if (
            WellnessFavourite.objects.filter(patient=patient_profile).count()
            >= MAX_FAVOURITES
        ):
            raise DomainValidationError({"non_field_errors": [TOO_MANY_FAVOURITES]})
        try:
            with transaction.atomic():
                WellnessFavourite.objects.create(patient=patient_profile, item=item)
        except IntegrityError:
            pass  # saved by a parallel request
    return item


def remove_favourite(*, patient_profile, item_id):
    WellnessFavourite.objects.filter(patient=patient_profile, item_id=item_id).delete()


# --- care plan: linking ------------------------------------------------------


def item_for_link(item_id):
    """A published item a psychologist may link to a care-plan task, or a 400.
    Locks it so a parallel hide or delete waits."""
    item = (
        WellnessItem.objects.select_for_update()
        .filter(pk=item_id, is_published=True)
        .first()
    )
    if item is None:
        raise DomainValidationError({"content": [NOT_PUBLISHED]})
    return item


def mark_linked(item):
    """Remember the item was linked: from now on it can only be hidden."""
    if not item.ever_linked:
        # Not a user-entered field, so QuerySet.update() is fine here.
        WellnessItem.objects.filter(pk=item.pk).update(ever_linked=True)
        item.ever_linked = True
