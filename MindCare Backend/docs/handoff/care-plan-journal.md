# Handoff: care plan + private journal

Backend for the care plan (psychologist sets goals and tasks for a current patient,
the patient tracks them) and the patient's private journal. Decisions:
`docs/decisions.md` (2026-11-19). Field rules and exact messages:
`docs/validation-rules.md`. All endpoints need `Authorization: Bearer <access>`; handle
401 (refresh, then login), 403, 404 and 429 as elsewhere. Errors are DRF's usual
`{"field": ["message"]}` / `{"non_field_errors": [...]}` / `{"detail": "..."}`.

## Care plan

### Psychologist (MindCare Web)

Base: `/api/v1/recommendations/psychologist/patients/{relationship_id}/care-plan/`,
where `relationship_id` is the id from the current-patients list. Approved, active
psychologists only; a patient who isn't your current patient → 404. Every read and
write is audited.

| Method | Path | What |
|---|---|---|
| GET | `` | The plan: goals, tasks, adherence. `id: null`, `goals: []` if none yet |
| POST | `goals/` | Add a goal (creates the plan) |
| PATCH | `goals/{goal_id}/` | Edit a goal or set `status` (`active` / `achieved` / `dropped`) |
| POST | `goals/{goal_id}/tasks/` | Add a task to an active goal |
| PATCH | `tasks/{task_id}/` | Edit a task or archive it (`status: "archived"`) |
| GET | `completions/?days=30` | The patient's completions (7 / 30 / 90 days), with notes and difficulty |
| GET | `versions/` | Every saved version (full snapshot), newest first |

Nothing is ever deleted: drop goals, archive tasks. Every change saves a version and
sends the patient a "care plan updated" notification (no content).

```json
POST goals/
{"title": "Sleep better before exams", "category": "sleep",
 "description": "Build a steady evening routine.", "target_date": "2027-01-15"}

POST goals/12/tasks/
{"title": "Keep a sleep diary", "frequency": "daily",
 "instructions": "Write down bedtime, wake time and how rested you feel."}

POST goals/12/tasks/
{"title": "No screens before bed", "frequency": "weekly", "times_per_week": 4,
 "start_date": "2026-11-20", "end_date": "2027-01-15"}
```

Plan response (`GET`, also the patient's detail):

```json
{
  "id": 3, "version": 5, "created_at": "...", "updated_at": "...",
  "can_track": true, "today": "2026-11-19",
  "psychologist": {"id": 1, "name": "Dr. Sara Ahmed"},
  "adherence": {"7": 64, "30": 64, "90": 64},
  "goals": [{
    "id": 12, "title": "...", "description": "...", "category": "sleep",
    "target_date": "2027-01-18", "status": "active", "created_at": "...",
    "updated_at": "...", "adherence": {"7": 60, "30": 60, "90": 60},
    "tasks": [{
      "id": 30, "title": "...", "instructions": "...", "frequency": "daily",
      "times_per_week": null, "start_date": null, "end_date": null,
      "status": "active", "created_at": "...", "updated_at": "...",
      "done_today": false, "last_completed_on": "2026-11-18",
      "is_done": null, "adherence": {"7": 71, "30": 50, "90": 50}
    }]
  }]
}
```

Adherence is a % (0–100) or `null` when nothing recurring was scheduled. One-off tasks
show `is_done` instead and aren't in the percentages; archived tasks and
achieved / dropped goals aren't either.

Errors to show as they come: `Target date must be between today and one year from
now.`, `Dates must be between today and one year from now.`, `End date can't be before
the start date.`, `Choose how many times a week (1 to 7).`, `Times per week is only for
weekly tasks.`, `A care plan can have at most 10 active goals.`, `A goal can have at
most 10 active tasks.`, `A care plan can have at most 30 active tasks.`, `You can only
add tasks to an active goal.` Writes: 120 an hour (429).

**Screens (Web):** the patient page's "Care plan" tab (replace the mock care-plan
editor): goals with their tasks and adherence, add / edit goal and task forms (category
and frequency dropdowns, date pickers, times-per-week only for weekly), achieve / drop
and archive actions, a completions list with notes, and a version history view.

### Patient (MindCare App)

Base: `/api/v1/recommendations/`. Patients only. Not audited when reading.

| Method | Path | What |
|---|---|---|
| GET | `care-plans/` | Your plans (one per psychologist you have had): `id`, `psychologist`, `can_track`, `active_goals`, `updated_at` |
| GET | `care-plans/{id}/` | The plan (same shape as above) |
| GET | `care-plans/{id}/completions/?days=30` | Your completions |
| POST | `care-plans/{id}/tasks/{task_id}/completions/` | Mark a task done |
| DELETE | `care-plans/{id}/tasks/{task_id}/completions/{completion_id}/` | Undo (only on the day you marked it) |

```json
POST care-plans/3/tasks/30/completions/
{"local_date": "2026-11-18", "note": "Fell asleep faster tonight.", "difficulty": 2}
```

`local_date` is optional (default today) and may only be today or yesterday. Show the
note field as "Your psychologist can read this". When `can_track` is false (care ended or
the psychologist is paused), show the plan read-only: logging answers 403 `This care
plan is read-only because care with this psychologist has ended or is paused.` Other
errors: `You can mark a task done for today or yesterday only.`, `This task isn't
scheduled for that day.`, `You've already marked this task done for that day.`, `This
one-off task is already done.`, `This task isn't active any more.`, `You can only undo a
completion on the day you marked it.` Logging: 60 an hour.

**Screens (App):** a "My care plan" screen (today's tasks with a done checkbox, goals with
progress bars from `adherence`), a "mark done" sheet (yesterday toggle, optional note,
difficulty 1–5), and a read-only state for older plans. Tapping the `care_plan_updated`
notification opens the plan (`target_id` is the plan id).

## Private journal (MindCare App)

Base: `/api/v1/journals/entries/`. Patients only, their own entries only. **Nobody else
can read the journal: there is no psychologist or admin endpoint.** Title, body and tags
are encrypted. Writes and deletes are audited (ids only).

| Method | Path | What |
|---|---|---|
| GET | `?date_from=&date_to=&tag=&page=` | Your entries, newest first, paginated, plus `safety_notice` |
| POST | `` | New entry for today (your local day) |
| GET | `{id}/` | One entry |
| PATCH | `{id}/` | Edit any field at any time; `check_in: null` unlinks |
| DELETE | `{id}/` | Delete for good (ask the patient to confirm) |

```json
POST /api/v1/journals/entries/
{"title": "A hopeful afternoon", "body": "Revised for two hours and still went for a walk.",
 "tags": ["hopeful"], "check_in": 41}
```

```json
{"id": 7, "local_date": "2026-11-19", "title": "A hopeful afternoon",
 "body": "...", "tags": ["hopeful"], "check_in": 41,
 "created_at": "...", "updated_at": "..."}
```

The list response is the usual paginated object (`count`, `next`, `previous`,
`results`) with an extra `safety_notice`; show it on the journal screen with links to SOS
and the helplines. There is no text search (entries are encrypted); filter by dates and
one feeling tag. `check_in` must be your check-in from the same day as the entry
(`GET /journals/check-ins/today/` gives today's). Errors: `Write something in your
entry.`, `Title must be between 3 and 120 characters.`, `Entry must be between 10 and
10000 characters.`, `Choose at most 5 feelings.`, `Choose your mood check-in from the
same day as this entry.`, `You can write at most 20 journal entries a day.`, `The start
date must be on or before the end date.` Writes: 60 an hour.

**Screens (App):** journal list (date filter, feeling chips, safety notice), an editor
(optional title, body with a 10,000-character counter, up to 5 feelings, "link today's
check-in" toggle) and a delete confirmation.

## Demo data (`seed_demo`)

Hina Raza (demo patient 1) ↔ Dr. Sara Ahmed: one plan with 2 goals ("Sleep better before
exams", "Feel calmer in group settings") and 3 tasks (two daily, one 4× a week), added
10 days ago, with completions on several of the last 6 days (two with notes). Hina also
has 2 private journal entries (3 days ago and yesterday). Added once; re-running skips
them.
