# Architecture Decisions

## 2026-09-12 - Chose Django + DRF over FastAPI for the core backend
**Why:** Team's Python familiarity, and the need for an admin panel + ORM + built-in auth given the number of entities in this system.
**Alternatives considered:** FastAPI — faster and more "modern" for pure APIs, but would have required building admin tooling, auth, and ORM integration from scratch.

## 2026-09-12 - Chose a modular monolith (Django apps per domain) over microservices
**Why:** Unified backend requirement across MindCare Web and MindCare App, plus the FYP timeline doesn't allow for the operational overhead of running and deploying separate services.
**Alternatives considered:** Microservices per domain (accounts, appointments, payments, etc.) — better long-term scalability and isolation, but far too much infrastructure and deployment complexity for the timeline.

## 2026-09-12 - Kept AI inference as a separate FastAPI service, not merged into the Django monolith
**Why:** Different runtime needs (AI/ML dependencies vs. web framework dependencies) and a clean API boundary between the two services.
**Alternatives considered:** Running inference inside the Django process — simpler deployment, but couples unrelated dependency sets and runtime characteristics together.

## 2026-09-12 - Chose service/selector pattern over strict hexagonal Clean Architecture
**Why:** Pragmatic tradeoff that fits Django's ORM-centric style and avoids repository-interface boilerplate that fights the framework.
**Alternatives considered:** Hexagonal/Clean Architecture with repository interfaces — more testable/portable in theory, but adds significant boilerplate for a Django project of this size and timeline.

## 2026-09-12 - Chose PostgreSQL via Supabase/Neon, Redis via Redis Cloud, hosting via Render
**Why:** Free-tier student budget — these providers offer usable free tiers for a project at FYP scale.
**Alternatives considered:** Self-hosted Postgres/Redis on a VPS — more control, but more setup/maintenance burden and no free tier.
