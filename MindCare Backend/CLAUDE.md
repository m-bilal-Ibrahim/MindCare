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
- Ask ONE hard, concrete question at a time; wait for the answer before the next.
- Challenge assumptions rather than agreeing with the requested approach by default.
- Actively surface missing requirements and ambiguities — don't silently fill gaps with assumptions.
- Explicitly consider: user roles, permissions/authorization, expected behavior, edge cases, failure states, validation, data requirements, integration/dependency implications, and acceptance criteria.
- Continue until requirements are sufficiently specified, then summarize the finalized requirements and proposed implementation approach, and ask for confirmation before implementing.
- Trivial changes with no meaningful ambiguity or design risk may skip the interview.

## Commands
- Activate venv: [OS-appropriate command]
- Run server: python manage.py runserver
- Run tests: pytest
- Make migrations: python manage.py makemigrations
- Migrate: python manage.py migrate

## Current status
See @docs/decisions.md and update it whenever an architectural choice is made.
