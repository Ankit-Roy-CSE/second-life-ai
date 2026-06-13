# Memory — Amazon Second Life AI — P1-A1 Complete (Member A)

Last updated: 2026-06-14

## What was built

Complete User Service implementation with authentication, profile management, and cross-service buyer matching for P1-A1.

**Files created in services/user/:**
- `app/db/session.py` — Async session with get_db() dependency (commit/rollback handling)
- `app/db/repository.py` — UserRepository: create, get_by_id, get_by_email, update, find_candidates
- `app/domain/service.py` — UserService with bcrypt password hashing, JWT issuance, Haversine distance for candidate matching
- `app/api/routes.py` — 6 endpoints: POST /auth/register, POST /auth/login, GET/PATCH /users/{id}, GET /users/{id}/credits, GET /users/candidates
- `app/main.py` — Updated with lifespan for table creation and route wiring
- `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` — Alembic async setup
- `alembic/versions/001_create_users_table.py` — Initial migration
- `tests/conftest.py` — In-memory SQLite test setup
- `tests/test_auth.py` — 5 auth tests (register, duplicate email, login, invalid credentials)
- `tests/test_users.py` — 5 user tests (get, update, credits, candidates with distance)
- `README.md`, `IMPLEMENTATION_SUMMARY.md`, `verify_implementation.py` — Documentation

**All 6 API endpoints per SERVICE_ENDPOINTS.md contract:**
1. POST /auth/register — bcrypt hash, return user (no password_hash)
2. POST /auth/login — verify password, issue JWT (HS256, 24h)
3. GET /users/{id} — get profile
4. PATCH /users/{id} — update display_name, location, interests
5. GET /users/{id}/credits — get green_credits balance
6. GET /users/candidates — find buyers (category + lat/lng/radius filters, sorted by distance)

## Decisions made

1. **Bcrypt for passwords** — passlib[bcrypt] for hashing. Minimum 8 chars. Never return password_hash in responses.
2. **JWT HS256 with shared secret** — Gateway verifies and forwards X-User-Id. 24h expiry (JWT_EXPIRE_MINUTES=1440).
3. **Haversine distance for matching** — Simplified geospatial (no PostGIS). Filters category in Python, calculates distance, sorts by proximity.
4. **In-memory SQLite for tests** — Fast, no external deps. Each test gets fresh DB via conftest fixture.
5. **Lifespan creates tables** — Dev convenience. Production uses alembic upgrade head.
6. **Green credits start at 0.0** — Sustainability service updates later via events.

## Problems solved

1. **Async session management** — get_db() dependency handles commit/rollback automatically
2. **Password security** — bcrypt.hash() for storage, bcrypt.verify() for login, never expose password_hash
3. **JWT issuance** — Used shared create_access_token() from shared_py.web.auth with user.id as subject
4. **Candidate matching** — Implemented /users/candidates with category filter (interests array) and Haversine radius filter
5. **Test isolation** — conftest.py creates in-memory SQLite per test, no shared state

## Current state

**Phase 0:** 11/11 complete (A: 5/5, B: 3/3, C: 3/3)

**Phase 1:** 1/7 complete
- ✅ P1-A1 User Service — DONE (6 endpoints, 10 tests, docs, migration)
- 📋 P1-A2 Gateway + Returns intake — Next for Member A
- 📋 P1-B1, P1-B2, P1-C1, P1-C2, P1-C3

**User Service ready for:**
- Gateway proxy (P1-A2)
- Matching service calls (P2-B1)
- Frontend via Gateway (P1-C1)

**Progress tracker updated:**
- P1-A1 marked ✅ Done
- Phase 1: 1/7 complete
- Service Readiness table: user service all ✅

## Next session starts with

**P1-A2 — API Gateway + Returns intake**

Build services/gateway/:
1. **Gateway owns Return table** — create slmai_gateway DB with Return entity (id, product_id, user_id, reason, media[], status, created_at)
2. **JWT verification middleware** — decode token, forward X-User-Id header to downstream services
3. **Proxy auth to User Service** — POST /auth/register and POST /auth/login → http://user:8001
4. **Returns endpoints:**
   - POST /returns → create Return, upload media to MinIO, emit ReturnSubmitted event
   - GET /returns → list returns (paginated, filter by user_id/status)
   - GET /returns/{id} → BFF aggregation (Return + Grade + Decision + Passport + Matches)
5. **MinIO integration** — upload media files, store S3 keys in Return.media[]
6. **Event emission** — publish ReturnSubmitted via shared events wrapper
7. **CORS** — allow frontend origin
8. **Tests** — proxy auth, create return, emit event, MinIO upload

Gateway has no Alembic (stateless except Return table created via SQLAlchemy metadata in lifespan).

## Open questions

None — P1-A1 complete and ready for integration
