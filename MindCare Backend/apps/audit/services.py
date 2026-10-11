"""Write path for the access audit trail.

record_access() must run in the SAME transaction as the access it records,
before the data is returned: if the audit row can't be written, the caller's
transaction fails and nothing is shown (fail closed; docs/decisions.md,
2026-10-11).
"""

from django.db import transaction

from apps.audit.models import AccessLog, AuditAction, AuditResource


def record_access(
    *, actor, action, resource_type, resource_id="", patient_user_id=None, ip=None
):
    if action not in AuditAction.values:
        raise ValueError(f"Unknown audit action: {action!r}")
    if resource_type not in AuditResource.values:
        raise ValueError(f"Unknown audit resource: {resource_type!r}")
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError(
            "record_access() must run inside the transaction of the access it records."
        )
    return AccessLog.objects.create(
        actor_id=getattr(actor, "pk", None),
        actor_role=getattr(actor, "role", "system") or "system",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id or ""),
        patient_user_id=patient_user_id,
        ip=ip,
    )
