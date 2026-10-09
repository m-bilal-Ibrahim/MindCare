# MindCare Web

React 19 + Vite 7 + Tailwind 4 + TypeScript frontend for MindCare (therapist, admin and NGO consoles, plus the public site). This folder is part of the monorepo `m-bilal-Ibrahim/MindCare`, whose git root is the parent `MindCare/` folder. The backend partner owns `MindCare Backend/`.

## Scope rules
- A session opened in this folder works on the **web only**. Do not edit `MindCare App/`, `MindCare Backend/` or `MindCare AI/` from here. App (Flutter) work happens in a separate session opened in `MindCare App/`.
- Branch names: `web/<feature>` for web, `mobile/<feature>` for the app. Branch from `main`, one feature per branch, push it, and open a PR to `main`.
- Do not merge a PR whose backend endpoint isn't on `main` yet. The backend partner says when it can be merged.

## Commands
- Dev server: `npm run dev` (Vite)
- Build / type check: `npm run build`
- API base URL: `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api/v1` in dev). See `src/constants/index.ts`.
- API docs from the backend: `/api/docs/` on the running backend.

## Code map
- `src/services/api.service.ts`: fetch wrapper with JWT refresh (`/accounts/refresh/`). All calls go through it.
- `src/services/psychologist.service.ts`, `src/services/tokens.ts`: psychologist endpoints and token storage.
- `src/hooks/useReferenceOptions.ts`: country/language reference dropdowns.
- `src/pages/*`: one component per route. Routes are in `src/router/index.tsx`.
- `src/components/therapist/*`, `src/components/admin/*`, `src/components/ngo/*`: console UI.
- `docs/ai-recommendations-api-contract.md`: the contract agreed with the backend for AI recommendations.

## Current status (update this section at the end of each session)
Last updated: 2026-10-09

Waiting on backend. Push these branches and open PRs, but **don't merge** until the backend partner confirms:
- `web/admin-psychologist-approvals`: admin Verifications page (`AdminVerificationsPage.tsx`)
- `web/ai-recommendations`: AI recommendations, severity tier and caveat

Still to build on the web:
1. City search in therapist signup. `TherapistRegisterWizard.tsx` currently uses a free-text City field; replace it with a searchable city lookup from the backend.
2. `ngo/me` page: NGO profile page backed by the `ngo/me` endpoint.

App (separate session, top priority for the team): nothing on `main` calls the backend yet. Merge `mobile/patient-signup-api` first, then wire these in order: token refresh → `patients/me` (with date of birth) → country/city/language dropdowns → psychologist directory → requests (create, cancel, current, end, recent) → motivation quotes. Run it with `flutter run -d chrome --web-port 5000`. The handoff docs are in `docs/handoff/` and at `/api/docs/`.
