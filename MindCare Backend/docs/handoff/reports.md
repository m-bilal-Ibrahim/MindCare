# Handoff: 6.14 patient reports

A report on one of the psychologist's current patients over a week, a month or a
custom range: sessions, therapy-note ratings and risk levels, mood, care-plan
adherence and SOS alerts, compared with the previous period, ready for charts.
Decisions: `docs/decisions.md` (2026-11-23). Query rules and exact messages:
`docs/validation-rules.md`. Needs `Authorization: Bearer <access>`; handle 401
(refresh, then login), 403, 404 and 429 as elsewhere. The backend cold-starts in about
40 s, so show a loader.

## Endpoint (MindCare Web, psychologist)

`GET /api/v1/reports/psychologist/patients/{relationship_id}/report/`

`relationship_id` is the id from the current-patients list (the same one the care plan
and notes use). Approved, active psychologists only.

| Query | Values | Default |
|---|---|---|
| `period` | `week` (Monday–Sunday), `month`, `custom` | `week` |
| `start` | week / month: any day inside it. custom: the first day (required) | the current week / month |
| `end` | custom only: the last day (required), at most 183 days after `start` | — |

Dates are the **patient's** local days (`period.timezone`). The current week or month
is allowed and comes back with `is_partial: true`. A period is clipped to the day care
with this patient started (`clipped_to_care_start: true`) and to today.

```
GET .../report/
GET .../report/?period=week&start=2026-11-16
GET .../report/?period=month&start=2026-10-01
GET .../report/?period=custom&start=2026-08-26&end=2026-11-23
```

Suggested UI: a period switch (Week / Month / Custom) with previous / next arrows that
move `start` by a week or a month, and a date-range picker for Custom limited to 183
days. Print with the browser (`window.print()`); there is no PDF endpoint.

## Errors

| Status | When | Body |
|---|---|---|
| 400 | bad `period`, an unknown query key, or a period rule | `{"period": [...]}`, `{"start": ["The period can't start in the future."]}`, `{"start": ["Choose a period after care with this patient started on 2026-08-20."]}`, `{"start": ["Choose a start and an end date for a custom period."]}`, `{"end": ["An end date is only for custom periods."]}`, `{"end": ["The end date can't be before the start date."]}`, `{"end": ["A custom period can be at most 183 days."]}`, `{"days": ["This field can't be set."]}` |
| 403 | not a psychologist, or not approved / paused | `{"detail": "..."}` |
| 404 | not your current patient (former, someone else's, unknown) | `{"detail": "..."}` |
| 429 | more than 30 reports an hour | `{"detail": "..."}` |

## Response

Shortened example (custom, 90 days, from the demo data):

```json
{
  "generated_at": "2026-11-23T04:10:00Z",
  "relationship_id": 4,
  "patient": {"display_name": "Hina Raza"},
  "period": {
    "type": "custom", "start": "2026-08-26", "end": "2026-11-23",
    "data_start": "2026-08-26", "data_end": "2026-11-23", "days": 90,
    "is_partial": false, "clipped_to_care_start": false,
    "care_started_on": "2026-08-20", "timezone": "Asia/Karachi", "granularity": "week"
  },
  "previous_period": {"start": "2026-08-20", "end": "2026-08-25"},
  "sessions": {
    "completed": 8, "no_show": 2,
    "cancelled_by_patient": {"on_time": 0, "late": 1},
    "cancelled_by_psychologist": 1, "cancelled_by_system": 0, "expired": 0,
    "attendance_rate": 80, "minutes_attended": 400, "next_confirmed_at": null,
    "series": {
      "completed": [{"date": "2026-08-24", "value": 0}, {"date": "2026-08-31", "value": 1}],
      "no_show": [{"date": "2026-08-24", "value": 0}, {"date": "2026-08-31", "value": 0}]
    }
  },
  "therapy_notes": {
    "count": 5,
    "progress": {"rated_notes": 5, "first": 2, "last": 6, "average": 3.6, "change": 4},
    "risk": {"counts": {"low": 1, "medium": 3, "high": 1}, "first": "high", "latest": "low"},
    "series": {
      "progress_rating": [{"date": "2026-08-31", "value": 2.0}],
      "risk_level": [{"date": "2026-08-31", "value": "high"}]
    }
  },
  "mood": {
    "check_ins": 80, "days_with_check_in_percent": 89, "average_mood": 3.02,
    "distribution": {"1": 6, "2": 20, "3": 27, "4": 20, "5": 7},
    "top_tags": [{"tag": "calm", "count": 22}, {"tag": "tired", "count": 22}],
    "longest_streak": 8,
    "series": {"average_mood": [{"date": "2026-08-24", "value": 2.2}]}
  },
  "care_plan": {
    "has_plan": true, "adherence": 51, "completions": 60, "average_difficulty": 2.78,
    "completion_notes": 5, "goals_achieved": 0, "goals_dropped": 0,
    "legacy_items_excluded": 0,
    "goals": [{
      "id": 3, "title": "Build a gentle exercise habit", "category": "exercise",
      "status": "active", "adherence": 54,
      "tasks": [
        {"id": 7, "title": "Twenty-minute walk", "frequency": "weekly",
         "times_per_week": 3, "status": "active", "completions": 30,
         "adherence": 81, "done_in_period": null},
        {"id": 8, "title": "Morning stretching", "frequency": "daily",
         "times_per_week": null, "status": "archived", "completions": 20,
         "adherence": 36, "done_in_period": null}
      ]
    }],
    "series": {"adherence": [{"date": "2026-08-24", "value": 40.0}]}
  },
  "sos": {"count": 1, "alerts": [{"date": "2026-10-14", "status": "closed"}]},
  "sensors": {"available": false},
  "comparison": {
    "attendance_rate": {"current": 80.0, "previous": null, "change": null},
    "average_mood": {"current": 3.02, "previous": null, "change": null},
    "adherence": {"current": 51.0, "previous": null, "change": null},
    "average_progress_rating": {"current": 3.6, "previous": null, "change": null}
  },
  "indicators": [
    {"code": "risk_level_changed", "message": "Risk level went from high to low."},
    {"code": "no_shows", "message": "2 no-shows."},
    {"code": "late_cancellations", "message": "1 late cancellation by the patient."},
    {"code": "sos_alerts", "message": "1 SOS alert in this period."}
  ]
}
```

Notes for the screens:

- **Series** are `[{"date", "value"}]`, one point per bucket, `null` where there is no
  data (draw a gap, not a zero). `period.granularity` is `day` (up to 31 days) or
  `week` (longer; `date` is the week's Monday, and the first and last weeks may be
  partial).
- **Percentages** (`attendance_rate`, `adherence`, `days_with_check_in_percent`) are
  whole numbers 0–100, or `null` when there's nothing to measure (no sessions held,
  no task scheduled).
- **Comparison:** `previous` / `change` are `null` when the previous period has no
  data or is before care started. Show change with an arrow; don't colour it as good
  or bad, since that's the psychologist's judgement.
- **Indicators** are plain factual sentences; list them as they are. There are no
  clinical thresholds behind them.
- **Care plan:** `adherence: null` on a task means it wasn't scheduled in the period;
  one-off tasks use `done_in_period`. In a report, today counts only once a task has
  been done today. If `legacy_items_excluded > 0`, show "N items archived before
  23 Nov 2026 aren't included."
- **Sensors:** show "Wearable data isn't available yet" while `available` is false.
- **Privacy:** the report never contains note text, the progress summary, check-in
  notes, completion note text, journal entries, SOS locations or contacts, or fees.
  Every report is audited.

## Seed data

`seed_demo` gives demo patient Hina Raza and Dr. Sara Ahmed (`demo.psych.sara@example.com`)
about 90 days of history: care started 95 days ago, check-ins most days, five rated
notes (risk high → medium → low), weekly past sessions with completed, no-show, late
and psychologist cancellations, an older exercise goal with an archived daily task,
and one closed SOS. Try `?period=custom` over the last 90 days and `?period=month`.
