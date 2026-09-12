"""
PHI-safe access logging.

Eventually this module will provide helpers (e.g. `log_access(user,
resource, action)`) that record who accessed or changed sensitive
data (patient records, journals, clinical notes) without ever writing
the PHI itself (patient names, journal content, health data) into
plaintext application logs. All access to sensitive resources should
go through here instead of `logging` directly.
"""
