# Memory — Amazon Second Life AI — Phase 0 Complete (Member A)

Last updated: 2026-06-13

## What was built

**Phase 0 COMPLETE for Member A** — all 5 foundation tasks shipped successfully.

### P0-A4 — shared-py/events wrapper (completed this session)
- `shared_py/events/schemas.py` — EventEnvelope + 10 event payload models with Pydantic validation, EVENT_TYPE_TO_MODEL registry
- `shared_py/events/client.py` — Redis async client singleton, publish() with envelope construction and validation
- `shared_py/events/handlers.py` — @subscribe() decorator, start_consumer()/stop_consumer(), XREADGROUP consumer loop, idempotency cache (event_id dedupe), retry logic with DLQ routing to `slmai:events:dlq` after MAX_RETRIES (3)
- `shared_py/events/__init__.py` — clean public API
- `tests/test_events.py` — 12 comprehensive tests covering publish, subscribe, idempotency, retry, DLQ

### P0-A5 — shared contracts (completed this session)
**Python side** (`packages/shared-py/shared_py/schemas/`):
- `enums.py` — 5 shared enums: Grade (A/B/C/D), LifecycleAction (RESELL/REFURBISH/DONATE/RECYCLE/HYPERLOCAL), ReturnStatus (SUBMITTED through SOLD plus FAILED), ListingChannel, ListingStatus
- `rest_contracts.py` — Cross-service DTOs: UserCandidatesListResponse (Matching→User contract), ReturnResponse (Gateway owns Return), ProductResponse (Passport owns Product), PaginatedResponse, HealthResponse, ErrorEnvelope
- `SERVICE_ENDPOINTS.md` — Complete REST catalog documenting all 7 services, every endpoint, cross-service call patterns

**TypeScript side** (`apps/web/types/`):
- `enums.ts` — TypeScript mirror of Python enums (exact value matching)
- `events.ts` — EventEnvelope<T> + 10 event payload interfaces + union types
- `api.ts` — Full API response types for all services (User, Return, Grade, Decision, Passport, Match, Listing, Sustainability)
- `index.ts` — barrel export, `README.md` — sync protocol documentation

### Package structure fix (this session)
- Reorganized `packages/shared-py/` to proper structure: moved modules into `shared_py/` subdirectory so imports work correctly (`from shared_py.events import ...`)
- Added `shared_py/__init__.py` with version info

---

## Decisions made

1. **Redis Streams for event bus** — at-least-once delivery with replay capability, wrapped in shared events package
2. **Idempotency via in-memory cache** — event_id deduplication using set (10k entry limit with FIFO eviction); production could use Redis-backed cache
3. **DLQ after 3 retries** — failed events move to `slmai:events:dlq` stream, owning service sets Return.status = FAILED to halt saga cleanly
4. **Contract-first approach** — all 10 events defined with Pydantic schemas before any service implementation
5. **TypeScript mirrors Python exactly** — enum values, field names, types match one-to-one for cross-stack consistency
6. **SERVICE_ENDPOINTS.md as binding catalog** — documents all REST endpoints, cross-service patterns, OpenAPI locations; serves as implementation reference

---

## Problems solved

1. **Package structure mismatch** — imports were failing because folders were at wrong level. Fixed by creating proper `shared_py/` parent directory and moving `ai/`, `config/`, `events/`, `schemas/`, `web/` inside it.
2. **Hatchling package discovery** — needed to structure package correctly for editable installs to work (`pip install -e packages/shared-py`)

---

## Current state

**Phase 0 — Member A: 5/5 tasks complete ✅**
- P0-A1: Monorepo scaffold ✅
- P0-A2: Docker Compose infra ✅  
- P0-A3: shared-py/web base ✅
- P0-A4: shared-py/events wrapper ✅ (completed this session)
- P0-A5: Shared contracts ✅ (completed this session)

**What works:**
- Docker Compose boots: Postgres (6 DBs), Redis, MinIO, all 7 services
- Shared-py package: config, web factory, events (publish/subscribe/DLQ), schemas (enums + REST contracts)
- 10 event types fully defined with validation
- 5 shared enums in both Python and TypeScript
- Cross-service contracts documented in SERVICE_ENDPOINTS.md
- TypeScript types ready in apps/web/types/

**Syntax validated:** All Python files compile cleanly with `python -m py_compile`

**Phase 0 overall status:**
- Member A: 5/5 ✅ (100% complete)
- Member B: 0/3 (P0-B1 AI wrapper, P0-B2 seed, P0-B3 observability)
- Member C: 0/3 (P0-C1 web scaffold, P0-C2 primitives, P0-C3 API client)

**CP0 checkpoint:**
- ✅ Infra boots
- ✅ Events wrapper with DLQ ready
- ✅ Enums + REST contracts in both stacks
- ⬜ Seed (needs P0-B2)
- ⬜ Frontend shell (needs P0-C1/C2/C3)

---

## Next session starts with

**Member A can proceed to Phase 1 immediately** — all dependencies satisfied.

**P1-A1 — User Service:**
- Auth endpoints (register/login) with password hashing
- JWT token issuance (HS256 with shared JWT_SECRET)
- User profile CRUD
- GET /users/candidates endpoint (for Matching service)
- SQLAlchemy models + Alembic migrations
- Tests

**P1-A2 — API Gateway + Returns intake:**
- JWT verification middleware
- POST /returns endpoint (creates Return, uploads to MinIO, emits ReturnSubmitted)
- Route proxying to services
- CORS configuration
- Aggregation endpoints for BFF pattern

Both can start now — P0-A3 (web base), P0-A4 (events), and P0-A5 (contracts) are complete.

---

## Open questions

None — Member A's foundation work is complete and unblocks the team.

---

## Key files created this session

**Events wrapper:**
- `packages/shared-py/shared_py/events/schemas.py` (218 lines)
- `packages/shared-py/shared_py/events/client.py` (125 lines)
- `packages/shared-py/shared_py/events/handlers.py` (278 lines)
- `packages/shared-py/shared_py/events/__init__.py` (updated)
- `packages/shared-py/tests/test_events.py` (380 lines)

**Shared contracts:**
- `packages/shared-py/shared_py/schemas/enums.py` (86 lines)
- `packages/shared-py/shared_py/schemas/rest_contracts.py` (170 lines)
- `packages/shared-py/shared_py/schemas/SERVICE_ENDPOINTS.md` (180 lines)
- `packages/shared-py/shared_py/schemas/__init__.py` (updated)

**TypeScript types:**
- `apps/web/types/enums.ts` (75 lines)
- `apps/web/types/events.ts` (150 lines)
- `apps/web/types/api.ts` (220 lines)
- `apps/web/types/index.ts` (barrel export)
- `apps/web/types/README.md` (sync protocol)

**Documentation updated:**
- `docs/progress-tracker.md` — P0-A4 and P0-A5 marked complete
