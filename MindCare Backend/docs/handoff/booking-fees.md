# Handoff: booking and fees — Phase 2 module 4

Base: `/api/v1/appointments/`. Bearer JWT. Decisions: `docs/decisions.md` (2026-10-28,
"Phase 2 module 4"). Field rules and exact messages: `docs/validation-rules.md`.
All times in responses are UTC ISO 8601 (`…Z`); show them in the viewer's timezone.
Writes are throttled (`bookings`, 60/hour per user).

**Flow:** psychologist sets fee + length + video link + weekly hours → patient (with an
accepted psychologist) picks a slot → **requested** → psychologist **confirms** or
**proposes** another slot → patient **accepts** → **confirmed** → after it ends the
psychologist marks **completed** or **no_show**. Unanswered requests/proposals become
**expired** when their start passes. Either side can **cancel** before the start.

## Psychologist (MindCare Web) — approved, active psychologists only

| Method | Path | Body / notes |
|---|---|---|
| GET / PATCH | `psychologist/settings/` | `{"session_minutes": 30\|50\|60, "fee_pkr": 3000, "video_link": "https://…zoom.us/j/…"}` (any subset; `""` clears the link) |
| GET / PUT | `psychologist/working-hours/` | `{"windows": [{"weekday": 0, "start_time": "09:00", "end_time": "13:00"}]}` — replaces all; Monday = 0; times in the psychologist's profile timezone (returned as `timezone`) |
| GET / POST | `psychologist/days-off/` | `{"date": "2026-11-05"}` → 201 `{"id": 3, "date": "2026-11-05"}`; GET lists today onwards |
| DELETE | `psychologist/days-off/{id}/` | 204 |
| GET | `psychologist/slots/` | your free slots (for proposing a time) |
| GET | `psychologist/sessions/?view=requests\|upcoming\|past` | paginated; default `upcoming` |
| POST | `psychologist/sessions/{id}/confirm/` | no body |
| POST | `psychologist/sessions/{id}/propose/` | `{"starts_at": "<one of your free slots>"}` |
| POST | `psychologist/sessions/{id}/cancel/` | no body |
| POST | `psychologist/sessions/{id}/outcome/` | `{"outcome": "completed"\|"no_show"}` (only after a confirmed session ends) |

Settings response:
```json
{"session_minutes": 50, "fee_pkr": 3000, "video_link": "https://zoom.us/j/123",
 "is_bookable": false, "not_bookable_reason": "no_working_hours"}
```
`not_bookable_reason`: `no_fee`, `no_video_link`, `no_working_hours`, or null. Show a
set-up checklist until it is null. To propose a new time, offer the times from
`GET psychologist/slots/` (`{"slots": ["…Z", …]}`, your free slots 12 h to 30 days
ahead) and send one back exactly as received.

Psychologist session:
```json
{"id": 12, "status": "requested", "starts_at": "2026-11-03T05:00:00Z",
 "ends_at": "2026-11-03T05:50:00Z", "duration_minutes": 50, "fee_pkr": 3000,
 "requested_starts_at": "2026-11-03T05:00:00Z", "confirmed_at": null,
 "cancelled_at": null, "cancelled_by": null, "is_late_cancellation": false,
 "created_at": "…", "relationship_id": 4,
 "patient": {"display_name": "Hina Khan", "is_real_name": true},
 "outcome_marked_at": null}
```
After care ends the patient shows as their pseudonym (`is_real_name: false`).

## Patient (MindCare App)

| Method | Path | Body / notes |
|---|---|---|
| GET | `slots/` | free slots with the current psychologist (12 h to 30 days ahead) |
| GET / POST | `sessions/` | POST `{"starts_at": "2026-11-03T05:00:00Z"}` → 201; GET paginated, newest first |
| POST | `sessions/{id}/accept/` | accept a `proposed` time |
| POST | `sessions/{id}/cancel/` | free until `free_cancellation_until`; later → `is_late_cancellation: true` |

Slots:
```json
{"bookable": true, "not_bookable_reason": null, "psychologist_timezone": "Asia/Karachi",
 "session_minutes": 50, "fee_pkr": 3000, "upcoming_sessions": 1,
 "max_upcoming_sessions": 2, "slots": ["2026-11-03T05:00:00Z", "2026-11-03T06:00:00Z"]}
```
Send a slot back exactly as received. When `bookable` is false, show "Your psychologist
hasn't opened bookings yet". When `upcoming_sessions` = `max_upcoming_sessions`,
disable booking.

Patient session: the psychologist fields above minus `relationship_id` / `patient` /
`outcome_marked_at`, plus `"psychologist": {"id": 7, "full_name": "Dr. Sara Ahmed"}`,
`"video_link"` (**only when `status` is `confirmed`**, else null) and
`"free_cancellation_until"` (confirmed only). Before cancelling a confirmed session
after that time, warn that it will count as a late cancellation.

**Directory** (`GET /api/v1/psychologists/directory/`): cards now carry
`session_fee_pkr` (PKR, null if not set) and `session_minutes`. Show as "PKR 3,000 /
50 min".

Statuses: `requested`, `proposed`, `confirmed`, `cancelled`, `expired`, `completed`,
`no_show`. `cancelled_by`: `patient`, `psychologist`, `system` (care ended).

## Errors
| Status | Body / when |
|---|---|
| 400 | Field rules (`fee_pkr`, `video_link`, `windows`, `date`, `starts_at`, `outcome`); `{"relationship": ["You need an accepted psychologist before booking a session."]}`; `{"psychologist": ["Your psychologist hasn't opened bookings yet."]}`; `{"starts_at": ["Book at least 12 hours ahead."]}` / `["You can book up to 30 days ahead."]` / `["That time isn't available any more. Pick another slot."]`; `{"non_field_errors": ["You can have at most 2 upcoming sessions."]}`; `{"video_link": ["Add your Zoom or Google Meet link before confirming sessions."]}`; `{"session": ["This session isn't waiting for your answer."]}` / `["There's no new time to accept for this session."]` / `["This session can't be cancelled any more."]` / `["You can mark the outcome once a confirmed session has ended."]` |
| 401 | Token missing or expired: refresh, then sign in |
| 403 | Wrong role, or the psychologist isn't approved and active |
| 404 | Not your session / day off |
| 429 | Too many writes; retry later |

On "That time isn't available any more", reload `slots/`: someone else just took it.

## Emails (module 1 layer, after commit)
New request → psychologist; confirmed / new time proposed / cancelled by the
psychologist → patient; proposal accepted / cancelled by the patient → psychologist.
The psychologist's emails never name the patient; no email has the video link. No
reminders yet.

## Manual steps (Bilal)
1. **Before deploying:** enable `btree_gist` on Supabase (Database → Extensions →
   `btree_gist`). Details and the fallback in `docs/deployment.md`, "Supabase
   settings". The migration also runs `CREATE EXTENSION IF NOT EXISTS`.
2. After the deploy, optionally re-run `seed_demo` (gives every demo psychologist a
   fee, hours Mon–Fri 10:00–17:00 and a fake Zoom link, plus one request from demo
   patient 1 to Dr. Sara Ahmed).
