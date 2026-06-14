# Implementation Plan: P3-A1 Demo-Narrative Seed & Gateway Dashboard

## Overview

This plan implements the P3-A1 feature: a complete demo narrative with 8 returns covering all lifecycle actions, pre-seeded event saga data, and Gateway BFF dashboard endpoints for sustainability metrics aggregation. The implementation extends the existing `seed_min.py` script and adds new dashboard routes to the Gateway service.

## Tasks

- [ ] 1. Create enhanced seed script with demo narrative data
  - [ ] 1.1 Create `scripts/seed.py` with demo return definitions
    - Extend `seed_min.py` with 6 additional demo returns covering DONATE, REFURBISH, RECYCLE, RESELL, HYPERLOCAL
    - Define `DEMO_RETURNS` list with deterministic UUIDs using `_det_uuid()`
    - Include narrative descriptions for each return (judge-ready demo story)
    - Reuse `seed_min` helpers for DB connections and constants
    - _Requirements: Design §1 (Enhanced Seed Script), Design §4 (Demo Return Structure)_

  - [ ] 1.2 Implement core seeding functions for demo data
    - Write `seed_demo_products()` → inserts into `slmai_passport.products`
    - Write `seed_demo_returns()` → inserts into `slmai_user.returns`
    - Write `seed_demo_grades()` → inserts into `slmai_grading.grades`
    - Write `seed_demo_decisions()` → inserts into `slmai_lifecycle.lifecycle_decisions`
    - Write `seed_demo_passports()` → inserts into `slmai_passport.passports`
    - Write `seed_demo_matches()` → inserts into `slmai_matching.match_requests` and `matches`
    - Write `seed_demo_listings()` → inserts into `slmai_matching.listings`
    - Write `seed_demo_sustainability()` → inserts into `slmai_sustainability.sustainability_records`
    - Use `_upsert()` helper with `ON CONFLICT DO UPDATE` for idempotency
    - Add try/except per function for graceful degradation
    - _Requirements: Design §1 (Seed Functions), Design §5 (Error Handling - Seed Script)_

  - [ ] 1.3 Add timestamp sequencing and demo data orchestration
    - Implement staggered timestamps using `datetime` and `timedelta` to show realistic timeline
    - Write `main()` function with `--reset` and `--quick` CLI flags
    - Call `seed_min.main()` first (unless `--quick` flag set)
    - Orchestrate all demo seeding functions in sequence
    - Add error collection and summary reporting
    - Update `print_manifest()` to include all 8 demo returns
    - _Requirements: Design §1 (Seed Orchestration), Design §5 (Error Handling)_

- [ ] 2. Checkpoint - Verify seed script runs successfully
  - Run `python scripts/seed.py --reset` and verify manifest output
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Implement Gateway dashboard routes for sustainability metrics
  - [ ] 3.1 Create dashboard routes module
    - Create `services/gateway/app/api/dashboard_routes.py`
    - Define FastAPI router with `/dashboard` prefix
    - Import dependencies: `get_current_user_id`, `service_client`, error types
    - _Requirements: Design §2 (Gateway Dashboard Routes)_

  - [ ] 3.2 Implement GET /dashboard/sustainability/metrics endpoint
    - Accept optional `user_id` query parameter (for filtering)
    - Use `get_current_user_id` dependency for authentication
    - Call `service_client.get_sustainability_metrics(user_id, current_user)`
    - Return aggregated metrics: `{co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits}`
    - Handle AppError(502) for upstream unreachable
    - _Requirements: Design §2 (Dashboard Routes), Design §4 (Sustainability Metrics Response)_

  - [ ] 3.3 Implement GET /dashboard/sustainability/records endpoint
    - Accept optional query params: `user_id`, `return_id`, `limit` (default 20, max 100), `offset` (default 0)
    - Use FastAPI Query validators: `ge=1, le=100` for limit, `ge=0` for offset
    - Use `get_current_user_id` dependency for authentication
    - Call `service_client.list_sustainability_records(user_id, return_id, limit, offset, current_user)`
    - Return paginated response: `{items: [], total: int, limit: int, offset: int}`
    - Handle AppError(502) for upstream unreachable
    - _Requirements: Design §2 (Dashboard Routes), Design §4 (Sustainability Record)_

  - [ ] 3.4 Wire dashboard routes into Gateway main app
    - Import `dashboard_routes` in `services/gateway/app/main.py`
    - Add `app.include_router(dashboard_routes.router)` after existing routes
    - Verify router is included before app startup
    - _Requirements: Design §2 (Wire into Gateway)_

- [ ] 4. Extend ServiceClient with sustainability methods
  - [ ] 4.1 Add `get_sustainability_metrics()` method to ServiceClient
    - Accept `user_id: Optional[str]` and `requesting_user_id: str` parameters
    - Build URL: `{settings.sustainability_service_url}/sustainability/metrics`
    - Set headers: `X-User-Id: requesting_user_id`
    - Add optional `user_id` query param if provided
    - Call `self.call_service("GET", url, params=params, headers=headers)`
    - Map httpx.RequestError to AppError(502, "upstream_unreachable")
    - Return metrics dict
    - _Requirements: Design §3 (ServiceClient Extensions)_

  - [ ] 4.2 Add `list_sustainability_records()` method to ServiceClient
    - Accept `user_id: Optional[str]`, `return_id: Optional[str]`, `limit: int`, `offset: int`, `requesting_user_id: str`
    - Build URL: `{settings.sustainability_service_url}/sustainability`
    - Set headers: `X-User-Id: requesting_user_id`
    - Add query params: `limit`, `offset`, and optional `user_id`, `return_id`
    - Call `self.call_service("GET", url, params=params, headers=headers)`
    - Map httpx.RequestError to AppError(502, "upstream_unreachable")
    - Return paginated response dict
    - _Requirements: Design §3 (ServiceClient Extensions)_

- [ ] 5. Update Gateway configuration for sustainability service
  - [ ] 5.1 Add sustainability_service_url to Gateway settings
    - Edit `services/gateway/app/config.py`
    - Add `sustainability_service_url: str = "http://localhost:8006"` to Settings class
    - Update `.env.example` with `SUSTAINABILITY_SERVICE_URL=http://localhost:8006`
    - _Requirements: Design §3 (Gateway Configuration)_

- [ ]* 6. Write unit tests for dashboard routes
  - [ ]* 6.1 Create test file for dashboard routes
    - Create `services/gateway/tests/test_dashboard_routes.py`
    - Set up test fixtures with mock service_client
    - Mock JWT authentication dependency
    - _Requirements: Design §6 (Unit Tests)_

  - [ ]* 6.2 Write happy path tests for metrics endpoint
    - Test `GET /dashboard/sustainability/metrics` returns aggregated data
    - Test `GET /dashboard/sustainability/metrics?user_id=<id>` with filter
    - Verify correct headers passed to service_client
    - _Requirements: Design §6 (Unit Tests - Coverage Requirements)_

  - [ ]* 6.3 Write error path tests for metrics endpoint
    - Test upstream service unreachable (502)
    - Test missing JWT (401)
    - Verify error envelope format
    - _Requirements: Design §6 (Unit Tests - Coverage Requirements)_

  - [ ]* 6.4 Write happy path tests for records endpoint
    - Test `GET /dashboard/sustainability/records` returns paginated list
    - Test `GET /dashboard/sustainability/records?return_id=<id>` with filter
    - Verify pagination params passed correctly
    - _Requirements: Design §6 (Unit Tests - Coverage Requirements)_

  - [ ]* 6.5 Write error path and validation tests for records endpoint
    - Test upstream service unreachable (502)
    - Test invalid query params: `limit=101` (422), `offset=-1` (422)
    - Test missing JWT (401)
    - _Requirements: Design §6 (Unit Tests - Coverage Requirements)_

- [ ] 7. Update documentation
  - [ ] 7.1 Update Gateway README with dashboard endpoints
    - Edit `services/gateway/README.md`
    - Add section documenting `GET /dashboard/sustainability/metrics`
    - Add section documenting `GET /dashboard/sustainability/records`
    - Include query parameters, response formats, example curl commands
    - _Requirements: Design §3 (Documentation Updates)_

- [ ] 8. Final checkpoint - End-to-end verification
  - Run full seed: `python scripts/seed.py --reset`
  - Verify dashboard endpoints return data via curl/Postman
  - Verify seed manifest shows all 8 demo returns
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific design sections for traceability
- The seed script extends `seed_min.py` rather than replacing it
- Dashboard routes follow the BFF (Backend-for-Frontend) pattern
- ServiceClient methods follow existing patterns (error handling, header propagation)
- All seeding uses idempotent upserts via `ON CONFLICT DO UPDATE`
- Graceful degradation: seed script continues if some service DBs aren't ready
- Implementation language: Python (FastAPI) as indicated by design pseudocode and existing codebase

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "3.1", "5.1"]
    },
    {
      "id": 1,
      "tasks": ["1.2", "3.2", "4.1"]
    },
    {
      "id": 2,
      "tasks": ["1.3", "3.3", "4.2", "6.1"]
    },
    {
      "id": 3,
      "tasks": ["3.4", "6.2", "6.3"]
    },
    {
      "id": 4,
      "tasks": ["6.4", "6.5", "7.1"]
    }
  ]
}
```
