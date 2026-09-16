"""Write-path business logic for accounts.

Views call into these functions instead of touching the ORM or enforcing
business rules themselves. Anything that mutates state belongs here.
"""

from django.contrib.auth import authenticate

from apps.accounts.models import ApprovalStatus, Role, User
from core.audit import log_auth_event

ROLES_REQUIRING_APPROVAL = {Role.PSYCHOLOGIST, Role.NGO}


def register_user(*, email, password, full_name, role):
    approval_status = (
        ApprovalStatus.PENDING
        if role in ROLES_REQUIRING_APPROVAL
        else ApprovalStatus.APPROVED
    )
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=role,
        approval_status=approval_status,
    )
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


def authenticate_and_check_approval(*, email, password, ip=None):
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
