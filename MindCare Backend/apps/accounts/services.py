"""Write-path business logic for accounts.

Views call into these functions instead of touching the ORM or enforcing
business rules themselves. Anything that mutates state belongs here.
"""

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
