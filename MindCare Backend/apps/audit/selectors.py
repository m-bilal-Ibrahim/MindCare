"""Read path for the access audit trail (admins only; used by the Django admin
today and by the 6.3 monitoring screens)."""

from apps.audit.models import AccessLog


def access_log_for_patient(*, patient_user_id):
    return AccessLog.objects.filter(patient_user_id=patient_user_id)
