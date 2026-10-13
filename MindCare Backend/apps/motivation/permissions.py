"""Permissions for the Motivation Corner."""

from rest_framework.permissions import BasePermission

from apps.motivation.selectors import has_opted_in_to_religious_content

OPT_IN_MESSAGE = (
    "Turn on Quran and dua content in your Motivation Corner settings to see this."
)


class HasReligiousOptIn(BasePermission):
    """Religious content only for patients who opted in (GDPR Art. 9 opt-in;
    docs/decisions.md, 2026-10-11). Use after IsPatient."""

    message = OPT_IN_MESSAGE

    def has_permission(self, request, view):
        return has_opted_in_to_religious_content(user=request.user)
