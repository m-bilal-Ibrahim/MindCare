"""Django admin for Motivation Corner quotes. A quote added or reactivated here
is served by the API on the next request."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from apps.motivation.models import Dua, Quote, Surah
from apps.motivation.services import remove_content_audio, set_content_audio
from core.files import check_audio


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["text", "author", "category", "is_active", "created_at"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["text", "author"]
    actions = ["activate", "deactivate"]

    @admin.action(description="Show selected quotes in the app")
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} quote(s) shown in the app.")

    @admin.action(description="Hide selected quotes from the app")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} quote(s) hidden from the app.")


# --- Religious content (6.10) -------------------------------------------------
# The opt-in record (ReligiousContentPreference) is deliberately NOT registered:
# it reveals religious belief (GDPR Art. 9) and admins have no need to browse it.


class ReligiousContentForm(forms.ModelForm):
    """Adds an audio upload (checked by content, stored privately) and a way to
    remove the current recitation. Only use audio you have the rights to."""

    audio_upload = forms.FileField(
        required=False,
        label="Recitation audio",
        help_text="MP3, M4A or OGG, max 15 MB. Replaces the current recitation.",
    )
    remove_audio = forms.BooleanField(required=False, label="Remove current audio")

    def clean_audio_upload(self):
        upload = self.cleaned_data.get("audio_upload")
        if not upload:
            return None
        try:
            return check_audio(upload)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc


class _ReligiousAdmin(admin.ModelAdmin):
    form = ReligiousContentForm
    readonly_fields = ["audio_type", "created_at"]
    exclude = ["audio_key"]
    actions = ["activate", "deactivate"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        checked = form.cleaned_data.get("audio_upload")
        if checked:
            set_content_audio(content=obj, checked=checked)
        elif form.cleaned_data.get("remove_audio") and obj.audio_key:
            remove_content_audio(content=obj)

    @admin.display(boolean=True, description="Audio")
    def has_audio(self, obj):
        return bool(obj.audio_key)

    @admin.action(description="Show selected items in the app")
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} item(s) shown in the app.")

    @admin.action(description="Hide selected items from the app")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} item(s) hidden from the app.")


@admin.register(Dua)
class DuaAdmin(_ReligiousAdmin):
    list_display = ["title", "reference", "sort_order", "has_audio", "is_active"]
    list_editable = ["sort_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "reference"]


@admin.register(Surah)
class SurahAdmin(_ReligiousAdmin):
    list_display = ["number", "name_english", "ayah_count", "has_audio", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["is_active"]
    search_fields = ["name_english", "name_meaning"]
