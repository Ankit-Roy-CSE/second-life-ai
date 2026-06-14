# Requirements Document

## Introduction

P2-A2 extends the API Gateway (port 8000) to complete the Backend-for-Frontend (BFF) layer
for the Amazon Second Life AI frontend. This feature covers four deliverables:

1. **Aggregated return detail** — `GET /returns/{id}` is enriched to return the Return entity
   together with Grade, Lifecycle Decision, Passport, and Matches in a single response, eliminating
   multiple round-trips from the frontend.
2. **Proxy routes for Passport and Matches** — `GET /passports/{id}` and
   `GET /matches?return_id=` are added so the frontend never talks to individual services directly.
3. **Purchase trigger** — `POST /purchase` (demo-triggered) emits a `PurchaseCompleted` event
   that advances the saga to the Sustainability Service.
4. **Marketplace proxy** — `GET /marketplace` proxies to the Matching Service's active listings
   endpoint so the frontend can display the marketplace.

All routes sit behind the existing JWT middleware. Internal service calls use
`httpx.AsyncClient`. All errors use the shared `ErrorEnvelope`.

---

## Glossary

- **Gateway**: The API Gateway FastAPI service on port 8000 — the sole entry point for the
  frontend.
- **BFF**: Backend for Frontend — an aggregation layer that stitches data from multiple
  services into one frontend-optimised response.
- **Passport_Service**: The Product Passport Service on port 8004, owned by Member A. Exposes
  `GET /passports/{id}` and `GET /passports/by-return/{return_id}`.
- **Matching_Service**: The Hyperlocal Matching Service on port 8005, owned by Member B.
  Exposes `GET /matches?return_id=` and `GET /listings?channel=&status=`.
- **Grading_Service**: The AI Grading Service on port 8002, owned by Member B. Exposes
  `GET /grades?return_id=`.
- **Lifecycle_Service**: The Lifecycle Decision Service on port 8003, owned by Member B.
  Exposes `GET /decisions?return_id=`.
- **ServiceClient**: The `httpx.AsyncClient`-based helper in
  `services/gateway/app/clients/http_client.py` used by the Gateway for all outbound
  service calls.
- **ErrorEnvelope**: The shared error response shape
  `{ error: { code, message, correlation_id } }` defined in `shared-py/web/errors.py`.
- **Return**: The `Return` ORM entity owned by the Gateway (`slmai_gateway` database),
  whose `id` is also the `correlation_id` for the entire saga.
- **ReturnDetailResponse**: The Pydantic DTO returned by `GET /returns/{id}`, extended in
  this feature to include `grade`, `decision`, `passport`, and `matches` fields.
- **PurchaseCompleted**: The event emitted by the Gateway on `POST /purchase` that signals
  the saga's purchase step to the Sustainability Service.
- **X-User-Id**: HTTP header forwarded by the Gateway to all internal services after JWT
  verification. Services trust this header on the internal network.
- **correlation_id**: The `Return.id` UUID propagated in every event envelope and
  `X-Correlation-Id` header throughout the saga.

---

## Requirements

### Requirement 1: Enriched Return Detail (BFF Aggregation)

**User Story:** As a frontend client, I want to retrieve a single return with its grade,
decision, passport, and matches in one call, so that the return detail page renders without
multiple round-trips.

#### Acceptance Criteria

1. WHEN a `GET /returns/{return_id}` request is received and the Return exists, THE Gateway
   SHALL return a response containing the `return_data`, `grade`, `decision`, `passport`, and
   `matches` fields in a single JSON body.

2. WHEN the Gateway fetches upstream data for `GET /returns/{return_id}`, THE Gateway SHALL
   issue concurrent requests to the Grading_Service, Lifecycle_Service, Passport_Service, and
   Matching_Service using `asyncio.gather` (or equivalent), so that total latency is bounded by
   the slowest upstream rather than the sum of all upstream latencies.

3. WHEN an upstream service returns a 404 or is unreachable during aggregation, THE Gateway
   SHALL populate the corresponding field (`grade`, `decision`, `passport`, or `matches`) as
   `null` (for scalar fields) or `[]` (for the matches list) and SHALL still return HTTP 200
   with the fields that are available.

4. WHEN a `GET /returns/{return_id}` request is received and no Return entity exists in the
   Gateway database, THE Gateway SHALL return HTTP 404 with an ErrorEnvelope.

5. THE Gateway SHALL forward the `X-User-Id` header derived from the verified JWT to each
   upstream service call made during `GET /returns/{return_id}` aggregation.

6. WHEN the `GET /returns/{return_id}` response is assembled, THE Gateway SHALL include the
   `grade` field sourced from `Grading_Service GET /grades?return_id={return_id}` (first
   result), the `decision` field sourced from `Lifecycle_Service GET /decisions?return_id=
   {return_id}` (first result), the `passport` field sourced from `Passport_Service GET
   /passports/by-return/{return_id}`, and the `matches` field sourced from `Matching_Service
   GET /matches?return_id={return_id}`.

---

### Requirement 2: Passport Proxy Route

**User Story:** As a frontend client, I want to fetch a passport by its ID through the
Gateway, so that I never need to know about individual backend service addresses.

#### Acceptance Criteria

1. WHEN a `GET /passports/{passport_id}` request is received, THE Gateway SHALL proxy the
   request to `Passport_Service GET /passports/{passport_id}` and return the response body
   unchanged with the same HTTP status code.

2. WHEN the Passport_Service returns HTTP 404 for `GET /passports/{passport_id}`, THE Gateway
   SHALL return HTTP 404 with an ErrorEnvelope to the caller.

3. WHEN the Passport_Service is unreachable for `GET /passports/{passport_id}`, THE Gateway
   SHALL return HTTP 502 with an ErrorEnvelope whose `code` is `upstream_unreachable`.

4. THE Gateway SHALL forward the `X-User-Id` header to the Passport_Service on every
   `GET /passports/{passport_id}` proxy call.

---

### Requirement 3: Matches Proxy Route

**User Story:** As a frontend client, I want to fetch matches for a return through the
Gateway, so that I can display nearby buyer matches without calling the Matching Service
directly.

#### Acceptance Criteria

1. WHEN a `GET /matches?return_id={return_id}` request is received, THE Gateway SHALL proxy
   the request to `Matching_Service GET /matches?return_id={return_id}` and return the
   response body unchanged with the same HTTP status code.

2. IF the `return_id` query parameter is absent from `GET /matches`, THEN THE Gateway SHALL
   return HTTP 422 with an ErrorEnvelope indicating the missing parameter.

3. WHEN the Matching_Service returns HTTP 404 for `GET /matches?return_id={return_id}`, THE
   Gateway SHALL return HTTP 404 with an ErrorEnvelope to the caller.

4. WHEN the Matching_Service is unreachable for `GET /matches`, THE Gateway SHALL return
   HTTP 502 with an ErrorEnvelope whose `code` is `upstream_unreachable`.

5. THE Gateway SHALL forward the `X-User-Id` header to the Matching_Service on every
   `GET /matches` proxy call, including when the header value is absent from the incoming
   request (forwarding the header with an empty or missing value rather than omitting it).

---

### Requirement 4: Purchase Trigger and PurchaseCompleted Event

**User Story:** As a demo operator, I want to trigger a purchase through the Gateway, so that
the PurchaseCompleted event advances the saga to the Sustainability Service and marks the
listing as sold.

#### Acceptance Criteria

1. WHEN a `POST /purchase` request is received with a valid `listing_id`, `buyer_user_id`, and
   `price`, THE Gateway SHALL emit a `PurchaseCompleted` event to the Redis Stream
   `slmai:events` using the shared `publish()` helper with the envelope:
   `{ event_id, event_type: "PurchaseCompleted", correlation_id: <return_id>, data: { listing_id, buyer_user_id, price } }`.

2. WHEN the Gateway emits `PurchaseCompleted`, THE Gateway SHALL resolve `correlation_id` by
   calling `Matching_Service GET /listings/{listing_id}` to obtain the `return_id` associated
   with the listing before publishing the event.

3. WHEN `POST /purchase` is received and the `listing_id` does not resolve to a known listing
   (Matching_Service returns 404), THE Gateway SHALL return HTTP 404 with an ErrorEnvelope
   and SHALL NOT emit any event.

4. WHEN `POST /purchase` event publishing fails (Redis unreachable or stream write error), THE
   Gateway SHALL return HTTP 503 with an ErrorEnvelope whose `code` is `event_publish_failed`
   and SHALL NOT return a success response.

5. WHEN `POST /purchase` succeeds, THE Gateway SHALL return HTTP 201 with a response body
   containing `{ listing_id, buyer_user_id, price, event_id, correlation_id }`.

6. IF `POST /purchase` is called without a valid JWT, THEN THE Gateway SHALL return HTTP 401
   with an ErrorEnvelope before performing any downstream calls.

7. THE Gateway SHALL ensure `buyer_user_id` in the `PurchaseCompleted` event matches the
   authenticated user's `X-User-Id` derived from the JWT, so that a user cannot trigger a
   purchase on behalf of another user.

---

### Requirement 5: Marketplace Proxy Route

**User Story:** As a frontend client, I want to browse active marketplace listings through the
Gateway, so that I can display the marketplace page without calling the Matching Service
directly.

#### Acceptance Criteria

1. WHEN a `GET /marketplace` request is received, THE Gateway SHALL proxy the request to
   `Matching_Service GET /listings?channel=MARKETPLACE&status=ACTIVE` (plus any caller-provided
   `category`, `limit`, and `offset` query parameters) and return the paginated listings
   response unchanged.

2. WHEN `GET /marketplace` is received with `limit` and `offset` query parameters, THE Gateway
   SHALL forward those values to the Matching_Service unchanged.

3. WHEN the Matching_Service is unreachable for `GET /marketplace`, THE Gateway SHALL retry
   the outbound request up to 2 additional times with exponential back-off, log each failed
   attempt at WARNING level including the `correlation_id`, and after all retries are
   exhausted return HTTP 502 with an ErrorEnvelope whose `code` is `upstream_unreachable`.

4. THE Gateway SHALL default `limit` to `20` and `offset` to `0` when those parameters are
   absent from `GET /marketplace`.

---

### Requirement 6: Route Authentication

**User Story:** As a system operator, I want all new Gateway routes to enforce JWT
authentication, so that only authenticated clients can access aggregated or proxied data.

#### Acceptance Criteria

1. THE Gateway SHALL require a valid JWT `Authorization: Bearer <token>` header for
   `GET /returns/{id}`, `GET /passports/{id}`, `GET /matches`, `POST /purchase`, and
   `GET /marketplace`.

2. WHEN a request to any of the routes listed in criterion 1 is received without a JWT or with
   an invalid JWT, THE Gateway SHALL return HTTP 401 with an ErrorEnvelope before making any
   upstream service call.

3. WHEN a valid JWT is verified, THE Gateway SHALL extract the `user_id` claim and set the
   `X-User-Id` header on every outbound upstream service call for that request.

---

### Requirement 7: Structured Error Responses

**User Story:** As a frontend developer, I want all Gateway errors to use the shared error
envelope, so that the API client can parse errors uniformly.

#### Acceptance Criteria

1. THE Gateway SHALL return all error responses in the ErrorEnvelope format:
   `{ error: { code: string, message: string, correlation_id: string } }`.

2. WHEN a return_id or passport_id path parameter is present in the request, THE Gateway
   SHALL populate `correlation_id` in the ErrorEnvelope with that value.

3. WHEN no correlation_id is available (e.g. a missing param error), THE Gateway SHALL
   populate `correlation_id` in the ErrorEnvelope with an empty string `""`.

---

### Requirement 8: Tests for New Routes

**User Story:** As a developer, I want tests covering all new routes, so that regressions
are caught before merge.

#### Acceptance Criteria

1. THE test suite SHALL include at least one happy-path test for each new route:
   `GET /returns/{id}` (aggregated), `GET /passports/{id}`, `GET /matches`, `POST /purchase`,
   and `GET /marketplace`.

2. THE test suite SHALL include at least one error-path test for each new route, covering the
   upstream-unavailable (502) and not-found (404) cases.

3. WHEN tests run, THE test suite SHALL mock all upstream service calls using
   `httpx.MockTransport` or `pytest-httpx` (or equivalent) so that no real service
   connections are required.

4. THE test suite SHALL assert that the `X-User-Id` header is forwarded correctly on
   upstream calls for authenticated routes.

5. FOR ALL valid `PurchaseCompleted` event inputs, the event envelope produced by
   `POST /purchase` SHALL contain a non-null `event_id`, an `event_type` equal to
   `"PurchaseCompleted"`, a `correlation_id` matching the listing's `return_id`, and a
   `data` object containing the original `listing_id`, `buyer_user_id`, and `price`
   (round-trip property: the values put in must equal the values in the published envelope).
