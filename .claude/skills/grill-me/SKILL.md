---
name: grill-me
description: Use before implementing any new feature or design in MindCare Backend — runs a requirements interview (one hard question at a time) to surface missing requirements, edge cases, roles/permissions, validation rules, failure states, data requirements, and acceptance criteria before any code is written.
disable-model-invocation: true
---

Run a relentless requirements interview before any implementation begins. Do not write or propose implementation code during this skill — the output of this skill is a finalized, confirmed requirements summary, nothing else.

## Rules

- Ask exactly **one question at a time**. Wait for the answer before asking the next.
- Each question should be the single highest-leverage thing left unresolved — prefer questions that eliminate the most ambiguity or risk.
- Challenge assumptions. If the user states something as a given, probe whether it's actually true or just convenient.
- Do not accept vague answers ("handle it properly", "the usual way") — push for a concrete, specific answer.
- Do not start writing code, pseudocode, file structures, or implementation plans while grilling. If asked to implement early, decline and continue the interview.

## Areas to cover

Work through these systematically, skipping only what's already fully answered by context (e.g. this project's CLAUDE.md and docs/architecture.md already fix some answers — don't re-ask those, but do confirm the feature doesn't violate them):

1. **Problem framing** — what is this feature for, who asked for it, what happens if it doesn't exist.
2. **User roles & permissions** — which roles (patient / psychologist / admin / NGO / etc.) can access this, and what object-level ownership checks apply (per this project's hard rule: role-based access alone is never sufficient).
3. **Data requirements** — what data is read/written, where it lives, whether any of it is PHI (patient names, journal content, clinical notes, health data) and therefore subject to the no-plaintext-logging rule.
4. **Validation rules** — what inputs are required/optional, valid ranges, uniqueness constraints, cross-field rules.
5. **Edge cases** — empty/missing data, concurrent access, boundary values, partial failures, retries.
6. **Failure states** — what should happen on each failure mode (bad input, downstream service down, permission denied, race condition) — and who sees what error.
7. **Side effects & integrations** — Celery tasks, Stripe, Zoom, FCM, AI recommendation approval workflow — does this feature touch any of them, and if so what's the contract.
8. **Acceptance criteria** — concrete, testable statements of done. These should map directly to what a service-layer test (tests/test_services.py) would assert.

## Ending the interview

Continue until every area above is either answered or explicitly ruled out as not applicable. Then:

1. Summarize the finalized requirements as a structured list (roles/permissions, data, validation, edge cases, failure states, acceptance criteria).
2. Ask the user to confirm the summary is correct and complete.
3. Only after explicit confirmation, stop — implementation is a separate, subsequent step, not part of this skill.
