# Design: Authentication & RBAC Foundation

**Date:** 2026-09-15
**Status:** Approved for planning (approved with one addition — see `is_super_admin` in Section 3)
**App:** `apps/accounts` (plus additions to `core/permissions.py`, `core/audit.py`, `config/settings/base.py`)

## 1. Purpose

Build the foundational authentication and role-based access control (RBAC) system
for MindCare Backend. This is the first real feature landing in the project — almost
every other app depends on knowing who is making a request (`User` + JWT) and what
they're allowed to touch (role-level + object-level permissions).

## 2. Scope

**In scope:**
- Custom `User` model (`apps/accounts`), replacing Django's default user, supporting
  four roles: `patient`, `psychologist`, `admin`, `ngo`.
- JWT auth (access + refresh) via `djangorestframework-simplejwt`, with rotation and
  blacklisting.
- `register` / `login` / `logout` / `refresh` endpoints.
- Role-level permission classes (`core/permissions.py`): `IsPatient`, `IsPsychologist`,
  `IsAdmin`, `IsNGO`.
- A reusable **object-level** permission base class (`core/permissions.py`):
  `IsOwnerOfObject`, demonstrated with a dummy object/view in `apps/accounts/tests/`.
- Structured, PHI-free audit logging of auth events (`core/audit.py`).
- Service-layer, API-layer, and permission tests per `CLAUDE.md`'s hard rules.
- `docs/module-reference.md` entries for everything new.

**Explicitly out of scope (deferred to later, app-specific tasks):**
- `PatientProfile`, `PsychologistProfile`, `NGOProfile` models and any profile
  completion flow — these belong to `apps/patients`, `apps/psychologists`, `apps/ngo`
  respectively, per `architecture.md`'s module ownership, and their `models.py` files
  stay empty scaffolding after this task.
- The concrete psychologist↔patient assignment relationship and the concrete
  "is this THEIR patient" check — this task only ships the reusable pattern
  (`IsOwnerOfObject`) that `apps/psychologists` will subclass once that relationship
  model exists.
- Admin approval *workflow* endpoints (an admin reviewing/approving a pending
  psychologist or NGO account) — this task only builds the `approval_status` field
  and the login-time gate that reads it. The endpoint(s) an admin uses to flip
  `pending → approved` are a future admin-app task.
- The super-admin promote/demote workflow (an existing super-admin creating
  sub-admin accounts, promoting a sub-admin to super-admin, a super-admin demoting
  themselves, and the invariant that at least one super-admin must always exist,
  checked atomically) — this task only ships the `is_super_admin` field as a
  bootstrap mechanism (see Section 3). The workflow is deferred to the same future
  admin-management task noted above. See `docs/decisions.md` (2026-09-15 entry).
- Email verification of any kind (no SMTP/email provider is configured anywhere in
  the project yet).
- "Log out all devices" / bulk refresh-token revocation (only the single presented
  refresh token is blacklisted on logout).
- Per-account login lockout (only IP-scoped throttling on the login endpoint).

## 3. User model (`apps/accounts/models.py`)

```python
class Role(models.TextChoices):
    PATIENT = "patient"
    PSYCHOLOGIST = "psychologist"
    ADMIN = "admin"
    NGO = "ngo"

class ApprovalStatus(models.TextChoices):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.APPROVED
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    objects = UserManager()
```

Design decisions:

- **Email-only login.** No `username` field at all. `USERNAME_FIELD = "email"`.
- **`approval_status` is independent of `is_active`.** `is_active` is the generic
  Django enable/disable switch (available for future admin-initiated suspension of
  an already-approved account). `approval_status` specifically tracks the
  psychologist/NGO approval gate. They are checked separately at login time so the
  two situations ("your account was disabled" vs. "your account is awaiting
  approval") can eventually produce distinct outcomes without redesigning the model.
- **Default `approval_status` is role-dependent, decided by the registration
  service, not user input:** `approved` for `patient` and `admin`, `pending` for
  `psychologist` and `ngo`.
- **No profile fields on `User`.** Anything role-specific (license numbers, org
  details, clinical specialties) lives in the relevant app's own profile model,
  built in a future task.
- **Custom `UserManager`** with `create_user()` (email/password/role required) and
  `create_superuser()` (forces `role=admin`, `approval_status=approved`,
  `is_staff=True`, `is_superuser=True`, and now `is_super_admin=True`).
- **`is_super_admin` (boolean, default `False`)** — added per the design owner's
  approval. This is the system's bootstrap mechanism for its first super-admin,
  since no promote/demote endpoint exists yet. `create_superuser()` is the only
  path that sets it `True` in this task; no other create/update path may set it.
  The promote/demote workflow itself (sub-admin creation, promotion, self-demotion,
  and the "at least one super-admin must always exist" invariant) is explicitly out
  of scope here — see Section 2 non-goals and `docs/decisions.md` (2026-09-15).
- `AUTH_USER_MODEL = "accounts.User"` added to `config/settings/base.py`.

## 4. Auth endpoints (`apps/accounts/api/`)

All mounted under `/api/v1/accounts/`. Views stay thin (parse → call
`services.py` → serialize), per `architecture.md`'s request-flow rule.

| Endpoint | Method | Behavior |
|---|---|---|
| `register/` | POST | Accepts `email`, `password`, `full_name`, `role` (`patient`\|`psychologist`\|`ngo` only — `admin` is rejected with a 400; there is no public path to create an admin account). `services.register_user()` creates the `User` with the role-appropriate default `approval_status`, logs a `register` audit event, returns 201 with the created user's public fields. No tokens are issued on register — the client must call `login/` separately. |
| `login/` | POST | Custom `TokenObtainPairSerializer` subclass (`accounts/api/serializers.py`). If `is_active=False`: simplejwt's default generic failure ("No active account found..."). If `approval_status=pending`: a distinct, explicit error ("Your account is pending admin approval") — not considered sensitive information, and it materially helps legitimate psychologist/NGO users understand their state. On success: injects a `role` custom claim into the access token payload (via an overridden `get_token()`), logs a `login` audit event, and logs `login_failed` on any failed attempt (still non-PHI: email attempted, IP, timestamp). Throttled with `AnonRateThrottle`, scoped specifically to this view (not global). |
| `refresh/` | POST | Thin wrapper around simplejwt's `TokenRefreshView`. `SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] = True` and `SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = True` — each call issues a new refresh token and blacklists the one just used. Logs a `token_refresh` audit event. |
| `logout/` | POST | Accepts the current refresh token in the body, blacklists it via `rest_framework_simplejwt.token_blacklist`. Logs a `logout` audit event. Single-session only — does not touch any other outstanding refresh tokens for the same user. |

Settings additions (`config/settings/base.py`):
- `AUTH_USER_MODEL = "accounts.User"`
- `"rest_framework_simplejwt.token_blacklist"` added to `THIRD_PARTY_APPS` (already
  part of the approved `djangorestframework-simplejwt` package — no new dependency,
  no `CLAUDE.md` package-approval needed) — requires a migration.
- `SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] = True`, `SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = True` added to the existing `SIMPLE_JWT` dict.
- `DEFAULT_PERMISSION_CLASSES` stays `IsAuthenticated` globally (already set) — role
  and object permissions are additive per-view, not a replacement for it.

## 5. RBAC permission architecture (`core/permissions.py`)

**Role-level** — simple, read the JWT-embedded `role` claim via `request.user.role`:
```python
class IsPatient(BasePermission): ...
class IsPsychologist(BasePermission): ...
class IsAdmin(BasePermission): ...
class IsNGO(BasePermission): ...
```

**Object-level** — one shared abstract base, not a full implementation, since the
concrete ownership relationships (e.g. psychologist↔patient) don't exist as models
yet:
```python
class IsOwnerOfObject(BasePermission):
    """
    Subclass and implement get_owner_user() to compare the requesting user
    against the resource's actual owner. Encodes the project's hard rule that
    role-based access alone is never sufficient for psychologist-patient data.
    """
    def get_owner_user(self, obj):
        raise NotImplementedError

    def has_object_permission(self, request, view, obj):
        return self.get_owner_user(obj) == request.user
```

A future app implements it like:
```python
# apps/psychologists/permissions.py (future work, not part of this task)
class IsAssignedPsychologist(IsOwnerOfObject):
    def get_owner_user(self, obj):
        return obj.assigned_psychologist.user
```

This task ships `IsOwnerOfObject` with a test against a dummy object/view in
`apps/accounts/tests/test_permissions.py`, proving the pattern works without
depending on a model this task doesn't own.

## 6. Audit logging (`core/audit.py`)

```python
def log_auth_event(event_type, *, user_id=None, email=None, role=None, ip=None, success=True):
    ...
```

- `event_type` ∈ `{"register", "login", "login_failed", "logout", "token_refresh"}`.
- Emits one structured JSON line via a dedicated `mindcare.audit` logger (Python
  `logging`, not print/stdout-raw) — never patient names, journal content, clinical
  notes, or any health data. Fields logged: user id (if known), attempted email,
  role, event type, success flag, source IP, timestamp. An email address is treated
  as an account identifier, not PHI, so it's safe to log for intrusion-detection
  purposes on failed logins.
- Called from `apps/accounts/services.py`, never directly from views or serializers,
  keeping business logic (including audit triggers) out of the view layer per
  `CLAUDE.md`.

## 7. Testing plan

Per `CLAUDE.md`'s hard rule ("service-layer test for new business logic before
considering a feature done"):

- `apps/accounts/tests/test_services.py` — `register_user()` per role sets the
  correct default `approval_status`; duplicate email is rejected; login
  success/failure/pending-approval paths; logout blacklists the presented token;
  refresh rotates correctly and blacklists the old token.
- `apps/accounts/tests/test_api.py` — endpoint status codes; throttle triggers after
  repeated failed logins; issued access token's payload contains the `role` claim.
- `apps/accounts/tests/test_permissions.py` — `IsPatient`/`IsPsychologist`/
  `IsAdmin`/`IsNGO`; `IsOwnerOfObject` against a dummy object/view.

## 8. Documentation

`docs/module-reference.md` gets a new `### apps/accounts` section with one row per
new service/selector/endpoint, in the existing table format, as part of this task's
completion — not deferred.

## 9. Non-goals recap (see Scope)

Profile models, the concrete psychologist-patient object-level check, admin-approval
*workflow* endpoints, email verification, multi-device logout, and per-account
lockout are all explicitly deferred to later tasks. This task's deliverable is the
foundation those tasks will build on, not those features themselves.
