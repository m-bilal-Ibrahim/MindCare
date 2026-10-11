# Handoff: 6.2 psychologist onboarding (credential documents)

**Breaking change for the therapist signup on the Web.** A psychologist registration
must now include the license and degree files. A JSON-only psychologist registration
gets a 400 asking for them. Ship the Web's upload fields **together with** the
backend PR (merged back to back).

## Endpoint

`POST /api/v1/accounts/register/`: same URL, same JSON fields. Unauthenticated,
throttled at 10/hour per address.

- **Patients and NGOs:** unchanged, `application/json`.
- **Psychologists:** `multipart/form-data` with these parts:

| Part | Required | Content |
|---|---|---|
| `data` | yes | The **same JSON body as before** (email, password, full_name, role `"psychologist"`, is_adult_confirmed, profile), as a string |
| `license_document` | yes | One file: PDF, JPG or PNG, max 5 MB |
| `degree_document` | yes | One file, same rules |
| `other_documents` | no | Up to 3 files, same rules (repeat the part name for each file) |

The type is checked by the file's content, not its name. Images are re-encoded on
the server (EXIF such as GPS location is removed).

### Example (browser `fetch`)

```ts
const form = new FormData();
form.append("data", JSON.stringify(body)); // the same body you send today
form.append("license_document", licenseFile);
form.append("degree_document", degreeFile);
for (const f of otherFiles) form.append("other_documents", f);
await fetch(`${API_BASE_URL}/accounts/register/`, { method: "POST", body: form });
// Don't set Content-Type yourself: the browser adds the multipart boundary.
```

### 201
As before, plus `profile.documents`:

```json
"documents": [
  {"id": 12, "kind": "license", "file_type": "pdf", "size": 182044, "uploaded_at": "2026-10-11T09:15:00Z"},
  {"id": 13, "kind": "degree", "file_type": "jpg", "size": 95210, "uploaded_at": "2026-10-11T09:15:00Z"}
]
```

`kind` is `license`, `degree` or `other`. There is no URL or key: psychologists can't
download their files back, and admins open them in the review screen (6.3).

### Errors (400)

| Body | When |
|---|---|
| `{"license_document": ["Upload your license document."]}` | Missing (also `degree_document`: `Upload your degree certificate.`) |
| `{"license_document": ["License document must be one of: PDF, JPG, PNG."]}` | Wrong type (by content) |
| `{"license_document": ["License document must be 5 MB or smaller."]}` | Too big |
| `{"degree_document": ["Degree certificate is empty."]}` | Empty file |
| `{"license_document": ["License document isn't a readable image."]}` | A corrupt JPG/PNG |
| `{"other_documents": ["Upload at most 3 other documents."]}` | More than 3 |
| `{"data": ["Send the registration details as JSON in the 'data' field."]}` | `data` missing or not a JSON object |
| `{"<file part>": ["This field can't be set."]}` | Files sent for a patient or NGO, or an unknown file part |
| `{"profile": {...}}`, `{"full_name": [...]}`, etc. | The same field errors as before (`docs/validation-rules.md`) |

If registration fails for any reason, no account is created and no file is kept.

`GET /api/v1/psychologists/me/` also returns `documents` (same shape).

## Screens (Web, once the partner's branches are on GitHub)

- **Therapist apply wizard** (`TherapistRegisterWizard.tsx`): a documents step with
  two required pickers (license, degree) and an optional "add another" (max 3);
  `accept=".pdf,.jpg,.jpeg,.png"`; show the size limit; check type and size before
  submit (messages above); the submit button stays disabled until both required
  files are chosen. Keep the loader for cold starts (~40 s), and show the backend's
  message per field.
- **Therapist profile:** list the uploaded documents (kind, type, date). Read-only.

## Deferred
- Working hours, session booking and video links: Phase 2 (designed with booking).
- NGO documents: Phase 2, with 6.12.
- Replacing a document after approval: Phase 2's credential re-review flow.
