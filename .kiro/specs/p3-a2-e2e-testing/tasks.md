# Implementation Tasks: P3-A2 E2E Testing & System Hardening

## Overview

This task list implements comprehensive end-to-end testing, failure path validation, and complete system documentation for the Amazon Second Life AI platform. The implementation focuses on ensuring production readiness through automated testing and clear documentation.

## Tasks

- [ ] 1. Create smoke test script for E2E validation
  - [x] 1.1 Set up smoke test script structure
    - Create `scripts/smoke_test.py` with async test runner class
    - Define service URLs and test configuration constants
    - Set up httpx client with appropriate timeouts
    - Implement results tracking and reporting framework
    - _Requirements: FR-1.1 (Service Health Validation)_

  - [ ] 1.2 Implement infrastructure health checks
    - Test Postgres connectivity (direct connection or health endpoint)
    - Test Redis connectivity (`redis-cli PING` or Python redis client)
    - Test MinIO health (`GET /minio/health/live`)
    - Record and report results for each infrastructure component
    - _Requirements: FR-1.1 (Service Health Validation)_

  - [ ] 1.3 Implement service health checks
    - For each of 7 services: test `GET /health` endpoint returns 200
    - For each of 7 services: test `GET /ready` endpoint returns 200  
    - Measure and record response times
    - Report any unhealthy services
    - _Requirements: FR-1.1 (Service Health Validation)_

  - [ ] 1.4 Implement auth flow tests
    - Test `POST /auth/register` with unique test user (timestamped email)
    - Verify 201 response with valid JWT in response
    - Test `POST /auth/login` with same credentials
    - Verify 200 response and store JWT for subsequent requests
    - _Requirements: FR-1.2 (Critical Endpoint Validation)_

  - [ ] 1.5 Implement return submission test
    - Test `POST /returns` with test return data and media
    - Verify 201 response with return_id
    - Query Redis to verify `ReturnSubmitted` event was published
    - Store return_id for saga validation
    - _Requirements: FR-1.2 (Critical Endpoint Validation)_

  - [ ] 1.6 Implement event saga validation
    - Poll `GET /grades/{return_id}` until 200 or 30s timeout
    - Poll `GET /decisions/{return_id}` until 200 or timeout
    - Poll `GET /passports/by-return/{return_id}` until 200 or timeout
    - Verify `GET /sustainability/metrics` shows updated aggregated data
    - Implement exponential backoff polling (1s, 2s, 4s, 8s intervals)
    - Fail test if any step times out (indicates saga stall)
    - _Requirements: FR-1.3 (Event Saga Validation)_

  - [ ] 1.7 Implement dashboard endpoint tests
    - Test `GET /dashboard/sustainability/metrics` returns 200 with expected schema
    - Test `GET /dashboard/sustainability/records?limit=5` returns paginated data
    - Verify response structures match documented APIs
    - _Requirements: FR-1.2 (Critical Endpoint Validation)_

  - [ ] 1.8 Add reporting and CLI output
    - Print progress with timestamps for each test phase
    - Display pass/fail status with colored output (green/red)
    - Print summary: X/Y tests passed, total duration
    - Exit with code 0 on full pass, 1 on any failure
    - Log detailed error messages to stderr for failures
    - _Requirements: FR-1.4 (Reporting)_

- [ ] 2. Create failure path test script
  - [ ] 2.1 Set up failure test script structure
    - Create `scripts/test_failure_path.py` with test runner class
    - Set up Redis client for DLQ inspection
    - Set up httpx client for API calls
    - Implement test orchestration framework
    - _Requirements: FR-2 (Failure Path Test)_

  - [ ] 2.2 Implement failure injection mechanism
    - Define `FAIL_GRADING_TEST_KEY` constant in AI wrapper
    - Update AI wrapper to raise intentional error when media key matches test key
    - Create failing return via `POST /returns` with special media key
    - Verify return creation succeeds (failure happens asynchronously)
    - _Requirements: FR-2.1 (Failure Injection)_

  - [ ] 2.3 Verify failed return status
    - Poll `GET /returns/{return_id}` until status becomes `FAILED` or timeout
    - Verify return status is `FAILED` (not stuck in PROCESSING)
    - Verify error message is logged (check service logs or return response)
    - Verify correlation_id is present in failure logs
    - _Requirements: FR-2.2 (Failure State Tracking)_

  - [ ] 2.4 Verify DLQ entry creation
    - Wait for max retries to complete (~10 seconds with exponential backoff)
    - Query Redis DLQ stream: `XREAD COUNT 100 STREAMS slmai:events:dlq 0`
    - Find entry with matching correlation_id (return_id)
    - Verify DLQ entry includes: event_type, error message, retry_count, timestamp
    - Verify DLQ entry is retrievable via `GET /debug/events/dlq`
    - _Requirements: FR-2.3 (DLQ Verification)_

  - [ ] 2.5 Verify failure isolation
    - Submit a normal return (different user, valid data)
    - Poll until normal return completes full saga
    - Verify normal return reaches COMPLETED status
    - Verify grade, decision, passport exist for normal return
    - Confirm failing return did not block event queue
    - _Requirements: FR-2.4 (Isolation Verification)_

  - [ ] 2.6 Add reporting and cleanup
    - Print test progress and results
    - Clean up test data (mark test returns for deletion or use --reset)
    - Exit with code 0 on pass, 1 on failure
    - _Requirements: FR-2 (Failure Path Test)_

- [ ] 3. Finalize `.env.example` documentation
  - [x] 3.1 Audit codebase for all environment variables
    - Grep all services for `os.getenv`, `os.environ`, `Settings` class fields
    - Compile complete list of env vars used across services
    - Identify which vars are required vs optional
    - Document default values for each var
    - _Requirements: FR-3.1 (Coverage)_

  - [ ] 3.2 Enhance `.env.example` with comprehensive documentation
    - Add clear section headers with separator comments
    - Add inline comment for each env var explaining purpose
    - Include format examples for complex vars (URLs, connection strings)
    - Add security notes (e.g., JWT_SECRET generation advice)
    - Organize vars by category: AI, Auth, Database, Redis, MinIO, Services, CORS, Frontend
    - Include header explaining how to use the file (copy to `.env`)
    - _Requirements: FR-3.2 (Documentation Quality), FR-3.3 (Organization)_

  - [ ] 3.3 Add optional/development variables section
    - Document optional vars like `LOG_LEVEL`, `ENABLE_DEBUG_ROUTES`
    - Document testing-specific vars like `MAX_EVENT_RETRIES`
    - Clearly mark these as optional
    - _Requirements: FR-3.1 (Coverage)_

- [ ] 4. Create comprehensive run documentation
  - [ ] 4.1 Write Quick Start guide
    - Document prerequisites (Docker, Python, Node.js versions)
    - Provide step-by-step setup instructions:
      1. Clone repository
      2. Copy `.env.example` to `.env`
      3. Start services with `docker compose up --build`
      4. Seed data with `python scripts/seed.py`
      5. Verify with `python scripts/smoke_test.py`
      6. Start frontend with `npm run dev`
    - List all service URLs (Gateway, MinIO console, Frontend)
    - _Requirements: FR-4.1 (Quick Start Guide)_

  - [ ] 4.2 Write troubleshooting section
    - Document "Connection refused" errors → check `docker compose ps`, verify ports
    - Document "Table does not exist" → run `alembic upgrade head` or rebuild
    - Document "Bucket does not exist" → check MinIO init, manually create bucket
    - Document "Event saga stalls" → use `events_tail.py`, check DLQ, inspect logs
    - Document port conflicts → how to change ports in docker-compose.yml
    - _Requirements: FR-4.2 (Troubleshooting Section)_

  - [ ] 4.3 Write testing instructions
    - Document how to run unit tests: `pytest` in service directories
    - Document how to run smoke test: `python scripts/smoke_test.py`
    - Document how to run failure test: `python scripts/test_failure_path.py`
    - Document how to verify specific services individually
    - _Requirements: FR-4.3 (Testing Instructions)_

  - [ ] 4.4 Choose documentation location
    - Option A: Add "Quick Start" and "Testing" sections to root `README.md`
    - Option B: Create `docs/RUNNING.md` for detailed run instructions
    - Link from root README to detailed docs if using Option B
    - _Requirements: FR-4 (Run Documentation)_

- [ ] 5. Fix integration gaps discovered during testing
  - [ ] 5.1 Run smoke test and document failures
    - Execute `python scripts/smoke_test.py` on fresh environment
    - Document any failures: which services, which endpoints, error messages
    - Categorize failures: configuration, code bugs, missing migrations, timing issues
    - _Requirements: NFR-2 (Reliability)_

  - [ ] 5.2 Address smoke test failures
    - Fix any service health check failures
    - Fix any endpoint failures (status codes, response formats)
    - Fix any saga completion issues (timeouts, missing events)
    - Re-run smoke test after each fix to verify resolution
    - _Requirements: Implicit (fix issues found)_

  - [ ] 5.3 Run failure test and document issues
    - Execute `python scripts/test_failure_path.py`
    - Document any issues: DLQ not populated, isolation failed, etc.
    - _Requirements: NFR-2 (Reliability)_

  - [ ] 5.4 Address failure test issues
    - Fix DLQ handling if events don't land in DLQ
    - Fix isolation issues if failed returns block queue
    - Fix status tracking if returns don't transition to FAILED
    - _Requirements: NFR-2 (Reliability)_

- [ ] 6. Cross-platform verification
  - [ ] 6.1 Test on Windows (PowerShell)
    - Follow Quick Start guide on Windows machine
    - Run smoke test and failure test
    - Document any Windows-specific issues
    - Update docs with Windows-specific notes if needed
    - _Requirements: NFR-4.3 (Cross-Platform)_

  - [ ] 6.2 Test on Unix-like system (bash)
    - Follow Quick Start guide on Linux/macOS
    - Run smoke test and failure test
    - Ensure all commands work as documented
    - _Requirements: NFR-4.3 (Cross-Platform)_

- [ ] 7. Update progress tracker and finalize
  - [ ] 7.1 Update progress tracker
    - Mark P3-A2 as `✅ Done` in `docs/progress-tracker.md`
    - Add notes: smoke test script, failure test script, finalized `.env.example`, run docs
    - Add link to commit/PR
    - Update phase completion counts
    - _Requirements: Definition of Done_

  - [ ] 7.2 Final verification
    - Clean environment test: `docker compose down -v && docker compose up --build`
    - Run smoke test → exit 0
    - Run failure test → exit 0
    - Verify docs are accurate and complete
    - _Requirements: Acceptance Criteria Summary_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "2.1", "3.1", "4.1"]
    },
    {
      "id": 1,
      "tasks": ["1.2", "1.3", "2.2", "3.2", "4.2"]
    },
    {
      "id": 2,
      "tasks": ["1.4", "1.5", "2.3", "3.3", "4.3"]
    },
    {
      "id": 3,
      "tasks": ["1.6", "1.7", "2.4", "4.4"]
    },
    {
      "id": 4,
      "tasks": ["1.8", "2.5", "2.6"]
    },
    {
      "id": 5,
      "tasks": ["5.1", "5.2", "5.3", "5.4"]
    },
    {
      "id": 6,
      "tasks": ["6.1", "6.2"]
    },
    {
      "id": 7,
      "tasks": ["7.1", "7.2"]
    }
  ]
}
```

## Notes

- **Implementation language**: Python (for test scripts), bash/markdown (for docs)
- **All test scripts** should use async/await with httpx for performance
- **Polling strategy**: Exponential backoff (1s, 2s, 4s, 8s) to balance speed and reliability
- **Test isolation**: Use unique identifiers (timestamps, UUIDs) for test data to avoid conflicts
- **Clean state**: Tests assume fresh environment (or use `--reset` flags)
- **Exit codes**: 0 = success, 1 = failure (for CI integration)
- **Cross-platform**: Use Python and Docker Compose to abstract OS differences

## Estimated Effort

| Component | Tasks | Estimated Time |
|-----------|-------|----------------|
| Smoke Test | 8 sub-tasks | 4-6 hours |
| Failure Test | 6 sub-tasks | 3-4 hours |
| `.env.example` | 3 sub-tasks | 1-2 hours |
| Run Documentation | 4 sub-tasks | 2-3 hours |
| Integration Fixes | 4 sub-tasks | 2-4 hours (varies) |
| Cross-Platform | 2 sub-tasks | 1-2 hours |
| Finalization | 2 sub-tasks | 1 hour |

**Total**: 27 sub-tasks, ~14-22 hours

## Success Criteria

P3-A2 is complete when:

1. ✅ `python scripts/smoke_test.py` passes on fresh `docker compose up`
2. ✅ `python scripts/test_failure_path.py` passes and demonstrates proper failure handling
3. ✅ `.env.example` documents all environment variables with clear comments
4. ✅ Run documentation (README or docs/) includes Quick Start, troubleshooting, and testing
5. ✅ All tests work on both Windows and Unix-like systems
6. ✅ All integration gaps discovered during testing are fixed
7. ✅ Progress tracker updated with completion notes

