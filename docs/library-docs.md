# Library Docs — Amazon Second Life AI

>**Project-specific usage rules for every third-party library** (outside the language
> standard library). Before using a library, read its entry here. Before adding a **new**
> library, add an entry here first and get team agreement. Pinned versions below are the
> contract — match them in `pyproject.toml` / `package.json`.

---

## How to read this file

Each entry has: **Purpose · Version · Where used · Usage rules · Gotchas**. The
**Usage rules** are mandatory project conventions, not general advice. Anything marked
🚫 is forbidden in this codebase.

---

## Part A — Backend (Python 3.12)

### Pinned versions (backend)

| Library | Version | Library | Version |
|---------|---------|---------|---------|
| fastapi | `0.115.*` | redis | `5.0.*` |
| uvicorn[standard] | `0.30.*` | boto3 | `1.35.*` |
| pydantic | `2.9.*` | httpx | `0.27.*` |
| pydantic-settings | `2.5.*` | python-jose[cryptography] | `3.3.*` |
| sqlalchemy | `2.0.*` | passlib[bcrypt] | `1.7.*` |
| asyncpg | `0.29.*` | pytest | `8.3.*` |
| alembic | `1.13.*` | pytest-asyncio | `0.24.*` |
| ruff | `0.6.*` | black | `24.*` |

> Python is **3.12**. Use `uv` or `pip` + `pyproject.toml`. All services share the same pins
> via `packages/shared-py`.

---

### FastAPI — `0.115.*`

-**Purpose:** HTTP API framework for every backend service.
-**Where:** all `services/*`.
-**Usage rules:**
- Build apps with the shared factory `create_app()` (`packages/shared-py/web`). 🚫 Do not
 create a bare `FastAPI()` per service — you'd lose health, CORS, error handlers, logging.
- Routers are thin (`app/api/routes.py`); business logic lives in `domain/service.py`.
- Every route: explicit `response_model` + `status_code`. Group with
 `APIRouter(prefix, tags)`.
- Dependencies via `Depends`; shared deps in `app/api/deps.py`.
- Use `lifespan` (not deprecated `@app.on_event`) for startup/shutdown (DB engine, Redis,
 event consumers).
-**Gotchas:** Don't do blocking I/O in `async def` handlers. Validation errors auto-return
 422 — keep that for input validation; use 400 for business validation.

### Uvicorn — `0.30.*`

-**Purpose:** ASGI server.
-**Usage rules:** Run via Docker `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0",
 "--port", "<service-port>"]`. Use `--reload` only in local dev. One worker per container in
 dev; the platform scales by replicas, not workers.

### Pydantic v2 — `2.9.*`

-**Purpose:** Request/response DTOs, validation, settings.
-**Usage rules:**
- v2 syntax only: `model_config = ConfigDict(...)`, `field_validator`, `model_validator`.
- Read models that come from ORM rows use `ConfigDict(from_attributes=True)`.
- Distinct `Create`/`Read`/`Update` models; never expose ORM objects directly.
- Reuse enums from `packages/shared-py/schemas`.
-**Gotchas:** 🚫 No Pydantic v1 patterns (`class Config`, `.dict()`, `orm_mode`). Use
 `.model_dump()` / `.model_validate()`.

### pydantic-settings — `2.5.*`

-**Purpose:** Typed env-var config.
-**Usage rules:** Each service has `Settings(BaseSettings)` in `app/config.py` with
 `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`. Defaults point at
 local Docker hosts. 🚫 No `os.getenv()` scattered in code — centralize in `Settings`.

### SQLAlchemy 2.0 — `2.0.*` (async)

-**Purpose:** ORM + data access.
-**Where:** every service except `gateway`.
-**Usage rules:**
- Async only: `create_async_engine("postgresql+asyncpg://...")` + `async_sessionmaker`.
- 2.0 typed models: `Mapped[...]`, `mapped_column(...)`. PK `id: Mapped[str]` (UUID v4 string).
- One session per request via dependency; commit/rollback handled in the dependency/context.
- Data access in `db/repository.py`; 🚫 no raw SQL strings in routers/services (use Core/ORM).
- 🚫 No foreign keys across service boundaries — store the other entity's id only.
-**Gotchas:** Remember `await session.execute(select(...))` then `.scalars()`. Don't share a
 session across requests/tasks.

### asyncpg — `0.29.*`

-**Purpose:** Async Postgres driver for SQLAlchemy.
-**Usage rules:** Only as the SQLAlchemy async dialect (`postgresql+asyncpg`). Not used
 directly. Ensure the URL uses the `+asyncpg` suffix everywhere.

### Alembic — `1.13.*`

-**Purpose:** DB migrations, per service.
-**Usage rules:** Each service owns `alembic/`. Autogenerate (`alembic revision
 --autogenerate -m "..."`) then **review** the diff. Run `alembic upgrade head` on container
 start in dev. 🚫 Never edit a committed migration — add a new one. Keep migrations additive
 and reversible where feasible.

### redis (redis-py) — `5.0.*`

-**Purpose:** Event bus (Redis **Streams** + consumer groups).
-**Where:** all event producers/consumers, via the shared `events` wrapper.
-**Usage rules:** 🚫 Do not call redis-py directly from a service. Use
 `packages/shared-py/events`:
- `await publish(event_type, correlation_id, data)` builds the envelope + `XADD`.
- `@subscribe(group="<service>")` consumes via `XREADGROUP`, acks on success.
- Handlers must be idempotent (dedupe on `event_id`).
- Use the async client (`redis.asyncio`).
-**Gotchas:** Ack (`XACK`) only after successful processing so failures are redelivered.
 Create the consumer group with `MKSTREAM` on startup.

### boto3 — `1.35.*` (Bedrock + Rekognition)

-**Purpose:** AWS AI calls.
-**Where:****only** inside `packages/shared-py/ai`. 🚫 Never import boto3 in a service
 router/domain.
-**Usage rules:**
- The `ai` wrapper (`from shared_py.ai import ai_client`) exposes typed async methods:
 `analyze_media(...) -> MediaLabels`, `summarize_damage(...) -> DamageSummary`,
 `decide_lifecycle(...) -> LifecycleDecision`, `match_rationale(...) -> MatchRationale`,
 plus convenience `grade_product(...) -> GradeResult` (combines analyze + summarize).
- All methods accept an optional `correlation_id: str` kwarg for structured logging.
- Golden-path demo constants: `GOLDEN_PATH_MEDIA_KEY`, `GOLDEN_PATH_CATEGORY`, `GOLDEN_PATH_REASON`.
- Mode via `AI_MODE` env: `mock` (default), `aws`, `hybrid`. Mock is deterministic and
 network-free. `BEDROCK_MODEL_ID` env configures which model to invoke.
- Bedrock: use `bedrock-runtime` `invoke_model`; prompts live in `ai/prompts/*` and are
 versioned. Rekognition: `detect_labels` / `detect_moderation_labels` (+ sampled frames for
 video).
- Wrapper **degrades gracefully**: on AWS error/timeout, log a WARNING and fall back to mock
 so demos never hard-fail.
- Read region/model id/credentials from settings (`AWS_REGION`, `BEDROCK_MODEL_ID`, etc.).
 🚫 Never hardcode credentials.
-**Gotchas:** Bedrock model availability is region-specific. Keep timeouts short (e.g. 8–12s)
 and always have the mock fallback.

### httpx — `0.27.*`

-**Purpose:** Async HTTP for server-to-server REST (Gateway → services, service → service).
-**Usage rules:** Use a shared `httpx.AsyncClient` (created in lifespan, reused). Set
 timeouts. Propagate `X-Correlation-Id` and forward `X-User-Id`. 🚫 No `requests` (sync).

### python-jose[cryptography] — `3.3.*`

-**Purpose:** JWT encode/verify.
-**Where:** `user` (issue), `gateway` (verify), shared helper in `packages/shared-py/web/auth`.
-**Usage rules:** HS256 with `JWT_SECRET` from settings. Standard claims `sub` (user id),
 `exp`, `iat`. Short-lived access tokens (e.g. 24h for the hackathon). Verify in the Gateway;
 forward `X-User-Id` to internal services.
-**Gotchas:** Always validate `exp`. Keep `JWT_SECRET` identical across `user` and `gateway`.

### passlib[bcrypt] — `1.7.*`

-**Purpose:** Password hashing (User Service).
-**Usage rules:** `CryptContext(schemes=["bcrypt"])`; hash on register, verify on login. 🚫
 Never store or log plaintext passwords.

### pytest / pytest-asyncio — `8.3.*` / `0.24.*`

-**Purpose:** Tests.
-**Usage rules:** `pytest-asyncio` in `auto` mode for async tests. Route tests use
 `httpx.AsyncClient(transport=ASGITransport(app=app))`. Force `AI_MODE=mock`; 🚫 no real AWS
 in tests. Use a disposable test DB or transactional rollback.

### ruff / black — `0.6.*` / `24.*`

-**Purpose:** Lint + format. Config in root `pyproject.toml` (line length 100).
-**Usage rules:** `ruff check .` and `black --check .` must pass pre-commit. ruff handles
 import sorting (isort rules). 🚫 Don't disable rules inline without a `# noqa: <code> —
 reason` justification.

---

## Part B — Frontend (Node 20, Next.js)

### Pinned versions (frontend)

| Library | Version | Library | Version |
|---------|---------|---------|---------|
| next | `14.2.*` | @tanstack/react-query | `5.*` |
| react / react-dom | `18.3.*` | zod | `3.23.*` |
| typescript | `5.5.*` | react-hook-form | `7.52.*` |
| tailwindcss | `3.4.*` | @hookform/resolvers | `3.9.*` |
| class-variance-authority | `0.7.*` | lucide-react | `0.4xx` |
| clsx | `2.1.*` | recharts | `2.12.*` |
| tailwind-merge | `2.5.*` | axios | `1.7.*` |

> Package manager: **npm**. Node **20 LTS**. shadcn/ui components are generated into
> `components/ui` (not a versioned dependency).

---

### Next.js — `14.2.*` (App Router)

-**Purpose:** React framework + routing for `apps/web`. Deploys to Vercel.
-**Usage rules:**
-**App Router only** (`app/`). 🚫 No `pages/` router.
- Server Components by default; `"use client"` only when needed (state/effects/handlers).
- Fonts via `next/font/google` (Inter). 🚫 No font `<link>` tags.
- Images via `next/image` where helpful. Env: only `NEXT_PUBLIC_*` is exposed to the
 browser — the API base URL is `NEXT_PUBLIC_API_BASE_URL`.
- Frontend talks to the **Gateway only**; 🚫 never call individual services.
-**Gotchas:** Don't import server-only code into client components. Keep secrets server-side
 (no secret in `NEXT_PUBLIC_*`).

### React — `18.3.*`

-**Usage rules:** Function components + hooks only. Follow the rules of hooks. Prefer derived
 state over duplicated state. 🚫 No class components.

### TypeScript — `5.5.*`

-**Usage rules:** `strict: true`. 🚫 No `any`. Type props with `type`. Infer API types from
 Zod. See [code-standards.md](code-standards.md) §3.3.

### Tailwind CSS — `3.4.*`

-**Purpose:** All styling.
-**Usage rules:****Tokens only** — classes map to tokens defined in
 [ui-tokens.md](ui-tokens.md) via `tailwind.config.ts`. 🚫 No arbitrary values with raw
 hex/px (`bg-[#22A06B]`, `p-[7px]`) except documented one-offs. Compose with `cn()`. Follow
 [ui-rules.md](ui-rules.md).
-**Gotchas:** Ensure `content` globs include `app/**`, `components/**`. Don't fight the
 preflight; use tokens.

### shadcn/ui (Radix primitives) — generated

-**Purpose:** Accessible primitive components (Button, Dialog, Select, Tabs, Toast, etc.).
-**Usage rules:** Generate into `components/ui` and adapt to our tokens. Treat them as the
 base layer of the [ui-registry.md](ui-registry.md). 🚫 Don't pull in a second component
 library (MUI/Chakra/AntD). Match existing variants (CVA) before adding new ones.
-**Gotchas:** Keep Radix `asChild`/ref forwarding intact for accessibility.

### class-variance-authority (CVA) — `0.7.*`

-**Purpose:** Type-safe component variants (button sizes/variants, badges).
-**Usage rules:** Define variants with `cva()`; expose via `VariantProps`. Variant values map
 to tokens. Reuse the registry's variant names; don't invent parallel systems.

### clsx + tailwind-merge — `2.1.*` / `2.5.*`

-**Purpose:** The `cn()` helper in `lib/utils.ts` (`twMerge(clsx(...))`).
-**Usage rules:** Always compose conditional classes with `cn()` so conflicting Tailwind
 classes resolve correctly. 🚫 No manual string concatenation of classes.

### TanStack Query — `5.*`

-**Purpose:** Server-state: fetching, caching, mutations.
-**Usage rules:** One `QueryClientProvider` at the root. Hooks per resource in `lib/hooks`
 (`useReturns`, `useGrade`, `usePassport`, `useMatches`, `useSustainability`). Stable keys
 `["resource", id]`. Surface `isLoading`/`isError`/empty in UI (required by ui-rules).
 Invalidate related keys after mutations.
-**Gotchas:** v5 renamed `cacheTime` → `gcTime`, `isLoading` semantics; use v5 API. Don't
 fetch in `useEffect` when a query hook fits.

### Zod — `3.23.*`

-**Purpose:** Runtime validation of API responses + form schemas; source of inferred TS types.
-**Usage rules:** Define response schemas in `lib/api`; `z.infer` for types. Reuse for RHF via
 `zodResolver`. Validate at the network boundary. Keep enums in sync with backend
 ([code-standards.md](code-standards.md) §4.1).

### React Hook Form + @hookform/resolvers — `7.52.*` / `3.9.*`

-**Purpose:** Forms (return submission, login/register, filters).
-**Usage rules:** `useForm({ resolver: zodResolver(schema) })`. Inline field errors, disable
 submit while pending, server errors via toast. 🚫 No uncontrolled ad-hoc form state.

### lucide-react — `0.4xx`

-**Purpose:** Icon set.
-**Usage rules:** Import per-icon (`import { Leaf } from "lucide-react"`). Size via Tailwind
 (`h-4 w-4`), color via `text-*` tokens. Meaningful icons get `aria-label`; decorative get
 `aria-hidden`. 🚫 Don't mix in another icon library.

### Recharts — `2.12.*`

-**Purpose:** Sustainability dashboard charts (CO₂, waste, value, credits).
-**Usage rules:** Wrap in `ResponsiveContainer`. Colors from the chart token sequence
 (`chart-1..6`) in [ui-tokens.md](ui-tokens.md) — 🚫 no hardcoded chart hex. Provide
 accessible labels/legends. Use a shared `ChartCard` registry component.
-**Gotchas:** Recharts is client-only — mark chart components `"use client"`.

### axios — `1.7.*` (or native fetch)

-**Purpose:** HTTP client inside the typed API layer (`lib/api`).
-**Usage rules:** One configured instance (baseURL = `NEXT_PUBLIC_API_BASE_URL`, JWT
 interceptor, error→envelope mapping). Components call hooks, not axios directly. Native
 `fetch` is acceptable if you prefer — pick one and keep it consistent in `lib/api`.

---

## Part C — Infrastructure & Tooling

### Docker / Docker Compose

-**Purpose:** Local stack: Postgres 16, Redis 7, MinIO, all 7 services.
-**Usage rules:** Root `docker-compose.yml` is the canonical dev environment. Services read
 config from env (compose injects). One `Dockerfile` per service (slim Python base). Healthchecks
 on Postgres/Redis/MinIO before services start (`depends_on: condition: service_healthy`).
-**Gotchas:** Use service names as hostnames (`postgres`, `redis`, `minio`) inside the compose
 network, not `localhost`.

### PostgreSQL 16

-**Usage rules:** Single container, **one database per service** (`slmai_user`,
 `slmai_grading`, …). An init script creates all DBs. 🚫 No cross-database queries. Each
 service connects only to its own DB.

### Redis 7

-**Usage rules:** Event bus via Streams (see redis entry). Optionally short-lived caches.
 Accessed only through the shared `events` wrapper for messaging.

### MinIO (S3-compatible)

-**Purpose:** Store uploaded product images/videos.
-**Usage rules:** Access via `boto3` S3 client **inside a shared storage helper** (not in
 routers), endpoint from settings (`S3_ENDPOINT_URL`). Bucket e.g. `slmai-media`. Store object
 keys (not bytes) in the DB. Generate presigned URLs for the frontend to display media.
-**Gotchas:** Set `endpoint_url` + path-style addressing for MinIO. Same code points at real
 S3 by swapping env.

### npm

-**Usage rules:** Frontend package manager. Commit `package-lock.json`. 🚫 Don't mix pnpm/yarn
 lockfiles.

---

## Part D — Adding a New Library (checklist)

Before introducing any dependency not listed above:

1. Confirm nothing already listed covers the need.
2. Add an entry here (purpose, version pin, usage rules, gotchas).
3. Pin the version in `pyproject.toml` / `package.json`.
4. Note it in the PR description; get a teammate ack.
5. Prefer well-maintained, widely-used libraries; avoid heavy deps for trivial needs.