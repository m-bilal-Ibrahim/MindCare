"""Django admin for psychologist profiles. Credential fields ARE editable here:
this is the interim correction path until Phase 2.5's re-review flow."""

from django import forms
from django.contrib import admin

from apps.psychologists.models import CredentialDocument, PsychologistProfile
from core.validators import normalize_display_text, normalize_identifier


class PsychologistProfileAdminForm(forms.ModelForm):
    """Same normalization as the service layer, so a value corrected here still
    matches what the API's locked-credential comparison expects."""

    class Meta:
        model = PsychologistProfile
        fields = "__all__"

    def clean_license_number(self):
        return normalize_identifier(self.cleaned_data["license_number"])

    def clean_license_issuing_authority(self):
        return normalize_display_text(self.cleaned_data["license_issuing_authority"])

    def clean_qualifications(self):
        return self.cleaned_data["qualifications"].strip()


class CredentialDocumentInline(admin.TabularInline):
    """Which credential files were uploaded. Read-only, and no file link here:
    opening a file goes through the audited admin review endpoint (6.3)."""

    model = CredentialDocument
    fields = ["kind", "file_type", "size", "uploaded_at"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PsychologistProfile)
class PsychologistProfileAdmin(admin.ModelAdmin):
    form = PsychologistProfileAdminForm
    inlines = [CredentialDocumentInline]
    list_display = [
        "user",
        "license_number",
        "license_issuing_country",
        "country",
        "created_at",
    ]
    list_filter = ["license_issuing_country", "country"]
    search_fields = ["user__email", "user__full_name", "license_number"]
    autocomplete_fields = ["license_issuing_country", "country", "city"]
    filter_horizontal = ["specializations", "languages"]
    readonly_fields = ["user", "created_at", "updated_at"]

    def has_add_permission(self, request):
        # Profiles are created only by register_user(), never in admin.
        return False
