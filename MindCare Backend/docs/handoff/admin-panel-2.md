# Handoff: admin-panel-2 and the super-admin workflow (Phase 2, module 0)

**Not a breaking change.** Every existing endpoint keeps its shape. Additions:
`must_change_password` on the login response, `submitted_at` on pending
approvals, `recent_account_actions` on the Overview, and open reports now come
oldest first.

All endpoints below need `Authorization: Bearer <access>`. Admin endpoints are
throttled at 120/min per user (429). Errors use the usual DRF shape: `{"field":
["message"]}` for 400, `{"detail": "..."}` for 401/403/404. The exact field rules
are in `docs/validation-rules.md`.

## 1. Temporary passwords and changing a password (Web and App)

### Login: one new field
`POST /api/v1/accounts/login/` now returns:

```json
{"refresh": "…", "access": "…", "must_change_password": false}
```

`true` only for an admin a super-admin just created. **Web:** when it's `true`,
go straight to a "Choose a new password" screen. Until they change it, every admin
endpoint answers:

```json
403 {"detail": "Change your temporary password before continuing."}
```

(`code`: `password_change_required`).

### `POST /api/v1/accounts/password/change/` (any signed-in user, Web and App)

```json
{"current_password": "…", "new_password": "…"}
```

**200:** a new token pair, same shape as login. **Replace both stored tokens**:
every other session (other devices too) is signed out, and the old refresh token
no longer works. Throttle: 10 per hour per user.

| 400 body | When |
|---|---|
| `{"current_password": ["Your current password is incorrect."]}` | wrong current password |
| `{"new_password": ["This password is too short. It must contain at least 8 characters."]}` | Django's rules (also `too common`, `entirely numeric`, `too similar to the email / full name`) |
| `{"new_password": ["Choose a password different from your current one."]}` | same as the current one |
| `{"<other key>": ["This field can't be set."]}` | unknown field |

**Screen:** current password, new password, confirm new password (checked on the
client only), the length and "not only digits" checks while typing, the backend's
message under the field. A "Change password" entry in the profile/settings menu
of both apps.

## 2. Managing admins (Web, super-admins only)

Ordinary admins get **403** on all of these (`{"detail": "Only a super-admin can do
this."}`). To decide whether to show the "Admins" page, call
`GET /api/v1/accounts/admin/admins/` once after login: a 403 means "not a
super-admin", so hide it.

| Method and path | Body | Result |
|---|---|---|
| `GET /api/v1/accounts/admin/admins/` | — | list, oldest first |
| `POST /api/v1/accounts/admin/admins/` | `{"email", "full_name"}` | **201** with `temporary_password` (see below) |
| `POST /api/v1/accounts/admin/admins/{id}/promote/` | — | make a super-admin |
| `POST /api/v1/accounts/admin/admins/me/demote/` | — | step down yourself |
| `POST /api/v1/accounts/admin/admins/{id}/deactivate/` | — | turn off an ordinary admin (signs them out) |
| `POST /api/v1/accounts/admin/admins/{id}/reactivate/` | — | turn them back on |

Admin row:

```json
{"id": 4, "email": "ayesha@example.com", "full_name": "Ayesha Khan",
 "is_super_admin": false, "is_active": true, "must_change_password": true,
 "created_at": "2026-10-15T09:00:00Z", "last_login": null}
```

**Create** returns the same plus `"temporary_password": "q3V…"`. **It is shown only
in this response.** Show it once in a dialog with a copy button and the text
"Give this password to the new admin privately. They must change it when they
first sign in. You won't see it again." Don't store it anywhere.

| 400 body | When |
|---|---|
| `{"email": ["A user with this email already exists."]}` | taken |
| `{"full_name": [...]}` | name rule (letters, spaces, `-` `'` `.`, 2–100) |
| `{"is_super_admin": ["This admin is already a super-admin."]}` | promote twice |
| `{"is_active": ["Reactivate this admin before promoting them."]}` | promote a deactivated admin |
| `{"is_super_admin": ["You're the only super-admin. Promote another admin first."]}` | last super-admin steps down |
| `{"is_active": ["You can't deactivate your own account."]}` | self |
| `{"is_active": ["A super-admin can't be deactivated. They must demote themselves first."]}` | target is a super-admin |
| `{"is_active": ["This admin is already deactivated."]}` / `["This admin is already active."]` | repeat |

404 = no admin with that id. **Screen:** a table (name, email, super-admin badge,
active, "must change password" badge, last login), "Add admin" form, and per row
Promote / Deactivate / Reactivate; a "Step down" button on your own row with a
confirmation. Disable Deactivate on your own row and on super-admin rows.

## 3. City verification (Web, any admin)

`GET /api/v1/reference/admin/cities/?status=unverified|verified|all&country=PK&search=`
(paginated `{count, next, previous, results}`; default `unverified`, oldest first):

```json
{"id": 88, "name": "Lahor", "country": "PK", "country_name": "Pakistan",
 "is_verified": false, "usage_count": 1}
```

`usage_count` = profiles and NGO service areas using the city.

| Action | Body | Result |
|---|---|---|
| `POST …/cities/{id}/verify/` | — | 200 city; it now appears in the public dropdown |
| `POST …/cities/{id}/merge/` | `{"into": <city id>}` | 200, the **target** city. Everything using the misspelt city moves to `into`, then it's deleted |
| `POST …/cities/{id}/reject/` | — | 204; deletes an **unused** unverified city |

400 messages: `This city is already verified.`, `Only an unverified city can be
merged away.`, `Choose a different city.`, `That city doesn't exist.`, `Choose a
city in the same country.`, `A verified city can't be rejected.`, `This city is used
by N profile(s) or service area(s). Merge it into the right city instead.`

**Screen:** list of unverified cities with usage count; buttons Verify, Merge
(a search box over `GET /reference/cities/?country=<code>&search=` to pick the
target), Reject (enabled only when `usage_count` is 0).

## 4. Content management: quotes, duas, surahs (Web, any admin)

Base: `/api/v1/motivation/admin/`. Each kind has the same five calls:

| Method and path | Notes |
|---|---|
| `GET quotes/`, `duas/`, `surahs/` (optional `?is_active=true` or `false`) | paginated, hidden items included |
| `POST quotes/` … | create; **201** |
| `GET` / `PATCH` / `DELETE quotes/{id}/` … | `PATCH` any subset; `DELETE` is permanent (prefer `is_active: false` to hide) |
| `PUT duas/{id}/audio/`, `surahs/{id}/audio/` | multipart, one part `audio`: MP3, M4A or OGG, max 15 MB |
| `DELETE duas/{id}/audio/`, `surahs/{id}/audio/` | removes the recitation |

Surahs are addressed by `id` here (not `number`, unlike the patient endpoint).

Fields (rules and messages in validation-rules.md):
- **Quote:** `text` (10–500), `author` (optional, name rule), `category`
  (`hope`, `resilience`, `calm`, `self_care` or empty), `is_active`.
- **Dua:** `title`, `reference` (e.g. `Quran 21:87`), `arabic`, `transliteration`
  (optional), `translation`, `sort_order` (0–32767), `is_active`.
- **Surah:** `number` (1–114, unique: `{"number": ["A surah with this number already
  exists."]}`), `name_arabic`, `name_english`, `name_meaning`, `ayah_count` (1–286),
  `arabic`, `transliteration`, `translation`, `is_active`. Keep one verse per line.

Duas and surahs also return `has_audio`, `audio_type` and `audio_url` (a signed
link valid for 5 minutes; fetch again rather than caching it). Audio errors:
`{"audio": ["Choose an audio file to upload."]}`, `Recitation must be one of: MP3,
M4A, OGG.`, `Recitation must be 15 MB or smaller.`, `Recitation is empty.`,
`{"audio": ["There is no recitation to remove."]}`.

**Screen:** three tabs; a table with an active switch (PATCH `is_active`), an
editor form (Arabic fields `dir="rtl"`, multi-line), an audio player plus Upload /
Remove for duas and surahs. Only upload recitations we hold the rights to.

## 5. Psychologist directory (Web, any admin)

`GET /api/v1/accounts/admin/psychologists/?accepting=true|false&status=active|pending|rejected|deactivated&search=`
(paginated, by name). **Counts only, never which patients:**

```json
{"id": 12, "full_name": "Sara Malik", "email": "sara@example.com",
 "approval_status": "approved", "is_active": true,
 "is_accepting_patients": false, "not_accepting_reason": "fully_booked",
 "current_patient_count": 7, "pending_request_count": 2,
 "last_active": "this_week", "country": "PK", "city": "Lahore",
 "years_of_experience": 6, "created_at": "2026-09-30T10:00:00Z"}
```

`id` is the user id, so "Open" goes to the existing `GET
/accounts/admin/users/{id}/`. `last_active`: `today`, `this_week`, `this_month`,
`over_a_month`, `never`.

## 6. Changes to existing admin screens (Web)

- **Pending approvals** (`GET /accounts/admin/pending/`): each row has
  `submitted_at`. Show "Waiting since 3 days" and keep the order (oldest first).
- **Reports** (`GET /moderation/admin/reports/?status=open`): now the
  **oldest first**, so the longest-waiting report is on top. Without the filter,
  newest first as before.
- **Overview** (`GET /accounts/admin/overview/`): new `recent_account_actions`,
  newest first, at most 10, last 30 days:

  ```json
  [{"id": 31, "role": "patient", "display_name": "Patient-4f2a9c",
    "is_real_name": false, "action": "deactivated", "at": "2026-10-14T12:00:00Z"}]
  ```

  `action` is `deactivated` or `rejected`. A private patient shows the pseudonym;
  the existing audited user detail reveals more. NGO counts were already in
  `users.ngo` and `pending_approvals.ngo`.

## Notes
- Django admin (`/admin/`): ordinary admins can edit content and reference data
  and only view users; super-admins see everything.
- An admin still on a temporary password can sign in to Django admin; tell new
  admins to change it in the console first.
