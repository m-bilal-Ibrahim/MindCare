# Handoff: therapy notes — Phase 2 module 5 (6.4)

Base: `/api/v1/clinical-notes/`. Bearer JWT. Decisions: `docs/decisions.md`
(2026-11-18). Field rules and exact messages: `docs/validation-rules.md`.

**Who:** only the patient's **current** psychologist (accepted relationship, approved
and active), addressed by the relationship id (the same id as
`/relationships/patients/{id}/`). Notes belong to the patient–psychologist pair, so
if a patient comes back, the old notes show again. Patients and admins never see
notes. Every psychologist call is audited. Writes are throttled (`clinical_notes`,
120/hour).

## Psychologist (MindCare Web)

| Method | Path | Body / notes |
|---|---|---|
| GET | `patients/{rel}/notes/` | paginated, newest first |
| POST | `patients/{rel}/notes/` | `{"session": 41?, "observations"?, "interventions"?, "plan"?, "progress_rating": 1-10?, "risk_level": "low"\|"medium"\|"high"?}` → 201 |
| GET | `patients/{rel}/notes/{id}/` | one note with its addenda |
| PATCH | `patients/{rel}/notes/{id}/` | any of the fields above except `session`; only while `is_locked` is false |
| GET | `patients/{rel}/notes/{id}/versions/` | every saved version, oldest first |
| POST | `patients/{rel}/notes/{id}/addenda/` | `{"text": "…"}` → 201; any time; can't be edited |
| GET | `patients/{rel}/progress/` | rated notes oldest first, for a chart |
| GET / PUT | `patients/{rel}/summary/` | `{"text": "…"}` — the summary **the patient sees** |

There is no DELETE. Every section is optional, but a note needs at least one section,
the rating or the risk level. `session` must be one of this pair's confirmed /
completed / no-show sessions (from `/appointments/psychologist/sessions/`), one note
per session.

Note:
```json
{"id": 9, "session_id": 41, "session_starts_at": "2026-11-17T05:00:00Z",
 "observations": "Reports sleeping poorly before exams.", "interventions": "",
 "plan": "Sleep diary for two weeks.", "progress_rating": 4, "risk_level": "medium",
 "version": 2, "created_at": "2026-11-18T06:10:00Z", "updated_at": "…",
 "locked_at": "2026-11-19T06:10:00Z", "is_locked": false,
 "addenda": [{"id": 3, "text": "Exams moved to June.", "created_at": "…"}]}
```
Show a countdown to `locked_at`; once `is_locked` is true, hide Edit and show
"Add addendum". Empty sections come back as `""`.

Progress point:
```json
{"note_id": 9, "date": "2026-11-18T06:10:00Z", "session_id": 41,
 "session_starts_at": "…", "progress_rating": 4, "risk_level": "medium"}
```
Either value can be null. Ask for both ratings on the "after session" form, since
the chart only includes notes with a rating.

Summary: `{"text": "You are sleeping better…", "updated_at": "…"}` (`text` null if
none). Say next to the field that the patient reads it word for word.

## Patient (MindCare App)
`GET me/progress/`:
```json
{"sessions": {"completed": 3, "upcoming": 1},
 "summary": {"text": "You are sleeping better…",
             "psychologist": {"id": 7, "full_name": "Dr. Sara Ahmed"},
             "updated_at": "…"},
 "mood": {"today": "2026-11-18", "streak": 3, "windows": {"7": {…}, "30": {…}, "90": {…}}}}
```
`summary` is null until a psychologist writes one. `mood` is the same shape as
`journals/check-ins/insights/`.

## Errors
| Status | Body / when |
|---|---|
| 400 | field rules; `{"non_field_errors": ["Write at least one section or add a progress rating or risk level."]}`; `{"non_field_errors": ["This note is locked (24 hours after it was written). Add an addendum instead."]}`; `{"session": ["Choose one of this patient's confirmed or past sessions."]}` / `["This session already has a note. Open it instead."]` |
| 401 | Token missing or expired: refresh, then sign in |
| 403 | Wrong role (patient, admin, NGO), or the psychologist isn't approved and active |
| 404 | Not your current patient (also after care ends), or no such note |
| 405 | DELETE (notes are never deleted) |
| 429 | Too many writes |

## Manual steps (Bilal)
1. Nothing to configure: new tables only (`clinical_notes.0001`, `audit.0005`); the
   deploy runs the migrations.
2. Optionally re-run `seed_demo` after deploying: Dr. Sara Ahmed gets two fictional
   notes about demo patient 1 (one locked, one still editable) and a summary.
3. Deleting a test account with notes: run the updated SQL in
   `docs/deployment.md` ("Removing test data"), which now deletes notes and
   summaries first. Never for real patients: they are anonymised, not deleted.
