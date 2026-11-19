# Handoff: secure messaging (patient ↔ psychologist)

Base: `/api/v1/messaging/`. Bearer JWT. Patients (MindCare App) and approved
psychologists (MindCare Web). Decisions: `docs/decisions.md` (2026-11-19).

- **One conversation per patient–psychologist pair.** It exists as soon as the
  psychologist accepts the request.
- **Only the two participants can open it.** Anyone else gets 404 (admins,
  other psychologists, and a **former** psychologist once care has ended).
- **Care ended:** the patient can still read (`can_send: false`); sending → 403.
- **Text only**, 1–2000 characters. No attachments, no editing. You can delete
  your own message within 5 minutes; it then shows as "Message deleted".
- **No push and no websockets:** poll the open conversation every **10 s**
  (`GET .../messages/`, first page) and `unread-count/` every **60 s** (and on
  app resume / tab focus).

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `conversations/` | Your conversations, most recent first. Never any message text |
| GET | `conversations/{id}/` | One conversation plus `safety_notice` |
| GET | `conversations/{id}/messages/` | Newest first. `?limit=` 1–50 (default 30), `?before=<message id>` for older ones |
| POST | `conversations/{id}/messages/` | `{"body": "..."}` → 201 with the message |
| POST | `conversations/{id}/read/` | No body. Marks the other side's messages read → `{"count": 2}` |
| DELETE | `conversations/{id}/messages/{message_id}/` | Your own, within 5 min → 204 |
| GET | `unread-count/` | `{"count": 3}` across all conversations |

Conversation:
```json
{"id": 4, "other_party": {"id": 12, "role": "psychologist", "name": "Dr. Sara Ahmed"},
 "last_message_at": "2026-11-19T09:12:03Z", "unread_count": 1, "can_send": true,
 "safety_notice": "Messages are not for emergencies ... press the SOS button ..."}
```
`safety_notice` is only on the detail. Show it **above the composer, always**,
with a button that opens SOS. For a psychologist, `other_party.id` is the patient
profile id and the name is the patient's real name (they are the current
psychologist).

Messages page:
```json
{"results": [{"id": 88, "body": "Thank you, see you Friday.", "is_mine": true,
  "is_deleted": false, "can_delete": true, "created_at": "...", "read_at": null}],
 "next_before": 61}
```
Deleted: `body: null`, `is_deleted: true` → show "Message deleted". `next_before`
is null when there is nothing older. `read_at` on your own message means the
other side has read it.

## Errors

| Status | When | Body |
|---|---|---|
| 400 | Bad body | `{"body": ["Message must be between 1 and 2000 characters."]}` (rules in `docs/validation-rules.md`, "Message") |
| 400 | Delete too late / twice | `{"non_field_errors": ["Messages can only be deleted within 5 minutes of sending."]}` |
| 403 | Sending after care ended | `{"detail": "This conversation is read-only because care with this psychologist has ended."}` |
| 403 | Deleting someone else's message | `{"detail": "You can only delete your own messages."}` |
| 404 | Not your conversation | — |
| 429 | More than 30 messages in 10 minutes (reads: 240/min) | DRF throttle message |

## Notifications

Each message creates a `new_message` notification for the other side: "New
message" / "You have a new message.", `target_type: "conversation"`,
`target_id` = conversation id. Never the text or the sender.

## Screens

- **App (patient):** a "Messages" entry (unread badge) → the conversation with
  their psychologist, plus older read-only ones. Composer disabled with the 403
  text when `can_send` is false. 2000-character counter; send disabled while the
  text is empty or invalid.
- **Web (psychologist):** a "Messages" tab on the patient detail page, and an
  inbox from `conversations/`.

Demo: Hina Raza and Dr. Sara Ahmed have a short conversation (`seed_demo`).
