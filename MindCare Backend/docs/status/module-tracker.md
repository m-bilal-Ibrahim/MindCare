# Module tracker

Status of every bullet in the official module list ([../modules.md](../modules.md)),
per component. Built from the 2026-10-08 audit ([2026-10-08-status.md](2026-10-08-status.md))
and checked against `main` at `a295f11`. **Update this file at the end of every module.**

Status values: **done** (works end to end on real data) · **partial** (some of the
bullet works; the note says what's missing) · **mock only** (screens exist with
hardcoded data, no backend calls) · **not started** · **—** (that component has no
role in the bullet).

The Web is the psychologist/admin client; the App is the patient client. "Branch"
means the work sits on an unmerged branch.

Last updated: 2026-11-23 (scheduler and reminders, backend; earlier the same day,
6.9 wellness library and 6.14 reports). Before that: 2026-11-19 (care
plan + private journal, backend; earlier the same day, secure messaging). Before
that: 2026-11-18
(in-app notifications, backend; earlier the same day, Phase 2 module 5: therapy
notes). Before that:
2026-10-28, module 4 (booking and fees), module 3 (mood check-ins) and module 2
(SOS), backend. Before that: 2026-10-19
(Phase 2 module 1: password reset + email, backend).
Before that: 2026-10-15 (Phase 2 module 0: super-admin workflow + admin-panel-2,
backend). Earlier: 2026-10-11 (6.10 backend). Re-checked against `origin` on
2026-10-11: the partner merged Web PRs #38 (city search), #40 (name validation), #44
(pricing) and App PRs #39, #41; her App backend wiring is not on GitHub yet.

## 6.1 User Onboarding and Profile

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Register with name, age, gender, contact details; optional mental health history | done (PR 6.1) | — | partial (branch `mobile/patient-signup-api`) | Quick signup unchanged (Q13); `profile_completion.missing` drives a skippable 'complete your profile' step (DOB, gender, phone, history). Encrypted, audited history at `/patients/me/history/`. App screens wait for the partner's branches |
| Profile photo upload; view and edit profile any time | done (PR 6.1) | — | mock only | `PUT/DELETE /patients/me/photo/` (EXIF removed, 1024 px, signed URLs); psychologists too (directory) |
| Choose which information is public and which is private | done (PR 6.1) | — | mock only | One switch covering name and photo (Q14); `privacy` lists what it reveals and what is always private |

## 6.2 Psychologist Onboarding

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Register with personal and professional info, certifications, background, specializations | done | done | — | Text credentials at registration (Phase 2). Web: searchable city field (PR #38) and the name rule (PR #40) merged 2026-10-11; the other signup fields don't follow validation-rules.md yet (see the partner message) |
| Upload credentials and licences for verification | done (PR 6.2) | not started | — | Multipart registration with license, degree and up to 3 more; private storage. Files **optional** until `REQUIRE_CREDENTIAL_DOCS=true`, so the live JSON signup keeps working. The Web upload step is the partner's |
| Set availability, manage session bookings, video conferencing (Zoom / Meet) | done (Phase 2 module 4) | partial | mock only | Weekly hours in the psychologist's timezone + days off, 30/50/60-minute sessions with a 10-minute gap, request → confirm / propose another time, cancel, completed / no-show, personal Zoom or Meet link shown on confirmed sessions; exclusion constraint against double booking. Web and App screens are the partner's: `docs/handoff/booking-fees.md` |

## 6.3 Admin Panel

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Verify psychologist credentials; approve or reject registrations | done (PR 6.3) | partial (branch `web/admin-psychologist-approvals`) | — | Endpoints exactly per the contract; audited document links; Django admin uses the same service. Web: merge the partner's branch, then add the document viewer |
| Monitor platform activities; ensure policies are followed | done (PR 6.3, admin-panel-2) | mock only | — | Overview (now with recent suspensions/rejections), Users (pseudonyms for private patients, audited reveal), deactivate/reactivate. admin-panel-2 adds the psychologist directory (counts only), city verification (verify/merge/reject), content CRUD for quotes/duas/surahs with audio, "waiting since" and oldest-first queues, and the super-admin workflow (create admins with a temporary password, promote, step down, deactivate) plus password change for everyone. Web screens: `docs/handoff/admin-panel-2.md` |
| Moderate community content; manage reports and complaints | partial (PR 6.3) | mock only | not started | Reports and complaints done (both directions, encrypted descriptions, dismiss/uphold). **Community content moderation deferred to 6.8** |

## 6.4 Patient Profiling

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Psychologists keep therapy notes and observations after each session | done (Phase 2 module 5) | mock only | — | Observations / interventions / plan, optional session link, all encrypted, every read and write audited; editable 24 h, then addenda; every version kept; current psychologist only, never admins. Web screens: `docs/handoff/therapy-notes.md` |
| Psychologists track progress and changes over time | done (Phase 2 modules 3, 5; care plan) | mock only | — | Progress rating 1–10 and risk level per note, over time for a chart (`clinical-notes/patients/{id}/progress/`), the patient's mood history, and care-plan adherence (7/30/90 days) with the patient's completion notes. Web screens: `docs/handoff/care-plan-journal.md` |
| Users view summarised insights of their progress | done (Phase 2 modules 3, 5; care plan) | — | mock only | `clinical-notes/me/progress/`: completed / upcoming sessions, the summary the psychologist writes for them, mood insights. Never notes. Care plan: goals, tasks, done today, adherence. App screens: `docs/handoff/therapy-notes.md`, `mood-check-ins.md`, `care-plan-journal.md` |

## 6.5 Sensor Monitoring and Health Tracking

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Track breathing rate, heart rate and sweating through sensors | not started | — | mock only | project-vision §15 dropped sweating for motion; resolve before this module starts |
| Use the data to monitor mental/physical state in real time and personalise exercise recommendations | not started | — | mock only | |
| Notifications and reminders based on sensor data | not started | — | mock only | Needs notifications (roadmap Phase 10) |

## 6.6 AI Recommendations with Therapy Sessions

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| AI analyses mental health and sensor data to recommend exercises, sleep schedule and diet | partial | partial | — | `/ai/anxiety-prediction/` forwards to `/patient-summary` (PR ai-patient-summary): self-rated social anxiety prediction, estimated tier and exercise/sleep/nutrition bundle from form input; nothing stored. Web display on branch `web/ai-recommendations`, needs no change. Sensor data and stored, approved recommendations are Phase 6/7 |
| AI learns from psychologist feedback (approval or update) | not started | not started | — | Needs the stored triple and separate training consent (decisions.md 2026-09-27) |
| Psychologist approves or updates recommendations | partial (care plan) | mock only | mock only | The care plan (psychologist-written goals and tasks the patient tracks) is built and is where approved recommendations will land. AI drafts and their approval step are Phase 6. Care plan editor on the Web is still mock: `docs/handoff/care-plan-journal.md` |

## 6.7 AI Chat Assistance

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| 24/7 chatbot answering common mental health questions | not started | — | mock only | Aida chat screen is mock |
| Suggests therapy or wellness options | not started | — | mock only | |
| Initial triage, coping strategies, directs to resources or psychologists | not started | — | mock only | |

## 6.8 Community Support

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Join or create communities; share experiences | not started | mock only | mock only | Creator approval required (project-vision §22) |
| Interact, advise, volunteer, organise real-world activities | not started | mock only | mock only | |
| Emotional support and belonging | not started | — | mock only | Outcome of the two bullets above |

## 6.9 Lifestyle and Wellness

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Content: diet plans, exercise routines, stress-reduction techniques | done (6.9 library) | not started | mock only | Admin-managed articles, practices (with an optional breathing pattern for the App's player) and routines; cover image, audio, YouTube / Vimeo link; favourites; psychologists link items to care-plan tasks. 14 seeded items are **hidden placeholders awaiting clinical review**. Screens are the partner's: `docs/handoff/wellness.md` |
| Personalised suggestions from mental health needs and sensor data | deferred to 6.6 / 6.5 | — | mock only | AI suggestions need the Phase 6 approval workflow; sensor-based ones need 6.5. Until then the psychologist personalises by linking library items to care-plan tasks |
| Resources: mindfulness, yoga, nutrition, relaxation | done (6.9 library) | not started | mock only | Same library: categories `mindfulness`, `yoga`, `nutrition`, `relaxation`, plus `exercise`, `stress_reduction`, `sleep` |

## 6.10 Motivation Corner

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Duas (audio + text) | done (PR 6.10) | — | mock only | 10 Quranic duas seeded (Tanzil text + Pickthall); admin-uploaded audio; patients who opted in only. App screens are the partner's |
| Quotes | done | — | mock only | `GET /motivation/quotes/`, `/random/`. App wiring is the partner's (not on GitHub yet) |
| Surahs (audio + text) | done (PR 6.10) | — | mock only | 5 short surahs seeded, verse per line; admin-uploaded audio; opt-in deleted on opt-out. App screens are the partner's |

## 6.11 Payments

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| View session fees, total sessions and total paid | partial (Phase 2 module 4) | mock only | mock only | Per-session fee in PKR on the directory and on every session (snapshot at booking); session history with completed / no-show / late cancellations recorded. Totals paid come with payments (Phase 3, 6.11) |
| Multiple secure payment methods (card, mobile wallets) | not started | mock only | mock only | Stripe test mode only (decisions.md 2026-10-06) |
| Invoicing, receipts and session booking | partial (Phase 2 module 4) | mock only | mock only | Session booking done; invoices and receipts come with 6.11 |

## 6.12 NGO Onboarding and Emergency SOS

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| SOS button on every screen starts an emergency flow | done (Phase 2 module 2) | — | mock only | `POST /emergency/sos/`: manual button only, never throttled or blocked, cancel within 5 min. App screens are the partner's: `docs/handoff/sos.md` |
| Helplines, nearby hospitals, emergency contacts, live psychologist connection | done (Phase 2 module 2) | not started | mock only | Admin-entered helplines (per country) and hospitals (per city), none seeded; up to 3 encrypted contacts emailed on SOS; the current psychologist is emailed (no on-call pool); approved NGOs serving the area. Device coordinates encrypted, cleared after 90 days |
| Chatbot detects distress and activates SOS; emergency activity logged for admins | partial (Phase 2 module 2) | not started | — | Admin SOS log done (audited detail, follow up, close with an outcome) plus a psychologist alert list. **Chatbot trigger deferred to 6.7** (no chatbot yet; thresholds must not be invented) |

## 6.13 Engagement and Rewards

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Points, badges and streaks for activities, sessions and check-ins | partial (Phase 2 module 3) | — | mock only | Daily mood check-ins and their streak exist; points and badges are 6.13 |
| Levels and milestones | not started | — | mock only | |
| Rewards (discounts, premium content, session benefits), optional leaderboards | not started | — | mock only | Premium model not decided (project-vision §28); leaderboards need a privacy review against the pseudonym rules |

## 6.14 Automated Reports

| Bullet | Backend | Web | App | Notes |
|---|---|---|---|---|
| Weekly and monthly reports on activity, mood and therapy progress | done (reports, on demand) | mock only | — | `GET reports/psychologist/patients/{id}/report/` (`period` = week, month or custom): sessions, note ratings and risk levels, mood, care-plan adherence, SOS; never note, check-in or journal text. On demand only (no scheduler, so no automatic weekly email). Web screens: `docs/handoff/reports.md` |
| Visual insights: trends, behaviour changes, sensor indicators | partial (reports) | mock only | — | Chart-ready series (daily ≤ 31 days, else weekly), comparison with the previous period, factual indicators. **Sensor indicators wait for 6.5** (`sensors.available: false`) |
| Psychologists use reports to adjust treatment | done (reports) | mock only | — | Current psychologist only, audited; per-goal and per-task adherence feeds care-plan edits |

## Cross-cutting

| Item | Status | Notes |
|---|---|---|
| Patient journal (project-vision §11) | backend done (2026-11-19) | Private entries (title, body, feeling tags, optional same-day check-in link), all encrypted; patient only, never the psychologist or admins; edit any time, hard delete, writes audited; 20 a day; fixed safety notice; no scanning. App screens are the partner's: `docs/handoff/care-plan-journal.md` |
| Secure messaging (patient ↔ psychologist) | backend done (2026-11-19) | One encrypted text conversation per pair; participants only (others 404, admins never); read-only for the patient after care ends, former psychologist loses access; delete within 5 min; 30 messages / 10 min; `new_message` notification without content; polling. Web and App screens are the partner's: `docs/handoff/messaging.md` |
| In-app notifications | backend done (2026-11-18) | Fixed-template notifications for booking, relationships, SOS, account review, password change and the progress summary; list / unread-count / read / read-all / delete; 90-day retention. No push. Web and App bell screens are the partner's: `docs/handoff/notifications.md` |
| Scheduler and reminders | backend done (2026-11-23) | GitHub Actions cron runs `run_maintenance` (daily purges + Supabase heartbeat) and `send_reminders` (every 15 min): session (~24 h, ~1 h), care request expiring, care-plan tasks due, check-in; in-app, email for the 24 h session and care-request ones; quiet hours, opt-out at `notifications/preferences/`. **Not live until the role and GitHub secrets are set up** (`docs/deployment.md`, "Scheduler"). Settings screens are the partner's: `docs/handoff/reminders.md` |
| Password reset and email | backend done (module 1) | 6-digit code by email; password-changed notice; approval/rejection emails; Brevo over HTTPS (Resend by settings). Web and App "Forgot password" screens are the partner's: `docs/handoff/password-reset-email.md`. Production sends nothing until the Render email variables are set |
| Super-admin workflow and password change | backend done (module 0) | Web screens (admin management, change password) and the App's change-password screen are the partner's; see `docs/handoff/admin-panel-2.md` |
| Patient ↔ psychologist relationships | Backend done, Web done, App mock only | Patient side in the App is Phase 1 item (f) |
| File storage (`integrations/storage_client`) | backend done (PR foundations) | Private Supabase bucket, signed URLs, magic-byte checks, EXIF removal. Used by 6.1, 6.2, 6.10 |
| DB-backed PHI access audit trail | backend done (PR foundations) | `apps/audit`, append-only, fail closed; field encryption for health data ready too |
| Web lint / typecheck / tests | missing | `package.json` has only `dev`, `build`, `preview` |
| Input validation (docs/validation-rules.md) | Backend done; Web partial (full name in therapist signup, PR #40); App not started | Frontend work is the partner's; open gaps listed in the 2026-10-11 partner message |
