# User Service — Amazon Second Life AI

**Owner:** Member A (Full-Stack)  
**Port:** 8001  
**Database:** `slmai_user` (PostgreSQL)

## Responsibility

The User Service handles:
- **Authentication:** User registration, login, JWT issuance (HS256)
- **Profile Management:** User profiles, preferences, location
- **Green Credits:** Sustainability credit balance tracking
- **Cross-Service:** Candidate buyer matching for the Matching service

## API Endpoints

### Auth Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user account |
| POST | `/auth/login` | Login and get JWT access token |

### User Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/{id}` | Get user profile by ID |
| PATCH | `/users/{id}` | Update user profile |
| GET | `/users/{id}/credits` | Get green credit balance |

### Cross-Service Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/candidates` | Find candidate buyers (called by Matching service) |

## Data Model

**User Entity:**
```python
{
    "id": "uuid-string",
    "email": "user@example.com",
    "password_hash": "bcrypt-hash",  # Never returned in API
    "display_name": "User Name",
    "location": {"lat": 12.97, "lng": 77.59, "city": "Bengaluru"},
    "interests": ["Electronics", "Books"],
    "green_credits": 150.5,
    "created_at": "2026-06-13T10:00:00Z"
}
```

## Technology Stack

- **Framework:** FastAPI 0.115
- **ORM:** SQLAlchemy 2.0 (async with asyncpg)
- **Migrations:** Alembic 1.13
- **Auth:** JWT (python-jose), bcrypt password hashing (passlib)
- **Testing:** pytest, pytest-asyncio, httpx

## Setup & Development

### Install Dependencies

```bash
# From repository root
pip install -e "packages/shared-py[dev]"

# Or from this directory
cd services/user
pip install -e ".[dev]"
```

### Environment Variables

Required environment variables (see `.env.example` in repo root):

```bash
# Database
DATABASE_URL_USER=postgresql+asyncpg://slmai:slmai_password@postgres:5432/slmai_user

# JWT Settings
JWT_SECRET=change-me-in-production-use-a-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Run Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "description"
```

### Run Service Locally

```bash
# With uvicorn (development)
uvicorn app.main:app --reload --port 8001

# Or via Docker Compose (recommended)
docker compose up user
```

The service will be available at: `http://localhost:8001`

API documentation: `http://localhost:8001/docs` (Swagger UI)

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

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

### Password Security

- Passwords are hashed using bcrypt (via passlib)
- Password hashes are never returned in API responses
- Minimum password length: 8 characters

### JWT Authentication

- Tokens are issued by this service
- Gateway verifies tokens and forwards `X-User-Id` header
- Token lifetime: 24 hours (configurable)
- Algorithm: HS256 with shared secret

### Candidate Matching

The `/users/candidates` endpoint supports hyperlocal buyer matching:

**Query Parameters:**
- `category`: Filter by product category in user interests
- `lat`, `lng`: Product location coordinates
- `radius_km`: Maximum distance from product location

**Example:**
```bash
GET /users/candidates?category=Electronics&lat=12.97&lng=77.59&radius_km=50
```

**Distance Calculation:**
- Uses Haversine formula for lat/lng distance
- Results sorted by distance (closest first)
- Simplified implementation (production would use PostGIS)

## File Structure

```
services/user/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Service settings
│   ├── api/
│   │   └── routes.py        # FastAPI routes (thin layer)
│   ├── domain/
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response DTOs
│   │   └── service.py       # Business logic (no FastAPI imports)
│   └── db/
│       ├── session.py       # Async session management
│       └── repository.py    # Data access layer (CRUD)
├── alembic/
│   ├── env.py               # Alembic environment
│   ├── script.py.mako       # Migration template
│   └── versions/
│       └── 001_create_users_table.py
├── tests/
│   ├── conftest.py          # Test configuration
│   ├── test_auth.py         # Auth endpoint tests
│   └── test_users.py        # User endpoint tests
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Container image
├── pyproject.toml           # Python package config
└── README.md                # This file
```

## Architecture Notes

### Layered Structure

The service follows a clean layered architecture:

1. **API Layer** (`api/routes.py`): Thin routes that validate input and call services
2. **Service Layer** (`domain/service.py`): Business logic, no FastAPI dependencies
3. **Repository Layer** (`db/repository.py`): Data access, returns ORM objects
4. **Model Layer** (`domain/models.py`): SQLAlchemy ORM definitions

**Dependency Direction:** `routes → service → repository → models`

### Contract-First Approach

All API contracts are defined in:
- `packages/shared-py/shared_py/schemas/SERVICE_ENDPOINTS.md` (REST endpoints)
- `packages/shared-py/shared_py/schemas/rest_contracts.py` (cross-service DTOs)

Services build against these contracts, not implementations.

### Cross-Service Communication

- Other services call User Service endpoints directly (server-to-server)
- No database access across services
- Example: Matching service calls `GET /users/candidates`

## Testing

Test coverage includes:

**Auth Tests** (`test_auth.py`):
- ✓ Successful registration
- ✓ Duplicate email handling (409)
- ✓ Successful login with JWT
- ✓ Invalid email (401)
- ✓ Invalid password (401)

**User Tests** (`test_users.py`):
- ✓ Get user profile
- ✓ User not found (404)
- ✓ Update user profile
- ✓ Get green credits
- ✓ Find candidates by category
- ✓ Find candidates with distance calculation

## Next Steps

After P1-A1 completion:
- **P1-A2:** API Gateway will proxy auth endpoints to this service
- **P2-B1:** Matching service will call `/users/candidates` for buyer matching
- **P3:** Sustainability service will update `green_credits` via events

## Troubleshooting

**Database connection fails:**
- Ensure PostgreSQL is running: `docker compose up postgres`
- Check `DATABASE_URL_USER` environment variable
- Verify database `slmai_user` exists

**JWT verification fails:**
- Ensure `JWT_SECRET` matches across User Service and Gateway
- Check token hasn't expired (default: 24h)

**Tests fail:**
- Ensure all dependencies installed: `pip install -e ".[dev]"`
- Run from service directory: `cd services/user`
- Tests use in-memory SQLite, no external dependencies needed

## Status

✅ **Complete** — P1-A1 (Phase 1, Task A1)

All endpoints implemented, tested, and ready for integration with Gateway.
