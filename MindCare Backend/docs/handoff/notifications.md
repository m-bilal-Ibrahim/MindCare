# Handoff: in-app notifications

Base: `/api/v1/notifications/`. Bearer JWT, **every role** (patient, psychologist,
admin, NGO). Decisions: `docs/decisions.md` (2026-11-18). Throttle: 120 requests a
minute per user (429 above that).

Everyone sees **only their own** notifications; another user's id answers 404.
Notifications are kept 90 days, then deleted.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `` (the base) | Paginated (`page`, `page_size` ≤ 50), newest first. `?unread=true` unread only; `?type=<type>` one type. A bad value → 400 |
| GET | `unread-count/` | `{"count": 3}` — **poll every 60 s** for the bell badge (and on app resume / tab focus) |
| POST | `{id}/read/` | No body. Returns the notification with `is_read: true` |
| POST | `read-all/` | No body. `{"updated": 3}` |
| DELETE | `{id}/` | 204 |

Notification:
```json
{"id": 41, "type": "session_confirmed", "title": "Session confirmed",
 "body": "Your session on Fri 21 Nov 2026, 10:00 (Asia/Karachi) was confirmed. The video link is on the session.",
 "target_type": "session", "target_id": 12, "is_read": false, "read_at": null,
 "created_at": "2026-11-18T09:12:03Z"}
```

Show `title` and `body` as they are: the text is final and never holds names or
health data. On tap: mark it read, then open the screen for `target_type`.

## Types and where a tap goes

| `type` | Who gets it | `target_type` → screen |
|---|---|---|
| `session_requested` | psychologist | `session` → Web: session requests |
| `session_proposal_accepted` | psychologist | `session` → Web: upcoming sessions |
| `session_cancelled` | the other party | `session` → Web: sessions / App: my sessions |
| `session_confirmed` | patient | `session` → App: session detail (video link) |
| `session_proposed` | patient | `session` → App: session detail (accept / cancel) |
| `session_declined` | patient | `session` → App: book a session |
| `session_completed`, `session_no_show` | patient | `session` → App: my sessions (past) |
| `care_requested` | psychologist | `care_relationship` → Web: request inbox |
| `care_accepted` | patient | `care_relationship` → App: my psychologist |
| `care_declined`, `care_ended` | patient | `care_relationship` → App: psychologist directory |
| `sos_alert`, `sos_cancelled` | psychologist | `sos_event` → Web: SOS alerts (`emergency/psychologist/alerts/`) |
| `sos_alert`, `sos_cancelled` | admin | `sos_event` → Web: admin SOS log, open that alert |
| `application_submitted` | admin | `pending_application` (`target_id` = user id) → Web: pending approvals |
| `account_approved`, `account_rejected` | psychologist / NGO | none → Web: dashboard |
| `password_changed` | anyone | none → no navigation |
| `progress_summary_updated` | patient | `progress_summary` → App: my progress |
| `new_message` | the other participant | `conversation` → Web / App: that conversation (`docs/handoff/messaging.md`) |
| `care_plan_updated` | patient | `care_plan` → App: that care plan (`docs/handoff/care-plan-journal.md`) |

`target_type` is `""` and `target_id` is `null` when there's nothing to open. If the
target screen answers 404/403 (e.g. care has ended since), show the backend message.

## Notes for the screens
- Bell icon with the unread count; list with unread rows highlighted; "Mark all as
  read"; swipe / menu to delete.
- No push notifications and no reminders yet (no scheduler): a user sees new items
  only on the next poll or list load. Emails still go out as before.
- Handle 401 (refresh, then login) and 429 (back off; skip the next poll).
