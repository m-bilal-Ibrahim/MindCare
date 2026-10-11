"""Write-path business logic for accounts.

Views call into these functions instead of touching the ORM or enforcing
business rules themselves. Anything that mutates state belongs here.
"""

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from apps.accounts.models import ApprovalStatus, Role, User
from apps.ngo.services import create_ngo_profile
from apps.patients.services import create_patient_profile
from apps.psychologists.services import (
    create_psychologist_profile,
    store_credential_documents,
)
from core.audit import log_admin_event, log_auth_event
from core.exceptions import DomainValidationError
from integrations.storage_client.client import delete_file

ROLES_REQUIRING_APPROVAL = {Role.PSYCHOLOGIST, Role.NGO}

# Direct calls, NOT signals: "every user has a profile, or neither exists" must
# be visible and testable (docs/decisions.md, 2026-09-26).
PROFILE_CREATORS = {
    Role.PATIENT: create_patient_profile,
    Role.PSYCHOLOGIST: create_psychologist_profile,
    Role.NGO: create_ngo_profile,
}


def register_user(
    *,
    email,
    password,
    full_name,
    role,
    is_adult_confirmed,
    profile_data,
    credential_documents=None,
):
    """Create the user and their role profile in one transaction. For a
    psychologist, `credential_documents` (DocumentKind -> [CheckedUpload],
    validated by the caller) are stored in the same transaction; if anything
    fails, no user, profile or file is left behind."""
    if is_adult_confirmed is not True:
        raise DomainValidationError(
            {"is_adult_confirmed": ["You must confirm you are 18 or older."]}
        )
    email = email.lower()
    approval_status = (
        ApprovalStatus.PENDING
        if role in ROLES_REQUIRING_APPROVAL
        else ApprovalStatus.APPROVED
    )
    stored_keys = []
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                approval_status=approval_status,
                adult_confirmed_at=now(),
            )
            profile = PROFILE_CREATORS[role](user=user, **profile_data)
            if credential_documents:
                stored_keys = store_credential_documents(
                    profile=profile, documents=credential_documents
                )
    except Exception as exc:
        # The transaction rolled back: remove files stored before the failure.
        for key in stored_keys:
            delete_file(key)
        if (
            isinstance(exc, IntegrityError)
            and User.objects.filter(email__iexact=email).exists()
        ):
            raise DuplicateEmailError("A user with this email already exists.") from exc
        raise
    log_auth_event("register", user_id=user.id, email=user.email, role=user.role)
    return user


class InvalidCredentialsError(Exception):
    """Raised when email/password don't match an active account."""


class AccountPendingApprovalError(Exception):
    """Raised when a psychologist/NGO account hasn't been approved yet."""

    def __init__(self, message="Your account is pending admin approval."):
        super().__init__(message)


class AccountRejectedError(Exception):
    """Raised when a psychologist/NGO account's application was rejected."""

    def __init__(self, message="Your account application was not approved."):
        super().__init__(message)


class DuplicateEmailError(Exception):
    """Raised when a race lets two registrations for the same email past the serializer's pre-check."""


def authenticate_and_check_approval(*, email, password, ip=None):
    email = email.lower()
    user = authenticate(username=email, password=password)
    if user is None:
        log_auth_event("login_failed", email=email, ip=ip, success=False)
        raise InvalidCredentialsError(
            "No active account found with the given credentials"
        )

    if user.approval_status == ApprovalStatus.PENDING:
        log_auth_event(
            "login_failed",
            user_id=user.id,
            email=email,
            role=user.role,
            ip=ip,
            success=False,
        )
        raise AccountPendingApprovalError()

    if user.approval_status == ApprovalStatus.REJECTED:
        log_auth_event(
            "login_failed",
            user_id=user.id,
            email=email,
            role=user.role,
            ip=ip,
            success=False,
        )
        raise AccountRejectedError()

    log_auth_event("login", user_id=user.id, email=user.email, role=user.role, ip=ip)
    return user


def record_token_refresh(*, user, ip=None):
    log_auth_event(
        "token_refresh", user_id=user.id, email=user.email, role=user.role, ip=ip
    )


def record_logout(*, user, ip=None):
    log_auth_event("logout", user_id=user.id, email=user.email, role=user.role, ip=ip)


# --- Admin account management (6.3) ------------------------------------------
# One service per decision, used by both the admin API and Django admin
# (docs/decisions.md, 2026-10-11, "option A"). No migration: the reject reason is
# recorded in the audit log line, not on the user.

REVIEWABLE_ROLES = {Role.PSYCHOLOGIST, Role.NGO}


class RejectReason:
    LICENSE_UNVERIFIED = "license_unverified"
    INCOMPLETE_DETAILS = "incomplete_details"
    NOT_ELIGIBLE = "not_eligible"
    OTHER = "other"
    CHOICES = [
        (LICENSE_UNVERIFIED, "License couldn't be verified"),
        (INCOMPLETE_DETAILS, "Details incomplete or incorrect"),
        (NOT_ELIGIBLE, "Not eligible"),
        (OTHER, "Other"),
    ]


class DeactivateReason:
    POLICY_VIOLATION = "policy_violation"
    REPORT_UPHELD = "report_upheld"
    USER_REQUEST = "user_request"
    OTHER = "other"
    CHOICES = [
        (POLICY_VIOLATION, "Broke platform policies"),
        (REPORT_UPHELD, "A report against them was upheld"),
        (USER_REQUEST, "The user asked for it"),
        (OTHER, "Other"),
    ]


class AccountNotFound(Exception):
    """No user with that id, or not a role this action applies to (404)."""


def _lock_user(user_id, *, roles=None):
    user = User.objects.select_for_update().filter(pk=user_id).first()
    if user is None or (roles is not None and user.role not in roles):
        raise AccountNotFound()
    return user


def review_pending_account(*, admin, user_id, decision, reason=None):
    """Approve or reject a pending psychologist / NGO account.

    decision: ApprovalStatus.APPROVED or ApprovalStatus.REJECTED. Locks the row so
    two admins can't act on the same application at once. A rejection ends the
    account's care relationships, exactly as Django admin always did.
    """
    if decision not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise ValueError(f"Not a review decision: {decision!r}")
    from apps.relationships.services import end_for_unavailable_account

    with transaction.atomic():
        user = _lock_user(user_id, roles=REVIEWABLE_ROLES)
        if user.approval_status != ApprovalStatus.PENDING:
            raise DomainValidationError(
                {"approval_status": ["This account isn't pending."]}
            )
        if not user.is_active:
            raise DomainValidationError(
                {
                    "approval_status": [
                        "This account is deactivated. Reactivate it before reviewing it."
                    ]
                }
            )
        user.approval_status = decision
        user.save(update_fields=["approval_status", "updated_at"])
        if decision == ApprovalStatus.REJECTED:
            end_for_unavailable_account(user=user)
        event = (
            "account_approved"
            if decision == ApprovalStatus.APPROVED
            else "account_rejected"
        )
        transaction.on_commit(
            lambda: log_admin_event(
                event=event,
                actor_id=admin.pk,
                target_user_id=user.pk,
                reason=reason,
            )
        )
    return user


def deactivate_account(*, admin, user_id, reason=None):
    """Turn an account off: it can't log in or refresh, and its care
    relationships end (pending requests expire). Admin accounts are managed only
    through Django admin and createsuperuser (super-admin workflow: Phase 2)."""
    from apps.relationships.services import end_for_unavailable_account

    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO})
        if not user.is_active:
            raise DomainValidationError(
                {"is_active": ["This account is already deactivated."]}
            )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        end_for_unavailable_account(user=user)
        transaction.on_commit(
            lambda: log_admin_event(
                event="account_deactivated",
                actor_id=admin.pk,
                target_user_id=user.pk,
                reason=reason,
            )
        )
    return user


def reactivate_account(*, admin, user_id):
    """Turn an account back on. Relationships that ended stay ended."""
    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO})
        if user.is_active:
            raise DomainValidationError(
                {"is_active": ["This account is already active."]}
            )
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        transaction.on_commit(
            lambda: log_admin_event(
                event="account_reactivated", actor_id=admin.pk, target_user_id=user.pk
            )
        )
    return user
