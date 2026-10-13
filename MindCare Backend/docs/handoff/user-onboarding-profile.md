# Handoff: 6.1 User onboarding and profile (App; plus Web for psychologists)

Bearer JWT required. 401 means refresh, then sign in. Errors are
`{"field": ["message"]}`; the messages are in `docs/validation-rules.md`.

## Signup (unchanged)
`POST /api/v1/accounts/register/` with JSON (`email`, `password`, `full_name`,
`role: "patient"`, `is_adult_confirmed: true`, `profile: {timezone}`). Right after
signup and sign-in, show a **skippable "complete your profile" step** driven by
`profile_completion.missing` from `GET /patients/me/`.

## `GET /api/v1/patients/me/` (new fields)

```json
{
  "photo_url": "https://...signed...",
  "privacy": {
    "is_profile_public": false,
    "shown_when_public": ["full_name", "photo"],
    "always_private": ["date_of_birth", "gender", "phone_number", "mental_health_history"]
  },
  "profile_completion": {"missing": ["gender", "phone_number", "photo", "mental_health_history"]}
}
```
`photo_url` is signed and works for about 5 minutes; refetch `me` to get a fresh one,
and don't cache it. Editing fields stays `PATCH /patients/me/`.

**Privacy screen:** one switch (`PATCH {"is_profile_public": true|false}`). Show the
two lists from `privacy` so the user sees exactly what the switch reveals, plus the
existing warning that going public can't be undone.

## Photo
- `PUT /api/v1/patients/me/photo/`: `multipart/form-data` with one `photo` file
  (JPG, PNG or WEBP, max 5 MB). Returns the full `me` body. The server removes EXIF
  (GPS location) and shrinks the image to 1024 px.
- `DELETE /api/v1/patients/me/photo/`: removes it and returns `me`.
- Errors (400): `{"photo": ["Choose a photo to upload."]}`,
  `{"photo": ["Photo must be one of: JPG, PNG, WEBP."]}`,
  `{"photo": ["Photo must be 5 MB or smaller."]}`,
  `{"photo": ["Photo isn't a readable image."]}`. 429 after 20 uploads an hour.
- Who sees a patient's photo: the patient, their current psychologist and admins;
  anyone else only if the profile is public.
- Psychologists (Web): the same endpoints at `/api/v1/psychologists/me/photo/`. The
  photo appears on directory cards (`photo_url`) in the App.

## Mental health history (optional)
- `GET /api/v1/patients/me/history/` →
  ```json
  {"concerns": [{"slug": "anxiety", "name": "Anxiety"}], "previous_diagnosis": "yes",
   "current_medication": null, "previous_therapy": "no", "notes": "...",
   "is_empty": false, "updated_at": "2026-10-11T10:00:00Z"}
  ```
  An empty history returns `is_empty: true` with nulls.
- `PUT /api/v1/patients/me/history/` **replaces the whole history** (anything not
  sent is cleared):
  `{"concerns": ["anxiety", "sleep-issues"], "previous_diagnosis": "yes" | "no" | "prefer_not_to_say", "current_medication": ..., "previous_therapy": "yes" | "no", "notes": "10-1000 chars"}`.
  Concern options come from `GET /api/v1/reference/specializations/`.
- `DELETE /api/v1/patients/me/history/` → 204.
- Tell the user, in the screen: it's encrypted, only they and their **current**
  psychologist can read it, and every time the psychologist opens it, that's
  recorded.

**Psychologist (Web, patient detail):** `GET /api/v1/relationships/patients/{relationship_id}/history/`,
with the same shape, for the current assigned psychologist only (404 otherwise).
Each open is audited, so load it when the psychologist opens that tab, not in a list.
Patient detail (`/relationships/patients/{id}/`) now also has `photo_url`.

## Screens
- **App:** sign-up (unchanged), "complete your profile" step, profile view/edit with
  photo picker (camera or gallery), privacy screen, mental health history form
  (multi-select concerns, three radio groups, optional notes with live character
  count). Loaders for the ~40 s cold start; field errors from the backend under each
  field.
- **Web:** therapist profile photo upload; patient detail shows the photo and a
  "History" tab.
