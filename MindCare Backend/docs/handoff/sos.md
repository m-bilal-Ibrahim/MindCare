# Handoff: SOS (6.12) — Phase 2 module 2

Base: `/api/v1/emergency/`. Bearer JWT. Decisions: `docs/decisions.md` (2026-10-28).
Field rules and messages: `docs/validation-rules.md`.

## Patient (MindCare App)

### `GET resources/` — the SOS screen without pressing
```json
{
  "message": "If you are in immediate danger, call your local emergency number now.",
  "helplines": [{"id": 1, "name": "…", "number": "1122", "description": "", "country": "PK"}],
  "hospitals": [{"id": 3, "name": "…", "phone": "042 …", "address": "…", "city": "Lahore"}],
  "ngos": [{"organization_name": "…", "official_phone": "+92…", "website": "https://…",
            "service_area": {"country": "Pakistan", "city": null}}],
  "psychologist": {"id": 7, "full_name": "Dr …"}
}
```
Every list may be empty and `psychologist` may be null. **Always show `message`.**
`country: null` on a helpline means it works from any country; `city: null` on a
service area means the whole country.

### `POST sos/` — press SOS (on every screen)
Body (optional): `{"latitude": 31.5204, "longitude": 74.3587}`. Send both or neither.
Never throttled. **Always 201** with the resources above plus:
```json
"alert": {"id": 12, "status": "open", "created_at": "…", "cancel_until": "…",
          "location_source": "device", "contacts_notified": 1, "psychologist_notified": true}
```
`alert` is null only if recording failed; still show the message and resources.
`contacts_notified: 0` on a second press within 30 minutes is expected (no repeat emails).

### `POST sos/{id}/cancel/` — "I'm safe"
200 with the alert (`status: "cancelled"`). 400 `{"non_field_errors": ["This alert can no
longer be cancelled."]}` after 5 minutes. 404 if not yours.

### `GET sos/` — your alerts (newest first)

### Emergency contacts (max 3)
- `GET contacts/` → `[{"id","name","relationship","email","phone","created_at"}]`
- `POST contacts/` `{"name","relationship","email","phone"?,"consent_confirmed": true}` → 201.
  `relationship`: `parent`, `sibling`, `spouse_partner`, `child`, `relative`, `friend`, `other`.
  Fourth contact → 400 `{"non_field_errors": ["You can add up to 3 emergency contacts."]}`.
- `PATCH contacts/{id}/` (any of name, relationship, email, phone) → 200
- `DELETE contacts/{id}/` → 204
Show a consent checkbox: "This person agreed to be my emergency contact".

## Psychologist (MindCare Web)
`GET psychologist/alerts/` → `[{"id","created_at","status","relationship_id","patient_name"}]`:
current patients only, last 30 days. Link to the patient page by `relationship_id`.

## Admin (MindCare Web)
- `GET admin/sos/?status=open|cancelled|followed_up|closed` (paginated; open = oldest
  first). Rows: `id, status, outcome, created_at, cancelled_at, followed_up_at,
  closed_at, patient {id, role, display_name, is_real_name}, city, country,
  location_source, has_coordinates, contacts_notified, psychologist_notified`.
- `GET admin/sos/{id}/` adds `latitude, longitude, patient_email, patient_phone,
  followed_up_by_id, closed_by_id`, with the real name. **Audited**: open it only to
  follow up.
- `POST admin/sos/{id}/follow-up/` → `followed_up`.
- `POST admin/sos/{id}/close/` `{"outcome": "patient_safe" | "contacted_patient" |
  "referred_emergency_services" | "false_alarm" | "unreachable" | "other"}`.
- Closed alert → 400 `{"status": ["This alert is already closed."]}`.

## Errors
| Status | When |
|---|---|
| 400 | Invalid contact fields (`{field: [message]}`), cancel window passed, alert closed |
| 401 | Token missing or expired: refresh, then sign in |
| 403 | Wrong role (e.g. a psychologist pressing SOS, a patient on admin endpoints) |
| 404 | Not your alert / contact |
| 429 | More than 30 contact adds or edits an hour |

## Your manual steps
1. Deploy, then run migrations on Render (`emergency.0001`, `audit.0002`).
2. In Django admin → Emergency → **Helplines**: add the helplines you have verified
   (country, name, number). Optionally **Hospitals** per city.
3. Existing ordinary admins get helpline/hospital permissions the next time a
   super-admin promotes or creates an admin, or now via a Render shell:
   `python manage.py shell -c "from apps.accounts.services import ensure_admin_group; ensure_admin_group()"`
4. Optional: a weekly Render cron job running `python manage.py purge_sos_locations`
   (every SOS also purges, so this is only a backstop).
5. Emails need the module 1 email variables on Render (already set).
