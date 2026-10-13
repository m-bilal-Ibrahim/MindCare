"""Read-path query logic for accounts.

Views call into these functions to fetch data. Object-level ownership
filtering (e.g. scoping a psychologist's queries to their own patients)
belongs here, not just in permission classes.
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ApprovalStatus, Role, User


def get_user_from_refresh_token(refresh_token):
    """Decode a refresh token and look up its owning user, or None if invalid."""
    try:
        token = RefreshToken(refresh_token)
    except TokenError:
        return None
    return User.objects.filter(pk=token["user_id"]).first()


# --- Admin monitoring (6.3) ---------------------------------------------------

ADMIN_STATUS_FILTERS = {
    "active": Q(is_active=True, approval_status=ApprovalStatus.APPROVED),
    "pending": Q(approval_status=ApprovalStatus.PENDING),
    "rejected": Q(approval_status=ApprovalStatus.REJECTED),
    "deactivated": Q(is_active=False),
}
SIGNUP_WEEKS = 12


def pending_accounts(*, role):
    """Pending psychologist / NGO applications, oldest first, with profiles and
    documents loaded for the review screen."""
    return (
        User.objects.filter(role=role, approval_status=ApprovalStatus.PENDING)
        .select_related(
            "psychologist_profile__license_issuing_country",
            "psychologist_profile__country",
            "psychologist_profile__city",
            "ngo_profile__registration_country",
            "ngo_profile__country",
            "ngo_profile__city",
        )
        .prefetch_related(
            "psychologist_profile__specializations",
            "psychologist_profile__languages",
            "psychologist_profile__documents",
            "ngo_profile__service_areas__country",
            "ngo_profile__service_areas__city",
        )
        .order_by("created_at", "id")
    )


def admin_users(*, role=None, status=None, search=None):
    """Every non-admin account for the admin Users page, newest first.

    Search never matches a patient's real name or email: patients are found by
    pseudonym only, so a search can't reveal who a private patient is.
    """
    qs = (
        User.objects.exclude(role=Role.ADMIN)
        .select_related("patient_profile", "psychologist_profile", "ngo_profile")
        .order_by("-created_at", "-id")
    )
    if role:
        qs = qs.filter(role=role)
    if status:
        qs = qs.filter(ADMIN_STATUS_FILTERS[status])
    if search:
        qs = qs.filter(
            Q(patient_profile__pseudonym__icontains=search)
            | (
                ~Q(role=Role.PATIENT)
                & (Q(full_name__icontains=search) | Q(email__icontains=search))
            )
        )
    return qs


def admin_user(*, user_id):
    return (
        User.objects.exclude(role=Role.ADMIN)
        .select_related("patient_profile", "psychologist_profile", "ngo_profile")
        .filter(pk=user_id)
        .first()
    )


def platform_overview():
    """Counts for the admin Overview. Numbers only: no names, no health data."""
    from apps.moderation.models import Report, ReportStatus
    from apps.relationships.models import CareRelationship

    by_role = {
        row["role"]: row
        for row in User.objects.exclude(role=Role.ADMIN)
        .values("role")
        .annotate(
            total=Count("id"),
            active=Count(
                "id", filter=Q(is_active=True, approval_status=ApprovalStatus.APPROVED)
            ),
            pending=Count("id", filter=Q(approval_status=ApprovalStatus.PENDING)),
            rejected=Count("id", filter=Q(approval_status=ApprovalStatus.REJECTED)),
            deactivated=Count("id", filter=Q(is_active=False)),
        )
    }
    roles = {}
    for role in (Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO):
        row = by_role.get(role, {})
        roles[role] = {
            key: row.get(key, 0)
            for key in ("total", "active", "pending", "rejected", "deactivated")
        }

    relationships = dict(
        CareRelationship.objects.values_list("status")
        .annotate(n=Count("id"))
        .values_list("status", "n")
    )

    since = timezone.now() - timedelta(weeks=SIGNUP_WEEKS)
    weekly = (
        User.objects.exclude(role=Role.ADMIN)
        .filter(created_at__gte=since)
        .annotate(week=TruncWeek("created_at"))
        .values("week", "role")
        .annotate(n=Count("id"))
        .order_by("week")
    )
    signups = {}
    for row in weekly:
        week = row["week"].date().isoformat()
        signups.setdefault(
            week, {"week_start": week, "patient": 0, "psychologist": 0, "ngo": 0}
        )
        signups[week][row["role"]] = row["n"]

    return {
        "users": roles,
        "pending_approvals": {
            "psychologist": roles[Role.PSYCHOLOGIST]["pending"],
            "ngo": roles[Role.NGO]["pending"],
        },
        "relationships": relationships,
        "open_reports": Report.objects.filter(status=ReportStatus.OPEN).count(),
        "weekly_signups": list(signups.values()),
    }
