from django.contrib import admin

from apps.audit.models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Read-only: nobody, not even a superuser, can add, edit or delete rows."""

    list_display = [
        "created_at",
        "actor_role",
        "actor_id",
        "action",
        "resource_type",
        "resource_id",
        "patient_user_id",
    ]
    list_filter = ["action", "resource_type", "actor_role"]
    search_fields = ["=actor_id", "=patient_user_id", "=resource_id"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
