# Service Endpoint Registry

> **Contract catalog for all REST endpoints across the 7 backend services.**  
> This is the binding reference for cross-service calls and Gateway routing.  
> Update this file whenever adding, removing, or changing an endpoint signature.

---

## Gateway (port 8000) — Owner: A

**Purpose:** Single entry point for the frontend; JWT verification; routing; aggregation.

### Public endpoints (called by frontend)

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| POST | `/auth/login` | `{ email, password }` | `{ access_token, user }` | Proxies to User Service |
| POST | `/auth/register` | `{ email, password, display_name, ... }` | `{ user }` | Proxies to User Service |
| GET | `/returns` | Query: `?user_id=&status=&limit=&offset=` | `PaginatedResponse + items[]` | Aggregates Return + Grade + Decision |
| POST | `/returns` | `ReturnCreateRequest` | `ReturnResponse` | Creates Return, uploads media to MinIO, emits `ReturnSubmitted` |
| GET | `/returns/{id}` | — | `ReturnResponse + grade + decision + passport + matches` | BFF aggregation |
| GET | `/passports/{id}` | — | `PassportResponse + timeline` | Proxies to Passport Service |
| GET | `/matches` | Query: `?return_id=` | `{ matches: [] }` | Proxies to Matching Service |
| GET | `/marketplace` | Query: `?category=&limit=&offset=` | `PaginatedResponse + listings[]` | Proxies to Matching Service |
| POST | `/purchase` | `{ listing_id }` | `{ purchase }` | Demo-triggered; emits `PurchaseCompleted` |
| GET | `/sustainability` | Query: `?user_id=` | `SustainabilityMetricsResponse` | Proxies to Sustainability Service |
| GET | `/sustainability/dashboard` | — | Dashboard aggregates (totals, charts) | Read-model built from `SustainabilityUpdated` events |

### Internal endpoints

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/debug/events` | — | Recent events + DLQ | Event-saga observability (P0-B3) |

---

## User Service (port 8001) — Owner: A

**Purpose:** Auth, user profiles, preferences, green-credit balance.

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| POST | `/auth/register` | `{ email, password, display_name, location, interests }` | `{ user }` | Hash password, create User, return JWT-ready data |
| POST | `/auth/login` | `{ email, password }` | `{ access_token, user }` | Verify password, issue JWT (HS256) |
| GET | `/users/{id}` | — | `UserResponse` | Get user profile |
| PATCH | `/users/{id}` | `{ display_name?, location?, interests? }` | `UserResponse` | Update profile |
| GET | `/users/{id}/credits` | — | `{ green_credits: float }` | Get green-credit balance |
| GET | `/users/candidates` | Query: `?category=&lat=&lng=&radius_km=` | `UserCandidatesListResponse` | **Cross-service:** Called by Matching to find nearby buyers |

---

## Grading Service (port 8002) — Owner: B

**Purpose:** AI-powered product condition grading.

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/grades` | Query: `?return_id=&product_id=` | `{ grades: [] }` | List grades |
| GET | `/grades/{id}` | — | `GradeResponse` | Get grade by ID |

**Events consumed:** `ReturnSubmitted`  
**Events produced:** `ProductGraded`

---

## Lifecycle Service (port 8003) — Owner: B

**Purpose:** Decide the best lifecycle action (Resell/Refurbish/Donate/Recycle/Hyperlocal).

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/decisions` | Query: `?return_id=&grade_id=` | `{ decisions: [] }` | List lifecycle decisions |
| GET | `/decisions/{id}` | — | `LifecycleDecisionResponse` | Get decision by ID |

**Events consumed:** `ProductGraded`  
**Events produced:** `LifecycleDecisionCreated`

---

## Passport Service (port 8004) — Owner: A

**Purpose:** Digital product passport (grade history, ownership, refurb, sustainability).

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/passports` | Query: `?product_id=&return_id=` | `{ passports: [] }` | List passports |
| GET | `/passports/{id}` | — | `PassportResponse + timeline` | Get passport with full history |
| GET | `/products/{id}` | — | `ProductResponse` | **Canonical Product source** — called by other services |

**Events consumed:** `ProductGraded`, `LifecycleDecisionCreated`, `MatchFound`, `PurchaseCompleted`  
**Events produced:** `PassportCreated`, `HyperlocalMatchRequested`

---

## Matching Service (port 8005) — Owner: B

**Purpose:** Hyperlocal buyer matching + marketplace listing.

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/matches` | Query: `?return_id=&product_id=` | `{ matches: [] }` | List matches for a return |
| GET | `/matches/{id}` | — | `MatchResponse` | Get match by ID |
| GET | `/listings` | Query: `?channel=&status=&category=&limit=&offset=` | `PaginatedResponse + listings[]` | Marketplace listings |
| GET | `/listings/{id}` | — | `ListingResponse` | Get listing by ID |

**Events consumed:** `HyperlocalMatchRequested`, `PurchaseCompleted`  
**Events produced:** `MatchFound`, `NoMatchFound`, `ProductListed`

---

## Sustainability Service (port 8006) — Owner: B

**Purpose:** CO₂ avoided, waste diverted, value recovered, green credits, dashboard metrics.

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/sustainability` | Query: `?return_id=&user_id=` | `{ records: [] }` | List sustainability records |
| GET | `/sustainability/{id}` | — | `SustainabilityRecordResponse` | Get record by ID |
| GET | `/sustainability/metrics` | Query: `?user_id=` | `{ totals: {...}, breakdown: [] }` | Aggregated metrics for dashboard |

**Events consumed:** `MatchFound`, `NoMatchFound`, `ProductListed`, `PurchaseCompleted`  
**Events produced:** `SustainabilityUpdated`

---

## Cross-Service Call Patterns

### 1. Matching → User: Find nearby buyers

```
GET /users/candidates?category=Electronics&lat=37.7749&lng=-122.4194&radius_km=50
→ UserCandidatesListResponse
```

### 2. Gateway creates Return (owns the table)

```
POST /returns { product_id, reason, media_urls }
→ ReturnResponse
→ Emits ReturnSubmitted event
```

### 3. Passport owns canonical Product

```
GET /products/{id}
→ ProductResponse (owned by Passport Service)
```

---

## OpenAPI / Swagger

Each service serves its OpenAPI schema at:

```
GET /<service>/openapi.json
```

The Gateway aggregates the public surface at:

```
GET /openapi.json
```

---

## Notes

- **JWT verification:** Gateway verifies JWT and forwards `X-User-Id` header to services.
- **Correlation ID:** `X-Correlation-Id` is propagated on all requests (generated if missing).
- **Error envelope:** All errors return `{ error: { code, message, correlation_id } }`.
- **Pagination:** Standard `?limit=&offset=` query params; response includes `total`, `limit`, `offset`.
- **Timestamps:** All timestamps are ISO-8601 UTC strings.
- **IDs:** All entity IDs are UUID v4 strings.
