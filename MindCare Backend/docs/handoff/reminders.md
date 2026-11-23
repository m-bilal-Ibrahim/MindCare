# Handoff: scheduled reminders and reminder settings

Decisions: `docs/decisions.md` (2026-11-23, scheduler). Reminders are ordinary
in-app notifications (`docs/handoff/notifications.md`), created by a scheduled job
every 15 minutes; a few also go by email. Clients need **no new polling**: the
bell's 60-second `unread-count/` poll picks them up.

## Endpoints

Base: `/api/v1/notifications/`. Bearer JWT, **every role**. Throttle 120/min.

| Method | Path | Notes |
|---|---|---|
| GET | `preferences/` | Your switches; all `true` until you change one |
| PATCH | `preferences/` | Any subset of the three booleans. Another key → 400 `This field can't be set.`; a non-boolean → 400 `Must be a valid boolean.` |

```json
{"check_in_reminders": true, "care_plan_reminders": true, "session_reminder_emails": true}
```

| Field | Who it matters to | What it switches |
|---|---|---|
| `check_in_reminders` | patient | the 20:00 "you haven't checked in today" reminder |
| `care_plan_reminders` | patient | the 18:00 "care-plan tasks for today" reminder |
| `session_reminder_emails` | patient, psychologist | the **email** copy of the 24-hour session reminder |

The in-app session and care-request reminders **can't be turned off** (they're about
a session or request the user already made or must answer). Show the switches that
matter to the role: the App shows all three; the Web shows `session_reminder_emails`
only.

## The reminders

All times are the **recipient's** profile timezone (Asia/Karachi if unset). Quiet
hours 22:00–08:00 apply to the care-plan and check-in reminders only.

| `type` | Who | When | Email too? | Tap → |
|---|---|---|---|---|
| `session_reminder` | patient and psychologist | ~24 h before a confirmed session (only if it was confirmed at least 24 h ahead) and again 5–90 min before | the 24 h one, unless `session_reminder_emails` is off | `session` → session detail (video link) |
| `care_request_expiring` | psychologist | a pending care request expires within 5 h | yes (always) | `care_relationship` → request inbox |
| `care_plan_reminder` | patient | once a day, 18:00–22:00, if a task of the current care plan is due today and not done | no | `care_plan` → that plan |
| `check_in_reminder` | patient | once a day, 20:00–22:00, if there's no mood check-in today | no | `check_in` (`target_id` null) → today's check-in |

Wording is fixed and never contains names, task titles or anything about mood. The
psychologist's notification and email never name the patient.

GitHub's scheduler can run late; a reminder may arrive up to ~30 minutes after the
times above, and one that's no longer useful (the session has started, the day is
over) is skipped. A reminder is never sent twice.

## Screens (partner)

- **App, Settings → Reminders:** three switches; `PATCH` on toggle, revert and show
  the backend message on error. Loader (cold start ~40 s), 401 (refresh, then login),
  429.
- **Web, Settings:** one switch, "Email me a reminder the day before a session".
- **Both:** route the four new `type`s from the bell as in the table.
