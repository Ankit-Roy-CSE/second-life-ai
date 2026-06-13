# Memory — Amazon Second Life AI — Phase 0 Complete (Member B)

Last updated: 2026-06-13

## What was built

### P0-B1 — AI Wrapper + Mock Mode (complete)
- `packages/shared-py/shared_py/ai/schemas.py` — Pydantic v2 response models: GradeResult, LifecycleDecision, MatchRationale, DefectItem, DamageSummary, MediaLabels. Uses `Annotated[float, Field(...)]` (not deprecated `confloat`). GradeResult has `model_config = ConfigDict(protected_namespaces=())` for `model_version` field.
- `packages/shared-py/shared_py/ai/mock.py` — Deterministic mock: seeded from media-key hash via `_media_seed()` (falls back to `reason:category` hash when media_keys is empty). Grade distribution: 35% A, 30% B, 20% C, 15% D.
- `packages/shared-py/shared_py/ai/client.py` — `AIClient` class with 5 public async methods matching spec: `analyze_media`, `summarize_damage`, `grade_product` (convenience combo), `decide_lifecycle`, `match_rationale`. All accept `correlation_id` kwarg for structured logging. Mode switching (mock/aws/hybrid) via `AI_MODE` env. Reads `BEDROCK_MODEL_ID`. Graceful fallback to mock on AWS failure. Golden-path constants: `GOLDEN_PATH_MEDIA_KEY`, `GOLDEN_PATH_CATEGORY`, `GOLDEN_PATH_REASON`.
- `packages/shared-py/shared_py/ai/prompts/` — grading.txt, lifecycle.txt, matching.txt
- `packages/shared-py/shared_py/ai/__init__.py` — Clean public API exporting all schemas + client + constants
- `packages/shared-py/tests/test_ai.py` — 22 tests: determinism, golden-path, spec function separation, grade logic, lifecycle logic, match rationale, mode switching, graceful degradation
- `packages/shared-py/conftest.py` — sys.path fix for running tests without editable install

### P0-B2 — Minimal Seed/Fixtures (complete)
- `scripts/seed_min.py` — 6 users (1 returner, 4 nearby buyers at varying distances in Bengaluru, 1 admin), 4 products (headphones golden-path, laptop, jacket, chair), 2 returns (golden-path + supporting). Deterministic UUIDs via uuid5. Idempotent (ON CONFLICT DO UPDATE). Gracefully skips unmigrated tables. MinIO placeholder uploads. `--reset` flag. Prints full manifest.

### P0-B3 — Event-Saga Observability (complete)
- `scripts/events_tail.py` — CLI tool with 5 subcommands: `tail` (live stream with ANSI colour, --dlq, --correlation-id filter), `dump` (historical), `trigger` (publish synthetic events with --golden-path flag), `replay` (DLQ recovery), `stats` (counts by event_type).
- `services/gateway/app/api/debug_routes.py` — REST endpoints: GET /debug/events, GET /debug/events/dlq, GET /debug/events/stats, POST /debug/events/trigger. Wired into gateway main.py.

### Other changes this session
- `context/problems.md` — Rewrote to map each problem to the solving microservice(s) with ✅/🟡/⛔ status
- `docs/ui-tokens.md` — Completely reworked to Amazon ecosystem aesthetic (gold primary, navy secondary, cream bg, small radii, border-first)
- `docs/build-plan.md` — Rebalanced workload: P0-A6/A7 moved to B as P0-B2/B3 (now A=11, B=11, C=11)
- `packages/shared-py/shared_py/schemas/rest_contracts.py` — Fixed Pydantic v2 deprecation: `class Config` → `model_config = ConfigDict(populate_by_name=True)`
- All 7 service `pyproject.toml` files — Added `[tool.hatch.build.targets.wheel] packages = ["app"]` (fixes Docker compose build failure)
- Switched frontend from pnpm to npm across all docs (README, AGENTS, architecture, build-plan, code-standards, library-docs, .gitignore). Deleted pnpm-lock.yaml.
- `README.md` — Added "Local Testing" section with venv setup + pytest instructions

## Decisions made

1. **Sustainability service is pure deterministic logic** — no LLM. Metrics (CO₂, waste, value, credits) are formula-based calculations, not AI-generated. Optionally can add LLM-generated explanation text later.
2. **AI wrapper exposes spec-named functions** — `analyze_media`, `summarize_damage`, `decide_lifecycle`, `match_rationale` as separate methods + `grade_product` as convenience combo.
3. **Golden-path demo product** — Zebronics headphones with `GOLDEN_PATH_MEDIA_KEY = "products/golden-path/demo-headphones-001.jpg"`. All seed scripts and demo flows reference this constant.
4. **UI tokens aligned to Amazon ecosystem** — Gold (#FF9900) primary, navy (#232F3E) header, cream (#FEF7ED) background, 4px base radius. Not a generic green sustainability theme.
5. **npm over pnpm** — Switched frontend package manager to npm (bundled with Node, no extra install).
6. **Hatchling needs explicit packages** — Every service pyproject.toml requires `[tool.hatch.build.targets.wheel] packages = ["app"]` for Docker editable installs to work.

## Problems solved

1. **ImportError when running pytest** — shared_py not on path. Fix: `pip install -e "packages/shared-py[dev]"` + conftest.py with sys.path insert as fallback.
2. **Pydantic `model_version` namespace warning** — `model_` prefix is protected in Pydantic v2. Fix: `model_config = ConfigDict(protected_namespaces=())`.
3. **Pydantic class-based Config deprecation** — `class Config: populate_by_name = True` in rest_contracts.py. Fix: `model_config = ConfigDict(populate_by_name=True)`.
4. **Docker compose build fails for services** — Hatchling can't discover `app/` package. Fix: add `[tool.hatch.build.targets.wheel] packages = ["app"]` to each service's pyproject.toml.
5. **Empty media_keys produces same grade** — was always hashing "default". Fix: `_media_seed()` falls back to hashing `reason:category`.

## Current state

**Phase 0: 11/11 complete (all members done)**
- A: 5/5 ✅ (scaffold, compose, shared-py web/events/contracts)
- B: 3/3 ✅ (AI wrapper, seed, observability)
- C: 3/3 ✅ (web scaffold, primitives, mock layer)

**CP0 NOT YET VERIFIED** — all tasks are done but the checkpoint hasn't been formally run. Backend should boot (`docker compose up --build`), frontend should render (`npm run dev`). Events round-trip testable via `events_tail.py trigger --golden-path`.

**Phase 1 is fully unblocked for Member B:**
- P1-B1 (AI Grading Service) — depends on P0-A4 ✅ + P0-B1 ✅
- P1-B2 (Lifecycle Decision Service) — depends on P0-A4 ✅ + P0-B1 ✅ + P1-B1

## Next session starts with

1. **Verify CP0** — run `docker compose up --build`, check all 7 services respond to `/health`, run `events_tail.py trigger ReturnSubmitted --golden-path` and confirm event appears, run `npm run dev` in apps/web and confirm shell renders.
2. **Start P1-B1 — AI Grading Service** — build `services/grading/`:
   - SQLAlchemy models + Alembic migration for Grade table
   - Event handler: consume `ReturnSubmitted` → call `ai_client.grade_product()` → persist Grade → emit `ProductGraded`
   - REST endpoint: `GET /grades/{return_id}`
   - Tests (happy path + mock AI)

## Open questions

- Member C's work quality not yet verified by B — need to run `npm run dev` and check if tokens/shell actually render correctly with the Amazon aesthetic
- Progress tracker overall count is stale (shows 8 done, should be 11) — minor doc inconsistency to fix
