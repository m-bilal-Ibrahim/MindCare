"""Django admin for SOS helplines and hospitals (6.12). Only add numbers you have
verified: they are shown to patients in a crisis.

SOS events and emergency contacts are deliberately NOT registered: contacts are
third parties' encrypted data, and opening an alert must go through the audited
admin API (`/api/v1/emergency/admin/sos/`)."""

from django.contrib import admin

from apps.emergency.models import Helpline, Hospital


@admin.register(Helpline)
class HelplineAdmin(admin.ModelAdmin):
    list_display = ["name", "number", "country", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active", "country"]
    search_fields = ["name", "number"]
    autocomplete_fields = ["country"]


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "city", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "city__country"]
    search_fields = ["name", "city__name"]
    autocomplete_fields = ["city"]
