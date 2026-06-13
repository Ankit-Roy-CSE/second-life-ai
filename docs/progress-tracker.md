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

**Last updated:** 2026-06-13 · **Updated by:** C · **Latest:** P0-C1, P0-C2, P0-C3 complete — **Phase 0 done for Member A, B and C!**

---

## Overall Progress

| Phase | Total | ✅ Done | 🚧 In progress | ⛔ Blocked | 📋 Not started |
|-------|-------|--------|----------------|-----------|----------------|
| Phase 0 — Foundation | 11 | 8 | 0 | 0 | 3 |
| Phase 1 — Core | 7 | 1 | 0 | 0 | 6 |
| Phase 2 — Integration | 9 | 0 | 0 | 0 | 9 |
| Phase 3 — Dashboard/Polish | 7 | 0 | 0 | 0 | 7 |
| **Total** | **34** | **12** | **0** | **0** | **22** |

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
| P1-A1 | A | User Service (auth/JWT, profile, credits) | 📋 Not started | — | — |
| P1-A2 | A | API Gateway + Returns intake (`ReturnSubmitted`) | 📋 Not started | — | — |
| P1-B1 | B | AI Grading Service (`ProductGraded`) | ✅ Done | Consumes `ReturnSubmitted` → `ai_client.grade_product()` → persist Grade → emit `ProductGraded`; `GET /grades/{return_id}` + `GET /grades`; SQLAlchemy Grade model + Alembic migration (001_create_grades_table); idempotent handler (skips re-grading); lifespan wires DB + event consumer; 10 tests (domain idempotency, all grades storable, route 200/404, list endpoint) | b/grading/p1-b1 |
| P1-B2 | B | Lifecycle Decision Service (`LifecycleDecisionCreated`) | 📋 Not started | — | — |
| P1-C1 | C | Auth UI + API client JWT | 📋 Not started | — | — |
| P1-C2 | C | Return submission + grade view | 📋 Not started | — | — |
| P1-C3 | C | Primitives batch 2 + Empty/Error/PageHeader | 📋 Not started | — | — |

**Checkpoint CP1:** ⬜ Not verified — _register → return → grade → decision (mock) via Gateway._

---

## Phase 2 — Integration & Remaining Services

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P2-A1 | A | Product Passport Service (`PassportCreated`, `HyperlocalMatchRequested`) | 📋 Not started | — | — |
| P2-A2 | A | Gateway aggregation + `PurchaseCompleted` | 📋 Not started | — | — |
| P2-B1 | B | Hyperlocal Matching Service (`MatchFound`/`NoMatchFound`, `ProductListed`) | 📋 Not started | — | — |
| P2-B2 | B | Sustainability Service (`SustainabilityUpdated`, metrics) | 📋 Not started | — | — |
| P2-B3 | B | Real AI path (`AI_MODE=aws/hybrid`) + prompt tuning + fallback | 📋 Not started | — | — |
| P2-B4 | B | Value-recovery + sustainability-score tuning | 📋 Not started | — | — |
| P2-C1 | C | Lifecycle decision UI (`DecisionCard`) | 📋 Not started | — | — |
| P2-C2 | C | Passport UI (`PassportTimeline` + history) | 📋 Not started | — | — |
| P2-C3 | C | Matching + marketplace UI (`MatchCard`, `ProductCard`) | 📋 Not started | — | — |

**Checkpoint CP2:** ⬜ Not verified — _full 10-event saga runs; each step visible in UI._

---

## Phase 3 — Dashboard, Polish & Demo

| Task ID | Owner | Task | Status | Notes | Link |
|---------|-------|------|--------|-------|------|
| P3-A1 | A | Demo-narrative seed + Gateway read-model + demo wiring | 📋 Not started | — | — |
| P3-A2 | A | E2E smoke + failure-path test + finalize `.env.example` | 📋 Not started | — | — |
| P3-B1 | B | Sustainability metrics finalize + dashboard endpoints | 📋 Not started | — | — |
| P3-B2 | B | Golden-path demo product + AI fallback test | 📋 Not started | — | — |
| P3-C1 | C | Sustainability Dashboard (StatCards + ChartCards) | 📋 Not started | — | — |
| P3-C2 | C | Polish + states + a11y pass | 📋 Not started | — | — |
| P3-C3 | C | Vercel deploy + final polish | 📋 Not started | — | — |

**Checkpoint CP3 (Demo-ready):** ⬜ Not verified — _judge happy path rehearsed; Vercel live; fallback verified._

---

## Event Saga Status (end-to-end health)

Track each event hop as it becomes live (producer → consumer wired and exercised).

| # | Event | Producer | Consumer(s) | Status |
|---|-------|----------|-------------|--------|
| 1 | `ReturnSubmitted` | gateway | grading | ✅ |
| 2 | `ProductGraded` | grading | lifecycle, passport | ✅ |
| 3 | `LifecycleDecisionCreated` | lifecycle | passport, matching | 📋 |
| 4 | `PassportCreated` | passport | matching | 📋 |
| 5 | `HyperlocalMatchRequested` | passport | matching | 📋 |
| 6 | `MatchFound` | matching | sustainability, passport | 📋 |
| 7 | `NoMatchFound` | matching | sustainability | 📋 |
| 8 | `ProductListed` | matching | sustainability | 📋 |
| 9 | `PurchaseCompleted` | gateway/matching | sustainability, passport | 📋 |
| 10 | `SustainabilityUpdated` | sustainability | gateway (read-model) | 📋 |

---

## Service Readiness

| Service | Owner | Scaffold | DB/Migrations | Endpoints | Events | Tests | Status |
|---------|-------|----------|---------------|-----------|--------|-------|--------|
| gateway | A | 📋 | n/a | 📋 | 📋 | 📋 | 📋 |
| user | A | 📋 | 📋 | 📋 | n/a | 📋 | 📋 |
| grading | B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| lifecycle | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| passport | A | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| matching | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| sustainability | B | 📋 | 📋 | 📋 | 📋 | 📋 | 📋 |
| web | C | 📋 | n/a | 📋 | n/a | 📋 | 📋 |

---

## Blockers & Decisions Log

> Record anything blocking a task and any decision that changes a contract or assumption
> (also update the source doc). Newest first.

| Date | Raised by | Item | Type | Status |
|------|-----------|------|------|--------|
| _—_ | _—_ | _No blockers yet._ | — | — |

---

## Notes for the next agent

- Pick the **lowest-numbered Not-started task for your member** whose dependencies are `✅ Done`.
- If your task depends on another member's unfinished work, build against the **contract/mock**
 and mark the dependency in Notes.
- Always update this file **and** [ui-registry.md](ui-registry.md) (if you built a component)
 before marking a task done.