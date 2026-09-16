"""
PHI-safe access logging.

Provides log_auth_event(), which records auth events (login, failed login,
logout, token refresh, registration) as structured JSON log lines, without
ever writing PHI (patient names, journal content, clinical notes, health
data) into plaintext application logs. All access to sensitive resources
should go through here instead of `logging` directly.
"""

import json
import logging

logger = logging.getLogger("mindcare.audit")

AUTH_EVENT_TYPES = {"register", "login", "login_failed", "logout", "token_refresh"}


def log_auth_event(
    event_type, *, user_id=None, email=None, role=None, ip=None, success=True
):
    if event_type not in AUTH_EVENT_TYPES:
        raise ValueError(f"Unknown auth event_type: {event_type!r}")
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "email": email,
        "role": role,
        "ip": ip,
        "success": success,
    }
    logger.info(json.dumps(payload))
