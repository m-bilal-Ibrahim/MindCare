from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Access audit trail"

    def ready(self):
        # Deployment guards for storage and encryption (core is not an app, so
        # its checks are registered here).
        from core import checks  # noqa: F401
