# Requirements: P3-A1 Demo-Narrative Seed & Gateway Dashboard

## Introduction

This document specifies the requirements for **P3-A1: Demo-narrative seed + Gateway read-model + demo wiring**, a Phase 3 task that creates a complete, judge-ready demo narrative for the Amazon Second Life AI platform. The feature expands the minimal seed data into a comprehensive dataset covering all lifecycle actions and adds Gateway BFF endpoints for the sustainability dashboard.

### Context

**Owner:** Member A (Full-Stack)  
**Phase:** 3 (Dashboard, Polish & Demo)  
**Dependencies:** P0-B2 (seed_min), P2-A2 (Gateway aggregation), P2-B2 (Sustainability Service)

The system currently has:
- **Minimal seed data** (`seed_min.py`): 6 users, 4 products, 2 returns with golden-path support
- **Complete event saga**: All 7 services operational with 10-event flow working end-to-end
- **Gateway BFF pattern**: Existing aggregation endpoints for returns, passports, matches
- **Sustainability Service**: Metrics aggregation endpoints already implemented (P2-B2)

### Business Goals

1. **Enable Judge Walkthrough**: Provide rich, compelling demo data that showcases all system capabilities for hackathon judging
2. **Support Dashboard Development**: Expose sustainability metrics via Gateway BFF so frontend (P3-C1) can build the dashboard
3. **Demonstrate Full Lifecycle Coverage**: Show all 5 lifecycle actions (RESELL, REFURBISH, DONATE, RECYCLE, HYPERLOCAL) in action
4. **Production-Ready Seeding**: Create idempotent, deterministic seed scripts that work in any environment

---

## User Stories

### US-1: Demo Data Seeding
**As a** developer/judge  
**I want to** run a single command to populate the system with a complete demo narrative  
**So that** the full event saga and dashboard are immediately visible without manual data entry

**Acceptance Criteria:**
1. Running `python scripts/seed.py` creates 8 demo returns covering all lifecycle actions
2. All event saga artifacts (grades, decisions, passports, matches, listings, sustainability records) are pre-seeded
3. Script is idempotent — running twice produces the same result
4. Script gracefully continues if some services aren't ready yet
5. Manifest output shows all seeded data with demo instructions

### US-2: Dashboard Metrics Aggregation
**As a** frontend developer building the sustainability dashboard  
**I want to** fetch aggregated sustainability metrics via a Gateway endpoint  
**So that** I can display total CO₂ saved, waste diverted, value recovered, and green credits

**Acceptance Criteria:**
1. Gateway exposes `GET /dashboard/sustainability/metrics` endpoint
2. Endpoint returns aggregated totals: `{co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits}`
3. Endpoint supports optional `user_id` query parameter for filtering
4. Endpoint requires JWT authentication
5. Endpoint handles upstream service failures gracefully (502 on unreachable)

### US-3: Dashboard Records History
**As a** frontend developer building the sustainability dashboard  
**I want to** fetch paginated sustainability records via a Gateway endpoint  
**So that** I can display detailed history of sustainability impact over time

**Acceptance Criteria:**
1. Gateway exposes `GET /dashboard/sustainability/records` endpoint
2. Endpoint returns paginated list: `{items: [], total: int, limit: int, offset: int}`
3. Endpoint supports optional filters: `user_id`, `return_id`
4. Endpoint supports pagination: `limit` (1-100, default 20), `offset` (default 0)
5. Endpoint requires JWT authentication
6. Endpoint validates query parameters (422 on invalid values)

### US-4: Judge Demo Walkthrough
**As a** hackathon judge  
**I want to** see a complete demo narrative with varied lifecycle outcomes  
**So that** I can evaluate the system's sustainability impact and decision logic

**Acceptance Criteria:**
1. Demo includes 8 returns with clear narratives (e.g., "Carol donates jacket in good condition")
2. All 5 lifecycle actions are represented: RESELL, REFURBISH, DONATE, RECYCLE, HYPERLOCAL
3. Each return has a complete saga: grade → decision → passport → matches/listings → sustainability
4. Golden-path return (headphones) demonstrates the full flow for judges
5. Dashboard shows aggregated metrics immediately after seeding

---

## Functional Requirements

### FR-1: Enhanced Seed Script

The system SHALL provide an enhanced seed script (`scripts/seed.py`) that extends `seed_min.py` with a complete demo narrative.

**FR-1.1: Demo Return Coverage**  
The seed script SHALL create 8 total returns (6 new + 2 from seed_min) covering:
- RESELL (Grade A, like-new smartwatch)
- REFURBISH (Grade C, smartphone needs repair)
- DONATE (Grade B, jacket in good condition)
- RECYCLE (Grade D, broken tablet)
- HYPERLOCAL (Grade B, heavy furniture, ergonomic chair)
- Golden-path HYPERLOCAL (Grade B, headphones from seed_min)
- Additional variety (laptop with dead pixels from seed_min)

**FR-1.2: Pre-Seeded Saga Data**  
The seed script SHALL pre-seed all event saga artifacts:
- **Grades:** One grade record per return in `slmai_grading.grades`
- **Decisions:** One lifecycle decision per return in `slmai_lifecycle.lifecycle_decisions`
- **Passports:** One passport per return in `slmai_passport.passports`
- **Matches:** Match requests and matches for HYPERLOCAL returns in `slmai_matching.match_requests` and `matches`
- **Listings:** Marketplace listings for RESELL/REFURBISH returns in `slmai_matching.listings`
- **Sustainability:** One sustainability record per return in `slmai_sustainability.sustainability_records`

**FR-1.3: Idempotent Seeding**  
The seed script SHALL use deterministic UUIDs (`uuid.uuid5`) and `ON CONFLICT DO UPDATE` to ensure idempotency. Running the script multiple times SHALL produce the same result.

**FR-1.4: Graceful Degradation**  
The seed script SHALL continue seeding other services if some service databases are unavailable, logging warnings but not failing completely.

**FR-1.5: CLI Flags**  
The seed script SHALL support:
- `--reset` flag to clean existing data before seeding
- `--quick` flag to skip `seed_min.py` (only add demo narrative)

**FR-1.6: Manifest Output**  
The seed script SHALL print a manifest showing:
- All 8 demo returns with narratives
- Golden-path return details
- Aggregated dashboard metrics (CO₂, waste, value, credits)
- Service endpoints
- Next steps for judge walkthrough

### FR-2: Gateway Dashboard Endpoints

The Gateway SHALL expose two new BFF endpoints for sustainability dashboard aggregation.

**FR-2.1: Metrics Aggregation Endpoint**  
The Gateway SHALL expose `GET /dashboard/sustainability/metrics` with:
- Optional `user_id` query parameter for filtering by user
- JWT authentication requirement (via `get_current_user_id` dependency)
- Response format:
  ```json
  {
    "co2_avoided_kg": float,
    "waste_diverted_kg": float,
    "value_recovered": float,
    "green_credits": int
  }
  ```
- Proxies to Sustainability Service `GET /sustainability/metrics`
- Returns 502 if Sustainability Service is unreachable
- Returns 401 if JWT is missing or invalid

**FR-2.2: Records List Endpoint**  
The Gateway SHALL expose `GET /dashboard/sustainability/records` with:
- Optional filters: `user_id`, `return_id`
- Pagination parameters: `limit` (1-100, default 20), `offset` (default 0)
- JWT authentication requirement
- Response format:
  ```json
  {
    "items": [SustainabilityRecord, ...],
    "total": int,
    "limit": int,
    "offset": int
  }
  ```
- Proxies to Sustainability Service `GET /sustainability`
- Returns 502 if Sustainability Service is unreachable
- Returns 422 if query parameters are invalid (e.g., limit > 100, offset < 0)
- Returns 401 if JWT is missing or invalid

### FR-3: ServiceClient Extensions

The Gateway ServiceClient SHALL be extended with two new methods for sustainability aggregation.

**FR-3.1: get_sustainability_metrics() Method**  
The ServiceClient SHALL provide `get_sustainability_metrics(user_id, requesting_user_id)` that:
- Calls Sustainability Service `GET /sustainability/metrics`
- Accepts optional `user_id` parameter for filtering
- Propagates `X-User-Id` header with `requesting_user_id`
- Returns metrics dict with `{co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits}`
- Raises `AppError(502, "upstream_unreachable")` on `httpx.RequestError`
- Propagates `AppError` status codes from upstream

**FR-3.2: list_sustainability_records() Method**  
The ServiceClient SHALL provide `list_sustainability_records(user_id, return_id, limit, offset, requesting_user_id)` that:
- Calls Sustainability Service `GET /sustainability`
- Accepts optional `user_id` and `return_id` filters
- Accepts pagination parameters `limit` and `offset`
- Propagates `X-User-Id` header with `requesting_user_id`
- Returns paginated response dict with `{items, total, limit, offset}`
- Raises `AppError(502, "upstream_unreachable")` on `httpx.RequestError`
- Propagates `AppError` status codes from upstream

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1: Seed Script Execution Time**  
The seed script SHALL complete in under 10 seconds for all 8 returns across 6 service databases.

**NFR-1.2: Dashboard Query Response Time**  
Dashboard endpoints SHALL respond in under 200ms for typical datasets (P95 latency).

### NFR-2: Reliability

**NFR-2.1: Idempotency**  
Running the seed script multiple times SHALL produce identical results (deterministic UUIDs, upsert logic).

**NFR-2.2: Graceful Degradation**  
The seed script SHALL continue if some services are unavailable, logging warnings and producing a partial seed.

**NFR-2.3: Upstream Failure Handling**  
Dashboard endpoints SHALL return 502 with error envelope if Sustainability Service is unreachable, allowing the frontend to show appropriate error states.

### NFR-3: Security

**NFR-3.1: Authentication**  
All dashboard endpoints SHALL require valid JWT authentication via `get_current_user_id` dependency.

**NFR-3.2: Header Propagation**  
Dashboard endpoints SHALL forward `X-User-Id` header to upstream services for auth context.

**NFR-3.3: Input Validation**  
Dashboard endpoints SHALL validate query parameters using FastAPI Pydantic validators (e.g., `ge=1, le=100` for limit).

### NFR-4: Maintainability

**NFR-4.1: Code Reuse**  
The seed script SHALL reuse helpers from `seed_min.py` (DB connections, deterministic UUIDs, golden-path constants).

**NFR-4.2: Pattern Consistency**  
ServiceClient methods SHALL follow existing patterns: error handling, header propagation, timeout configuration.

**NFR-4.3: Documentation**  
The seed script SHALL include docstrings for all functions. Gateway README SHALL document new dashboard endpoints with examples.

### NFR-5: Testability

**NFR-5.1: Unit Test Coverage**  
Dashboard routes SHALL have unit tests covering:
- Happy path (metrics and records endpoints)
- Error paths (upstream 502, missing JWT 401, invalid params 422)
- Filtering and pagination

**NFR-5.2: Manual Verification**  
The seed script SHALL output a manifest with verification steps for manual testing.

---

## Constraints

### Technical Constraints

**C-1: Database Direct Access**  
The seed script uses direct database insertion (via `asyncpg`) rather than REST APIs to avoid circular dependencies and ensure immediate demo availability.

**C-2: Existing Sustainability Service**  
Dashboard endpoints proxy to the Sustainability Service (P2-B2), which already implements aggregation logic. Gateway does not duplicate this logic.

**C-3: BFF Pattern**  
Dashboard endpoints follow the Backend-for-Frontend (BFF) pattern established in P2-A2, aggregating data from upstream services.

**C-4: JWT Dependency**  
Dashboard endpoints depend on the existing `get_current_user_id` middleware for authentication.

### Operational Constraints

**C-5: Service Availability**  
The seed script assumes all service databases are migrated (`alembic upgrade head`) but degrades gracefully if not.

**C-6: MinIO Dependency**  
The seed script references MinIO S3 keys for media but does not upload actual files (uses placeholders).

**C-7: Environment Variables**  
The seed script requires environment variables for all 6 service database URLs (from `.env` or docker-compose).

---

## Glossary

| Term | Definition |
|------|------------|
| **BFF (Backend-for-Frontend)** | API Gateway pattern where the gateway aggregates data from multiple upstream services to serve frontend needs |
| **Demo Narrative** | A curated dataset with realistic stories (e.g., "Carol donates jacket") that showcases system capabilities |
| **Golden-Path** | A predetermined return (headphones) with deterministic grading for reproducible demos |
| **Idempotent** | An operation that produces the same result when executed multiple times |
| **Lifecycle Action** | The AI-decided outcome for a return: RESELL, REFURBISH, DONATE, RECYCLE, or HYPERLOCAL |
| **Event Saga** | The 10-event choreography across 7 services that processes a return from submission to sustainability impact |
| **Seed Script** | A script that populates databases with demo/test data |
| **Upstream Service** | A backend service (e.g., Sustainability Service) that Gateway calls via HTTP |

---

## Acceptance Criteria Summary

This feature is complete when:

1. ✅ **Seed Script**: `python scripts/seed.py --reset` creates 8 demo returns covering all lifecycle actions
2. ✅ **Pre-Seeded Saga**: All grades, decisions, passports, matches, listings, sustainability records exist
3. ✅ **Idempotency**: Running seed script twice produces identical results
4. ✅ **Graceful Degradation**: Seed script continues if some services unavailable
5. ✅ **Dashboard Metrics Endpoint**: `GET /dashboard/sustainability/metrics` returns aggregated totals
6. ✅ **Dashboard Records Endpoint**: `GET /dashboard/sustainability/records` returns paginated list
7. ✅ **Authentication**: Both endpoints require JWT and return 401 if missing
8. ✅ **Error Handling**: Both endpoints return 502 if Sustainability Service unreachable
9. ✅ **Input Validation**: Records endpoint validates limit/offset (422 on invalid)
10. ✅ **ServiceClient Methods**: `get_sustainability_metrics()` and `list_sustainability_records()` implemented
11. ✅ **Tests**: 9+ unit tests covering happy/error paths for dashboard endpoints
12. ✅ **Documentation**: Gateway README documents new endpoints; seed script includes manifest output

---

## References

- [Architecture](../../../docs/architecture.md) — System design, service boundaries
- [Build Plan](../../../docs/build-plan.md) — Task P3-A1 definition and dependencies
- [Progress Tracker](../../../docs/progress-tracker.md) — Task completion status
- [seed_min.py](../../../scripts/seed_min.py) — Base seed script this extends
- [P2-B2 Requirements](../sustainability-service/requirements.md) — Sustainability Service metrics endpoints

---

**Status**: Requirements Complete  
**Next**: [Technical Design](./design.md)
