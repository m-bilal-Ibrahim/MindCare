# Handoff: 6.3 Admin panel (Web admin console) and reports (Web + App)

All admin endpoints need a Bearer JWT of an **admin** account (anyone else gets 403).
They are throttled at 120 requests a minute per admin. Error bodies are
`{"field": ["message"]}` or `{"detail": "..."}`. Standard statuses: 401 (refresh,
then sign in), 403, 404, 429.

## 1. Approvals: exactly `MindCare Web/docs/admin-approvals-api-contract.md`

| Method and path | Body | 200 |
|---|---|---|
| `GET /api/v1/accounts/admin/pending/?role=psychologist` (or `ngo`) | — | a plain list, oldest first (shape below) |
| `POST /api/v1/accounts/admin/{user_id}/approve/` | none | `{"id", "approval_status": "approved", "is_active"}` |
| `POST /api/v1/accounts/admin/{user_id}/reject/` | `{}` or `{"reason": "license_unverified" \| "incomplete_details" \| "not_eligible" \| "other"}` | `{"id", "approval_status": "rejected", "is_active"}` |

Each pending item: `id, email, full_name, role, approval_status, created_at,
psychologist_profile, ngo_profile`. `psychologist_profile` has the same shape as
`GET /psychologists/me/`, **including `documents`**
(`[{id, kind, file_type, size, uploaded_at}]`). `ngo_profile` is the NGO's `me`
shape for NGO rows; for each row, the field for the other role is `null`.

Errors: unknown `role` → 400 `{"role": [...]}`. Not pending → 400
`{"approval_status": ["This account isn't pending."]}`. Deactivated → 400
`{"approval_status": ["This account is deactivated. Reactivate it before reviewing it."]}`.
Missing, or not a psychologist/NGO → 404. Unknown body key → 400
`{"key": ["This field can't be set."]}`.

The "endpoints aren't deployed yet" fallback (404 on the list) can stay; it no longer
triggers once this is live.

## 2. Viewing a credential document

`GET /api/v1/accounts/admin/documents/{document_id}/` →
`{"id", "kind", "file_type", "url", "expires_in": 300}`. Open `url` in a new tab or
an `<iframe>`/`<img>` straight away: it stops working after `expires_in` seconds, so
fetch a fresh one on each click and never store it. Every call is recorded in the
access audit trail. 404 if the document doesn't exist.

## 3. Monitoring

`GET /api/v1/accounts/admin/overview/`:
```json
{
  "users": {"patient": {"total": 120, "active": 118, "pending": 0, "rejected": 0, "deactivated": 2},
            "psychologist": {...}, "ngo": {...}},
  "pending_approvals": {"psychologist": 3, "ngo": 1},
  "relationships": {"pending": 4, "accepted": 37, "ended": 12, "declined": 3, "cancelled": 1, "expired": 2},
  "open_reports": 2,
  "weekly_signups": [{"week_start": "2026-09-28", "patient": 9, "psychologist": 2, "ngo": 0}]
}
```

`GET /api/v1/accounts/admin/users/?role=&status=&search=&page=&page_size=`
(paginated: `{count, next, previous, results}`; `status` is `active`, `pending`,
`rejected` or `deactivated`). Each row: `id, role, display_name, is_real_name, email,
approval_status, is_active, created_at, last_login`. **A private patient shows
their pseudonym and `email: null`.** Search matches psychologists'/NGOs' names and
emails, and patients **by pseudonym only**.

`GET /api/v1/accounts/admin/users/{id}/`: one account, with `identity`
(`{id, role, display_name, is_real_name}`), `email`, statuses, and `patient` /
`psychologist_profile` / `ngo_profile`. **Opening a private patient reveals their
real name and email, and that reveal is audited.** So show the list first and open
details only on click. There is never any health data here.

`POST /api/v1/accounts/admin/users/{id}/deactivate/` with `{}` or
`{"reason": "policy_violation" | "report_upheld" | "user_request" | "other"}`, and
`POST .../reactivate/`. Both return `{id, approval_status, is_active}`. Deactivating
ends the person's care relationships, and reactivating doesn't restore them. Already
in that state → 400. Admin accounts → 404 (managed in Django admin).

## 4. Reports and complaints

**Submitting** (App for patients, Web for psychologists):
`POST /api/v1/moderation/reports/`

| Who | Body |
|---|---|
| Patient (App) | `{"psychologist": <directory id>, "reason": "...", "description": "optional, 10–1000 chars"}`, for a current or former psychologist |
| Psychologist (Web) | `{"relationship": <relationship_id from /relationships/patients/ or /history/>, "reason": "...", "description": "..."}` |

`reason`: `harassment`, `threats_or_violence`, `inappropriate_content`,
`unprofessional_conduct`, `privacy_breach`, `other`. 201 →
`{id, reason, status: "open", created_at, resolved_at}`. Errors (400):
`{"psychologist": ["You can only report a psychologist you have been in care with."]}`,
`{"relationship": ["You can only report your own current or former patients."]}`,
`{"non_field_errors": ["You already have an open report about this person."]}`,
`{"description": ["Description must be between 10 and 1000 characters."]}`.
429 after 10 reports a day. NGOs, admins and unapproved psychologists → 403.

`GET /api/v1/moderation/reports/`: the user's own reports (status only).

**Admin review (Web Moderation page):**
- `GET /api/v1/moderation/admin/reports/?status=open|dismissed|actioned` (paginated):
  `id, reason, status, created_at, resolved_at, reporter, reported_user,
  has_description`. `reporter` and `reported_user` are `{id, role, display_name,
  is_real_name}`; private patients show their pseudonym. No description in the list.
- `GET /api/v1/moderation/admin/reports/{id}/`: adds `description`,
  `relationship_id`, `resolved_by_id`, `reported_user_is_active`, and **real
  identities (audited reveal)**. Reading the description is audited too.
- `POST .../{id}/dismiss/` (no violation) or `POST .../{id}/uphold/` (deactivates the
  reported account, ends their care relationships, closes all open reports about
  them). Already resolved → 400 `{"status": ["This report has already been resolved."]}`.

## Screens

**Web (admin console), once the partner's branches are on GitHub:**
- **Verifications** (`web/admin-psychologist-approvals`): merge it, then add a
  "View" button per document that calls the documents endpoint and opens the URL.
- **Overview:** replace `PLATFORM_STATS`, `GROWTH_CHART_DATA`,
  `VERIFICATION_QUEUE_PREVIEW`, `MODERATION_QUEUE_OPEN` with `/admin/overview/`.
- **Users:** replace `USERS_SUMMARY` / `PLATFORM_USERS` with `/admin/users/`
  (search, filters, pages); a detail drawer on click; Deactivate/Reactivate with a
  confirm sheet and a reason.
- **Therapists (admin):** `/admin/users/?role=psychologist` plus the detail view.
- **Moderation:** replace `MODERATION_SUMMARY`, `MODERATION_QUEUE`,
  `MODERATION_CASE_DETAIL` with the reports endpoints; Dismiss and Uphold with a
  confirm.
- **Therapist console, patient detail:** a "Report" action (psychologist → patient).
- Delete the replaced mock constants from `constants/adminConsole.ts`.

**App:** a "Report" action on the current psychologist and on recent psychologists,
with a reason picker and an optional description (10–1000 characters, the same rules).

## Deferred
Community content moderation and time-limited bans: 6.8. Super-admin
create/promote/demote: Phase 2.
