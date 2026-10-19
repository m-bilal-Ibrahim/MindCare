"""MindCare's Django admin site (`/admin/`).

Same as Django's, except that an account still on the temporary password a
super-admin gave it can't sign in or keep using a session until it changes the
password in the admin console (docs/decisions.md, 2026-10-19). Wired in through
config.apps.MindCareAdminConfig, so every `@admin.register` lands here.
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm

TEMPORARY_PASSWORD_MESSAGE = (
    "Change your temporary password in the MindCare admin console before "
    "signing in here."
)


class MindCareAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.must_change_password:
            raise forms.ValidationError(
                TEMPORARY_PASSWORD_MESSAGE, code="password_change_required"
            )


class MindCareAdminSite(admin.AdminSite):
    login_form = MindCareAdminAuthenticationForm

    def has_permission(self, request):
        return super().has_permission(request) and not getattr(
            request.user, "must_change_password", False
        )
