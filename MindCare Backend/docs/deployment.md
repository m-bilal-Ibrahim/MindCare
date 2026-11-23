# Deployment

Production backend runs on **Render**, with **Supabase** (Postgres) and
**Redis Cloud** (Redis). See @decisions.md for why these providers were chosen.
**No secrets belong in this file.** Values live only in Render's dashboard.

## Render (live)

- **URL:** https://mindcare-ajri.onrender.com (API under `/api/v1/`, docs at `/api/docs/`)
- **Instance tier:** free.
- **Settings module:** `DJANGO_SETTINGS_MODULE=config.settings.prod`.
- **Production superuser:** a real production superuser account exists (created
  via `createsuperuser`, so `is_super_admin=True`). Its credentials are not
  recorded in the repo.
  It is the first super-admin: other admins are created from the admin console
  (`POST /api/v1/accounts/admin/admins/`, one-time temporary password), not with
  `createsuperuser`. Keep at least two super-admins so one lost password can't
  lock everyone out.

### Environment variables (configured in Render)

| Variable | Value / source |
|----------|----------------|
| `DATABASE_URL` | Supabase **connection pooler** URL, with `sslmode=require` |
| `REDIS_URL` | Redis Cloud instance |
| `SECRET_KEY` | generated fresh for production; not shared with any dev `.env` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `CORS_EXTRA_ALLOWED_ORIGINS` | optional, comma-separated extra browser origins on top of the Vercel origin, e.g. `http://localhost:5000` for a local Flutter web demo. Unset normally; remove after a demo |
| `FIELD_ENCRYPTION_KEY` | Fernet key for health data at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. **Save a copy in a password manager first**: losing it makes encrypted data unreadable. Missing or invalid → the deploy's system check fails (`mindcare.E001`) |
| `EMAIL_PROVIDER` | `brevo` (or `resend`). Unset → `disabled`: no email is sent and the deploy shows warning `mindcare.W001`. `console` fails the deploy (`mindcare.E003`). Setup steps: `docs/handoff/password-reset-email.md` |
| `EMAIL_PROVIDER_API_KEY` | the provider's API key (Brevo: SMTP & API → API Keys, starts `xkeysib-`). Required when a provider is set (`mindcare.E004`) |
| `DEFAULT_FROM_EMAIL` | the sender address verified with the provider |
| `DEFAULT_FROM_NAME` | optional, default `MindCare` |
| `SUPPORT_EMAIL` | address shown in emails for questions (e.g. after a rejection) |
| `FIELD_ENCRYPTION_PREVIOUS_KEYS` | optional, comma-separated old keys during a rotation; unset normally |
| `SUPABASE_S3_BUCKET` | name of the **private** Supabase Storage bucket for uploads (e.g. `mindcare-private`) |
| `SUPABASE_S3_ENDPOINT` | `https://<project-ref>.supabase.co/storage/v1/s3` (Supabase → Storage → Settings → S3 Connection) |
| `SUPABASE_S3_REGION` | the region shown on the same page (e.g. `ap-south-1`) |
| `SUPABASE_S3_ACCESS_KEY_ID` / `SUPABASE_S3_SECRET_ACCESS_KEY` | an S3 access key created on that page (storage-only; **not** the `service_role` key). Any of the five missing → uploads would use local disk, so the deploy's system check fails (`mindcare.E002`) |
| `REQUIRE_CREDENTIAL_DOCS` | optional; `true` makes the license and degree files required at psychologist registration. Default `false`, so the current JSON therapist signup keeps working. Turn on only when the Web sends the files |
| `NUM_PROXIES` | `3`: measured 2026-10-11, `X-Forwarded-For` = `client, cloudflare, render-internal` (see @decisions.md). Re-measure if the proxy chain changes |
| `AI_SERVICE_URL` | the MindCare AI service's base URL, no trailing `/predict` (e.g. `https://mindcare-api-fysd.onrender.com`). Unset → `POST /api/v1/ai/anxiety-prediction/` answers 503 |

**Local development:** the developer's local `.env` `DATABASE_URL` points at the
local docker Postgres (switched 2026-09-30); production credentials live only in
Render. Keep it that way: tests are guarded against remote databases (see
@decisions.md, 2026-09-28), but `runserver`, `migrate` and `dbshell` use
`DATABASE_URL` as-is.

**Supabase password resets:** after resetting the Supabase database password,
update `DATABASE_URL` on Render to match. On 2026-09-30 a stale `DATABASE_URL`
after a reset caused `/admin/` 500s and a failed deploy (not caused by Phase 2
code). It was fixed by updating the variable on Render.

`JWT_SIGNING_KEY` is not set, so JWTs are signed with `SECRET_KEY` (see
`config/settings/base.py`).

### CORS

`config/settings/prod.py` allows the MindCare Web frontend,
`https://mind-care-web-seven.vercel.app`, plus any origins in the optional
`CORS_EXTRA_ALLOWED_ORIGINS` env var (unset normally; e.g. `http://localhost:5000`
for a local Flutter web demo, removed afterwards). `CORS_ALLOW_CREDENTIALS=False`
(JWT bearer auth, no cookies). The local Vite origin is allowed only in `dev.py`.

**Status:** shipped to `main` in PR #17 (`backend-cors-and-prod-pins`). Before it
merged, a preflight against the live service (2026-09-27) returned `200` with no
`Access-Control-*` headers. Re-check after each deploy that
`OPTIONS /api/v1/accounts/login/` with `Origin: https://mind-care-web-seven.vercel.app`
returns `Access-Control-Allow-Origin` for that origin.

### Known tradeoffs (free tier)

- **Cold starts:** Render's free instances spin down after ~15 min without traffic.
  The next request waits for a cold start (~50s documented; ~36s measured on
  2026-09-27). Frontends should show a loading state rather than time out quickly.
- **Supabase inactivity pause:** Supabase free-tier projects are paused after
  **7 days** without activity, which takes the production database offline until
  someone manually restores it.

## Pre-deploy checklist for the Phase 2 merge

Status 2026-10-11: all done (`NUM_PROXIES=3` set on Render).

- [x] **Rate limits behind Render's proxy:** measured 2026-10-11:
      `X-Forwarded-For` = `client, cloudflare, render-internal`, so
      `NUM_PROXIES=3` is set on Render (see @decisions.md, 2026-10-11).
- [x] **Migrations run on deploy** (confirmed from Render's dashboard,
      2026-09-30). Render's build command:
      `pip install -r requirements/prod.txt && python manage.py collectstatic --noinput && python manage.py migrate`.
      The Phase 2 migrations (reference 0001–0003, accounts 0002, patients/
      psychologists/ngo 0001) apply automatically on the deploy after the merge.
- [x] **Existing production users** (checked 2026-09-30): only the admin account
      remains. The one test account was deleted directly in Supabase. No
      patient/psychologist/NGO user exists without a profile.
- [x] **Frontend readiness** (2026-09-30): the register body is a breaking change
      (`is_adult_confirmed` + nested `profile`). Both the Web and App teams have
      reviewed the new contract. MindCare Web's signup is built on its own branch
      and ships after this backend is live, so it is tested against the real
      backend. Until each frontend ships its signup, any old-format register
      request gets a 400.
- [ ] **After deploy:** re-run the CORS preflight check (see CORS section) and
      check `/api/docs/` shows the register and `/me/` contracts.

## Demo accounts

`DEMO_PASSWORD=<choose one> python manage.py seed_demo` creates 6 approved demo
psychologists, 2 demo patients, 1 pending demo applicant (Dr. Nadia Siddiqui, with two
fictional PDF documents) and 1 open demo report (all `demo.*@example.com`; psychologist bios start
"Demo account, not a real psychologist."; names are plain because of the name rule). It
can be re-run safely. Demo patient 1 (Hina) has an accepted relationship with
Dr. Sara Ahmed and demo patient 2 (Daniyal) a pending request to her, so
`demo.psych.sara@example.com` shows both the inbox and the patient list. Pending
requests expire after 3 days; re-running the command renews it. `python manage.py seed_demo --remove` deletes exactly those
accounts with their reports, relationship rows and document files. Render's free tier
has no Shell, so run it locally with `DATABASE_URL` set to the production URL for that
one command, then remove the variable again. **Also set the five `SUPABASE_S3_*`
variables in that shell** (same values as on Render): they switch storage to the
bucket in any environment, so the applicant's demo documents land in the real bucket
and open from the admin review screen. Without them the files would be written to
your laptop and the links would not work. Demo cities outside Pakistan
(London, Dubai) are created unverified, like any typed city.

## Removing test data (Phase 3 onwards)

`CareRelationship` rows reference profiles with `on_delete=PROTECT`, so a user who
has relationship rows **can't be deleted from Django admin**. To remove test
accounts, delete in this order, scoped to the test users' ids (replace `<ids>`):

```sql
-- 0a. therapy notes and summaries (Phase 2 module 5; versions and addenda
--     cascade). TEST ACCOUNTS ONLY: real clinical records are anonymised, never
--     deleted (docs/decisions.md, 2026-11-18).
DELETE FROM clinical_notes_therapynote
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
DELETE FROM clinical_notes_progresssummary
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
-- 0a2. conversations (messaging; messages cascade). TEST ACCOUNTS ONLY.
DELETE FROM messaging_conversation
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
-- 0a3. care plans (completions, tasks, goals and versions first). TEST ACCOUNTS ONLY.
--      Journal entries go with the patient profile (CASCADE in Django; delete
--      journals_journalentry rows first when deleting with SQL).
DELETE FROM recommendations_taskcompletion WHERE task_id IN (
  SELECT t.id FROM recommendations_careplantask t
  JOIN recommendations_careplangoal g ON g.id = t.goal_id
  JOIN recommendations_careplan p ON p.id = g.plan_id
  WHERE p.patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
     OR p.psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>)));
DELETE FROM recommendations_careplantask WHERE goal_id IN (
  SELECT g.id FROM recommendations_careplangoal g
  JOIN recommendations_careplan p ON p.id = g.plan_id
  WHERE p.patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
     OR p.psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>)));
DELETE FROM recommendations_careplangoal WHERE plan_id IN (
  SELECT id FROM recommendations_careplan
  WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
     OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>)));
DELETE FROM recommendations_careplanversion WHERE plan_id IN (
  SELECT id FROM recommendations_careplan
  WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
     OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>)));
DELETE FROM recommendations_careplan
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
DELETE FROM journals_journalentry
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>));
-- 0b. sessions (Phase 2 module 4; they PROTECT relationships and profiles)
DELETE FROM appointments_session
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
-- 1. relationship rows first (PROTECT blocks everything else otherwise)
DELETE FROM relationships_carerelationship
 WHERE patient_id IN (SELECT id FROM patients_patientprofile WHERE user_id IN (<ids>))
    OR psychologist_id IN (SELECT id FROM psychologists_psychologistprofile WHERE user_id IN (<ids>));
-- 2. profiles (psychologist M2M rows and NGO service areas cascade)
DELETE FROM patients_patientprofile WHERE user_id IN (<ids>);
DELETE FROM psychologists_psychologistprofile WHERE user_id IN (<ids>);
DELETE FROM ngo_ngoprofile WHERE user_id IN (<ids>);
-- 3. users
DELETE FROM accounts_user WHERE id IN (<ids>);
```

Check the ids with a `SELECT` first, and run it inside a transaction
(`BEGIN; … COMMIT;`) so a mistake can be rolled back.

## Supabase settings

- **Storage bucket for uploads:** Supabase → Storage → New bucket → name it (e.g.
  `mindcare-private`), **Public bucket: OFF**. No policies are needed: the backend
  uses S3 access keys, and nothing else should read the bucket. Then Storage →
  Settings → S3 Connection: note the endpoint and region, and create an access key
  (copy the secret at once; it's shown only once). Put all five values on Render
  (see the table above).

- **`btree_gist` extension: ON** (needed from Phase 2 module 4, before deploying
  it). The no-double-booking constraint in `appointments.0001_initial` needs it.
  The migration runs `CREATE EXTENSION IF NOT EXISTS btree_gist` itself, which
  works when the migration role may create extensions; to be safe, enable it
  first: Supabase → Database → Extensions → search `btree_gist` → enable (the
  default `extensions` schema is fine). Or in the SQL editor:
  `CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA extensions;`
  Check with `SELECT extname FROM pg_extension WHERE extname = 'btree_gist';`.
  If the migration still fails, the deploy stops before the new code runs; enable
  the extension and redeploy. An error like "data type bigint has no default
  operator class for access method gist" means the extension's schema isn't on the
  connection's `search_path`: run `SHOW search_path;` and, if `extensions` is
  missing, enable `btree_gist` in the `public` schema instead.

- **Data API: OFF** (turned off 2026-10-10). Django never used it, and with it on,
  any table without RLS was readable with the anon key. Keep it off; see
  @decisions.md, 2026-10-10.

## Security headers

- **HSTS:** `prod.py` sends `Strict-Transport-Security: max-age=86400` (one day).
  After a week with no HTTPS problems, raise `SECURE_HSTS_SECONDS` to `31536000`.

## Scheduler (GitHub Actions cron)

Decisions: @decisions.md, 2026-11-23. Two workflows in the repository root run
management commands on GitHub's runner, straight against Supabase, as a
low-privilege role. There is no Celery worker or beat.

| Workflow | Schedule (UTC) | Command |
|---|---|---|
| `.github/workflows/backend-scheduler-maintenance.yml` | `17 22 * * *` (03:17 Asia/Karachi) | `run_maintenance`: purge notifications (90 days), SOS coordinates (90 days), reset codes (1 day) and sent-reminder records (30 days). The queries double as the **Supabase heartbeat** |
| `.github/workflows/backend-scheduler-reminders.yml` | `7,22,37,52 * * * *` | `send_reminders`: sessions (~24 h and ~1 h), care requests expiring within 5 h, care-plan tasks (18:00 local), check-in (20:00 local) |

Both take `--dry-run` (do everything in a transaction, then roll back; nothing is
sent) and `--only <jobs>`. They print one JSON line of counts: **the repository is
public, so its Actions logs are public**. Never add a log line with names, emails,
ids or text.

### 1. Create the database role (Supabase SQL editor, once)

Pick a long random password (a password manager's generator) and keep it there.
The role can read only what the jobs read and change only what they change. It
can't see the encrypted columns' key, so even its reads of those tables return
ciphertext.

```sql
CREATE ROLE mindcare_scheduler LOGIN PASSWORD '<a long random password>'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;

GRANT USAGE ON SCHEMA public TO mindcare_scheduler;

-- Accounts and profiles: only the columns the jobs use. Never password hashes,
-- dates of birth, phone numbers or any other profile field.
GRANT SELECT (id, email, full_name, is_active, approval_status, role)
  ON accounts_user TO mindcare_scheduler;
GRANT SELECT (id, user_id, timezone) ON patients_patientprofile TO mindcare_scheduler;
GRANT SELECT (id, user_id, timezone)
  ON psychologists_psychologistprofile TO mindcare_scheduler;

-- Read only (encrypted columns read as ciphertext; the jobs never select them)
GRANT SELECT ON
  appointments_session,
  relationships_carerelationship,
  recommendations_careplan,
  recommendations_careplangoal,
  recommendations_careplantask,
  recommendations_taskcompletion,
  journals_moodcheckin,
  notifications_reminderpreference
TO mindcare_scheduler;

-- Reminders write notifications and their sent-records; maintenance deletes old ones
GRANT SELECT, INSERT, DELETE ON
  notifications_notification,
  notifications_sentreminder
TO mindcare_scheduler;

-- Maintenance: delete old reset codes, blank old SOS coordinates (that column only)
GRANT SELECT, DELETE ON accounts_passwordresetcode TO mindcare_scheduler;
GRANT SELECT (id, created_at, coordinates), UPDATE (coordinates)
  ON emergency_sosevent TO mindcare_scheduler;

-- The two tables it inserts into get their ids from these sequences
DO $$
DECLARE seq text;
BEGIN
  FOREACH seq IN ARRAY ARRAY[
    pg_get_serial_sequence('notifications_notification', 'id'),
    pg_get_serial_sequence('notifications_sentreminder', 'id')
  ] LOOP
    EXECUTE format('GRANT USAGE ON SEQUENCE %s TO mindcare_scheduler', seq);
  END LOOP;
END $$;

-- Long queries are a bug for these jobs: cut them off.
ALTER ROLE mindcare_scheduler SET statement_timeout = '60s';
```

This SQL hasn't been run anywhere yet (local runs used the local owner role). If
a grant is missing, the first dry run fails with `permission denied for table …`
or `… column …`: add that grant and run again.

**When a later module adds a reminder or a purge on another table, grant it here
and in this list.** A missing grant fails the run with `permission denied for
table …`.

To remove the role: `DROP OWNED BY mindcare_scheduler; DROP ROLE mindcare_scheduler;`.

### 2. GitHub secrets and variables

Repository → Settings → Secrets and variables → Actions. Secrets aren't passed to
workflows run from forks.

| Name | Kind | Where the value comes from |
|---|---|---|
| `SCHEDULER_DATABASE_URL` | Secret | Supabase → Connect → **Session pooler** (port 5432; IPv4, which GitHub's runners need: the direct connection is IPv6-only). Replace the user with `mindcare_scheduler.<project-ref>` (keep the `.<project-ref>` suffix the pooler shows) and the password with the role's password from step 1 |
| `SCHEDULER_SECRET_KEY` | Secret | A new random value, **not** Render's `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(50))"`. The jobs sign nothing with it |
| `EMAIL_PROVIDER_API_KEY` | Secret | The same Brevo (or Resend) API key as Render's `EMAIL_PROVIDER_API_KEY`. Leave unset to send no reminder emails |
| `EMAIL_PROVIDER` | Variable | Same as on Render (`brevo` / `resend`). Unset = no email; `console` is turned into "off" |
| `DEFAULT_FROM_EMAIL` | Variable | Same as on Render (the verified sender) |
| `DEFAULT_FROM_NAME` | Variable | Same as on Render (optional; default `MindCare`) |
| `SUPPORT_EMAIL` | Variable | Same as on Render (optional) |

Not needed, deliberately: `FIELD_ENCRYPTION_KEY`, `SUPABASE_S3_*`, `REDIS_URL`
(the workflow sets a placeholder; the scheduler settings use an in-memory cache),
`JWT_*`.

### 3. First run

1. Merge, so the workflows are on `main` (GitHub only runs scheduled and manual
   workflows from the default branch).
2. Actions → **Backend scheduler (maintenance)** → Run workflow. `dry_run` is ticked
   by default; leave it. The log ends with
   `{"command": "maintenance", "dry_run": true, "database": "ok", ...}`.
3. The same for **Backend scheduler (reminders)**.
4. Both green: the cron schedules take over (scheduled runs are never dry runs).
   A manual run with `dry_run` unticked runs for real.

### When something goes wrong

- **A failed scheduled run** emails whoever last changed the workflow's cron (GitHub's
  default notification). `database unreachable or paused?` means Supabase paused the
  project or the role's password/URL is wrong.
- **60-day auto-disable:** GitHub turns off scheduled workflows in a public repository
  after 60 days without any repository activity (no commits). Nothing fails: the runs
  just stop, and so do the reminders and the heartbeat, and Supabase pauses after 7
  quiet days. Re-enable under Actions → the workflow → **Enable workflow** (GitHub
  also shows a banner and emails a warning beforehand). Check both workflows after a
  long break.
- **Late runs:** GitHub often starts scheduled runs 5-30 minutes late, or skips them
  under load. Reminders work on windows, so a late run still sends what's still
  useful and never sends twice.
- **If the repository becomes private:** the reminders workflow (~96 runs a day) would
  exceed the 2,000 free minutes a month. Change its cron to `7 * * * *` (hourly).

## TODO

- [x] **Supabase heartbeat**: the daily maintenance workflow (above) queries the
      database every day.
- [ ] Celery worker as a separate Render service. Not needed while the scheduler runs
      on GitHub Actions; only if a job needs work queued from a request.
