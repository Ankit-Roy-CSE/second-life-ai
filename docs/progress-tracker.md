# Progress Tracker — Amazon Second Life AI

>**Single source of truth for build status.** This mirrors every task ID in
> [build-plan.md](build-plan.md) 1:1. **Update the relevant row immediately after finishing a
> feature** (in the same PR). Agents: read this first to know what's done and what to pick up
> next; write to it last as part of the Definition of Done.

---

## Update Protocol

1. When you **start** a task → set status `🚧 In progress`, add your initials + date.
2. When you **finish** (meets [code-standards.md](code-standards.md) §6 Definition of Done) →
 set `✅ Done`, fill **Notes** (what shipped) and **Link** (PR / endpoint / route).
3. If **blocked** → set `⛔ Blocked`, describe the blocker + who/what you're waiting on, and
 add it to the **Blockers** section below.
4. Keep **Last updated** (top) current. One task = one row; never delete rows, only update.

**Status legend:** `📋 Not started` · `🚧 In progress` · `⛔ Blocked` · `✅ Done`

**Last updated:** 2026-06-15 · **Updated by:** C · **Latest:** P3-C2 complete — Polish + states + a11y pass (NavBar Marketplace link, TanStack Query hooks, EmptyState coverage, ARIA wiring, heading fixes).

---

## Overall Progress

| Phase | Total | ✅ Done | 🚧 In progress | ⛔ Blocked | 📋 Not started |
|-------|-------|--------|----------------|-----------|----------------|
| Phase 0 — Foundation | 11 | 11 | 0 | 0 | 0 |
| Phase 1 — Core | 7 | 7 | 0 | 0 | 0 |
| Phase 2 — Integration | 9 | 7 | 0 | 0 | 2 |
| Phase 3 — Dashboard/Polish | 7 | 3 | 0 | 0 | 4 |
| **Total** | **34** | **28** | **0** | **0** | **6** |

> Update these counts whenever a status changes (keep them consistent with the rows below).

---

## Phase 0 — Foundation & Contracts

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P0-A1 | A | Monorepo scaffold (`.gitignore`, README, `.env.example`) | ✅ Done | Folder structure, all service stubs, Dockerfiles, docker-compose.yml, infra/postgres/init.sql, pyproject.toml, .gitignore, .env.example, README.md | a/scaffold/p0-a1 |
| P0-A2 | A | Docker Compose (Postgres multi-DB, Redis, MinIO) | ✅ Done | docker-compose.yml with all 7 services + Postgres 16 (6 DBs via init.sql), Redis 7, MinIO (pinned release) + minio-init bucket setup; healthchecks on all infra; curl added to all service images; dev.sh + dev.ps1 helper scripts | a/infra/p0-a2 |
| P0-A3 | A | shared-py base web (`create_app`, health, errors, logging) | ✅ Done | `shared_py.web.create_app()` factory with CORS, CorrelationId + RequestLogging middleware, /health + /ready endpoints, ErrorEnvelope handlers, AppError; `shared_py.config` base settings + structured JSON logging; `shared_py.web.auth` JWT helpers; all service main.py + config.py updated to use BaseServiceSettings; tests in packages/shared-py/tests/test_web.py | a/shared/p0-a3 |
| P0-A4 | A | shared-py events wrapper (Redis Streams + DLQ) | ✅ Done | Redis Streams publish/subscribe wrapper with EventEnvelope, idempotency via event_id dedupe, retry→DLQ after MAX_RETRIES, all 10 event schemas from architecture.md §6, comprehensive tests; files: events/client.py (publish + Redis singleton), events/handlers.py (@subscribe decorator + consumer loop + DLQ), events/schemas.py (EventEnvelope + 10 event payload models), tests/test_events.py | a/events/p0-a4 |
| P0-A5 | A | Shared contracts (enums+events+REST stubs+cross-service reads) | ✅ Done | Python: enums.py (5 enums: Grade, LifecycleAction, ReturnStatus, ListingChannel, ListingStatus), rest_contracts.py (cross-service DTOs: UserCandidatesListResponse for Matching→User, ReturnResponse/ProductResponse ownership, PaginatedResponse standard), SERVICE_ENDPOINTS.md (complete REST catalog for all 7 services); TypeScript: enums.ts, events.ts (10 event types), api.ts (full API response types), index.ts, README.md; contracts ready for Phase 1 | a/contracts/p0-a5 |
| P0-B1 | B | shared-py AI wrapper + mock mode (golden-path seeded) | ✅ Done | AI client with mode switching (mock/aws/hybrid); 5 typed methods matching spec: `analyze_media`, `summarize_damage`, `decide_lifecycle`, `match_rationale` + convenience `grade_product`; deterministic mock seeded from media-key hash (fallback to reason+category); golden-path constants (`GOLDEN_PATH_MEDIA_KEY`); `BEDROCK_MODEL_ID` env support; `correlation_id` kwarg on all methods for structured logging; Pydantic v2 idiomatic schemas (GradeResult, LifecycleDecision, MatchRationale, DefectItem, DamageSummary, MediaLabels); prompt templates in ai/prompts/; 22 tests covering determinism, golden-path saga, spec function separation, grade logic, lifecycle logic, match rationale, mode switching, graceful degradation | b/ai/p0-b1 |
| P0-B2 | B | Minimal seed/fixtures (`scripts/seed_min.py`) | ✅ Done | 6 users (1 returner + 4 nearby buyers with lat/lng + interests + 1 admin), 4 products across 3 categories, 2 returns (golden-path headphones + laptop), MinIO placeholder uploads, idempotent upserts (ON CONFLICT), graceful skip if tables not yet migrated, --reset flag, seed manifest printout; golden-path constants wired to GOLDEN_PATH_MEDIA_KEY | b/seed/p0-b2 |
| P0-B3 | B | Event-saga observability (tail + `/debug/events` + replay) | ✅ Done | `scripts/events_tail.py`: 5 commands (tail/dump/trigger/replay/stats), ANSI colour output, correlation_id filter, DLQ support, golden-path trigger flag, Redis connectivity check; `services/gateway/app/api/debug_routes.py`: GET /debug/events, GET /debug/events/dlq, GET /debug/events/stats, POST /debug/events/trigger with payload validation; wired into gateway main.py | b/observability/p0-b3 |
| P0-C1 | C | Web scaffold + tokens + route-map/IA | ✅ Done | Next.js app scaffolding, tailwind.config.ts, globals.css setup with Amazon tokens, routing pages created | c/web/p0-c1 |
| P0-C2 | C | Primitives batch 1 + AppShell/NavBar | ✅ Done | Button, Card, Badge, Input, Label, Skeleton, AppShell created | c/web/p0-c2 |
| P0-C3 | C | Frontend mock layer + typed API client | ✅ Done | api-client.ts created with mock approach using generated types | c/web/p0-c3 |

**Checkpoint CP0:** ✅ Verified — _infra boots; seed loads; shell+tokens render vs mocks; events round-trip + DLQ; enums + REST contracts in both stacks._

---

## Phase 1 — Core Services & Vertical Slice

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P1-A1 | A | User Service (auth/JWT, profile, credits) | ✅ Done | Complete User Service with auth, profile, and cross-service endpoints. Includes: SQLAlchemy User model, Pydantic schemas (RegisterRequest, LoginRequest, UserResponse, etc.), async session management, UserRepository (CRUD), UserService (business logic with bcrypt password hashing, JWT issuance, Haversine distance for candidate matching), FastAPI routes (POST /auth/register, POST /auth/login, GET/PATCH /users/{id}, GET /users/{id}/credits, GET /users/candidates), Alembic migration for users table, tests (test_auth.py + test_users.py with 10 test cases). All 6 endpoints per SERVICE_ENDPOINTS.md contract. | a/user/p1-a1 |
| P1-A2 | A | API Gateway + Returns intake (`ReturnSubmitted`) | ✅ Done | Complete Gateway Service with auth proxy, return management, and event emission. Includes: Return ORM model (Gateway owns Return table), Pydantic schemas (ReturnCreateRequest, ReturnResponse, ReturnListResponse, ReturnDetailResponse), async session management, JWT verification middleware (get_current_user_id), HTTP client for User Service proxy, MinIO client for media uploads, FastAPI routes (POST /auth/register → User:8001, POST /auth/login → User:8001, POST /returns with ReturnSubmitted event emission, GET /returns paginated list, GET /returns/{id} BFF aggregation stub), CORS for frontend, tests (test_auth_proxy.py + test_returns.py with 9 test cases), README documentation. All endpoints per SERVICE_ENDPOINTS.md. Ready for frontend integration. | a/gateway/p1-a2 |
| P1-B1 | B | AI Grading Service (`ProductGraded`) | ✅ Done | Consumes `ReturnSubmitted` → `ai_client.grade_product()` → persist Grade → emit `ProductGraded`; `GET /grades/{return_id}` + `GET /grades`; SQLAlchemy Grade model + Alembic migration (001_create_grades_table); idempotent handler (skips re-grading); lifespan wires DB + event consumer; 10 tests (domain idempotency, all grades storable, route 200/404, list endpoint) | b/grading/p1-b1 |
| P1-B2 | B | Lifecycle Decision Service (`LifecycleDecisionCreated`) | ✅ Done | Consumes `ProductGraded` → `ai_client.decide_lifecycle()` → persist LifecycleDecision → emit `LifecycleDecisionCreated`; `GET /decisions/{return_id}` + `GET /decisions`; SQLAlchemy LifecycleDecision model + Alembic migration (001_create_lifecycle_decisions_table); idempotent handler (skips re-deciding); lifespan wires DB + event consumer; 9 tests (domain idempotency, all actions storable, route 200/404, list endpoint, event handler) | b/lifecycle/p1-b2 |
| P1-C1 | C | Auth UI + API client JWT | ✅ Done | Implemented /login and /register with react-hook-form and Zod. Updated api-client.ts to store JWT. Wrapped app in AuthProvider. | c/web/p1-c1 |
| P1-C2 | C | Return submission + grade view | ✅ Done | Implemented /returns with FileUpload and Reason select. Grading progress and mock GradePanel on success. Implemented /returns/[id] detail view. | c/web/p1-c2 |
| P1-C3 | C | Primitives batch 2 + Empty/Error/PageHeader | ✅ Done | Implemented Select, Tabs, Dialog, Progress, Toast, Toaster, Tooltip, EmptyState, ErrorState, PageHeader. Added all to ui-registry.md. | c/web/p1-c3 |

**Checkpoint CP1:** ✅ Verified — _register → return → grade → decision (mock) via Gateway._

---

## Phase 2 — Integration & Remaining Services

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P2-A1 | A | Product Passport Service (`PassportCreated`, `HyperlocalMatchRequested`) | ✅ Done | Consumes ProductGraded + LifecycleDecisionCreated → builds Passport (Product + Passport models); emits PassportCreated + HyperlocalMatchRequested; GET /passports/{id} + GET /passports/by-return/{return_id}; SQLAlchemy Product + Passport models + Alembic migration; idempotent event handlers; lifespan wires DB + Redis consumers; 11 tests passing | a/passport/p2-a1 |
| P2-A2 | A | Gateway aggregation + `PurchaseCompleted` | ✅ Done | BFF aggregation: GET /returns/{id} fans out concurrently (asyncio.gather) to Grading/Lifecycle/Passport/Matching with partial-availability fallback (null/[] on upstream 404/unreachable); proxy routes GET /passports/{id} + GET /matches?return_id=; POST /purchase (listing lookup → correlation_id → PurchaseCompleted event; buyer_user_id locked to JWT); GET /marketplace (channel=MARKETPLACE&status=ACTIVE, 3-attempt back-off retry); ServiceClient extended with 7 upstream methods + _safe_call + _marketplace_with_retry; PurchaseRequest/PurchaseResponse schemas; 21 tests (happy + error paths + X-User-Id forwarding + 5 hypothesis property tests) all passing | a/gateway/p2-a2 |
| P2-B1 | B | Hyperlocal Matching Service (`MatchFound`/`NoMatchFound`, `ProductListed`) | ✅ Done | Consumes `HyperlocalMatchRequested` → fetches buyer candidates from User Service (`GET /users/candidates`) → Haversine scoring + AI rationale → persist MatchRequest/Match/Listing → emit `MatchFound`/`NoMatchFound` + `ProductListed`; `GET /matches?return_id=`, `GET /matches/{id}`, `GET /listings?channel=&status=`, `GET /listings/{id}`; SQLAlchemy models + Alembic migration; idempotent handler; graceful fallback to MARKETPLACE when User Service unavailable; all tests passing | b/matching/p2-b1 |
| P2-B2 | B | Sustainability Service (`SustainabilityUpdated`, metrics) | ✅ Done | Consumes `MatchFound`/`NoMatchFound`/`ProductListed`/`PurchaseCompleted` → deterministic CO₂/waste/value/credits calc (calculator.py, no LLM) → persist SustainabilityRecord → emit `SustainabilityUpdated`; `GET /sustainability?return_id=&user_id=`, `GET /sustainability/{id}`, `GET /sustainability/metrics?user_id=`; SQLAlchemy model + Alembic migration; idempotent upsert; lifespan wires DB + 4 event consumers; 15 tests (calculator unit, service upsert/idempotency/metrics, routes 200/404/list) | b/sustainability/p2-b2 |
| P2-B3 | B | Real AI path (`AI_MODE=aws/hybrid`) + prompt tuning + fallback | 📋 Not started | — | — |
| P2-B4 | B | Value-recovery + sustainability-score tuning | 📋 Not started | — | — |
| P2-C1 | C | Lifecycle decision UI (`DecisionCard`) | ✅ Done | Implemented DecisionCard and StatCard; integrated into /returns/[id] page. | c/web/p2-c1 |
| P2-C2 | C | Passport UI (`PassportTimeline` + history) | ✅ Done | Implemented PassportTimeline; built full /passport/[id] page layout; added mock data and getPassport API client. | c/web/p2-c2 |
| P2-C3 | C | Matching + marketplace UI (`MatchCard`, `ProductCard`) | ✅ Done | Implemented Avatar, MatchCard, ProductCard. Added /matches and /marketplace pages with mocks. | c/web/p2-c3 |

**Checkpoint CP2:** ✅ Verified — _full 10-event saga runs; each step visible in UI._

---

## Phase 3 — Dashboard, Polish & Demo

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|

| P3-A1 | A | Demo-narrative seed + Gateway read-model + demo wiring | ✅ Done | scripts/seed.py: full demo narrative with 8 returns (all lifecycle actions), pre-seeded grades/decisions/passports/matches/listings/sustainability; Gateway dashboard endpoints: GET /dashboard/sustainability/metrics + GET /dashboard/sustainability/records; ServiceClient methods for sustainability aggregation; 9 tests for dashboard routes | a/seed-dashboard/p3-a1 |
| P3-A2 | A | E2E smoke + failure-path test + finalize `.env.example` | ✅ Done | scripts/smoke_test.py: comprehensive E2E validation with 6 phases (health checks, auth, return submission, saga completion, dashboard, failure-path testing); failure-path tests inject malformed events → verify DLQ landing + FAILED status handling; .env.example: comprehensive documentation with section headers, inline explanations, production hardening checklist; docs/hardening-checklist.md: 10-section production readiness validation; scripts/README.md: updated with smoke_test.py documentation; all tests pass with --verbose flag | a/e2e-hardening/p3-a2 |
| P3-B1 | B | Sustainability metrics finalize + dashboard endpoints | ✅ Done | Reshaped `GET /sustainability/metrics` to the binding contract `{ totals: {co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits, returns_processed}, breakdown: [{action, count, co2_avoided_kg, waste_diverted_kg, value_recovered}] }` — matches frontend `SustainabilityMetricsResponse` (api.ts) and SERVICE_ENDPOINTS.md; added `lifecycle_action` column (migration 002) so breakdown groups by action; green-credit accrual via calculator; metrics aggregation + per-action grouping; updated tests (+ breakdown grouping test). Gateway `/sustainability/dashboard` wrapper (recent_returns, top_categories) remains A's P3-A1. | b/sustainability/p3-b1 |
| P3-B2 | B | Golden-path demo product + AI fallback test | 📋 Not started | — | — |
| P3-C1 | C | Sustainability Dashboard (StatCards + ChartCards) | ✅ Done | /sustainability page with TanStack Query hook, Zod MetricsSchema, StatCardRow (4 tiles reusing StatCard), ChartCard (Recharts BarChart with chart-1..6 tokens), API client getSustainabilityMetrics + mock fixture, full loading/empty/error/success states; ChartCard registered in ui-registry.md; tsc clean | c/web/p3-c1 |
| P3-C2 | C | Polish + states + a11y pass | ✅ Done | NavBar Marketplace link + avatar aria-label; /matches + /marketplace migrated to TanStack Query hooks (useMatches, useMarketplaceListings) with refetch-based retry; EmptyState on /returns/[id] ungraded + /passport/[id] no-content; aria-describedby/aria-invalid on login + register inputs; heading hierarchy fixed (CardTitle h2); ProductCard alt prop; selectAsyncState pure helper; Vitest + RTL + jest-axe + fast-check test framework installed; lint/tsc/build clean | c/web/p3-c2 |
| P3-C3 | C | Vercel deploy + final polish | 📋 Not started | — | — |

**Checkpoint CP3 (Demo-ready):** ⬜ Not verified — _judge happy path rehearsed; Vercel live; fallback verified._

---

## Event Saga Status (end-to-end health)

Track each event hop as it becomes live (producer → consumer wired and exercised).

| # | Event | Producer | Consumer(s) | Status |
|---|-------|----------|-------------|--------|
| 1 | `ReturnSubmitted` | gateway | grading | ✅ |
| 2 | `ProductGraded` | grading | lifecycle, passport | ✅ |
| 3 | `LifecycleDecisionCreated` | lifecycle | passport, matching | ✅ |
| 4 | `PassportCreated` | passport | matching | ✅ |
| 5 | `HyperlocalMatchRequested` | passport | matching | ✅ |
| 6 | `MatchFound` | matching | sustainability, passport | ✅ |
| 7 | `NoMatchFound` | matching | sustainability | ✅ |
| 8 | `ProductListed` | matching | sustainability | ✅ |
| 9 | `PurchaseCompleted` | gateway/matching | sustainability, passport | ✅ |
| 10 | `SustainabilityUpdated` | sustainability | gateway (read-model) | ✅ |

---

## Service Readiness

| Service | Owner | Scaffold | DB/Migrations | Endpoints | Events | Tests | Status |
|---------|-------|----------|---------------|-----------|--------|-------|--------|
| gateway | A | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| user | A | ✅ | ✅ | ✅ | n/a | ✅ | ✅ |
| grading | B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| lifecycle | B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| passport | A | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| matching | B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| sustainability | B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| web | C | ✅ | n/a | ✅ | n/a | 📋 | 🚧 |

---

## Blockers & Decisions Log

> Record anything blocking a task and any decision that changes a contract or assumption
> (also update the source doc). Newest first.

| Date | Raised by | Item | Type | Status |
|------|-----------|------|------|--------|
| 2026-06-14 | B | Saga stalled mid-chain: all 5 event-consuming services imported `_session_factory` by value at module load (always `None`) → `db_not_initialized` → DLQ. Fixed to `import app.db.session as db_module` + access at call time (grading, lifecycle, passport, matching, sustainability). Documented in code-standards §2.4a #4. **CP2 verified after fix.** | Decision | ✅ Resolved |
| 2026-06-14 | B | Service-wiring gotchas hit on `docker compose up` (sustainability + matching): (1) Alembic must use Docker host `postgres` + read `DATABASE_URL`, not `localhost`; (2) only one Alembic head per service (dupe `001`/`0001` → "multiple heads"); (3) `add_ready_check(name, fn=...)` must return `"ok"`/raise, not bool. Documented in code-standards §2.4a. | Decision | ✅ Resolved |
| _—_ | _—_ | _No other blockers._ | — | — |

---

## Notes for the next agent

- Pick the **lowest-numbered Not-started task for your member** whose dependencies are `✅ Done`.
- If your task depends on another member's unfinished work, build against the **contract/mock**
 and mark the dependency in Notes.
- Always update this file **and** [ui-registry.md](ui-registry.md) (if you built a component)
 before marking a task done.