# Handoff: password reset and email (Phase 2, module 1)

**Not a breaking change.** Two new public endpoints. Psychologists and NGOs now
also get an email when an admin approves or rejects them, and every user gets a
notice when their password changes.

## 1. Forgot password (Web and App)

Two screens: "Forgot password?" (email) → "Enter the code" (code + new password).
Both endpoints are public: send **no** `Authorization` header.

### `POST /api/v1/accounts/password/reset/`

```json
{"email": "sara@example.com"}
```

**Always 200**, whether or not the email has an account:

```json
{"detail": "If an account exists for that email, we've sent a 6-digit code to it. It works for 15 minutes."}
```

Show that text and move to the code screen. 400 only for a malformed email
(`{"email": ["Enter a valid email address."]}`). 429 after 5 requests an hour from
one address; an account gets at most 3 codes an hour (extra requests still answer
200 but send nothing), and a new code replaces the previous one.

Who gets a code: any active account in any role, including psychologists and
NGOs still waiting for approval. Deactivated, rejected and unknown emails get the
same 200 and no email.

### `POST /api/v1/accounts/password/reset/confirm/`

```json
{"email": "sara@example.com", "code": "042917", "new_password": "…"}
```

**200** `{"detail": "Your password was changed. Sign in again."}`. Every session on
every device is signed out, so delete any stored tokens and go to the sign-in
screen. A "your password was changed" email follows.

| 400 body | When |
|---|---|
| `{"code": ["Enter the 6-digit code from the email."]}` | not exactly 6 digits |
| `{"code": ["That code is wrong or has expired. Request a new one."]}` | wrong, expired, already used, replaced by a newer code, 5 wrong tries, or unknown email (deliberately one message) |
| `{"new_password": ["This password is too short. It must contain at least 8 characters."]}` | Django's password rules (also *too common*, *entirely numeric*, *too similar to the email / full name*). The code is **not** used up: let them pick another password |
| `{"email": ["Enter a valid email address."]}` | malformed email |
| `{"<key>": ["This field can't be set."]}` | unknown field |

429 after 20 confirms an hour from one address. Each code dies after 5 wrong tries.

**Screens:** a 6-digit numeric input (`inputmode="numeric"`, `maxlength=6`,
paste-friendly), new password + confirm (checked on the client), the length and
"not only digits" checks while typing, the backend's message under the field, and
a "Send a new code" link that calls the first endpoint again. Keep the email from
the first screen; don't ask for it twice.

## 2. Emails people now receive

| Email | When |
|---|---|
| Password reset code | after a reset request (above) |
| Your password was changed | after a reset or `POST /accounts/password/change/` |
| Your account is approved | an admin approves a psychologist or NGO |
| Your application | an admin rejects one; includes the reason label (if any) and `SUPPORT_EMAIL` |

Ask users to check their spam folder: with a free-mail sender (see below) some
providers file these as spam.

## 3. Django admin
An admin still on the temporary password a super-admin gave them can no longer
sign in at `/admin/` ("Change your temporary password in the MindCare admin
console before signing in here."). This closes the gap noted for module 0.

## 4. Backend owner: Brevo setup and Render env vars

Render's free plan blocks outbound SMTP, so the backend calls Brevo's HTTPS API.
Nothing else needs installing.

### Brevo (free plan, about 300 emails a day)
1. Sign up at brevo.com and confirm your account.
2. **Senders, Domains & Dedicated IPs → Senders → Add a sender.** Use the address
   you want mail to come from (e.g. a Gmail address). Brevo emails it a
   confirmation link: open it. The sender must show as verified.
3. **SMTP & API → API Keys → Generate a new API key.** Name it `mindcare-render`.
   Copy it **now** (Brevo shows it once) into your password manager. This is an
   **API key** (starts `xkeysib-`), not the SMTP key.
4. **Security → Authorised IPs:** if this protection is on, Brevo refuses API calls
   from new IPs, and Render's outgoing IPs change. Turn the blocking off (or add
   Render's outbound IPs from the service's **Connect → Outbound** tab). Symptom if
   you skip this: `"email_failed", "reason": "http_401"` in the Render logs.

### Render → mindcare service → Environment

| Variable | Value |
|---|---|
| `EMAIL_PROVIDER` | `brevo` |
| `EMAIL_PROVIDER_API_KEY` | the Brevo API key from step 3 |
| `DEFAULT_FROM_EMAIL` | the verified sender address from step 2 (must match exactly) |
| `DEFAULT_FROM_NAME` | `MindCare` (optional; this is the default) |
| `SUPPORT_EMAIL` | the address people should write to (shown in rejection and other emails) |

Save, and Render redeploys. Until `EMAIL_PROVIDER` is set, production sends **no**
email (default `disabled`) and the deploy log shows warning `mindcare.W001`.
`EMAIL_PROVIDER=console` in production fails the deploy (`mindcare.E003`), because
it would print reset codes into the logs. A provider without its key fails it too
(`mindcare.E004`).

**Check it works:** use "Forgot password" on the Web with your own account. In the
Render logs, look for `{"event": "email_sent", "template": "password_reset_code"}`.
Logs never contain the address, the code or the body.

### Switching to Resend later (settings only)
1. In Resend, **verify a domain you own** (Resend only lets an unverified account
   send to your own address).
2. Create an API key.
3. On Render set `EMAIL_PROVIDER=resend`, `EMAIL_PROVIDER_API_KEY=<resend key>` and
   `DEFAULT_FROM_EMAIL=<address on that domain>`. No code change.

### Before real release
Authenticate a domain you own (SPF/DKIM/DMARC) in Brevo or Resend, so mail stops
going to spam. Recorded in `docs/decisions.md` (2026-10-19).
