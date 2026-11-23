# Handoff: 6.9 wellness library (App: patient; Web: psychologist + admin)

Admin-managed general wellbeing content: articles, guided practices and
routines. Patients browse and save items; psychologists browse them and link one
to a care-plan task; admins write and publish them. Rules and messages:
`docs/validation-rules.md` (wellness rows). Decision: `docs/decisions.md`,
2026-11-23.

**Important:** the 14 seeded items are **hidden placeholders** that a clinical
advisor must review before an admin publishes them. Until something is published,
the library is empty: show the empty state.

`W` = `/api/v1/wellness/`. All endpoints need a Bearer JWT.

## Values

- `kind`: `article` (read), `practice` (guided steps, e.g. breathing), `routine`
  (an exercise or yoga sequence)
- `category`: `nutrition`, `exercise`, `yoga`, `stress_reduction`, `mindfulness`,
  `relaxation`, `sleep`
- `difficulty`: `gentle`, `moderate`, `demanding`

## Library (patients, and approved, active psychologists)

Throttle `wellness`, 120/min. Anyone else gets 403.

### `GET W items/`
Query (all optional): `category`, `kind`, `difficulty`, `max_duration` (1–180),
`search` (title and summary, 120 characters), `page`, `page_size` (max 50).
Sorted by the admin's order, then newest.

```json
{
  "count": 1, "next": null, "previous": null,
  "disclaimer": "General wellbeing information, not medical advice. Talk to your psychologist or doctor before starting something new.",
  "results": [
    {"id": 7, "kind": "practice", "category": "stress_reduction",
     "title": "Box breathing", "summary": "Breathe in, hold, ...",
     "duration_minutes": 3, "difficulty": "gentle",
     "image_url": null, "has_audio": false, "is_favourite": false}
  ]
}
```
`is_favourite` is `null` for psychologists. `image_url` is a signed link that works for a
few minutes: don't cache it, fetch the list again.

### `GET W items/{id}/`
The fields above, plus:

| Field | Type | Notes |
|---|---|---|
| `body` | string | Plain text; keep the line breaks. May be `""` for practices and routines |
| `steps` | array of string | In order; may be empty for articles |
| `safety_note` | string or null | Show it above the steps when present |
| `source` | string or null | |
| `video_url` | string or null | YouTube or Vimeo; open outside the app |
| `audio_url`, `audio_type` | string or null | Signed link (a few minutes); `mp3`, `m4a` or `ogg` |
| `breathing` | object or null | Practices only: `breath_in_seconds`, `breath_hold_seconds`, `breath_out_seconds`, `breath_hold_after_out_seconds`; feed the breathing player |
| `updated_at` | date-time | |
| `disclaimer` | string | Show it on the item screen |

404 for an unknown or hidden item.

## Favourites (patients only)

- `PUT W items/{id}/favourite/` (no body) → 200 `{"is_favourite": true}`. Saving again
  changes nothing. 404 if the item isn't published; 400
  `{"non_field_errors": ["You can save up to 200 items."]}`. Throttle 60/hour.
- `DELETE W items/{id}/favourite/` → 204 (also when it wasn't saved).
- `GET W favourites/` → paginated cards (same shape as the list) of saved items
  that are still published, newest save first.

Favourites are private: nobody else sees them.

## Care plan link (psychologist, Web)

The existing task endpoints take one new optional key:

- `POST .../care-plan/goals/{goal_id}/tasks/` and `PATCH .../care-plan/tasks/{task_id}/`:
  `"content": <item id>` links a published item, `"content": null` removes the link.
  Not published → 400 `{"content": ["Choose a published item from the wellness library."]}`.
  The write result returns `content` as the id (or null).
- Every plan response (psychologist and patient) now has `content` on each task:

```json
"content": {"id": 7, "is_available": true, "kind": "practice",
            "category": "stress_reduction", "title": "Box breathing",
            "duration_minutes": 3, "message": null}
```
When an admin later hides the item: `{"id": 7, "is_available": false, "kind": null,
"category": null, "title": null, "duration_minutes": null, "message": "This resource is no
longer available."}`; show `message`, no link. `content` is `null` when nothing is
linked. Versions include `content` (the id) from now on.

Linking changes the plan, so the patient gets the usual `care_plan_updated`
notification. Completing the task stays the progress signal: the library has no
tracking of its own.

## Admin console (Web; any admin)

Throttle `admin`; uploads also 20/hour.

| Method + path | What |
|---|---|
| `GET W admin/items/` | Every item, `?is_published=true/false`, `?category=`, `?kind=`; paginated |
| `POST W admin/items/` | Create (hidden unless `is_published: true`) |
| `GET/PATCH W admin/items/{id}/` | Read / edit; `is_published: false` hides it |
| `DELETE W admin/items/{id}/` | 204; 400 `{"non_field_errors": ["This item has been used in a care plan. Hide it instead."]}` once it was ever linked |
| `PUT/DELETE W admin/items/{id}/image/` | multipart `image`: JPG / PNG / WEBP, 5 MB |
| `PUT/DELETE W admin/items/{id}/audio/` | multipart `audio`: MP3 / M4A / OGG, 15 MB |

The admin item has every field above (as stored: `""` instead of null) plus
`sort_order`, `is_published`, `ever_linked`, `image_type`, `image_url`, `audio_type`,
`audio_url`, `created_at`. Articles need `body`; practices and routines need at
least one step. The breathing pattern is for practices only, all four values or none.

## Errors (all endpoints)

400 field errors as in validation-rules.md; 401 refresh then sign in; 403 wrong
role (a paused psychologist too); 404; 429 throttled. The backend cold-starts in
about 40 s: show a loader.

## Screens

- **App:** a library tab (category chips, kind / duration filters, search, cards
  with a heart), item detail (disclaimer, safety note, steps, audio player, video
  button, breathing player when `breathing` is set), saved items, and on a care-plan
  task the linked item (or the "no longer available" message). Replace the mock
  program and breathing data with these.
- **Web (psychologist):** a library browser, and an item picker on the care-plan
  task form (`content`).
- **Web (admin):** a wellness content list with publish / hide, an editor, and
  image / audio upload.

## Manual step for existing admins

Ordinary admins get the new Django admin permissions when the group is next
refreshed. After deploying, run once:
`python manage.py shell -c "from apps.accounts.services import ensure_admin_group; ensure_admin_group()"`
