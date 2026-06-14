# Implementation Plan: P2-A2 — Gateway Aggregation + PurchaseCompleted

## Overview

Extends the existing `services/gateway` FastAPI service — no new files, only additions to
three existing modules. The work falls into four layers that must be built in order:

1. **ServiceClient** — add seven new async methods (fan-out helpers, proxy helpers, retry logic)
2. **Schemas** — add `PurchaseRequest` and `PurchaseResponse` Pydantic DTOs
3. **Routes** — replace the `GET /returns/{id}` stub and add four new route handlers
4. **Tests** — example-based tests first, then five property-based tests with `hypothesis`

All code is Python 3.12 / FastAPI 0.115 / Pydantic v2, matching the existing service.
`hypothesis>=6.111,<7` must be added to `pyproject.toml` before the PBT tasks run.

---

## Tasks

- [ ] 1. Add `hypothesis` dev dependency to `services/gateway/pyproject.toml`
  - Under `[project.optional-dependencies] dev`, add `"hypothesis>=6.111,<7"` and
    `"pytest-httpx>=0.30,<1"` (for mocking httpx calls)
  - Verify `uv pip install -e ".[dev]"` (or equivalent) resolves cleanly inside the
    service's venv — no version conflicts
  - _Requirements: 8.5 (hypothesis needed for PBT), design §Testing Strategy_

- [ ] 2. Extend `ServiceClient` with upstream helper methods
  - [ ] 2.1 Add `_safe_call` private helper and four partial-availability methods
    - In `services/gateway/app/clients/http_client.py`, add the `_safe_call(coro, *, default)`
      async helper that returns `default` on `AppError(404)` or `httpx.RequestError` and
      re-raises anything else
    - Add `get_grade(return_id, user_id)` → `GET {grading_url}/grades?return_id=` · swallows
      404/ConnectError → returns `None`
    - Add `get_decision(return_id, user_id)` → `GET {lifecycle_url}/decisions?return_id=` ·
      swallows 404/ConnectError → returns `None`
    - Add `get_passport_by_return(return_id, user_id)` → `GET {passport_url}/passports/by-return/{return_id}` ·
      swallows 404/ConnectError → returns `None`
    - Add `get_matches(return_id, user_id)` → `GET {matching_url}/matches?return_id=` ·
      swallows 404/ConnectError → returns `[]`
    - Each method must include `X-User-Id: user_id` and `X-Correlation-Id: return_id` headers
    - _Requirements: 1.2, 1.3, 1.5, 1.6_

  - [ ] 2.2 Add three strict-proxy methods and one retry method
    - Add `get_passport(passport_id, user_id)` → `GET {passport_url}/passports/{passport_id}` ·
      raises `AppError(404)` on 404, `AppError(502, "upstream_unreachable")` on `RequestError`
    - Add `get_matches_for_return(return_id, user_id)` → `GET {matching_url}/matches?return_id=` ·
      raises `AppError` on errors (strict mode for the `/matches` proxy route)
    - Add `get_listing(listing_id, user_id)` → `GET {matching_url}/listings/{listing_id}` ·
      raises `AppError(404)` on 404, `AppError(502)` on `RequestError`
    - Add `_marketplace_with_retry(params, user_id)` — internal method that calls
      `GET {matching_url}/listings?channel=MARKETPLACE&status=ACTIVE&{params}` up to 3 times
      (back-off: attempt 1 → 0 s, attempt 2 → `asyncio.sleep(1)`, attempt 3 → `asyncio.sleep(2)`)
      and logs each failure at `WARNING` with `correlation_id`; raises `AppError(502,
      "upstream_unreachable")` after all retries exhausted
    - Each method includes `X-User-Id` and `X-Correlation-Id` headers
    - _Requirements: 2.1–2.4, 3.1–3.4, 4.2, 4.3, 5.1–5.3_

- [ ] 3. Add `PurchaseRequest` and `PurchaseResponse` Pydantic schemas
  - In `services/gateway/app/domain/schemas.py`, append the two new DTOs:
    ```python
    class PurchaseRequest(BaseModel):
        listing_id: str = Field(..., description="UUID of the listing being purchased")
        buyer_user_id: str = Field(..., description="Must match JWT user_id")
        price: float = Field(..., gt=0, description="Purchase price (must be > 0)")

    class PurchaseResponse(BaseModel):
        listing_id: str
        buyer_user_id: str
        price: float
        event_id: str
        correlation_id: str
    ```
  - No changes to existing schemas
  - _Requirements: 4.1, 4.5, design §Schemas_

- [ ] 4. Implement `GET /returns/{id}` BFF aggregation (replaces P1 stub)
  - In `services/gateway/app/api/routes.py`:
    - Add `import asyncio` at the top (if not present)
    - Replace the stub body in `get_return_detail` with the full aggregation logic:
      1. `user_id = require_auth(user_id)`
      2. DB fetch → `AppError(404, "not_found")` with `correlation_id=return_id` if missing
      3. `asyncio.gather` across `client.get_grade`, `client.get_decision`,
         `client.get_passport_by_return`, `client.get_matches` (all `_safe_call`-wrapped,
         so `return_exceptions=False` is safe)
      4. Build `ReturnDetailResponse`: grade/decision/passport → result or `None`;
         matches → result or `[]`
      5. Return HTTP 200 with `response_model=ReturnDetailResponse`
    - Import `AppError` from `shared_py.web.errors` (already available)
    - Forward `X-User-Id: user_id` in each gather call (handled inside `ServiceClient`)
    - _Requirements: 1.1–1.6_

- [ ] 5. Implement proxy routes — `GET /passports/{id}` and `GET /matches`
  - In `services/gateway/app/api/routes.py`, add two new route handlers after the returns block:
    - `GET /passports/{passport_id}` (tags=["passports"]):
      1. `user_id = require_auth(user_id)`
      2. `body = await service_client.get_passport(passport_id, user_id)`
      3. Return `JSONResponse(body)` with status 200
      4. `AppError(404)` and `AppError(502)` propagate via the shared error handler
    - `GET /matches` with `return_id: str = Query(...)` (tags=["matches"]):
      1. `user_id = require_auth(user_id)`
      2. `Query(...)` with no default makes `return_id` required → FastAPI returns 422 if absent
      3. `body = await service_client.get_matches_for_return(return_id, user_id)`
      4. Return `JSONResponse(body)` with status 200
    - Import `JSONResponse` from `fastapi.responses`
    - _Requirements: 2.1–2.4, 3.1–3.5_

- [ ] 6. Implement `POST /purchase`
  - In `services/gateway/app/api/routes.py`, add the purchase handler:
    1. `user_id = require_auth(user_id)`
    2. Validate `request.buyer_user_id == user_id` → raise `AppError(403, "forbidden")` on mismatch
    3. `listing = await service_client.get_listing(request.listing_id, user_id)` →
       `AppError(404)` if not found
    4. `correlation_id = listing["return_id"]`
    5. `event_id = await publish(event_type="PurchaseCompleted", correlation_id=correlation_id,
       data={"listing_id": request.listing_id, "product_id": listing.get("product_id", ""),
       "return_id": correlation_id, "buyer_user_id": user_id, "price": request.price})` —
       wrap in `try/except Exception` → `AppError(503, "event_publish_failed")` on failure
    6. Return HTTP 201 with `PurchaseResponse(listing_id=..., buyer_user_id=user_id,
       price=..., event_id=event_id, correlation_id=correlation_id)`
    - Import `PurchaseRequest`, `PurchaseResponse` from `app.domain.schemas`
    - `buyer_user_id` in the event envelope MUST be `user_id` (JWT-derived), not `request.buyer_user_id`
    - _Requirements: 4.1–4.7_

- [ ] 7. Implement `GET /marketplace`
  - In `services/gateway/app/api/routes.py`, add the marketplace handler:
    1. `user_id = require_auth(user_id)`
    2. Apply defaults: `limit = limit or 20`, `offset = offset or 0`
    3. Build `params` dict: always include `channel="MARKETPLACE"`, `status="ACTIVE"`, plus
       `limit`, `offset`, and `category` (only if provided)
    4. `body = await service_client._marketplace_with_retry(params, user_id)` →
       `AppError(502)` propagates after all retries
    5. Return `JSONResponse(body)` with status 200
    - Route signature: `category: Optional[str] = Query(None)`,
      `limit: Optional[int] = Query(None, ge=1, le=100)`,
      `offset: Optional[int] = Query(None, ge=0)`
    - _Requirements: 5.1–5.4_

- [ ] 8. Checkpoint — unit-level sanity before writing tests
  - Run `ruff check services/gateway/app` and `black --check services/gateway/app`
  - Run `mypy services/gateway/app` (or `ruff check --select ANN`) for type issues
  - Fix any lint/type errors before proceeding
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Write example-based tests (happy paths + error paths)
  - Create `services/gateway/tests/test_aggregation.py`
  - Mock strategy: use `monkeypatch` on `service_client` methods (same pattern as `conftest.py`)
    and `mock_publish` fixture for event publish; use `test_db` fixture for DB

  - [ ] 9.1 Happy-path examples (one per route)
    - `test_get_return_detail_aggregated_success` — all four upstreams return valid mock data;
      assert 200, all five top-level fields present and sourced correctly
    - `test_get_passport_success` — Passport_Service returns 200 mock body; assert 200, body unchanged
    - `test_get_matches_success` — Matching_Service returns 200 mock body; assert 200, body unchanged
    - `test_post_purchase_success` — listing lookup returns `{return_id, product_id}`, publish
      returns event_id; assert 201, `PurchaseResponse` fields match
    - `test_get_marketplace_success` — Matching_Service returns paginated listings on first attempt;
      assert 200, body unchanged
    - _Requirements: 8.1_

  - [ ]* 9.2 Error-path examples (502 and 404 per route)
    - `test_get_return_detail_not_found` — Return not in DB → 404 + ErrorEnvelope
    - `test_get_passport_not_found` — Passport_Service 404 → 404 + ErrorEnvelope
    - `test_get_passport_unreachable` — ConnectError → 502, `code == "upstream_unreachable"`
    - `test_get_matches_missing_param` — no `return_id` query param → 422
    - `test_get_matches_unreachable` — ConnectError → 502, `code == "upstream_unreachable"`
    - `test_post_purchase_listing_not_found` — listing 404 → 404, `mock_publish.assert_not_called()`
    - `test_post_purchase_event_publish_fail` — publish raises → 503, `code == "event_publish_failed"`
    - `test_post_purchase_buyer_mismatch` — `buyer_user_id` ≠ JWT user → 403
    - `test_get_marketplace_all_retries_fail` — three ConnectErrors → 502, `code ==
      "upstream_unreachable"`, verify `_marketplace_with_retry` was called (or inner mock 3×)
    - _Requirements: 8.2, 8.3_

  - [ ]* 9.3 X-User-Id header forwarding example tests
    - `test_x_user_id_forwarded_on_aggregation` — capture kwargs of each `service_client` mock
      call; assert `X-User-Id` matches the JWT user
    - `test_x_user_id_forwarded_on_purchase` — assert listing lookup call carries `X-User-Id`
    - _Requirements: 8.4, 1.5, 2.4, 3.5, 6.3_

- [ ] 10. Write property-based tests with `hypothesis`
  - Append to `services/gateway/tests/test_aggregation.py` (or a new
    `tests/test_aggregation_pbt.py`); import `from hypothesis import given, settings as
    h_settings` and `from hypothesis import strategies as st`

  - [ ]* 10.1 Property 1 — partial upstream failure still returns HTTP 200
    - **Property 1: Partial upstream failure does not fail the aggregated response**
    - **Validates: Requirements 1.3**
    - `@given(failing=st.frozensets(st.sampled_from(["grading","lifecycle","passport","matching"]),
      min_size=1))`
    - `@h_settings(max_examples=100)`
    - For each service in `failing`, monkeypatch its `ServiceClient` method to raise
      `httpx.ConnectError` (or mock `AppError(404)`); services not in `failing` return mock dicts
    - Assert: `response.status_code == 200`
    - Assert: fields for failed services are `None` (scalar) or `[]` (matches list)
    - Assert: fields for available services are non-null

  - [ ]* 10.2 Property 2 — X-User-Id forwarded on every upstream call
    - **Property 2: X-User-Id is forwarded to every upstream call on authenticated routes**
    - **Validates: Requirements 1.5, 2.4, 3.5, 6.3**
    - `@given(user_id=st.text(min_size=1, max_size=64,
      alphabet=st.characters(whitelist_categories=("L","N","Nd"))))`
    - `@h_settings(max_examples=100)`
    - Mock `service_client` methods to record the `user_id` argument received
    - Call `GET /returns/{id}` with a DB-seeded Return and a JWT mocked to emit `user_id`
    - Assert all four gather calls received the same `user_id`

  - [ ]* 10.3 Property 3 — unknown return_id always returns 404
    - **Property 3: Missing Return produces 404 for any unknown return_id**
    - **Validates: Requirements 1.4**
    - `@given(return_id=st.uuids().map(str))`
    - `@h_settings(max_examples=100)`
    - DB is always empty (fresh `test_db` per invocation via `hypothesis` + `@pytest_asyncio`)
    - Call `GET /returns/{return_id}` with a valid mocked JWT
    - Assert: `response.status_code == 404`
    - Assert: response body matches `ErrorEnvelope` shape
      (`{"error": {"code": ..., "message": ..., "correlation_id": ...}}`)
    - Assert: no upstream `service_client` method was called (mock call count == 0)

  - [ ]* 10.4 Property 4 — PurchaseCompleted is a faithful round-trip
    - **Property 4: PurchaseCompleted event is a faithful round-trip of the request inputs**
    - **Validates: Requirements 4.1, 4.5, 4.7, 8.5**
    - `@given(listing_id=st.uuids().map(str), price=st.floats(min_value=0.01, max_value=10_000.0,
      allow_nan=False, allow_infinity=False), user_id=st.uuids().map(str))`
    - `@h_settings(max_examples=100)`
    - Mock `service_client.get_listing` to return
      `{"return_id": str(uuid4()), "product_id": str(uuid4())}`
    - Capture the `publish` call via `monkeypatch`
    - Assert event: `event_type == "PurchaseCompleted"`, `event_id` is non-empty,
      `correlation_id == listing["return_id"]`
    - Assert event `data`: `listing_id == listing_id`, `buyer_user_id == user_id`,
      `price == price`
    - Assert response 201 body: same `listing_id`, `buyer_user_id`, `price`, plus non-empty
      `event_id` and `correlation_id`

  - [ ]* 10.5 Property 5 — marketplace always appends fixed channel and status filters
    - **Property 5: Marketplace proxy always appends fixed channel and status filters**
    - **Validates: Requirements 5.1, 5.2, 5.4**
    - `@given(category=st.one_of(st.none(), st.text(min_size=1, max_size=32)),
      limit=st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
      offset=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)))`
    - `@h_settings(max_examples=100)`
    - Mock `service_client._marketplace_with_retry` to capture the `params` dict it receives
    - Assert: `params["channel"] == "MARKETPLACE"` and `params["status"] == "ACTIVE"`
    - Assert: `params["limit"] == (limit if limit is not None else 20)`
    - Assert: `params["offset"] == (offset if offset is not None else 0)`
    - Assert: if `category` is not None, `params["category"] == category`; otherwise
      `"category"` not in `params`

- [ ] 11. Final checkpoint — full test suite passes
  - Run `pytest services/gateway/tests/ -v` and confirm all tests pass
  - Run `ruff check services/gateway/app` and `black --check services/gateway/app`
  - Confirm `AI_MODE=mock` path works (no AWS keys needed)
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Update `docs/progress-tracker.md` for P2-A2
  - Set P2-A2 row to `✅ Done`
  - Fill **Notes**: what shipped (five routes: enriched `GET /returns/{id}`, `GET /passports/{id}`,
    `GET /matches`, `POST /purchase`, `GET /marketplace`; `PurchaseCompleted` event; 5 PBT
    properties)
  - Fill **Link**: PR or branch name (e.g. `a/gateway/p2-a2`)
  - Update Event Saga Status table: set row 9 (`PurchaseCompleted`) to `✅`
  - Update Service Readiness table gateway row if any columns changed
  - Update **Overall Progress** counts (Phase 2: increment ✅ Done by 1)
  - _Requirements: code-standards.md §6 Definition of Done, AGENTS.md Operating Rule 9_

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP (example-based
  tests in 9.1 are **not** optional — they are the minimum required by Requirement 8.1)
- Tasks 2 → 3 → 4–7 must be executed in order; tasks 4–7 are independent of each other once
  2 and 3 are done
- Task 9 depends on tasks 4–7 being complete; task 10 depends on task 9 (shares the test file)
- The `_safe_call` helper (2.1) is used only inside the four partial-availability methods;
  the strict-proxy methods in 2.2 do NOT use `_safe_call` — they raise on error
- `buyer_user_id` in the `PurchaseCompleted` event data MUST be the JWT-derived `user_id`,
  not the request body field — this is enforced in task 6 step 5
- `ErrorEnvelope` shape is already registered by `create_app()` in shared-py; no new error
  handler code needed — just raise `AppError` with the correct `status_code` and `code`
- `X-Correlation-Id` header is passed as `return_id` or `listing_id` in scope; when neither
  is available (e.g. marketplace), generate a request-scoped UUID or omit it

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "3"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["4", "5", "6", "7"] },
    { "id": 4, "tasks": ["9.1"] },
    { "id": 5, "tasks": ["9.2", "9.3"] },
    { "id": 6, "tasks": ["10.1", "10.2", "10.3", "10.4", "10.5"] },
    { "id": 7, "tasks": ["12"] }
  ]
}
```
