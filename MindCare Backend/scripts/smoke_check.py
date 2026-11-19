"""Read-only smoke test of every module built so far.

Usage:
    DEMO_PASSWORD=... python scripts/smoke_check.py <BASE_URL>
    (optional) ADMIN_EMAIL=... ADMIN_PASSWORD=... for the admin checks

Only GET requests, plus the JWT login POSTs. Nothing is created, changed or
deleted, no email is sent, no SOS is pressed and the AI service is never called.
Prints status codes and item counts only: never tokens, passwords or bodies.
Exit code 1 if any check fails. Stdlib only.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

PATIENT_EMAIL = "demo.patient.hina@example.com"
PSYCH_EMAIL = "demo.psych.sara@example.com"
WAKE_TIMEOUT = 90
TIMEOUT = 30

results = []  # (module, check, expected, got, ok)


def request(base, method, path, token=None, body=None, timeout=TIMEOUT):
    """Return (status, parsed JSON or None). Status 0 means no response."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, None
    try:
        return status, json.loads(raw) if raw else None
    except ValueError:
        return status, None


def count(body, key=None):
    """Item count of a list, a paginated page, or body[key]; None if not a list."""
    if key and isinstance(body, dict):
        body = body.get(key)
    if isinstance(body, list):
        return len(body)
    if isinstance(body, dict) and isinstance(body.get("results"), list):
        return body.get("count", len(body["results"]))
    return None


def check(base, module, name, path, token, expected=(200,), key=None):
    status, body = request(base, "GET", path, token)
    ok = status in expected
    got = str(status)
    if ok and status == 200:
        n = count(body, key)
        if n is not None:
            got += f" ({n} items)"
    results.append((module, name, "/".join(map(str, expected)), got, ok))
    return body if ok else None


def record(module, name, expected, got, ok):
    results.append((module, name, expected, got, ok))


def wake(base):
    for attempt in range(1, 4):
        status, _ = request(base, "GET", "/api/v1/", timeout=WAKE_TIMEOUT)
        if status:  # any HTTP answer (even 404) means the server is up
            record("server", "wake GET /api/v1/", "any HTTP", str(status), True)
            return True
        print(f"  server not answering (attempt {attempt}/3)...", file=sys.stderr)
        time.sleep(5)
    record("server", "wake GET /api/v1/", "any HTTP", "no response", False)
    return False


def login(base, label, email, password):
    status, body = request(
        base,
        "POST",
        "/api/v1/accounts/login/",
        body={"email": email, "password": password},
    )
    token = body.get("access") if status == 200 and isinstance(body, dict) else None
    record("6.1 auth", f"login {label}", "200", str(status), bool(token))
    return token


def patient_checks(base, t):
    check(base, "6.1 profile", "patient GET /patients/me/", "/api/v1/patients/me/", t)
    check(
        base,
        "6.1 profile",
        "patient GET /patients/me/history/",
        "/api/v1/patients/me/history/",
        t,
        expected=(200, 404),
    )
    check(
        base,
        "3 relationships",
        "patient GET current",
        "/api/v1/relationships/current/",
        t,
    )
    check(base, "6.10 motivation", "GET quotes", "/api/v1/motivation/quotes/", t)
    check(
        base,
        "6.10 motivation",
        "GET random quote",
        "/api/v1/motivation/quotes/random/",
        t,
    )
    check(
        base,
        "6.10 motivation",
        "GET religious preference",
        "/api/v1/motivation/religious/preference/",
        t,
    )
    duas = check(base, "6.10 motivation", "GET duas", "/api/v1/motivation/duas/", t)
    first = (duas.get("results") if isinstance(duas, dict) else duas) or []
    if first and isinstance(first[0], dict) and "id" in first[0]:
        check(
            base,
            "6.10 motivation",
            "GET one dua",
            f"/api/v1/motivation/duas/{first[0]['id']}/",
            t,
        )
    check(base, "6.10 motivation", "GET surahs", "/api/v1/motivation/surahs/", t)
    check(base, "6.10 motivation", "GET surah 1", "/api/v1/motivation/surahs/1/", t)
    res = check(base, "6.12 SOS", "GET resources", "/api/v1/emergency/resources/", t)
    if isinstance(res, dict):
        for key in ("helplines", "hospitals", "ngos"):
            n = count(res, key)
            record(
                "6.12 SOS",
                f"resources.{key} is a list",
                "list",
                f"{n} items",
                n is not None,
            )
    check(base, "6.12 SOS", "GET contacts", "/api/v1/emergency/contacts/", t)
    check(base, "6.12 SOS", "GET my SOS history", "/api/v1/emergency/sos/", t)
    check(base, "6.4 mood", "GET check-ins", "/api/v1/journals/check-ins/", t)
    check(
        base,
        "6.4 mood",
        "GET today's check-in",
        "/api/v1/journals/check-ins/today/",
        t,
        expected=(200, 404),
    )
    ins = check(
        base, "6.4 mood", "GET insights", "/api/v1/journals/check-ins/insights/", t
    )
    if isinstance(ins, dict):
        windows = ins.get("windows") or {}
        record(
            "6.4 mood",
            "insights windows 7/30/90",
            "3 windows",
            f"{len(windows)} windows",
            len(windows) == 3,
        )
        record(
            "6.4 mood",
            "insights streak",
            "number",
            type(ins.get("streak")).__name__,
            isinstance(ins.get("streak"), int),
        )
    d = check(
        base, "6.2 booking", "GET directory", "/api/v1/psychologists/directory/", t
    )
    rows = (d.get("results") if isinstance(d, dict) else d) or []
    with_fee = sum(1 for r in rows if isinstance(r, dict) and r.get("session_fee_pkr"))
    record(
        "6.2 booking",
        "directory shows fees",
        ">=1 with fee",
        f"{with_fee} with fee",
        with_fee >= 1,
    )
    check(
        base,
        "6.2 booking",
        "patient GET slots",
        "/api/v1/appointments/slots/",
        t,
        key="slots",
    )
    check(
        base,
        "6.2 booking",
        "patient GET my sessions",
        "/api/v1/appointments/sessions/",
        t,
    )
    check(
        base,
        "6.4 notes",
        "patient GET /clinical-notes/me/progress/",
        "/api/v1/clinical-notes/me/progress/",
        t,
    )
    check(
        base,
        "6.4 care plan",
        "patient GET care-plans",
        "/api/v1/recommendations/care-plans/",
        t,
    )
    check(base, "journal", "patient GET entries", "/api/v1/journals/entries/", t)
    notification_checks(base, t, "patient")


def notification_checks(base, t, who):
    check(
        base,
        "notifications",
        f"{who} GET notifications",
        "/api/v1/notifications/",
        t,
    )
    check(
        base,
        "notifications",
        f"{who} GET unread-count",
        "/api/v1/notifications/unread-count/",
        t,
    )
    messaging_checks(base, t, who)


def messaging_checks(base, t, who):
    check(
        base,
        "messaging",
        f"{who} GET conversations",
        "/api/v1/messaging/conversations/",
        t,
    )
    check(
        base,
        "messaging",
        f"{who} GET message unread-count",
        "/api/v1/messaging/unread-count/",
        t,
    )


def psych_checks(base, t):
    notification_checks(base, t, "psych")
    me = check(
        base,
        "6.2 onboarding",
        "psych GET /psychologists/me/",
        "/api/v1/psychologists/me/",
        t,
    )
    if isinstance(me, dict):
        n = count(me, "documents")
        record(
            "6.2 onboarding",
            "credential documents list",
            "list",
            f"{n} items",
            n is not None,
        )
    check(base, "3 relationships", "psych GET inbox", "/api/v1/relationships/inbox/", t)
    pats = check(
        base,
        "3 relationships",
        "psych GET patients",
        "/api/v1/relationships/patients/",
        t,
    )
    check(
        base,
        "3 relationships",
        "psych GET history",
        "/api/v1/relationships/history/",
        t,
    )
    check(
        base,
        "6.2 booking",
        "psych GET settings",
        "/api/v1/appointments/psychologist/settings/",
        t,
    )
    check(
        base,
        "6.2 booking",
        "psych GET working hours",
        "/api/v1/appointments/psychologist/working-hours/",
        t,
    )
    check(
        base,
        "6.2 booking",
        "psych GET days off",
        "/api/v1/appointments/psychologist/days-off/",
        t,
    )
    check(
        base,
        "6.2 booking",
        "psych GET slots",
        "/api/v1/appointments/psychologist/slots/",
        t,
        key="slots",
    )
    for view in ("requests", "upcoming", "past"):
        check(
            base,
            "6.2 booking",
            f"psych GET sessions view={view}",
            f"/api/v1/appointments/psychologist/sessions/?view={view}",
            t,
        )
    check(
        base,
        "6.12 SOS",
        "psych GET alerts",
        "/api/v1/emergency/psychologist/alerts/",
        t,
    )
    rel_id = None
    if isinstance(pats, list) and pats and isinstance(pats[0], dict):
        rel_id = pats[0].get("relationship_id")
    record(
        "3 relationships",
        "psych has an accepted patient",
        "1+",
        str(count(pats)),
        rel_id is not None,
    )
    if rel_id is None:
        return None
    base_p = f"/api/v1/clinical-notes/patients/{rel_id}/"
    check(base, "6.4 notes", "psych GET notes list", base_p + "notes/", t)
    check(base, "6.4 notes", "psych GET progress chart", base_p + "progress/", t)
    check(
        base,
        "6.4 notes",
        "psych GET summary",
        base_p + "summary/",
        t,
        expected=(200, 404),
    )
    check(
        base,
        "6.1 profile",
        "psych GET patient history",
        f"/api/v1/relationships/patients/{rel_id}/history/",
        t,
        expected=(200, 404),
    )
    for days in (7, 30, 90):
        check(
            base,
            "6.4 mood",
            f"psych GET patient moods days={days}",
            f"/api/v1/journals/psychologist/patients/{rel_id}/moods/?days={days}",
            t,
        )
    return rel_id


def admin_checks(base, t, rel_id):
    for name, path in [
        ("GET pending approvals", "/api/v1/accounts/admin/pending/?role=psychologist"),
        ("GET overview", "/api/v1/accounts/admin/overview/"),
        ("GET users", "/api/v1/accounts/admin/users/"),
        ("GET psychologists", "/api/v1/accounts/admin/psychologists/"),
        ("GET reports", "/api/v1/moderation/admin/reports/"),
        ("GET cities", "/api/v1/reference/admin/cities/"),
        ("GET SOS log", "/api/v1/emergency/admin/sos/"),
        ("GET quotes (admin)", "/api/v1/motivation/admin/quotes/"),
        ("GET duas (admin)", "/api/v1/motivation/admin/duas/"),
        ("GET surahs (admin)", "/api/v1/motivation/admin/surahs/"),
    ]:
        check(base, "6.3 admin", name, path, t)
    # Super-admins only; an ordinary admin gets 403.
    check(
        base,
        "6.3 admin",
        "GET admins",
        "/api/v1/accounts/admin/admins/",
        t,
        expected=(200, 403),
    )
    if rel_id is not None:
        check(
            base,
            "permissions",
            "admin GET clinical notes",
            f"/api/v1/clinical-notes/patients/{rel_id}/notes/",
            t,
            expected=(403, 404),
        )


def public_checks(base):
    check(base, "reference", "GET countries", "/api/v1/reference/countries/", None)
    check(
        base,
        "reference",
        "GET specializations",
        "/api/v1/reference/specializations/",
        None,
    )
    check(base, "stats", "GET public stats", "/api/v1/stats/public/", None)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/smoke_check.py <BASE_URL>", file=sys.stderr)
        return 2
    base = sys.argv[1].rstrip("/")
    password = os.environ.get("DEMO_PASSWORD", "")
    if not password:
        print("Set DEMO_PASSWORD first.", file=sys.stderr)
        return 2

    if wake(base):
        public_checks(base)
        check(
            base,
            "permissions",
            "unauthenticated GET /patients/me/",
            "/api/v1/patients/me/",
            None,
            expected=(401,),
        )
        pt = login(base, "patient", PATIENT_EMAIL, password)
        ps = login(base, "psychologist", PSYCH_EMAIL, password)
        if pt:
            patient_checks(base, pt)
        rel_id = psych_checks(base, ps) if ps else None
        if pt and rel_id is not None:
            check(
                base,
                "permissions",
                "patient GET psychologist's notes",
                f"/api/v1/clinical-notes/patients/{rel_id}/notes/",
                pt,
                expected=(403, 404),
            )
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_email and admin_password:
            at = login(base, "admin", admin_email, admin_password)
            if at:
                admin_checks(base, at, rel_id)
        else:
            print("ADMIN_EMAIL / ADMIN_PASSWORD not set: admin checks skipped.")

    widths = [
        max(len(str(r[i])) for r in results + [("module", "check", "expected", "got")])
        for i in range(4)
    ]
    header = ("module", "check", "expected", "got", "result")
    fmt = " | ".join(f"{{:<{w}}}" for w in widths) + " | {}"
    print(fmt.format(*header))
    print("-+-".join("-" * w for w in widths) + "-+-------")
    for module, name, expected, got, ok in results:
        print(fmt.format(module, name, expected, got, "PASS" if ok else "FAIL"))
    failed = sum(1 for r in results if not r[4])
    print(
        f"\nTotal: {len(results)} checks, {len(results) - failed} passed, {failed} failed"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
