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
        user.reviewed_at = now()
        user.save(update_fields=["approval_status", "reviewed_at", "updated_at"])
        if decision == ApprovalStatus.REJECTED:
            end_for_unavailable_account(user=user)
        _send_review_email(user, decision, reason)
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


def _send_review_email(user, decision, reason):
    """Tell a psychologist or NGO the outcome; they can't find out otherwise."""
    from apps.notifications import emails
    from apps.notifications.services import send_email_after_commit

    if decision == ApprovalStatus.APPROVED:
        template = "account_approved"
        message = emails.account_approved(full_name=user.full_name, role=user.role)
    else:
        template = "account_rejected"
        message = emails.account_rejected(
            full_name=user.full_name,
            role=user.role,
            reason_label=dict(RejectReason.CHOICES).get(reason),
        )
    send_email_after_commit(template=template, to=user.email, message=message)


def deactivate_account(*, admin, user_id, reason=None):
    """Turn an account off: it can't log in or refresh, and its care
    relationships end (pending requests expire) and every refresh token is
    revoked. Admin accounts are managed by super-admins (deactivate_admin)."""
    from apps.relationships.services import end_for_unavailable_account

    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO})
        if not user.is_active:
            raise DomainValidationError(
                {"is_active": ["This account is already deactivated."]}
            )
        user.is_active = False
        user.deactivated_at = now()
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        end_for_unavailable_account(user=user)
        sign_out_everywhere(user=user)
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
        user.deactivated_at = None
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        transaction.on_commit(
            lambda: log_admin_event(
                event="account_reactivated", actor_id=admin.pk, target_user_id=user.pk
            )
        )
    return user


# --- Sessions and passwords ---------------------------------------------------


def sign_out_everywhere(*, user):
    """Revoke every refresh token the user holds (all devices). Access tokens
    still work until they expire (JWT_ACCESS_TOKEN_LIFETIME_MINUTES, 15 by
    default), except that JWTAuthentication refuses deactivated accounts at once."""
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    outstanding = OutstandingToken.objects.filter(
        user=user, blacklistedtoken__isnull=True
    )
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in outstanding],
        ignore_conflicts=True,
    )


class WrongCurrentPassword(Exception):
    """The current password given for a password change is wrong (400)."""


def change_password(*, user, current_password, new_password, ip=None):
    """Change the user's own password. Signs them out everywhere and clears
    must_change_password; the caller issues a fresh token pair for this device.
    `new_password` must already have passed Django's password validators."""
    if not user.check_password(current_password):
        raise WrongCurrentPassword()
    if current_password == new_password:
        raise DomainValidationError(
            {"new_password": ["Choose a password different from your current one."]}
        )
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        sign_out_everywhere(user=user)
        _send_password_changed_notice(user)
    log_auth_event(
        "password_changed", user_id=user.id, email=user.email, role=user.role, ip=ip
    )
    return user


def _send_password_changed_notice(user):
    from apps.notifications import emails
    from apps.notifications.services import send_email_after_commit

    send_email_after_commit(
        template="password_changed",
        to=user.email,
        message=emails.password_changed(full_name=user.full_name),
    )


# --- Password reset by emailed code (Phase 2, module 1) -----------------------
# docs/decisions.md, 2026-10-19. A 6-digit code, stored hashed, valid 15 minutes
# and 5 wrong tries; a new request supersedes the old code. The request always
# answers the same way, so it never tells anyone whether an account exists.

RESET_CODE_MINUTES = 15
RESET_MAX_FAILED_ATTEMPTS = 5
RESET_MAX_REQUESTS_PER_HOUR = 3
INVALID_RESET_CODE = "That code is wrong or has expired. Request a new one."


class InvalidResetCode(Exception):
    """Unknown email, no live code, wrong code, or too many tries: one answer for
    all of them (400 on `code`)."""


def _resettable_user(email):
    """Any active account in any role, pending ones included; never a
    deactivated or rejected one."""
    return (
        User.objects.filter(email__iexact=(email or "").strip(), is_active=True)
        .exclude(approval_status=ApprovalStatus.REJECTED)
        .first()
    )


def request_password_reset(*, email, ip=None):
    """Email a reset code if the address belongs to a resettable account that
    hasn't had 3 codes in the last hour. Returns nothing either way."""
    import secrets
    from datetime import timedelta

    from django.contrib.auth.hashers import make_password

    from apps.accounts.models import PasswordResetCode
    from apps.notifications import emails
    from apps.notifications.services import send_email_after_commit

    current = now()
    PasswordResetCode.objects.filter(
        created_at__lt=current - timedelta(days=1)
    ).delete()
    user = _resettable_user(email)
    if user is None:
        return
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        recent = PasswordResetCode.objects.filter(
            user=user, created_at__gte=current - timedelta(hours=1)
        ).count()
        if recent >= RESET_MAX_REQUESTS_PER_HOUR:
            return
        PasswordResetCode.objects.filter(user=user, closed_at__isnull=True).update(
            closed_at=current
        )
        code = f"{secrets.randbelow(10**6):06d}"
        PasswordResetCode.objects.create(
            user=user,
            code_hash=make_password(code),
            expires_at=current + timedelta(minutes=RESET_CODE_MINUTES),
        )
        send_email_after_commit(
            template="password_reset_code",
            to=user.email,
            message=emails.password_reset_code(
                full_name=user.full_name, code=code, minutes=RESET_CODE_MINUTES
            ),
        )
    log_auth_event(
        "password_reset_requested",
        user_id=user.id,
        email=user.email,
        role=user.role,
        ip=ip,
    )


def confirm_password_reset(*, email, code, new_password, ip=None):
    """Check the code and set the new password. A wrong code counts as a try
    (the 5th one kills the code); a right code with a password that breaks the
    rules isn't used up, so the person can pick another password. On success
    every session is signed out and a notice is emailed."""
    from django.contrib.auth.hashers import check_password
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError

    from apps.accounts.models import PasswordResetCode

    user = _resettable_user(email)
    if user is None:
        raise InvalidResetCode()
    current = now()
    with transaction.atomic():
        reset = (
            PasswordResetCode.objects.select_for_update()
            .filter(user=user, closed_at__isnull=True, expires_at__gt=current)
            .order_by("-created_at")
            .first()
        )
        if reset is None:
            raise InvalidResetCode()
        wrong = not check_password(code, reset.code_hash)
        if wrong:
            reset.failed_attempts += 1
            if reset.failed_attempts >= RESET_MAX_FAILED_ATTEMPTS:
                reset.closed_at = current
            reset.save(update_fields=["failed_attempts", "closed_at"])
    if wrong:  # raised outside the block, so the counted try is kept
        raise InvalidResetCode()

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise DomainValidationError({"new_password": list(exc.messages)}) from exc

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        # Lock again: another request may have used or replaced it meanwhile.
        if (
            not PasswordResetCode.objects.select_for_update()
            .filter(pk=reset.pk, closed_at__isnull=True, expires_at__gt=now())
            .exists()
        ):
            raise InvalidResetCode()
        PasswordResetCode.objects.filter(user=user, closed_at__isnull=True).update(
            closed_at=now()
        )
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        sign_out_everywhere(user=user)
        _send_password_changed_notice(user)
    log_auth_event(
        "password_reset", user_id=user.id, email=user.email, role=user.role, ip=ip
    )
    return user


# --- Super-admin workflow (Phase 2, module 0) ---------------------------------
# Only super-admins create, promote, demote, deactivate or reactivate admins.
# Invariants (docs/decisions.md, 2026-10-15): at least one active super-admin
# always exists (checked under a row lock), a super-admin demotes only
# themselves, a super-admin must be demoted before being deactivated, and nobody
# deactivates themselves.

ADMIN_GROUP_NAME = "MindCare admins"

# Ordinary admins in Django admin: edit motivation content and reference data,
# view (never change) accounts. Everything else stays with super-admins.
ADMIN_GROUP_PERMISSIONS = {
    "motivation": {
        "quote": ("add", "change", "delete", "view"),
        "dua": ("add", "change", "delete", "view"),
        "surah": ("add", "change", "delete", "view"),
    },
    "reference": {
        "city": ("add", "change", "view"),
        "country": ("view",),
        "language": ("add", "change", "view"),
        "specialization": ("add", "change", "view"),
    },
    "accounts": {"user": ("view",)},
}


class NotSuperAdmin(Exception):
    """The acting admin isn't an active super-admin (403)."""


def ensure_admin_group():
    """Create the 'MindCare admins' group, or bring its permissions up to date."""
    from django.contrib.auth.models import Group, Permission

    group, _ = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
    wanted = {
        (app, f"{action}_{model}")
        for app, models in ADMIN_GROUP_PERMISSIONS.items()
        for model, actions in models.items()
        for action in actions
    }
    permissions = [
        permission
        for permission in Permission.objects.filter(
            content_type__app_label__in=ADMIN_GROUP_PERMISSIONS
        ).select_related("content_type")
        if (permission.content_type.app_label, permission.codename) in wanted
    ]
    group.permissions.set(permissions)
    return group


def _require_super_admin(actor):
    if not (actor.role == Role.ADMIN and actor.is_super_admin and actor.is_active):
        raise NotSuperAdmin()


def generate_temporary_password():
    import secrets

    # 16 URL-safe characters (~96 bits). Shown once; must be changed at first use.
    return secrets.token_urlsafe(12)


def create_admin_account(*, actor, email, full_name):
    """A super-admin creates an ordinary admin with a one-time temporary
    password. Returns (user, temporary_password). The password is never stored
    or logged in plain text."""
    _require_super_admin(actor)
    email = email.lower()
    password = generate_temporary_password()
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=Role.ADMIN,
                approval_status=ApprovalStatus.APPROVED,
                is_staff=True,
                must_change_password=True,
            )
            user.groups.add(ensure_admin_group())
            transaction.on_commit(
                lambda: log_admin_event(
                    event="admin_created", actor_id=actor.pk, target_user_id=user.pk
                )
            )
    except IntegrityError as exc:
        if User.objects.filter(email__iexact=email).exists():
            raise DuplicateEmailError("A user with this email already exists.") from exc
        raise
    return user, password


def promote_admin(*, actor, user_id):
    """Make an active ordinary admin a super-admin (full Django admin too)."""
    _require_super_admin(actor)
    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.ADMIN})
        if user.is_super_admin:
            raise DomainValidationError(
                {"is_super_admin": ["This admin is already a super-admin."]}
            )
        if not user.is_active:
            raise DomainValidationError(
                {"is_active": ["Reactivate this admin before promoting them."]}
            )
        user.is_super_admin = True
        user.is_superuser = True
        user.save(update_fields=["is_super_admin", "is_superuser", "updated_at"])
        transaction.on_commit(
            lambda: log_admin_event(
                event="admin_promoted", actor_id=actor.pk, target_user_id=user.pk
            )
        )
    return user


def demote_self(*, actor):
    """A super-admin steps down to ordinary admin. Refused for the last active
    super-admin: every active super-admin row is locked first, so two
    super-admins demoting themselves at the same moment can't both succeed."""
    _require_super_admin(actor)
    with transaction.atomic():
        super_admins = list(
            User.objects.select_for_update()
            .filter(role=Role.ADMIN, is_super_admin=True, is_active=True)
            .order_by("pk")
        )
        me = next((u for u in super_admins if u.pk == actor.pk), None)
        if me is None:
            raise NotSuperAdmin()
        if len(super_admins) < 2:
            raise DomainValidationError(
                {
                    "is_super_admin": [
                        "You're the only super-admin. Promote another admin first."
                    ]
                }
            )
        me.is_super_admin = False
        me.is_superuser = False
        me.is_staff = True
        me.save(
            update_fields=["is_super_admin", "is_superuser", "is_staff", "updated_at"]
        )
        me.groups.add(ensure_admin_group())
        transaction.on_commit(
            lambda: log_admin_event(
                event="admin_demoted", actor_id=me.pk, target_user_id=me.pk
            )
        )
    return me


def deactivate_admin(*, actor, user_id):
    """Turn off an ordinary admin and revoke their sessions. A super-admin must
    demote themselves first, and nobody deactivates their own account."""
    _require_super_admin(actor)
    if int(user_id) == actor.pk:
        raise DomainValidationError(
            {"is_active": ["You can't deactivate your own account."]}
        )
    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.ADMIN})
        if user.is_super_admin:
            raise DomainValidationError(
                {
                    "is_active": [
                        "A super-admin can't be deactivated. They must demote "
                        "themselves first."
                    ]
                }
            )
        if not user.is_active:
            raise DomainValidationError(
                {"is_active": ["This admin is already deactivated."]}
            )
        user.is_active = False
        user.deactivated_at = now()
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        sign_out_everywhere(user=user)
        transaction.on_commit(
            lambda: log_admin_event(
                event="admin_deactivated", actor_id=actor.pk, target_user_id=user.pk
            )
        )
    return user


def reactivate_admin(*, actor, user_id):
    _require_super_admin(actor)
    with transaction.atomic():
        user = _lock_user(user_id, roles={Role.ADMIN})
        if user.is_active:
            raise DomainValidationError(
                {"is_active": ["This admin is already active."]}
            )
        user.is_active = True
        user.deactivated_at = None
        user.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        transaction.on_commit(
            lambda: log_admin_event(
                event="admin_reactivated", actor_id=actor.pk, target_user_id=user.pk
            )
        )
    return user
