# Requirements: P3-A2 E2E Testing & System Hardening

## Introduction

This document specifies the requirements for **P3-A2: E2E smoke + failure-path test + finalize `.env.example`**, a Phase 3 task that ensures system reliability through comprehensive end-to-end testing, failure scenario validation, and complete documentation of the runtime environment.

### Context

**Owner:** Member A (Full-Stack)  
**Phase:** 3 (Dashboard, Polish & Demo)  
**Dependencies:** CP2 (Checkpoint 2 - full 10-event saga operational)

The system currently has:
- **Complete event saga**: All 7 services operational with 10-event flow
- **Demo seed data**: `scripts/seed.py` creates 8 returns with full lifecycle coverage
- **All services deployed**: Gateway, User, Grading, Lifecycle, Passport, Matching, Sustainability
- **Partial `.env.example`**: Base configuration exists but may be incomplete

### Business Goals

1. **Ensure Production Readiness**: Validate that the complete system works end-to-end in a realistic deployment scenario
2. **Validate Failure Handling**: Confirm that the event saga handles failures gracefully without stalling or losing data
3. **Complete Documentation**: Provide a comprehensive `.env.example` that serves as the configuration contract
4. **Enable Demo Confidence**: Give judges and developers confidence that the system is robust and well-tested

---

## User Stories

### US-1: Full System Smoke Test
**As a** developer/DevOps engineer  
**I want to** run a single command that validates the entire system is operational  
**So that** I can quickly verify a clean deployment or catch regressions

**Acceptance Criteria:**
1. Running `docker compose up --build` brings up all 7 services + infrastructure (Postgres, Redis, MinIO)
2. All service healthchecks pass within 60 seconds
3. All database migrations complete successfully
4. The event bus (Redis Streams) is operational
5. A smoke test script validates each service's critical endpoints return 200/201
6. The full 10-event saga completes successfully for a test return

### US-2: Failure Path Validation
**As a** system architect  
**I want to** verify that event saga failures are handled gracefully  
**So that** the system doesn't stall on bad data and failed events are observable for debugging

**Acceptance Criteria:**
1. A test return that intentionally fails grading results in `ReturnStatus.FAILED`
2. The failure is logged with correlation_id for traceability
3. After max retries, the failed event lands in the DLQ (dead-letter queue)
4. Other returns continue processing normally (failure is isolated)
5. The failed return is visible in `/debug/events/dlq` for inspection
6. Failed return does not block other returns in the saga

### US-3: Complete Environment Documentation
**As a** new developer onboarding to the project  
**I want to** see all required environment variables documented in `.env.example`  
**So that** I know exactly what configuration is needed to run the system

**Acceptance Criteria:**
1. `.env.example` includes all env vars used by all 7 services
2. Each env var has a comment explaining its purpose
3. Sensitive values (secrets, passwords) show placeholder format
4. Required vs optional vars are clearly marked
5. Default values are provided where applicable
6. Service-specific sections are organized clearly
7. Instructions for Docker vs local development are included

### US-4: Run Documentation
**As a** developer setting up the system for the first time  
**I want to** follow clear, step-by-step instructions to get the system running  
**So that** I can start contributing without tribal knowledge

**Acceptance Criteria:**
1. README.md or docs/ includes a "Quick Start" section
2. Instructions cover: prerequisites, environment setup, running services, seeding data, verifying health
3. Common troubleshooting scenarios are documented
4. Commands for running tests are provided
5. Instructions work on both Windows and Unix-like systems

---

## Functional Requirements

### FR-1: E2E Smoke Test Script

The system SHALL provide an automated smoke test that validates end-to-end functionality.

**FR-1.1: Service Health Validation**  
The smoke test SHALL verify:
- All 7 services respond to `GET /health` with 200 status
- All 7 services respond to `GET /ready` with 200 status (DB + Redis connected)
- Gateway CORS is configured correctly
- MinIO bucket `slmai-media` exists and is accessible

**FR-1.2: Critical Endpoint Validation**  
The smoke test SHALL verify:
- **Auth**: `POST /auth/register` creates a user and returns JWT
- **Returns**: `POST /returns` creates a return and emits `ReturnSubmitted` event
- **Grading**: `GET /grades/{return_id}` returns grade after event processed
- **Lifecycle**: `GET /decisions/{return_id}` returns decision after event processed
- **Passport**: `GET /passports/by-return/{return_id}` returns passport after events processed
- **Matching**: `GET /matches?return_id=` returns matches for HYPERLOCAL returns
- **Sustainability**: `GET /sustainability/metrics` returns aggregated metrics
- **Dashboard**: `GET /dashboard/sustainability/metrics` returns BFF-aggregated data

**FR-1.3: Event Saga Validation**  
The smoke test SHALL:
- Submit a test return via Gateway
- Poll until all 10 events in the saga have completed
- Verify final state: grade exists, decision exists, passport exists, sustainability record exists
- Fail if saga does not complete within 30 seconds (indicates stall or failure)

**FR-1.4: Reporting**  
The smoke test SHALL:
- Print progress with timestamps for each validation step
- Report pass/fail for each service and endpoint
- Exit with code 0 on full pass, non-zero on any failure
- Log detailed error messages for failures

### FR-2: Failure Path Test

The system SHALL provide a test that validates failure handling in the event saga.

**FR-2.1: Failure Injection**  
The failure test SHALL:
- Create a return with invalid/corrupted data that causes grading to fail
- OR trigger a grading failure via mock configuration
- Verify that the Grading Service catches the failure and does not emit `ProductGraded`

**FR-2.2: Failure State Tracking**  
The failure test SHALL verify:
- The return's status is updated to `ReturnStatus.FAILED`
- The failure event includes error details and correlation_id
- The failure is logged in structured format for observability

**FR-2.3: DLQ Verification**  
The failure test SHALL verify:
- After MAX_RETRIES (default 3), the failed event lands in `slmai:events:dlq` stream
- The DLQ entry includes: original event payload, error message, retry count, timestamp
- DLQ entries are retrievable via `GET /debug/events/dlq`

**FR-2.4: Isolation Verification**  
The failure test SHALL verify:
- Other returns submitted before/after the failed return continue processing normally
- Event consumers do not crash or stop processing due to one failure
- The failed return does not block the event queue

### FR-3: Complete `.env.example`

The repository SHALL include a comprehensive `.env.example` file that documents all configuration.

**FR-3.1: Coverage**  
`.env.example` SHALL include all env vars for:
- AI Mode configuration (`AI_MODE`, `AWS_REGION`, `BEDROCK_MODEL_ID`)
- JWT configuration (`JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`)
- Database URLs for all 7 databases
- Redis configuration (`REDIS_URL`)
- MinIO/S3 configuration (`S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`)
- Service URLs for Gateway routing
- CORS configuration
- Frontend configuration (`NEXT_PUBLIC_API_BASE_URL`)

**FR-3.2: Documentation Quality**  
Each env var SHALL have:
- A comment explaining its purpose
- Acceptable value formats/examples
- Default value (if applicable)
- Clear indication if required vs optional

**FR-3.3: Organization**  
`.env.example` SHALL:
- Group related vars by service/category
- Use clear section headers with separator comments
- List vars in logical order (infra → services → frontend)
- Include a header explaining how to use the file

### FR-4: Run Documentation

The repository documentation SHALL provide clear instructions for running the system.

**FR-4.1: Quick Start Guide**  
Documentation SHALL include:
- Prerequisites (Docker, Docker Compose, Python, Node.js versions)
- Steps to copy `.env.example` to `.env` and customize
- Command to start all services: `docker compose up --build`
- Command to seed demo data: `python scripts/seed.py`
- Command to verify system health: `python scripts/smoke_test.py`
- URLs for accessing services (Gateway, MinIO console, Frontend)

**FR-4.2: Troubleshooting Section**  
Documentation SHALL include solutions for:
- "Connection refused" errors → check `docker compose ps`, verify ports
- "Table does not exist" errors → run migrations `alembic upgrade head`
- "Bucket does not exist" errors → verify MinIO init container ran
- Event saga stalls → check `python scripts/events_tail.py tail`, inspect DLQ
- Port conflicts → how to change ports in docker-compose.yml

**FR-4.3: Testing Instructions**  
Documentation SHALL include:
- How to run unit tests: `pytest` in each service directory
- How to run smoke test: `python scripts/smoke_test.py`
- How to run failure test: `python scripts/test_failure_path.py`
- How to verify specific services

---

## Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1: Startup Time**  
All services SHALL be healthy within 60 seconds of `docker compose up`.

**NFR-1.2: Saga Completion Time**  
A full 10-event saga SHALL complete within 10 seconds under normal conditions.

**NFR-1.3: Smoke Test Duration**  
The smoke test SHALL complete in under 2 minutes.

### NFR-2: Reliability

**NFR-2.1: Failure Isolation**  
A single service failure SHALL NOT bring down other services or block event processing.

**NFR-2.2: Event Idempotency**  
All event handlers SHALL be idempotent (safe to retry/replay).

**NFR-2.3: DLQ Retention**  
Failed events SHALL be retained in the DLQ indefinitely for debugging (or per configured TTL).

### NFR-3: Observability

**NFR-3.1: Structured Logging**  
All failures SHALL log structured JSON with correlation_id, error message, stack trace.

**NFR-3.2: Health Endpoints**  
All services SHALL expose `/health` and `/ready` endpoints for monitoring.

**NFR-3.3: DLQ Inspection**  
Failed events SHALL be inspectable via `/debug/events/dlq` endpoint and `events_tail.py dlq` command.

### NFR-4: Maintainability

**NFR-4.1: Test Automation**  
Smoke tests and failure tests SHALL be executable via single commands without manual setup.

**NFR-4.2: Documentation Freshness**  
`.env.example` and run docs SHALL be updated whenever new env vars or setup steps are added.

**NFR-4.3: Cross-Platform**  
Run instructions SHALL work on Windows, macOS, and Linux (Docker Compose abstracts OS differences).

---

## Constraints

### Technical Constraints

**C-1: Docker Dependency**  
E2E tests assume Docker Compose is installed and services run in containers.

**C-2: Existing Infrastructure**  
Tests build on existing `docker-compose.yml`, `seed.py`, and `events_tail.py`.

**C-3: Mock AI Mode**  
Smoke tests run with `AI_MODE=mock` to avoid AWS dependencies.

### Operational Constraints

**C-4: Clean State**  
Smoke tests assume a fresh environment (no stale data). Use `docker compose down -v` before running.

**C-5: Port Availability**  
Tests assume default ports (3000, 8000-8006, 5432, 6379, 9000) are available.

---

## Glossary

| Term | Definition |
|------|------------|
| **Smoke Test** | A high-level test that validates critical functionality works without going deep into edge cases |
| **E2E (End-to-End)** | Testing the complete system flow from user action to final outcome |
| **DLQ (Dead-Letter Queue)** | A queue for events that failed processing after max retries, for manual inspection/replay |
| **Event Saga** | The choreographed sequence of events across services (ReturnSubmitted → ... → SustainabilityUpdated) |
| **Failure Path** | A test scenario where something intentionally goes wrong to validate error handling |
| **Healthcheck** | An endpoint that reports service health (typically `/health` and `/ready`) |
| **Idempotent** | An operation that produces the same result when executed multiple times |

---

## Acceptance Criteria Summary

This feature is complete when:

1. ✅ **Smoke Test Script**: `python scripts/smoke_test.py` validates all services, critical endpoints, and full event saga
2. ✅ **Failure Test Script**: `python scripts/test_failure_path.py` validates failure handling, DLQ, and isolation
3. ✅ **Smoke Test Passes**: Running smoke test on fresh `docker compose up` exits with code 0
4. ✅ **Failure Test Passes**: Running failure test demonstrates proper failure handling
5. ✅ **Complete `.env.example`**: All env vars documented with comments and defaults
6. ✅ **Run Documentation**: README or docs/ includes Quick Start, troubleshooting, and testing instructions
7. ✅ **Cross-Platform Verified**: Instructions work on Windows and Unix-like systems
8. ✅ **Integration Gaps Fixed**: Any issues discovered during testing are resolved
9. ✅ **Progress Tracker Updated**: P3-A2 marked Done with notes and links

---

## References

- [Architecture](../../../docs/architecture.md) — System design, event saga
- [Build Plan](../../../docs/build-plan.md) — Task P3-A2 definition
- [Progress Tracker](../../../docs/progress-tracker.md) — Task status
- [AGENTS.md](../../../AGENTS.md) — Team workflow, commands cheat sheet
- [seed.py](../../../scripts/seed.py) — Demo data seeding
- [events_tail.py](../../../scripts/events_tail.py) — Event observability tool

---

**Status**: Requirements Complete  
**Next**: [Technical Design](./design.md)
