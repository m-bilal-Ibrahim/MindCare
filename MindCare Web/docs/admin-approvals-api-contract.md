# Admin approvals API — contract for the backend (Phase 2.5)

The web admin console's **Verifications** page (`/admin/verifications`) is built against
the three endpoints below. Until they are deployed, the page shows "approval endpoints
aren't on the backend yet" and links to Django admin (`/admin/accounts/user/`), which
stays the fallback.

Client code: `MindCare Web/src/services/admin.service.ts`.

All three: `IsAuthenticated` + `IsAdmin` (403 for anyone else). Mounted under the
existing accounts app, so `apps/accounts/api/urls.py`.

---

## 1. List pending applications

`GET /api/v1/accounts/admin/pending/?role=psychologist`

- `role` filter: `psychologist` or `ngo` (the web only uses `psychologist` today).
  Unknown role → 400 `{"role": ["..."]}`.
- Only `approval_status == "pending"`. Oldest first (`created_at`, then `id`).
- A plain list is fine; a paginated `{"count", "next", "previous", "results"}` body also
  works (the web reads `results` if present).

**200** — one item per pending user:

```json
[
  {
    "id": 42,
    "email": "new.psych@example.com",
    "full_name": "Dr. Ayesha Khan",
    "role": "psychologist",
    "approval_status": "pending",
    "created_at": "2026-10-07T10:15:00Z",
    "psychologist_profile": {
      "license_number": "PMDC-12345",
      "license_issuing_country": { "code": "PK", "name": "Pakistan" },
      "license_issuing_authority": "Pakistan Medical & Dental Council",
      "qualifications": "MPhil Clinical Psychology",
      "specializations": [{ "slug": "anxiety", "name": "Anxiety" }],
      "years_of_experience": 6,
      "languages": [{ "code": "ur", "name": "Urdu" }],
      "country": { "code": "PK", "name": "Pakistan" },
      "city": { "id": 3, "name": "Lahore" },
      "timezone": "Asia/Karachi",
      "gender": "female",
      "bio": "..."
    }
  }
]
```

`psychologist_profile` uses the same shapes as `PsychologistProfileOwnerSerializer`
(reuse it). It is `null` for an NGO row (an `ngo_profile` key can be added later).

## 2. Approve

`POST /api/v1/accounts/admin/{user_id}/approve/` — no body.

- Sets `approval_status = "approved"`.
- **200** `{"id": 42, "approval_status": "approved"}`
- **400** `{"approval_status": ["This account isn't pending."]}` if it isn't pending.
- **404** if the user doesn't exist or isn't a psychologist/NGO.

## 3. Reject

`POST /api/v1/accounts/admin/{user_id}/reject/`

Body (optional reason):

```json
{ "reason": "license_unverified" }
```

`reason` choices: `license_unverified`, `incomplete_details`, `not_eligible`, `other`
(optional; `{}` is valid). Unknown keys → 400, as elsewhere (`RejectUnknownFieldsMixin`).

- Sets `approval_status = "rejected"`.
- **Must call `apps.relationships.services.end_for_unavailable_account(user=...)`**, the
  same as `UserAdmin.save_model` does today when an admin rejects in Django admin.
- **200** `{"id": 42, "approval_status": "rejected"}`
- **400** / **404** as for approve.

## Both actions

- Run in a transaction with the user row locked (`select_for_update`) so two admins
  can't act on the same application at once.
- Write an audit entry (who, which user, approve/reject, reason, when), as the
  relationship actions do in `core/audit.py`.
- The login messages already exist and need no change: pending → "Your account is
  pending admin approval.", rejected → "Your account application was not approved."

## How to check it end-to-end

1. Register a test psychologist on the web (`/therapist/apply`).
2. Sign in to the web admin console (`/admin/sign-in`) as an admin account.
3. Verifications lists the new application → Approve.
4. The test psychologist can now sign in at `/therapist/sign-in`.
