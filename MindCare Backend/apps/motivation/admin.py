"""Django admin for Motivation Corner quotes. A quote added or reactivated here
is served by the API on the next request."""

from django.contrib import admin

from apps.motivation.models import Quote


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
