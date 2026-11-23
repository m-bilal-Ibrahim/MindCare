"""Django admin for the wellness library. Favourites are deliberately not
registered: what a patient saved is theirs. An item a care plan has ever linked
to can't be deleted here either, only hidden."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from apps.wellness.api.admin_serializers import check_cover, check_item_audio
from apps.wellness.models import WellnessItem
from apps.wellness.services import remove_media, set_media


class WellnessItemForm(forms.ModelForm):
    image_upload = forms.FileField(
        required=False,
        label="Cover image",
        help_text="JPG, PNG or WEBP, max 5 MB. Replaces the current image.",
    )
    remove_image = forms.BooleanField(required=False, label="Remove current image")
    audio_upload = forms.FileField(
        required=False,
        label="Audio",
        help_text="MP3, M4A or OGG, max 15 MB. Replaces the current audio.",
    )
    remove_audio = forms.BooleanField(required=False, label="Remove current audio")

    def _check(self, field, check):
        upload = self.cleaned_data.get(field)
        if not upload:
            return None
        try:
            return check(upload)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc

    def clean_image_upload(self):
        return self._check("image_upload", check_cover)

    def clean_audio_upload(self):
        return self._check("audio_upload", check_item_audio)


@admin.register(WellnessItem)
class WellnessItemAdmin(admin.ModelAdmin):
    form = WellnessItemForm
    list_display = [
        "title",
        "kind",
        "category",
        "duration_minutes",
        "sort_order",
        "is_published",
        "ever_linked",
    ]
    list_editable = ["sort_order", "is_published"]
    list_filter = ["is_published", "kind", "category", "difficulty"]
    search_fields = ["title", "summary"]
    readonly_fields = ["image_type", "audio_type", "ever_linked", "created_at"]
    exclude = ["image_key", "audio_key"]
    actions = ["publish", "hide"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for media in ("image", "audio"):
            checked = form.cleaned_data.get(f"{media}_upload")
            if checked:
                set_media(item=obj, media=media, checked=checked)
            elif form.cleaned_data.get(f"remove_{media}") and getattr(
                obj, f"{media}_key"
            ):
                remove_media(item=obj, media=media)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and (obj.ever_linked or obj.care_plan_tasks.exists()):
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        # Bulk delete would skip the "ever linked" rule; delete one at a time.
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    @admin.action(description="Publish selected items")
    def publish(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} item(s) published.")

    @admin.action(description="Hide selected items")
    def hide(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} item(s) hidden.")
