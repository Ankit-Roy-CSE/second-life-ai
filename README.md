# Amazon Second Life AI

> Giving every product its most meaningful second life through AI-powered lifecycle intelligence.

An event-driven microservices platform that decides the best, most sustainable "second life" for every returned product — Resell / Refurbish / Donate / Recycle / Hyperlocal match — with AI grading, a digital product passport, hyperlocal buyer matching, and a sustainability dashboard.

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.12 + [uv](https://docs.astral.sh/uv/) or pip
- Node 20 + pnpm (`npm i -g pnpm`)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work for local Docker Compose
```

### 2. Start the full stack

```bash
docker compose up --build
```

This starts Postgres (6 DBs), Redis, MinIO, and all 7 backend services.

### 3. Run the frontend

```bash
cd apps/web
pnpm install
pnpm dev
# → http://localhost:3000
```

### 4. Seed demo data

```bash
# After services are up:
python scripts/seed_min.py   # minimal fixtures (Phase 0)
python scripts/seed.py       # full demo narrative (Phase 3)
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

### Services & Ports

| Service | Owner | Port |
|---------|-------|------|
| API Gateway / BFF | A | 8000 |
| User Service | A | 8001 |
| AI Grading Service | B | 8002 |
| Lifecycle Decision Service | B | 8003 |
| Product Passport Service | A | 8004 |
| Hyperlocal Matching Service | B | 8005 |
| Sustainability Service | B | 8006 |
| Web Frontend | C | 3000 |
| PostgreSQL | — | 5432 |
| Redis | — | 6379 |
| MinIO | — | 9000/9001 |

### AI Mode

Set `AI_MODE` in `.env`:

| Value | Behavior |
|-------|---------|
| `mock` | Deterministic, no network, no AWS keys needed (**default**) |
| `aws` | Real Bedrock + Rekognition |
| `hybrid` | Rekognition for vision + Bedrock for reasoning |

---

## Development

### Per-service (Python)

```bash
cd services/grading
uvicorn app.main:app --reload --port 8002
alembic upgrade head
pytest
ruff check . && black --check .
```

### Frontend

```bash
cd apps/web
pnpm dev
pnpm lint && pnpm build
```

### Reset everything

```bash
docker compose down -v
docker compose up --build
```

---

## Project Structure

```
.
├── AGENTS.md              # Agent/team entry point — read first
├── docker-compose.yml     # Full local stack
├── .env.example           # Config contract (copy to .env)
├── pyproject.toml         # Root Python tooling config
├── docs/                  # Architecture, build plan, standards, tokens
├── packages/
│   └── shared-py/         # Shared Python lib (web, events, ai, schemas, config)
├── services/
│   ├── gateway/           # API Gateway · :8000 (Owner: A)
│   ├── user/              # User Service · :8001 (Owner: A)
│   ├── grading/           # AI Grading · :8002 (Owner: B)
│   ├── lifecycle/         # Lifecycle Decision · :8003 (Owner: B)
│   ├── passport/          # Product Passport · :8004 (Owner: A)
│   ├── matching/          # Hyperlocal Matching · :8005 (Owner: B)
│   └── sustainability/    # Sustainability · :8006 (Owner: B)
├── apps/
│   └── web/               # Next.js frontend · :3000 (Owner: C)
├── scripts/
│   ├── seed.py            # Full demo seed (P3-A1)
│   ├── seed_min.py        # Minimal fixtures (P0-B2)
│   └── events_tail.py     # Event-saga observability (P0-B3)
└── infra/
    └── postgres/init.sql  # Multi-DB init script
```

---

## Team

| Member | Role | Owns |
|--------|------|------|
| **A** | Full-Stack | gateway, user, passport, shared-py (web/events/config/schemas), Docker, DB, scripts |
| **B** | AI & Backend | grading, lifecycle, matching, sustainability, shared-py/ai, prompts, scoring |
| **C** | Frontend | apps/web, design system, Vercel deploy |

See [docs/build-plan.md](docs/build-plan.md) for the phased task list and [docs/progress-tracker.md](docs/progress-tracker.md) for live status.
