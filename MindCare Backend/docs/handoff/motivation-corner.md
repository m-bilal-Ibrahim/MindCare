# Handoff: 6.10 Motivation Corner (App)

Patients only (Bearer JWT). Throttle `motivation`, 60 requests a minute. 401 means
refresh, then sign in.

## Quotes (unchanged, any logged-in user)
`GET /api/v1/motivation/quotes/?category=hope|resilience|calm|self_care&page=` →
`{count, next, previous, results: [{id, text, author, category}]}`.
`GET /api/v1/motivation/quotes/random/?category=` → one quote (404 if none).

## Opt-in to Quran and dua content (off by default)
- `GET /api/v1/motivation/religious/preference/` → `{"opted_in": false}`
- `PUT /api/v1/motivation/religious/preference/` with `{"opted_in": true}` or
  `{"opted_in": false}` → the same shape. **Turning it off deletes the record.**
- Show it as a clear, optional switch in Motivation Corner settings (for example
  "Show Quran and duas"). It's sensitive (it reveals religious belief), so never
  pre-select it.

## Duas and surahs (only after opting in)
- `GET /api/v1/motivation/duas/` →
  `[{id, title, reference, arabic, transliteration, translation, audio_url}]`
  (`transliteration` and `audio_url` may be null).
- `GET /api/v1/motivation/duas/{id}/` → one dua.
- `GET /api/v1/motivation/surahs/` →
  `[{number, name_arabic, name_english, name_meaning, ayah_count, has_audio}]`.
- `GET /api/v1/motivation/surahs/{number}/` →
  `{number, name_arabic, name_english, name_meaning, ayah_count, arabic, transliteration, translation, audio_url}`.
  `arabic` and `translation` hold one verse per line (`\n`), so show them line by line
  side by side.
- `audio_url` is signed and works for about 5 minutes: fetch the item again right
  before playing. `null` means no recitation yet (hide the play button).
- Not opted in → **403** `{"detail": "Turn on Quran and dua content in your Motivation Corner settings to see this."}`:
  show the switch. Missing or hidden item → 404.

Arabic text: Tanzil Quran Text (Simple), CC BY 3.0, tanzil.net. English: Pickthall
(1930). Show this attribution on the screen (for example in an info sheet).

## Screens (App)
Motivation Corner: the quotes feed (and quote of the moment) on real data; settings
switch for Quran and duas; dua list → dua detail (Arabic right-to-left, translation,
play button if audio); surah list → surah reader. Loaders for the ~40 s cold start;
empty and error states from the backend messages.
