# MindCare Backend

Unified Django REST Framework backend serving MindCare Web (React) and MindCare App (Flutter). See @docs/architecture.md for full system design and @docs/decisions.md for the reasoning behind key choices.

## Stack
Django + DRF, PostgreSQL, Celery + Redis, JWT auth (simplejwt), Stripe, Zoom API, Firebase Cloud Messaging.

## Hard rules — do not violate these
- NEVER put business logic in views.py. Views parse requests, call a service/selector function, serialize the result. All business rules live in services.py (writes) or selectors.py (reads).
- NEVER let AI-generated patient recommendations reach a patient without going through the psychologist approval workflow in apps/recommendations. This is a non-negotiable product rule.
- NEVER touch files inside "MindCare Web" or "MindCare App" folders from this branch.
- ALWAYS filter psychologist-facing querysets to that psychologist's own patients — role-based access alone is not enough, every query needs an object-level ownership check.
- NEVER log PHI (patient names, journal content, clinical notes, health data) in plaintext in application logs. Use core/audit.py for access logging instead.
- ALWAYS write a service-layer test (tests/test_services.py) for new business logic before considering a feature done.
- Ask before adding a new third-party package not already in requirements/base.txt.
- After implementing any new service, selector, or API endpoint, append an entry to docs/module-reference.md in its existing table format. Never skip this — it is required for the project's final documentation.

## Requirements Interview
Before implementing any new feature, significant change, or design decision, run a requirements interview first — do not start writing code while it's unresolved.
- Ask the questions in ONE batch per phase (see "Working agreement" below), not one at a time.
- Challenge assumptions rather than agreeing with the requested approach by default.
- Actively surface missing requirements and ambiguities — don't silently fill gaps with assumptions.
- Explicitly consider: user roles, permissions/authorization, expected behavior, edge cases, failure states, validation, data requirements, integration/dependency implications, and acceptance criteria.
- Continue until requirements are sufficiently specified, then summarize the finalized requirements and proposed implementation approach, and ask for confirmation before implementing.
- Trivial changes with no meaningful ambiguity or design risk may skip the interview.

## Working agreement
- Batch questions: before implementing, collect EVERY decision for the
  whole phase into ONE numbered list, each with options (A/B/C), your
  recommendation marked (Recommended), and one line on why. I answer
  once, e.g. "defaults except 3: B".
- Then work autonomously to the end. Decide small things yourself
  using decisions.md and the existing conventions, and log them. Stop
  mid-way ONLY for: production data or Render/Supabase settings,
  security or privacy trade-offs not covered by decisions.md, payments,
  changing existing behaviour, or a real blocker. If you must stop,
  batch everything again.
- Never run anything against production; give me the exact commands.
- One branch per module, off main. Files staged by name. No .env changes.

### Definition of done (every module)
A module is done only when every bullet in its description in @docs/modules.md works
end to end:
1. Backend: models, services, endpoints, permissions, throttling, OpenAPI docs, tests
   first. Full suite with warnings as errors, `makemigrations --check`, strict schema
   check, pre-commit.
2. MindCare Web (psychologist/admin) and MindCare App (patient, run with
   `flutter run -d chrome --web-port 5000`): every screen for that module calls the
   real backend. No mock, static or hardcoded data left in that module's screens;
   delete the mock data once replaced.
3. Frontend quality: reuse the existing design system, components, API client and
   token handling; no redesigns. Loaders (the backend cold-starts in ~40s), empty
   states and the backend's error messages. Handle 401 (refresh, then login), 403 and
   429. Run `flutter analyze` (plus `flutter test`) and the Web's checks.
4. Demo data: extend `seed_demo` with realistic, clearly fake data for the module.
5. `docs/handoff/<module>.md`: endpoints, examples, errors, screens.
6. One PR per module (backend + Web + App) with a checklist of the module's bullets,
   each marked done or deferred with the reason.
If a bullet conflicts with @docs/decisions.md or can't be done in the phase, put it in
the question list with options; never skip it silently. Before editing a Web or App
screen, check the open frontend branches and build on them. Update
@docs/status/module-tracker.md after every module.

## Commands
- Activate venv: [OS-appropriate command]
- Run server: python manage.py runserver
- Run tests: pytest
- Make migrations: python manage.py makemigrations
- Migrate: python manage.py migrate

## Current status
See @docs/decisions.md and update it whenever an architectural choice is made.
