# Scripts — Amazon Second Life AI

Utility scripts for seeding demo data, observing events, and managing the system.

---

## Seeding Scripts

### `seed_min.py` — Minimal Baseline Seed

**Owner:** B (P0-B2)

Creates the minimum reproducible dataset that all services and the frontend can build against.

**What it creates:**
- 6 users (1 returner, 4 nearby buyers, 1 admin)
- 4 products across 3 categories
- 2 returns (1 golden-path, 1 supporting)
- MinIO placeholders for all media

**Usage:**
```bash
# From repo root (services must be up)
python scripts/seed_min.py

# Reset and re-seed
python scripts/seed_min.py --reset
```

**When to use:**
- Early development (Phase 0-1)
- Quick testing of individual services
- Building against stable baseline data
- Testing the golden-path return flow

---

### `seed.py` — Full Demo Narrative Seed

**Owner:** A (P3-A1)

Builds on top of `seed_min.py` with a compelling demo narrative for judges. Creates a complete dataset showing off all system capabilities.

**What it creates:**
- Everything from `seed_min.py`
- 8 total returns covering all lifecycle actions:
  - `RESELL` (Grade A, like-new smartwatch)
  - `REFURBISH` (Grade C, smartphone needs repair)
  - `HYPERLOCAL` (Grade B, heavy furniture item)
  - `DONATE` (Grade B, jacket in good condition)
  - `RECYCLE` (Grade D, broken tablet beyond repair)
- Pre-seeded grades, decisions, passports, matches, listings
- Sustainability records with CO₂/waste/value metrics
- Dashboard-ready aggregated data

**Usage:**
```bash
# From repo root (all services must be up and migrated)
python scripts/seed.py

# Reset everything and re-seed
python scripts/seed.py --reset

# Quick mode (skip seed_min, only add demo data)
python scripts/seed.py --quick
```

**When to use:**
- Phase 3 (Dashboard & Polish)
- Demo preparation and rehearsal
- Judge walkthrough
- Testing the sustainability dashboard
- Showcasing all lifecycle decision types

**Demo Flow:**
1. Login as `demo.returner@slmai.dev` / `demo1234`
2. View Returns → See full event saga for each return
3. Open Sustainability Dashboard → See aggregated impact metrics:
   - Total CO₂ avoided: ~16kg
   - Total waste diverted: ~11kg
   - Total value recovered: ~$450
   - Total green credits: ~88
4. Browse Marketplace → See active listings
5. View Matches → See hyperlocal buyer matches

---

## Event Observability Scripts

### `events_tail.py` — Event Stream Observability

**Owner:** B (P0-B3)

Tail, dump, trigger, replay, and analyze events on the Redis stream.

**Commands:**
```bash
# Tail events in real-time
python scripts/events_tail.py tail

# Dump all events
python scripts/events_tail.py dump

# Show stream statistics
python scripts/events_tail.py stats

# Trigger a test event
python scripts/events_tail.py trigger --event ProductGraded --correlation-id test-123

# Replay a specific event
python scripts/events_tail.py replay <event-id>

# Filter by correlation_id
python scripts/events_tail.py tail --correlation-id <return-id>

# View DLQ (dead-letter queue)
python scripts/events_tail.py dlq
```

**When to use:**
- Debugging event saga issues
- Observing the full 10-event flow
- Identifying stuck returns or failed events
- Replaying events after fixing bugs

---

## Service Requirements

All seeding scripts require:
- Docker Compose running (`docker compose up`)
- All services healthy (`GET /health` → 200)
- Database migrations applied (`alembic upgrade head` per service)
- MinIO bucket created (`slmai-media`)
- Redis accessible on `localhost:6379`

**Check service health:**
```bash
# Quick health check for all services
curl http://localhost:8000/health  # Gateway
curl http://localhost:8001/health  # User
curl http://localhost:8002/health  # Grading
curl http://localhost:8003/health  # Lifecycle
curl http://localhost:8004/health  # Passport
curl http://localhost:8005/health  # Matching
curl http://localhost:8006/health  # Sustainability
```

---

## Environment Variables

Seeding scripts read from `.env` or environment variables. Key vars:

```env
# Database URLs (one per service)
DATABASE_URL_USER=postgresql://slmai:slmai_password@localhost:5432/slmai_user
DATABASE_URL_GRADING=postgresql://slmai:slmai_password@localhost:5432/slmai_grading
DATABASE_URL_LIFECYCLE=postgresql://slmai:slmai_password@localhost:5432/slmai_lifecycle
DATABASE_URL_PASSPORT=postgresql://slmai:slmai_password@localhost:5432/slmai_passport
DATABASE_URL_MATCHING=postgresql://slmai:slmai_password@localhost:5432/slmai_matching
DATABASE_URL_SUSTAINABILITY=postgresql://slmai:slmai_password@localhost:5432/slmai_sustainability

# MinIO / S3
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=slmai-media

# Redis
REDIS_URL=redis://localhost:6379/0

# Service URLs (for seed.py to call REST endpoints)
GATEWAY_URL=http://localhost:8000
GRADING_URL=http://localhost:8002
LIFECYCLE_URL=http://localhost:8003
PASSPORT_URL=http://localhost:8004
MATCHING_URL=http://localhost:8005
SUSTAINABILITY_URL=http://localhost:8006
```

---

## Troubleshooting

**"Connection refused" errors:**
- Ensure `docker compose up` is running
- Check service logs: `docker compose logs <service-name>`
- Verify port mappings match `.env`

**"Table does not exist" errors:**
- Run migrations: `docker compose exec <service> alembic upgrade head`
- Or rebuild: `docker compose down -v && docker compose up --build`

**"Bucket does not exist" (MinIO):**
- Check MinIO console: http://localhost:9001 (minioadmin / minioadmin)
- Bucket `slmai-media` should exist (created by `seed_min.py`)

**Stale data / want fresh start:**
- Use `--reset` flag: `python scripts/seed.py --reset`
- Or nuke everything: `docker compose down -v && docker compose up --build`

---

## Golden Path Constants

Both seed scripts use deterministic constants for the golden-path demo return:

```python
from shared_py.ai.client import (
    GOLDEN_PATH_MEDIA_KEY,    # "products/electronics/zebronics-headphones-001.jpg"
    GOLDEN_PATH_CATEGORY,     # "electronics"
    GOLDEN_PATH_REASON,       # "Sound quality degraded in one ear"
)
```

The AI wrapper hashes `GOLDEN_PATH_MEDIA_KEY` to produce a reproducible **Grade B** result in mock mode, ensuring the demo saga always follows the same narrative.

---

## Notes for Agents

- `seed_min.py` is the foundation — run it first or include it in `seed.py` (default)
- `seed.py` is idempotent — safe to re-run (uses ON CONFLICT DO UPDATE)
- Both scripts gracefully skip tables that don't exist yet (useful during early Phase 0-1 development)
- Demo data includes realistic personas, distances, and narratives to make the judge walkthrough compelling
- Sustainability metrics are pre-calculated (deterministic) to match the demo narrative

---

**Questions?** See [docs/architecture.md](../docs/architecture.md) for system design or [docs/build-plan.md](../docs/build-plan.md) for task context.
