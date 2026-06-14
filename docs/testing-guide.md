# Testing Guide — Amazon Second Life AI

>**Quick reference for running tests across the system.** This covers unit tests,
> integration tests, E2E smoke tests, and failure-path testing.

---

## Quick Start

```bash
# 1. Start the full stack
docker compose up --build

# 2. Wait for all services to be healthy (~30s)
curl http://localhost:8000/health

# 3. Run E2E smoke test
python scripts/smoke_test.py --verbose
```

**Expected output:** All tests pass in ~50 seconds.

---

## E2E Smoke Test

### Full Test Suite

```bash
# Comprehensive E2E validation (6 phases)
python scripts/smoke_test.py

# With verbose output (shows each step)
python scripts/smoke_test.py --verbose
```

**Phases tested:**
1. Service health checks (all 7 services `/health` and `/ready`)
2. Authentication flow (register + login)
3. Return submission (product creation + return intake)
4. Event saga completion (10-event choreography in 30s)
5. Dashboard endpoints (BFF aggregation)
6. Failure-path testing (DLQ verification + FAILED status)

**Run time:** ~50-55 seconds with all phases

### Fast Mode (CI/CD)

```bash
# Skip failure-path tests for faster validation
python scripts/smoke_test.py --skip-failure-tests
```

**Run time:** ~35-40 seconds

### Exit Codes

- `0` = All tests passed (CI-friendly)
- `1` = One or more tests failed

### What Gets Tested

#### Happy Path
- ✅ All services healthy and ready
- ✅ User registration and JWT issuance
- ✅ Product creation via Gateway
- ✅ Return submission with media upload
- ✅ Event saga choreography (ReturnSubmitted → ... → SustainabilityUpdated)
- ✅ Grade, Decision, Passport, Match endpoints respond
- ✅ Dashboard aggregation endpoints return valid data

#### Failure Path
- ✅ Malformed events are retried MAX_RETRIES (3) times
- ✅ Failed events land in DLQ after retries
- ✅ DLQ is queryable via `/debug/events/dlq`
- ✅ ReturnStatus.FAILED enum exists and is usable
- ✅ System doesn't stall on event failures

---

## Unit Tests (Per Service)

Each service has its own test suite. Run from the service directory:

```bash
# Example: User Service
cd services/user
pytest -v

# With coverage
pytest --cov=app --cov-report=term-missing

# Single test file
pytest tests/test_auth.py -v
```

### Test Coverage by Service

| Service | Test Files | Coverage |
|---------|-----------|----------|
| User | `test_auth.py`, `test_users.py` | Auth flow, profile CRUD, candidates endpoint |
| Gateway | `test_auth_proxy.py`, `test_returns.py`, `test_aggregation.py` | Return intake, BFF aggregation, event emission |
| Grading | `test_grading_handler.py`, `test_grading_routes.py` | Event handler, grade endpoints, idempotency |
| Lifecycle | `test_lifecycle_handler.py`, `test_lifecycle_routes.py` | Decision logic, event handler, endpoints |
| Passport | `test_passport_handlers.py`, `test_passport_routes.py` | Passport creation, multi-event handling |
| Matching | `test_matching_handler.py`, `test_matching_routes.py` | Match scoring, listing creation, User Service fallback |
| Sustainability | `test_sustainability_handlers.py`, `test_sustainability_routes.py` | Metrics calculation, aggregation, idempotency |

### Running All Backend Tests

```bash
# From repo root
for service in gateway user grading lifecycle passport matching sustainability; do
  echo "Testing $service..."
  docker compose exec $service pytest -v
done
```

---

## Integration Tests

### Full Stack Validation

```bash
# 1. Ensure all services are up
docker compose ps

# 2. Run smoke test (validates integration points)
python scripts/smoke_test.py --verbose
```

### Event Saga Validation

```bash
# Tail events in real-time
python scripts/events_tail.py tail

# In another terminal, trigger a return submission
# Watch events flow: ReturnSubmitted → ProductGraded → ... → SustainabilityUpdated

# Check for failed events in DLQ
python scripts/events_tail.py dlq
```

### Manual Integration Test

```bash
# 1. Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234","name":"Test User"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234"}' | jq -r '.access_token')

# 3. Submit a return
RETURN_ID=$(curl -X POST http://localhost:8000/returns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"<uuid>","reason":"Test return","media":[]}' | jq -r '.id')

# 4. Poll for saga completion
watch -n 2 "curl -s http://localhost:8000/returns/$RETURN_ID -H 'Authorization: Bearer $TOKEN' | jq '.status'"

# 5. Check dashboard
curl http://localhost:8000/dashboard/sustainability/metrics -H "Authorization: Bearer $TOKEN" | jq
```

---

## Failure-Path Testing

### DLQ Verification

```bash
# 1. Inject a malformed event (smoke test does this automatically)
python scripts/smoke_test.py --verbose

# 2. Check DLQ contents
python scripts/events_tail.py dlq

# 3. View DLQ via Gateway API
curl http://localhost:8000/debug/events/dlq?limit=10 | jq
```

### Simulate Service Failure

```bash
# 1. Stop a service mid-saga
docker compose stop grading

# 2. Submit a return (will fail at grading stage)
# ... submit return via Gateway ...

# 3. Check return status (should not stall, may show partial progress)
curl http://localhost:8000/returns/$RETURN_ID -H "Authorization: Bearer $TOKEN" | jq '.status'

# 4. Restart service and verify recovery
docker compose start grading
```

### Event Retry Testing

```bash
# 1. Tail DLQ in one terminal
python scripts/events_tail.py dlq --follow

# 2. In another terminal, inject a bad event
python scripts/events_tail.py trigger --event ProductGraded --correlation-id test-fail-123

# 3. Watch it retry 3 times then land in DLQ
# Check logs: docker compose logs -f grading
```

---

## Frontend Tests (Future)

```bash
# Unit tests for components (vitest + React Testing Library)
cd apps/web
npm run test

# E2E tests (Playwright, when implemented)
npm run test:e2e
```

---

## Property-Based Tests (Future)

Property-based tests are planned for Phase 4+ (post-demo). Example targets:

- Event envelope round-trip: `serialize(deserialize(envelope)) == envelope`
- Grade determinism: Same media + reason → same grade in mock mode
- Match scoring: Score always in [0, 100]
- Sustainability metrics: CO₂/waste/value always non-negative

---

## Test Data Management

### Seed Fixtures

```bash
# Minimal baseline (6 users, 4 products, 2 returns)
python scripts/seed_min.py

# Full demo narrative (8 returns, all lifecycle actions)
python scripts/seed.py

# Reset and re-seed
python scripts/seed.py --reset
```

### Clean Slate

```bash
# Nuclear option: wipe all volumes and restart
docker compose down -v
docker compose up --build

# Re-seed
python scripts/seed.py
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Smoke Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: docker compose up -d --build
      
      - name: Wait for health
        run: |
          for i in {1..30}; do
            curl -f http://localhost:8000/health && break
            sleep 2
          done
      
      - name: Run smoke test
        run: python scripts/smoke_test.py --skip-failure-tests
      
      - name: Stop services
        if: always()
        run: docker compose down -v
```

### Exit Code Usage

```bash
# In CI script
python scripts/smoke_test.py
if [ $? -ne 0 ]; then
  echo "❌ Smoke tests failed"
  exit 1
fi
echo "✅ All tests passed"
```

---

## Debugging Test Failures

### Service Not Healthy

```bash
# Check service logs
docker compose logs -f <service>

# Check health endpoint
curl http://localhost:8001/health
curl http://localhost:8001/ready

# Check database migrations
docker compose exec user alembic current
docker compose exec user alembic upgrade head
```

### Event Saga Stalled

```bash
# Check event stream
python scripts/events_tail.py tail --correlation-id <return-id>

# Check DLQ for failures
python scripts/events_tail.py dlq

# Check consumer logs
docker compose logs -f grading | grep event_handler
```

### Smoke Test Timeout

```bash
# Run with verbose to see where it hangs
python scripts/smoke_test.py --verbose

# Common causes:
# - Service not healthy (check /ready endpoints)
# - Event consumer not running (check lifespan startup)
# - Database migration not applied
# - Redis connection failed
```

### Connection Refused Errors

```bash
# Verify docker compose is running
docker compose ps

# Verify ports are mapped correctly
docker compose ps | grep 8000
docker compose ps | grep 5432

# Check .env matches docker-compose.yml
grep DATABASE_URL .env
grep REDIS_URL .env
```

---

## Test Metrics & Goals

### Performance Targets

- E2E smoke test (full): < 60 seconds
- E2E smoke test (fast): < 45 seconds
- Event saga completion: < 30 seconds
- Service health check: < 2 seconds
- Unit test suite per service: < 10 seconds

### Coverage Goals

- Backend unit tests: > 80% line coverage
- Critical paths: 100% coverage (auth, event handlers, payment)
- Frontend components: > 70% coverage (Phase 4+)

### Reliability

- Smoke test should pass 100% of the time on clean stack
- No flaky tests (retries should be deterministic)
- All tests runnable in CI without AWS credentials (AI_MODE=mock)

---

## Troubleshooting FAQ

**Q: Smoke test fails at Phase 1 (health checks)**
A: Services aren't ready. Wait 30s after `docker compose up`, check logs.

**Q: Smoke test fails at Phase 4 (saga timeout)**
A: Event consumers may not be running. Check service logs for `consumer_started`.

**Q: DLQ test fails (event not found)**
A: Retry timeout too short or handler not failing. Check MAX_RETRIES in handlers.py.

**Q: Tests pass locally but fail in CI**
A: Timing issue. Add wait-for-health step, increase timeouts, or use --skip-failure-tests.

**Q: "Connection refused" on localhost:8000**
A: Docker compose not running or port conflict. Check `docker compose ps`.

---

## Next Steps

- [ ] Add property-based tests for core domain logic (Phase 4+)
- [ ] Add frontend unit tests with vitest (Phase 4+)
- [ ] Add E2E UI tests with Playwright (Phase 4+)
- [ ] Set up mutation testing (PITest for backend, Stryker for frontend)
- [ ] Add load tests (k6 or Locust) for saga throughput
- [ ] Add chaos engineering tests (random service failures)

---

**Questions?** See [docs/hardening-checklist.md](hardening-checklist.md) for production
readiness or [scripts/README.md](../scripts/README.md) for script documentation.
