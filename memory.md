# Memory — Amazon Second Life AI — Phase 0 Foundation (A's tasks)

**Last updated:** 2026-06-13 · **Session:** Member A (Full-Stack) Phase 0 progress (3 of 5 tasks done)

---

## What was built

**Phase 0 partially done for Member A.** Three of five tasks (P0-A1, P0-A2, P0-A3) shipped. P0-A4 and P0-A5 remain.

### P0-A1 — Monorepo scaffold
- Full folder structure: `services/`, `packages/shared-py/`, `apps/web`, `scripts/`, `infra/`
- All 7 service scaffolds created with `app/`, `tests/`, `Dockerfile`, `pyproject.toml`, `config.py`, `api/routes.py`, `domain/`, `db/`, `events/`
- `.gitignore`, `.env.example` (config contract with all 20+ env vars documented)
- Root `README.md` with quick start, port table, team ownership, structure overview
- Root `pyproject.toml` with monorepo-wide ruff/black/pytest config
- `packages/shared-py/pyproject.toml` with all pinned versions from `library-docs.md`

### P0-A2 — Docker Compose infra
- `docker-compose.yml` with Postgres 16 (6 service DBs), Redis 7, MinIO (pinned release) + minio-init bucket setup
- All 7 services included with proper healthchecks, service-to-service dependencies (minio dependency for grading)
- All Dockerfiles updated: curl added for healthchecks, proper COPY paths for repo-root build context, commented-out alembic copies
- `infra/postgres/init.sql` — idempotent multi-DB init script
- `scripts/dev.sh` and `scripts/dev.ps1` — helper commands (up / up infra / down / reset / logs / ps)

### P0-A3 — shared-py/web package (create_app factory, health, errors, logging)
- **`shared_py.config`** — `BaseServiceSettings(BaseSettings)` with service_name, log_level, redis_url, ai_mode, aws fields, cors_origins; `configure_logging()` + `get_logger()` emitting single-line JSON logs
- **`shared_py.web.factory`** — `create_app(service_name, lifespan)` wires CORS, CorrelationIdMiddleware, RequestLoggingMiddleware, /health + /ready endpoints, three exception handlers (AppError → ErrorEnvelope, HTTPException → ErrorEnvelope, ValidationError → ErrorEnvelope)
- **`shared_py.web.health`** — /health (liveness) + /ready (readiness with `add_ready_check()` registration)
- **`shared_py.web.errors`** — `AppError` exception class (raise from domain/service without FastAPI import), handlers emit structured `ErrorEnvelope` JSON
- **`shared_py.web.middleware`** — `CorrelationIdMiddleware` (read/generate X-Correlation-Id), `RequestLoggingMiddleware` (structured JSON request/response logging, skips /health + /ready)
- **`shared_py.web.auth`** — `create_access_token()` + `decode_access_token()` JWT helpers (HS256, raise AppError(401) on failure)
- **All 7 service configs + main.py updated** — now inherit BaseServiceSettings and call `create_app()` properly
- **Tests:** `packages/shared-py/tests/test_web.py` — covers health, readiness, error handlers, middleware, auth; all passing

---

## Decisions made

1. **Single Postgres container, one DB per service** (logical isolation without 6 containers) — acceptable for 48h hackathon; no-cross-DB rule still enforced.
2. **Redis Streams for event bus** — chosen for at-least-once delivery + replay; hidden behind `events` wrapper so it can be swapped later.
3. **All config via pydantic-settings + .env** — never hardcoded secrets/URLs/ports. `.env.example` is the binding contract.
4. **Structured JSON logging from the start** — service_name, level, timestamp, correlation_id always present; single line per event for easy grep.
5. **CorrelationId on every request** — generated if absent, propagated to response header and request.state; enables cross-service tracing.
6. **ErrorEnvelope (error.code + error.message + error.correlation_id) everywhere** — standardized error shape across all services.
7. **AppError + three HTTP exception handlers** — domain logic raises AppError (no FastAPI import), handlers convert to ErrorEnvelope JSON.
8. **JWT HS256 with shared JWT_SECRET** — User Service issues, Gateway verifies, internal services trust X-User-Id header.

---

## Problems solved

None in this session — all three P0-A tasks completed cleanly without blockers.

---

## Current state

**Phase 0 — Foundation: 3 of 5 Member A tasks done. CP0 checkpoint NOT yet green.**

- ✅ P0-A1 — Monorepo scaffold done
- ✅ P0-A2 — Docker Compose infra done
- ✅ P0-A3 — shared-py/web (create_app factory) done
- 📋 P0-A4 — shared-py events wrapper (Redis Streams, DLQ) — NOT STARTED
- 📋 P0-A5 — shared contracts (enums, event payloads, OpenAPI stubs) — NOT STARTED

**What works right now:**
- Docker Compose stack boots: Postgres (6 DBs), Redis, MinIO, all 7 services with /health returning 200
- Shared-py package: services can `from shared_py.web import create_app` and get fully wired app
- Config inheritance, structured logging, error envelope, correlation-id middleware, auth helpers all tested

**What's still missing for CP0:**
- Events wrapper (publish/subscribe, DLQ, idempotency) — needed for the saga
- Shared contracts (enums, event payloads) — needed by B and C
- Until those land, B cannot start P0-B1 (AI wrapper depends on P0-A3 ✅ but P0-B3 depends on P0-A4)

---

## Next session starts with

**Member A next task: P0-A4 — shared-py/events wrapper**

Deliverable per build-plan.md:
- Redis Streams `publish()` + `@subscribe()` decorator over `slmai:events` stream
- Envelope builder (event_id, event_type, event_version, occurred_at, correlation_id, producer, data)
- Idempotency via event_id deduplication
- Retry → dead-letter (`slmai:events:dlq`) on repeated handler failure
- Handlers must be async and idempotent
- Propagate correlation_id always

Files to create:
- `packages/shared-py/events/__init__.py` — exports `publish`, `subscribe`, `EventEnvelope`
- `packages/shared-py/events/client.py` — Redis client singleton + `publish(event_type, correlation_id, data)` function
- `packages/shared-py/events/handlers.py` — `@subscribe(group, handler_name)` decorator, consumer loop, idempotency cache, DLQ routing
- `packages/shared-py/events/schemas.py` — Pydantic models for `EventEnvelope` + all event types (10 events from architecture.md §6)
- `packages/shared-py/tests/test_events.py` — tests for publish, subscribe, DLQ, idempotency

This depends on:
- P0-A2 (Docker Compose with Redis) — ✅ done
- P0-A3 (shared config, logging) — ✅ done

After P0-A4 ships, Member B can build P0-B1 (AI wrapper) because both depend on the events foundation.

---

## Open questions

None. Path forward is clear: P0-A4 next, then P0-A5 contracts, then Phase 1 services (P1-A1 User, P1-A2 Gateway). Phase 0 is NOT complete until A4 + A5 ship and CP0 is verified.

---

## Key files and paths

**Monorepo root:** `d:\Content\CSE\Hackathons\Hackon 2026\second-life-ai\`

**Core config:**
- `.env.example` — all env vars documented (copy to `.env` to run locally)
- `docker-compose.yml` — full local stack
- `pyproject.toml` — monorepo lint/test config (ruff, black, pytest)

**Shared library:**
- `packages/shared-py/` — web factory, config, logging, auth, tests
- `packages/shared-py/config/` — BaseServiceSettings, configure_logging, get_logger
- `packages/shared-py/web/` — create_app, health, errors, middleware, auth, schemas

**Service stubs:**
- `services/{gateway,user,passport,grading,lifecycle,matching,sustainability}/`
  - Each has `app/main.py`, `app/config.py`, `Dockerfile`, `pyproject.toml`
  - Main.py already calls `create_app(settings.service_name)` — ready for Phase 1 implementation

**Documentation:**
- `docs/architecture.md` — system design, services, event flow
- `docs/code-standards.md` — implementation rules, naming, git workflow
- `docs/build-plan.md` — phased tasks, dependencies, checkpoints
- `docs/progress-tracker.md` — live status (P0-A1/A2/A3 marked ✅ Done)
- `docs/library-docs.md` — pinned versions + usage rules per library

**Helper scripts:**
- `scripts/dev.sh` — Linux/Mac: up, down, reset, logs, ps
- `scripts/dev.ps1` — PowerShell: same commands
- `scripts/seed.py`, `seed_min.py`, `events_tail.py` — stubs for Phase 0-B work

