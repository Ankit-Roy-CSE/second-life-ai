# Hardening Checklist — Amazon Second Life AI

>**Pre-production validation checklist for P3-A2.** This document ensures the system
> is production-ready with proper error handling, security measures, and operational
> safeguards in place.

---

## 1. Event Saga Resilience

### 1.1 Retry & Dead-Letter Queue (DLQ)

- [x] Events retry up to MAX_RETRIES (3 attempts) on handler failure
- [x] Failed events after MAX_RETRIES land in `slmai:events:dlq`
- [x] DLQ is queryable via Gateway `/debug/events/dlq` endpoint
- [x] Idempotency enforced via `event_id` deduplication
- [x] `correlation_id` propagated through entire saga
- [x] Handlers are idempotent (safe to process same event multiple times)

### 1.2 Failure Status Handling

- [x] `ReturnStatus.FAILED` enum value exists
- [x] Services can mark returns as FAILED when saga encounters unrecoverable errors
- [x] FAILED returns don't silently stall the system
- [x] Failed returns are visible in UI with appropriate error state

### 1.3 Saga Observability

- [x] `scripts/events_tail.py` provides real-time event stream monitoring
- [x] Gateway `/debug/events` endpoint shows recent events
- [x] Gateway `/debug/events/stats` shows event counts per type
- [x] Structured logging includes `event_id`, `correlation_id`, `event_type`
- [x] Logs clearly distinguish success vs. failure paths

---

## 2. Service Health & Readiness

### 2.1 Health Checks

- [x] All services expose `/health` (liveness) endpoint
- [x] All services expose `/ready` (readiness with dependency checks)
- [x] `/ready` checks database connectivity
- [x] `/ready` checks Redis connectivity (for event consumers)
- [x] Docker Compose healthchecks configured for all services
- [x] Services wait for dependencies (postgres, redis, minio) via `depends_on`

### 2.2 Graceful Degradation

- [x] AI wrapper falls back to mock mode on AWS errors (no 500s)
- [x] Gateway BFF returns partial data when upstream services are unavailable
- [x] Matching service falls back to MARKETPLACE when User service is unreachable
- [x] Gateway marketplace endpoint retries with exponential backoff (3 attempts)
- [x] Cross-service HTTP calls have timeouts configured

---

## 3. Security

### 3.1 Authentication & Authorization

- [x] JWT issued by User Service on login
- [x] Gateway verifies JWT on all authenticated routes
- [x] JWT contains `user_id` and expiration
- [x] `X-User-Id` header forwarded to downstream services
- [x] Services trust Gateway's `X-User-Id` on internal network
- [x] Passwords hashed with bcrypt before storage
- [x] JWT_SECRET is configurable via environment variable
- [x] Default JWT_SECRET in `.env.example` is clearly marked as insecure

### 3.2 Input Validation

- [x] All API endpoints validate input with Pydantic schemas
- [x] File uploads validated (type, size) before MinIO upload
- [x] Event payloads validated against typed schemas before publishing
- [x] SQL injection prevented via SQLAlchemy parameterized queries
- [x] No raw user input directly interpolated into queries or commands

### 3.3 Secrets Management

- [x] `.env` is git-ignored
- [x] `.env.example` committed with safe defaults and documentation
- [x] No secrets hardcoded in source code
- [x] Logs never contain JWT tokens, passwords, or AWS keys
- [x] MinIO media uploads don't log full file contents

### 3.4 CORS

- [x] Gateway CORS configured to allow frontend origin
- [x] CORS_ORIGINS is configurable via environment variable
- [x] Individual services not publicly exposed (Gateway is the only entry point)

---

## 4. Database Integrity

### 4.1 Migrations

- [x] Every service has Alembic migrations directory
- [x] Migrations auto-run on container start (`alembic upgrade head`)
- [x] Migration files follow naming convention: `001_*.py`
- [x] No duplicate Alembic heads per service
- [x] Database URLs read from environment (Docker vs. localhost)

### 4.2 Data Isolation

- [x] Each service has its own database (no cross-service foreign keys)
- [x] Cross-service data fetched via REST or events
- [x] No direct database connections between services
- [x] Database credentials different per service (logical isolation)

### 4.3 Connection Management

- [x] Async database sessions used throughout
- [x] Sessions created per-request and properly closed
- [x] Connection pooling configured via SQLAlchemy
- [x] No database connections held open indefinitely

---

## 5. Configuration

### 5.1 Environment Variables

- [x] `.env.example` is comprehensive and well-documented
- [x] All required env vars documented with purpose and format
- [x] Sensible defaults provided for local development
- [x] Production hardening checklist included in `.env.example`
- [x] Service-specific DATABASE_URL vars clearly labeled
- [x] AI_MODE options clearly explained (mock/aws/hybrid)

### 5.2 Docker Compose

- [x] All services defined with correct ports
- [x] Health checks configured for infrastructure (postgres, redis, minio)
- [x] Service dependencies declared (`depends_on` with `condition: service_healthy`)
- [x] Volumes configured for postgres and minio persistence
- [x] MinIO bucket auto-created via `minio-init` service
- [x] Environment variables passed via `env_file: .env`

---

## 6. Testing

### 6.1 E2E Smoke Test

- [x] `scripts/smoke_test.py` validates full stack
- [x] Tests all service health checks
- [x] Tests authentication flow (register + login)
- [x] Tests return submission
- [x] Tests full event saga completion
- [x] Tests dashboard aggregation endpoints
- [x] Tests failure-path scenarios (malformed events → DLQ)
- [x] Tests FAILED status handling
- [x] Runs in under 60 seconds (with --skip-failure-tests)
- [x] Returns 0 on success, 1 on failure (CI-friendly)

### 6.2 Unit & Integration Tests

- [x] User Service has auth and user management tests
- [x] Gateway has return submission and aggregation tests
- [x] Grading Service has event handler and grade tests
- [x] Lifecycle Service has decision logic tests
- [x] Passport Service has passport creation tests
- [x] Matching Service has match scoring tests
- [x] Sustainability Service has metrics calculation tests
- [x] All tests pass in mock mode (no AWS required)

---

## 7. Error Handling

### 7.1 HTTP Errors

- [x] Consistent error envelope: `{ "error": { "code", "message", "correlation_id" } }`
- [x] Appropriate status codes used (400, 401, 404, 409, 422, 502, 503)
- [x] No stack traces exposed to clients in production mode
- [x] Validation errors return 422 with field-level details
- [x] Upstream service failures return 502/503, not 500

### 7.2 Event Errors

- [x] Event publishing failures logged and raised (don't silently swallow)
- [x] Event handler exceptions logged with full context
- [x] Failed events don't block the consumer loop indefinitely
- [x] DLQ accumulation monitored (observable via `/debug/events/dlq`)

### 7.3 Logging

- [x] Structured JSON logging used throughout (not print statements)
- [x] Log levels used appropriately (INFO/WARNING/ERROR)
- [x] Every log includes service name
- [x] Business events include `correlation_id`
- [x] Errors include stack traces in DEBUG/ERROR logs
- [x] No PII (emails, names) logged at INFO level in production

---

## 8. Operational Readiness

### 8.1 Observability Scripts

- [x] `scripts/events_tail.py` streams events in real-time
- [x] `scripts/events_tail.py dump` shows event history
- [x] `scripts/events_tail.py stats` shows event counts
- [x] `scripts/events_tail.py trigger` can inject test events
- [x] `scripts/smoke_test.py` validates system end-to-end
- [x] `scripts/seed.py` creates demo narrative with all lifecycle actions

### 8.2 Demo Readiness

- [x] Full demo narrative seeded via `scripts/seed.py`
- [x] 8 returns covering all lifecycle actions (RESELL, REFURBISH, etc.)
- [x] Golden-path product deterministic across runs
- [x] All dashboard metrics populated with meaningful data
- [x] Frontend can display all saga stages visually

### 8.3 Documentation

- [x] `README.md` provides quick start instructions
- [x] `docs/architecture.md` describes system design
- [x] `docs/code-standards.md` provides implementation rules
- [x] `docs/build-plan.md` outlines phased development
- [x] `docs/progress-tracker.md` tracks completion status
- [x] `.env.example` fully documented with production checklist
- [x] `scripts/README.md` documents available scripts

---

## 9. Performance

### 9.1 Timeouts & Retries

- [x] HTTP client timeouts configured (connect=5s, read=30s, write=10s)
- [x] Database query timeouts reasonable (no infinite hangs)
- [x] Event consumer doesn't block indefinitely on single message
- [x] Marketplace endpoint retries with exponential backoff
- [x] Saga completion tested within 30 seconds

### 9.2 Resource Management

- [x] Database connections properly pooled and closed
- [x] HTTP clients reused (not created per-request)
- [x] Redis client singleton per service
- [x] MinIO client singleton per service
- [x] No memory leaks in long-running event consumers

---

## 10. Production Deployment Checklist

### Before Going Live

- [ ] Generate secure JWT_SECRET (64+ random characters, not default)
- [ ] Set AI_MODE=aws or hybrid with real AWS credentials
- [ ] Update CORS_ORIGINS to production domain
- [ ] Update NEXT_PUBLIC_API_BASE_URL to production Gateway URL
- [ ] Disable or protect Gateway `/debug/*` endpoints
- [ ] Use managed PostgreSQL (AWS RDS, Azure Database, etc.)
- [ ] Use managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- [ ] Use real S3 instead of MinIO
- [ ] Enable HTTPS/TLS on all public endpoints
- [ ] Set up CloudWatch or equivalent monitoring
- [ ] Configure log aggregation (ELK, CloudWatch Logs, Datadog)
- [ ] Set up alerts for DLQ depth > threshold
- [ ] Set up alerts for saga failures (FAILED status)
- [ ] Enable database automated backups
- [ ] Test database recovery from backup
- [ ] Review and rotate all secrets
- [ ] Perform load testing (concurrent returns, saga throughput)
- [ ] Perform security audit (OWASP Top 10 checklist)
- [ ] Document incident response procedures
- [ ] Set up on-call rotation and runbooks

---

## Sign-Off

**P3-A2 Complete:** All E2E smoke tests pass, failure-path scenarios verified (malformed
events land in DLQ, FAILED status handling works), and `.env.example` is production-ready
with comprehensive documentation.

**Integration gaps fixed:** Services boot reliably, migrations run correctly, healthchecks
report accurate status, and the full 10-event saga completes within 30 seconds.

**Next:** P3-A3 (if exists) or move to Phase 3 polish tasks (dashboard, demo rehearsal).
