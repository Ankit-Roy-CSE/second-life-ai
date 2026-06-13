# Memory — Amazon Second Life AI — Phase 1 Complete (Member B)

Last updated: 2026-06-14

## What was built

### This session (Member B — AI & Backend)

**P0-B1 — AI Wrapper + Mock Mode (built + reviewed + fixed)**
- `packages/shared-py/shared_py/ai/` — full wrapper with 5 async methods: `analyze_media`, `summarize_damage`, `grade_product`, `decide_lifecycle`, `match_rationale`
- Deterministic mock seeded from media-key hash (fallback to `reason:category` when empty)
- Golden-path constants: `GOLDEN_PATH_MEDIA_KEY`, `GOLDEN_PATH_CATEGORY`, `GOLDEN_PATH_REASON`
- `AI_MODE` + `BEDROCK_MODEL_ID` env config; `correlation_id` kwarg on all methods
- Pydantic v2 idiomatic schemas (Annotated types, ConfigDict for protected_namespaces)
- Prompt templates in `ai/prompts/`
- 22 tests in `tests/test_ai.py`

**P0-B2 — Minimal Seed (`scripts/seed_min.py`)**
- 6 users (returner + 4 buyers at varying distances + admin), 4 products, 2 returns
- Deterministic UUIDs via uuid5, idempotent upserts, MinIO placeholders, `--reset` flag

**P0-B3 — Event-Saga Observability**
- `scripts/events_tail.py` — 5 subcommands: tail, dump, trigger, replay, stats
- `services/gateway/app/api/debug_routes.py` — GET /debug/events, /dlq, /stats, POST /trigger

**P1-B1 — AI Grading Service (`services/grading/`)**
- Full service: domain/models.py, domain/service.py (idempotent), domain/schemas.py, db/session.py, api/routes.py (with `?return_id=&product_id=` filters), events/handlers.py (`@subscribe("ReturnSubmitted")` → emit `ProductGraded`), main.py (lifespan), Alembic migration, 10 tests
- Dockerfile runs `alembic upgrade head` before uvicorn

**P1-B2 — Lifecycle Decision Service (`services/lifecycle/`)**
- Same pattern as grading: domain layer, db, routes (with `?return_id=&grade_id=` filters), event handler (`@subscribe("ProductGraded")` → emit `LifecycleDecisionCreated`), Alembic, 9 tests
- Dockerfile fixed: runs `alembic upgrade head && uvicorn ...`

### Other changes
- `context/problems.md` — rewritten with microservice → problem mapping (✅/🟡/⛔)
- `docs/ui-tokens.md` — completely reworked to Amazon ecosystem (gold primary, navy header, cream bg, 4px radius)
- `docs/build-plan.md` — rebalanced A→B (P0-A6/A7 → P0-B2/B3); switched pnpm→npm everywhere
- All 7 service `pyproject.toml` — added `[tool.hatch.build.targets.wheel] packages = ["app"]`
- `packages/shared-py/shared_py/schemas/rest_contracts.py` — fixed Pydantic v2 class Config deprecation
- `README.md` — added Local Testing section; all pnpm→npm
- `docs/progress-tracker.md` — fixed summary count inconsistencies (now 15 Done / 19 Not started)

## Decisions made

1. Sustainability service = pure deterministic math (no LLM). Formulas for CO₂/waste/value/credits.
2. AI wrapper exposes spec-named functions (`analyze_media`, `summarize_damage`, `decide_lifecycle`, `match_rationale`) plus `grade_product` convenience.
3. Golden-path demo = Zebronics headphones, `GOLDEN_PATH_MEDIA_KEY = "products/golden-path/demo-headphones-001.jpg"`.
4. UI tokens = Amazon ecosystem (gold #FF9900 primary, navy #232F3E, cream #FEF7ED bg, 4px base radius).
5. npm over pnpm for frontend.
6. Hatchling needs `[tool.hatch.build.targets.wheel] packages = ["app"]` in every service pyproject.toml.
7. All services run `alembic upgrade head` in Dockerfile CMD before starting uvicorn.
8. List endpoints match SERVICE_ENDPOINTS.md contract filters (grading: `?return_id=&product_id=`, lifecycle: `?return_id=&grade_id=`).

## Problems solved

1. ImportError running pytest — fix: `pip install -e "packages/shared-py[dev]"` + conftest.py sys.path fallback.
2. Pydantic `model_version` namespace warning — fix: `ConfigDict(protected_namespaces=())` on GradeResult and GradeResponse.
3. Pydantic class-based Config deprecation — fix: `model_config = ConfigDict(populate_by_name=True)` in rest_contracts.py.
4. Docker compose build fails — fix: `[tool.hatch.build.targets.wheel] packages = ["app"]` in all service pyproject.toml.
5. Empty media_keys same hash — fix: `_media_seed()` fallback hashes `reason:category`.
6. Lifecycle Dockerfile missing `alembic upgrade head` — saga stalls at step 3. Fixed.
7. Progress tracker summary counts were stale — fixed to match actual task rows (15/34 done).

## Current state

**Phase 0: 11/11 ✅** (all members complete, CP0 verified)
**Phase 1: 4/7 ✅** (A: 2/2 done, B: 2/2 done, C: 0/3 not started)

Event saga: steps 1–3 wired and producing (`ReturnSubmitted` → `ProductGraded` → `LifecycleDecisionCreated`)

CP1 NOT YET VERIFIED — requires C's Auth UI + Return submission UI (P1-C1/C2). Backend side of CP1 is complete.

**Member B's Phase 2 tasks (next):**
- P2-B1 (Matching Service) — depends on P2-A1 (Passport, not started)
- P2-B2 (Sustainability Service) — depends on P2-B1
- P2-B3 (Real AI path) — depends on P1-B1 ✅ + P1-B2 ✅ (ready!)
- P2-B4 (Score tuning) — depends on P1-B2 ✅ + P2-B2

## Next session starts with

**Option A (unblocked now):** Build **P2-B3 — Real AI path** (`AI_MODE=aws/hybrid`). Dependencies satisfied. Tune prompts in `ai/prompts/`, implement real Bedrock + Rekognition calls in `client.py`, verify graceful fallback.

**Option B (if A ships P2-A1 first):** Build **P2-B1 — Hyperlocal Matching Service**. Consumes `HyperlocalMatchRequested`, fetches buyer candidates from User service, scores via Haversine + Bedrock rationale, emits `MatchFound`/`NoMatchFound`/`ProductListed`.

Check progress-tracker.md at session start to see if P2-A1 landed.

## Open questions

1. Review issue #1 (hardcoded `product_category="electronics"` and `value_estimate=100.0` in lifecycle handler) — acknowledged as P2-B3/B4 scope, but the demo will show flattened decision variety until fixed.
2. CP1 verification blocked on Member C's frontend tasks (P1-C1/C2/C3). Backend end-to-end can be tested via `events_tail.py trigger` + checking `/grades/{return_id}` + `/decisions/{return_id}`.
