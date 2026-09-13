# Module Reference

This is a running technical reference of the backend codebase, built up incrementally
as features are implemented. For every file that carries logic (services, selectors,
API views, tasks, etc.) it records:

- the file and the function/class in it
- what that function/class does
- the API endpoint it powers, if any
- which frontend (MindCare Web, MindCare App, or neither) consumes it

This file is not architecture documentation — see @architecture.md for that. Its
purpose is to give whoever writes the final FYP project documentation a complete,
accurate inventory of the codebase to work from, without having to re-derive it from
the source at the end of the project. It is kept up to date as we go rather than
reconstructed later, per the rule in @../CLAUDE.md.

## How to add an entry

Append a row to the relevant app's table below (add a new `### apps/<app_name>`
section, in alphabetical order, if one doesn't exist yet) whenever you implement a
new service, selector, or API endpoint. Keep entries one row per function/class.

| File | Function / Class | Purpose | API Endpoint | Frontend Consumer |
|------|-------------------|---------|--------------|--------------------|
| _example:_ `apps/accounts/services.py` | `register_patient()` | Creates a `User` + `PatientProfile` in one transaction, sends verification email | `POST /api/v1/accounts/register/` | MindCare Web, MindCare App |

---

<!-- Add new `### apps/<app_name>` sections below as modules are implemented. -->
