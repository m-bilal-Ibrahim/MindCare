"""Django admin for users — the interim approval path for pending psychologist
and NGO accounts until Phase 2.5's approval endpoints.

Deliberately NOT editable here:
- password (use the manage.py changepassword command)
- is_superuser and is_super_admin (Phase 2.5 owns promote/demote and the
  at-least-one-super-admin invariant)
- role (read-only; changing it would leave a profile that doesn't match the role;
  users are created only through accounts.services.register_user(), which creates
  the role's profile in the same transaction)

Users cannot be added through this interface; users are created only through
accounts.services.register_user(). Admin accounts come from manage.py createsuperuser.

Deactivating or rejecting a user here ends their care relationships (moving a
psychologist back to pending only pauses them).
"""

from django.contrib import admin
from django.contrib import messages as messages_module

from apps.accounts.models import ApprovalStatus, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "full_name",
        "role",
        "approval_status",
        "is_active",
        "created_at",
    ]
    list_filter = ["role", "approval_status", "is_active"]
    search_fields = ["email", "full_name"]
    ordering = ["-created_at"]
    fields = [
        "email",
        "full_name",
        "role",
        "approval_status",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_super_admin",
        "adult_confirmed_at",
        "last_login",
        "created_at",
        "updated_at",
    ]
    readonly_fields = [
        "role",
        "is_superuser",
        "is_super_admin",
        "adult_confirmed_at",
        "last_login",
        "created_at",
        "updated_at",
    ]

    def has_add_permission(self, request):
        # Users are created only through accounts.services.register_user(), which
        # creates the role's profile in the same transaction ("every user has a
        # profile"). Admin accounts come from `manage.py createsuperuser`.
        return False

    def save_model(self, request, obj, form, change):
        """Approving or rejecting a pending application goes through the same
        service as the admin API (one rule set, audit line included). Every other
        change keeps the earlier behaviour: deactivating or rejecting ends care
        relationships, moving back to pending only pauses them."""
        changed = set(form.changed_data) if change else set()
        old_status = form.initial.get("approval_status")
        review = (
            "approval_status" in changed
            and old_status == ApprovalStatus.PENDING
            and obj.approval_status
            in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
        )
        decision = obj.approval_status
        if review:
            obj.approval_status = ApprovalStatus.PENDING  # the service applies it
        super().save_model(request, obj, form, change)
        if review:
            from apps.accounts.services import review_pending_account
            from core.exceptions import DomainValidationError

            try:
                review_pending_account(
                    admin=request.user, user_id=obj.pk, decision=decision
                )
            except DomainValidationError as exc:
                for messages in exc.errors.values():
                    for message in messages:
                        self.message_user(request, message, level=messages_module.ERROR)
            obj.refresh_from_db()
            return
        if change and {"is_active", "approval_status"} & changed:
            if not obj.is_active or obj.approval_status == ApprovalStatus.REJECTED:
                # Deactivated or rejected: end their relationships. Becoming
                # pending (re-review) is a pause and ends nothing.
                from apps.relationships.services import end_for_unavailable_account

                end_for_unavailable_account(user=obj)
