# Code Standards — Amazon Second Life AI

>**Implementation rules for the whole monorepo.** These are non-negotiable conventions so
> three people (and their agents) produce code that fits together. When in doubt, match the
> patterns here and in existing code. Read alongside [architecture.md](architecture.md) and
> [library-docs.md](library-docs.md).

---

## 0. Golden Rules (read first)

1.**Contract-first.** Define/adjust the OpenAPI route shape and event payload **before**
 implementing. Other members code against the contract.
2.**Services own their data.** Never query another service's DB. Cross-service = REST or events.
3.**AI only through the shared wrapper.** Never `import boto3` in a service router/domain.
4.**Tokens only in UI.** No hardcoded hex/px — see [ui-tokens.md](ui-tokens.md) / [ui-rules.md](ui-rules.md).
5.**Update the trackers.** After each feature: update [progress-tracker.md](progress-tracker.md);
 after each component: update [ui-registry.md](ui-registry.md).
6.**Small PRs, green checks.** Lint + type-check + tests pass before merge. No direct pushes to `main`.

---

## 1. Repository & Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Repo folders | `kebab-case` | `services/ai-grading` → use `services/grading` |
| Python package/module | `snake_case` | `domain/service.py` |
| Python class | `PascalCase` | `class GradingService` |
| Python function/var | `snake_case` | `def grade_product()` |
| Python constant | `UPPER_SNAKE` | `MAX_MEDIA = 8` |
| SQL table | `snake_case`, plural | `lifecycle_decisions` |
| SQL column | `snake_case` | `value_recovery_estimate` |
| Env var | `UPPER_SNAKE` | `JWT_SECRET`, `AI_MODE` |
| TS variable/function | `camelCase` | `useGradeQuery` |
| TS type/interface/component | `PascalCase` | `type GradeResult`, `function GradeBadge()` |
| React component file | `PascalCase.tsx` | `GradeBadge.tsx` |
| TS hook file | `camelCase.ts` starting `use` | `useReturns.ts` |
| Route segment | `kebab-case` | `app/sustainability/page.tsx` |
| Event type | `PascalCase` | `ProductGraded` |
| REST path | `kebab-case`, plural nouns | `GET /lifecycle-decisions/{id}` |

Service folder names are fixed: `gateway, user, grading, lifecycle, passport, matching, sustainability`.

---

## 2. Backend Standards (FastAPI / Python 3.12)

### 2.1 Layered structure (per service)

```
app/
 main.py # create_app() — wires router, events, lifespan
 config.py # Settings(BaseSettings)
 api/routes.py # APIRouter — HTTP only, no business logic
 domain/
 schemas.py # Pydantic v2 DTOs (request/response)
 models.py # SQLAlchemy ORM models
 service.py # business logic — pure, no FastAPI imports
 db/
 session.py # async engine + session factory
 repository.py # data access (CRUD), returns ORM/domain objects
 events/handlers.py # event consumers (idempotent)
 clients/ # outbound: other services, shared ai/events
```

**Dependency direction:** `api → domain.service → db.repository → models`. Routers depend on
services via FastAPI `Depends`. `domain/service.py` must not import `fastapi`.

### 2.2 FastAPI rules

- Use an **app factory** `create_app()` built on the shared base (`packages/shared-py/web`).
 Do not instantiate `FastAPI()` ad hoc; the base wires health, error handlers, logging, CORS.
-**All I/O is async.** Async DB sessions (asyncpg), async Redis, `httpx.AsyncClient`. No
 blocking calls in request handlers; wrap unavoidable sync work in `run_in_threadpool`.
- Routers are thin: validate input (Pydantic), call a `service`, map result to a response
 model. No SQL or AI calls in routers.
- Every route declares `response_model` and an explicit `status_code`.
- Use `APIRouter(prefix=..., tags=[...])`. Group by resource.
- Inject dependencies (DB session, current user, services) via `Depends`. Define shared deps
 in `app/api/deps.py` when more than one route needs them.

### 2.3 Pydantic v2

- Separate models: `XxxCreate` (input), `XxxRead` (output), `XxxUpdate` (partial). Never
 expose ORM models directly.
- `model_config = ConfigDict(from_attributes=True)` for read models built from ORM objects.
- Use `Field(...)` for constraints + `description` (feeds OpenAPI). Enums from
 `packages/shared-py/schemas`.
- Validate at the boundary only; trust validated data internally.

### 2.4 SQLAlchemy 2.0 + Alembic

- Declarative models with `Mapped[...]` / `mapped_column(...)` typing.
- Async engine (`create_async_engine`) + `async_sessionmaker`; one session per request via
 dependency; always `await session.commit()` / rollback on error (handled by a context dep).
- Primary keys: `id: Mapped[str]` UUID v4 (string). Timestamps: `created_at`, `updated_at`
 with server defaults.
-**Every schema change ships an Alembic migration.** Never edit a committed migration; add a
 new one. Autogenerate then review.
- No cross-service foreign keys. Reference other services' entities by **id only**.

### 2.5 Configuration & secrets

- All config via `pydantic-settings` `Settings(BaseSettings)` reading env vars; provide
 defaults that point at local Docker services.
- The contract is `.env.example` (committed). Real `.env` is git-ignored. **Never commit
 secrets.** Never hardcode URLs, ports, or keys — read from settings.
- Required env vars per service are documented in the service `README.md` and `.env.example`.

### 2.6 Events

- Publish/consume only via `packages/shared-py/events`. Build the envelope through the helper.
- Consumers must be **idempotent**: dedupe on `event_id`; processing the same event twice has
 no extra effect (use an upsert or a processed-events guard).
- Always propagate `correlation_id`. Never block the HTTP request on downstream event
 processing — publish and return.
- On repeated handler failure the wrapper **retries, then dead-letters** to `slmai:events:dlq`;
 the owning service sets the affected `Return.status = FAILED` so the saga halts cleanly
 instead of silently stalling. Do not swallow exceptions to fake success.

### 2.7 Errors & status codes

- Raise `HTTPException` (or shared `AppError`) with a stable `code`. The shared error handler
 renders `{ "error": { "code", "message", "correlation_id" } }`.
- Status map: `200` ok · `201` created · `204` no content · `400` validation/bad input ·
 `401` unauthenticated · `403` forbidden · `404` not found · `409` conflict/duplicate ·
 `422` Pydantic validation (FastAPI default) · `502/503` upstream/AI failure.
- AI/upstream failures degrade gracefully (mock fallback) instead of 500 where possible.

### 2.8 Logging

- Use the shared structured logger (JSON). Always include `service` and `correlation_id`.
- `INFO` for lifecycle/business events, `WARNING` for degraded paths (AI fallback), `ERROR`
 for failures with stack context. **Never log secrets, tokens, or full media bytes.**

### 2.9 Formatting, linting, typing

-**black** (line length 100) + **ruff** (lint + import sort). Config in root `pyproject.toml`.
- Type hints on every function signature. Run `ruff check` + `black --check` before commit.
- No unused imports/vars; no `print()` (use logger); no bare `except:`.

### 2.10 Testing (pytest)

- `tests/` per service. Use `pytest` + `pytest-asyncio` + `httpx.ASGITransport` for route tests.
- Minimum per feature: 1 happy-path route test + 1 domain-logic unit test. Mock AI via
 `AI_MODE=mock`; do not call AWS in tests.
- Name tests `test_<thing>_<condition>_<expected>()`.

---

## 3. Frontend Standards (Next.js 14 / TypeScript)

### 3.1 App Router structure

- Routes in `app/<segment>/page.tsx`. Shared chrome in `app/layout.tsx`.
-**Server Components by default.** Add `"use client"` only when you need state, effects,
 event handlers, or browser APIs. Keep client components small and leaf-ward.
- Data mutations and most fetching for interactive views use **TanStack Query** in client
 components via hooks in `lib/hooks`. Server Components may fetch directly for static reads.

### 3.2 Component organization

- `components/ui/` = design-system **primitives** (the [ui-registry.md](ui-registry.md)
 source). Generic, no business logic, fully token-driven.
- `components/features/` = composites that use primitives + domain data (e.g. `GradePanel`,
 `PassportTimeline`).
- One component per file, named export matching the filename. Co-locate component-only types.

### 3.3 TypeScript rules

- `strict` mode on. **No `any`** — use `unknown` + narrowing or precise types. No non-null
 `!` except provably-safe cases with a comment.
- Validate all data crossing the network with **Zod** schemas in `lib/api`; infer TS types
 from Zod (`z.infer`). Backend DTO mirrors live in `types/`.
- Props typed via `type` (not `interface`) for components; use discriminated unions for variants.
- Prefer pure functions and derived state; avoid duplicated source-of-truth state.

### 3.4 Styling

-**Tailwind only**, tokens only (see [ui-rules.md](ui-rules.md)). No inline `style={{}}` for
 themeable values, no raw hex/px, no CSS modules for tokens.
- Compose class names with `cn()` (clsx + tailwind-merge) from `lib/utils.ts`.
- Variants via **CVA** (`class-variance-authority`). Match registry patterns before inventing.

### 3.5 Data fetching & API client

- One typed client in `lib/api` wrapping the Gateway base URL (`NEXT_PUBLIC_API_BASE_URL`).
 Attach JWT from auth store. Centralize error parsing to the shared error envelope.
- TanStack Query: stable query keys `["resource", id]`; co-locate hooks per resource in
 `lib/hooks`. Handle `isLoading` / `isError` / empty in the UI (required — see ui-rules).
- Never call individual backend services directly; always go through the Gateway.

### 3.6 Forms

-**React Hook Form** + **Zod** resolver. Show inline field errors, disable submit while
 pending, surface server errors via toast.

### 3.7 Accessibility & semantics

- Semantic HTML; label every input; keyboard-navigable; visible focus ring (`ring`). Meet
 WCAG AA contrast (tokens are pre-checked). Icons that convey meaning need `aria-label`.

### 3.8 Frontend tooling

-**eslint** (next + ts) + **prettier**. No eslint errors at commit. Optional minimal tests
 with **vitest** + React Testing Library for critical components.

---

## 4. Shared Contracts (the seams between members)

### 4.1 Shared enums & contracts

Single source for both stacks; keep in sync:

- Python: `packages/shared-py/schemas/enums.py` and `events.py`.
- TS: `apps/web/types/enums.ts` and `events.ts`.

| Enum | Values |
|------|--------|
| `Grade` | `A`, `B`, `C`, `D` |
| `LifecycleAction` | `RESELL`, `REFURBISH`, `DONATE`, `RECYCLE`, `HYPERLOCAL` |
| `ReturnStatus` | `SUBMITTED`, `GRADED`, `DECIDED`, `PASSPORTED`, `MATCHING`, `LISTED`, `SOLD`, `FAILED` |
| `ListingChannel` | `HYPERLOCAL`, `MARKETPLACE` |
| `ListingStatus` | `ACTIVE`, `RESERVED`, `SOLD`, `EXPIRED` |

### 4.2 REST contract conventions

- JSON only. Resource paths are plural nouns; use sub-resources for relations
 (`/returns/{id}/grade`). Filtering via query params. Pagination: `?limit=&offset=`,
 response `{ items, total, limit, offset }`.
- Timestamps are ISO-8601 UTC strings. IDs are UUID strings. Money/value as number + a
 `currency` field where relevant; CO₂/weight in SI units with explicit unit in the field name
 (`co2_avoided_kg`).
- The OpenAPI doc each service serves at `/openapi.json` is the binding contract. The Gateway
 aggregates the public surface the frontend consumes.

### 4.3 Event contract conventions

- Envelope per [architecture.md](architecture.md) §6. `event_type` is `PascalCase`. Payload
 field names are `snake_case`. Versioned via `event_version`; additive changes only within a
 version.

---

## 5. Git Workflow

-**Branch naming:** `<member>/<service-or-area>/<short-desc>` → `b/grading/rekognition-client`,
 `c/ui/grade-badge`, `a/gateway/auth-passthrough`.
-**Conventional commits:** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`. Scope
 optional: `feat(grading): add damage summary`.
-**No direct commits to `main`.** Open a PR; at least one teammate (or a green CI + self-review
 for solo-owned areas) before merge. Keep PRs small and focused on one task/feature.
- Rebase or squash-merge to keep history linear. Resolve conflicts locally; never force-push
 shared branches.
- Do not commit: `.env`, secrets, `node_modules`, `__pycache__`, build artifacts, large media.
 `.gitignore` covers these.

---

## 6. Definition of Done (every feature)

A task is **Done** only when all of the following hold:

- [ ] Matches the contract (OpenAPI / event payload / TS types) and architecture boundaries.
- [ ] Lint + format pass (ruff/black or eslint/prettier); type-check passes (mypy-clean hints / `tsc`).
- [ ] At least the minimum tests exist and pass; `AI_MODE=mock` path works with no AWS keys.
- [ ] Runs locally via Docker Compose / `npm run dev` without manual patching.
- [ ] UI work uses only tokens and existing registry components where applicable.
- [ ] Health/`ready` still green; no secrets or stray `print`/`console.log` left behind.
- [ ] [progress-tracker.md](progress-tracker.md) row updated (status, notes, link). New
 components added to [ui-registry.md](ui-registry.md).
- [ ] Demo-relevant happy path verified end-to-end where the feature touches the saga.

---

## 7. Quick Reference — Do / Don't

| ✅ Do | ❌ Don't |
|------|---------|
| Call AI via the shared wrapper | `import boto3` in a service |
| Read other services via REST/events | Query another service's DB |
| Use `Settings` + env vars | Hardcode URLs, ports, secrets |
| Thin routers, logic in `service.py` | Business logic / SQL in routers |
| Tokens + registry components | Raw hex/px, one-off components |
| Idempotent event handlers | Assume exactly-once delivery |
| Small PRs, conventional commits | Push to `main`, giant PRs |
| Update trackers after each unit | Leave the tracker/registry stale |
