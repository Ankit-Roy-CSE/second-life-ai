# Gateway Service — Amazon Second Life AI

**Owner:** Member A (Full-Stack)  
**Port:** 8000  
**Database:** `slmai_gateway` (PostgreSQL) — only the Return table

## Responsibility

The Gateway is the **single entry point** for the frontend (BFF pattern). It handles:
- **Auth Proxy:** Forwards registration and login to User Service
- **JWT Verification:** Verifies tokens, forwards `X-User-Id` to downstream services
- **Return Management:** Creates Return entities, emits `ReturnSubmitted` events
- **Data Aggregation:** Combines data from multiple services for frontend views
- **CORS:** Configured for frontend development

## API Endpoints

### Auth Endpoints (Proxy to User Service)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user (proxy to User:8001) |
| POST | `/auth/login` | Login and get JWT (proxy to User:8001) |

### Returns Endpoints (Gateway owns Return table)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/returns` | Create new return, emit ReturnSubmitted event |
| GET | `/returns` | List returns (paginated, filter by user_id/status) |
| GET | `/returns/{id}` | Get return details (BFF aggregation) |

### Debug Endpoints (P0-B3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/debug/events` | View recent events + DLQ |

## Data Model

**Return Entity (Gateway owns this table):**
```python
{
    "id": "uuid-string",  # Also the correlation_id for the saga
    "product_id": "uuid-string",
    "user_id": "uuid-string",
    "reason": "User-provided return reason",
    "media": ["media/img1.jpg", "media/img2.jpg"],  # S3 keys
    "status": "SUBMITTED",  # ReturnStatus enum
    "created_at": "2026-06-14T10:00:00Z"
}
```

## Technology Stack

- **Framework:** FastAPI 0.115
- **ORM:** SQLAlchemy 2.0 (async with asyncpg)
- **HTTP Client:** httpx (for calling User Service)
- **Object Storage:** MinIO/S3 (boto3) for media uploads
- **Events:** Redis Streams (via shared events wrapper)
- **Auth:** JWT verification (python-jose)
- **Testing:** pytest, pytest-asyncio, httpx

## Setup & Development

### Install Dependencies

```bash
# From repository root
pip install -e "packages/shared-py[dev]"
```

### Environment Variables

Required environment variables (see `.env.example` in repo root):

```bash
# JWT Settings (shared with User Service)
JWT_SECRET=change-me-in-production-use-a-long-random-string
JWT_ALGORITHM=HS256

# Upstream Service URLs
USER_SERVICE_URL=http://user:8001
GRADING_SERVICE_URL=http://grading:8002
LIFECYCLE_SERVICE_URL=http://lifecycle:8003
PASSPORT_SERVICE_URL=http://passport:8004
MATCHING_SERVICE_URL=http://matching:8005
SUSTAINABILITY_SERVICE_URL=http://sustainability:8006

# MinIO / S3
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=slmai-media
S3_REGION=us-east-1

# Redis (for events)
REDIS_URL=redis://redis:6379
```

### Run Service Locally

```bash
# With uvicorn (development)
uvicorn app.main:app --reload --port 8000

# Or via Docker Compose (recommended)
docker compose up gateway
```

The service will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs` (Swagger UI)

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_proxy.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Lint & Format

```bash
# Check code quality
ruff check app/

# Auto-fix issues
ruff check app/ --fix

# Format code
black app/ tests/
```

## Implementation Details

### Auth Proxy Pattern

Gateway proxies auth endpoints to User Service:

```
Frontend → Gateway:8000/auth/login → User:8001/auth/login → JWT
```

User Service issues the JWT. Gateway forwards it back to the frontend.

### JWT Verification

For protected endpoints, Gateway:
1. Extracts JWT from `Authorization: Bearer <token>` header
2. Verifies JWT signature with shared `JWT_SECRET`
3. Extracts `user_id` from JWT `sub` claim
4. Forwards `user_id` to route handlers

Downstream services trust the `X-User-Id` header from Gateway (internal network).

### Return Creation Flow

When POST /returns is called:

1. **Verify JWT** — Extract and verify user_id
2. **Create Return** — Insert into Gateway database
3. **Upload Media** — (Optional) Upload to MinIO, store S3 keys
4. **Emit Event** — Publish `ReturnSubmitted` to Redis Streams
5. **Return Response** — Return `ReturnResponse` to frontend

The `ReturnSubmitted` event starts the saga:
```
ReturnSubmitted → ProductGraded → LifecycleDecisionCreated → ...
```

### BFF Aggregation (Future)

`GET /returns/{id}` is designed as a BFF endpoint to aggregate:
- Return data (Gateway)
- Grade data (Grading Service)
- Decision data (Lifecycle Service)
- Passport data (Passport Service)
- Matches (Matching Service)

**P1-A2:** Only Return data is returned.  
**P2+:** Will call other services and aggregate.

### MinIO Integration

Gateway uploads media files to MinIO:
- Client uploads to Gateway (or Gateway fetches from presigned URLs)
- Gateway stores in MinIO bucket `slmai-media`
- S3 object keys stored in `Return.media[]`
- Keys follow pattern: `media/{uuid}.{ext}`

### CORS Configuration

Gateway allows CORS from frontend origins:
```python
allow_origins=["http://localhost:3000", "http://localhost:3001"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

## File Structure

```
services/gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point + lifespan
│   ├── config.py            # Service settings
│   ├── api/
│   │   ├── routes.py        # Main routes (auth proxy, returns)
│   │   ├── middleware.py    # JWT verification middleware
│   │   └── debug_routes.py  # Debug/observability (P0-B3)
│   ├── domain/
│   │   ├── models.py        # Return ORM model
│   │   └── schemas.py       # Pydantic DTOs
│   ├── db/
│   │   └── session.py       # Async session management
│   └── clients/
│       ├── http_client.py   # Upstream service HTTP client
│       └── minio_client.py  # MinIO/S3 client
├── tests/
│   ├── conftest.py          # Test configuration
│   ├── test_auth_proxy.py   # Auth proxy tests
│   └── test_returns.py      # Returns endpoint tests
├── Dockerfile               # Container image
├── pyproject.toml           # Python package config
└── README.md                # This file
```

## Architecture Notes

### Why Gateway Owns the Return Table

Per architecture.md §5, the Gateway creates the Return entity because:
- Return is the entry point of the saga
- Gateway is closest to the frontend (creates on user action)
- Return flows through all services, but is created once

Other services read Return via events (not database access).

### No Alembic Migrations

Gateway has minimal database needs (only Return table).  
Tables are created via SQLAlchemy metadata in lifespan for simplicity.

If schema changes are needed, migrations can be added later.

### Event-Driven Saga

After creating a Return, Gateway emits `ReturnSubmitted`:
```python
await publish(
    event_type="ReturnSubmitted",
    correlation_id=return.id,  # Return ID threads the saga
    data={
        "return_id": return.id,
        "product_id": return.product_id,
        "user_id": return.user_id,
        "reason": return.reason,
        "media": return.media,
    },
)
```

Grading Service consumes this event and starts processing.

## Testing

Test coverage includes:

**Auth Proxy Tests** (`test_auth_proxy.py`):
- ✓ Register proxy success
- ✓ Login proxy success
- ✓ Validation errors

**Returns Tests** (`test_returns.py`):
- ✓ Create return success (with auth, event emission)
- ✓ Create return without auth (401)
- ✓ List returns (empty, with data, with filters)
- ✓ Get return detail (success, not found)

## Integration Points

**Upstream (Gateway calls):**
- User Service: POST /auth/register, POST /auth/login
- (P2+) Grading, Lifecycle, Passport, Matching, Sustainability

**Downstream (calls Gateway):**
- Frontend: All API calls go through Gateway

**Events:**
- Produces: `ReturnSubmitted` (after POST /returns)
- Consumes: (P3+) `SustainabilityUpdated` for dashboard read-model

**Database:**
- Own DB: `slmai_gateway` with Return table
- No cross-service database access

## Next Steps

**Phase 2 (P2-A2):**
- Implement BFF aggregation in GET /returns/{id}
- Proxy endpoints for Passport, Matching, Sustainability
- Emit `PurchaseCompleted` event (demo button)

**Phase 3 (P3-A1):**
- Build dashboard read-model from `SustainabilityUpdated` events
- Implement GET /sustainability/dashboard aggregation

## Status

✅ **Complete** — P1-A2 (Phase 1, Task A2)

All endpoints implemented:
- Auth proxy to User Service (register, login)
- Returns endpoints (create, list, detail)
- JWT verification middleware
- Event emission (ReturnSubmitted)
- MinIO client (media upload support)
- 9 test cases

Gateway is ready for frontend integration and Phase 2 service integration.
