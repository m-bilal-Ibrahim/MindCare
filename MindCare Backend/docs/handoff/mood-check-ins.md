# Handoff: mood check-ins — Phase 2 module 3

Base: `/api/v1/journals/`. Bearer JWT. Decisions: `docs/decisions.md` (2026-10-28).
Field rules: `docs/validation-rules.md`.

**Local day** = the patient's profile timezone (Asia/Karachi if none). One check-in per
local day; it can be edited only on that day and deleted any time.

## Patient (MindCare App)

| Method | Path | Notes |
|---|---|---|
| GET | `check-ins/today/` | `{"local_date": "2026-10-28", "check_in": {…} \| null}` — decide between "Check in" and "Edit today" |
| POST | `check-ins/` | `{"mood": 1-5, "tags": [...]?, "note": "..."?}` → 201 |
| PATCH | `check-ins/{id}/` | any of `mood`, `tags`, `note` (today's only) |
| DELETE | `check-ins/{id}/` | 204 |
| GET | `check-ins/` | paginated, newest first |
| GET | `check-ins/insights/` | streak and 7 / 30 / 90-day summaries |

`mood`: 1 Very low, 2 Low, 3 Okay, 4 Good, 5 Great.
`tags` (at most 5): `calm`, `happy`, `grateful`, `hopeful`, `motivated`, `tired`,
`anxious`, `stressed`, `sad`, `lonely`, `angry`, `overwhelmed`.
`note`: optional, 10–500 characters, private to the patient (encrypted; the
psychologist never sees it). Say so next to the field.

Check-in:
```json
{"id": 5, "local_date": "2026-10-28", "mood": 4, "tags": ["calm"],
 "note": "Went for a walk.", "created_at": "…", "updated_at": "…"}
```
Insights:
```json
{"today": "2026-10-28", "streak": 3,
 "windows": {"7": {"check_ins": 3, "average_mood": 3.0,
                   "distribution": {"1": 1, "2": 0, "3": 1, "4": 0, "5": 1},
                   "top_tags": [{"tag": "calm", "count": 2}]},
             "30": {…}, "90": {…}}}
```
The streak counts consecutive days ending today, or yesterday if today's check-in
isn't in yet. `average_mood` is null when there are no check-ins in that window.

**Low mood:** the backend does nothing automatically (Q25). Always show a link to the
SOS / helplines screen (`GET /api/v1/emergency/resources/`) on the check-in screen.

## Psychologist (MindCare Web)
`GET psychologist/patients/{relationship_id}/moods/?days=7|30|90` (default 30):
```json
{"check_ins": [{"id": 5, "local_date": "…", "mood": 4, "tags": ["calm"]}],
 "insights": {…same shape as above…}}
```
Current patients only (404 otherwise, including after care ends). Never includes notes.
Every read is audited.

## Errors
| Status | Body / when |
|---|---|
| 400 | `{"mood": ["Mood must be a whole number between 1 and 5."]}`, `{"tags": ["Choose at most 5 feelings."]}`, note rules; `{"non_field_errors": ["You've already checked in today. Edit today's check-in instead."]}`; `{"non_field_errors": ["A check-in can only be edited on the day it was made."]}`; `days` not 7/30/90 |
| 401 | Token missing or expired: refresh, then sign in |
| 403 | Wrong role |
| 404 | Not your check-in / not your current patient |
| 429 | More than 30 check-in writes an hour |

## Your manual steps
1. Deploy and run migrations on Render (`journals.0001`, `audit.0003`).
   `django.contrib.postgres` is now installed (built into Django, no new package).
2. Optional: re-run `seed_demo` locally to give demo patient 1 a week of check-ins.
