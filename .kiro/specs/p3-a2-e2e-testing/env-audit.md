# Environment Variables Audit — Amazon Second Life AI

**Task**: P3-A2 Task 3.1  
**Date**: 2026-06-14  
**Purpose**: Complete inventory of all environment variables used across services

---

## Audit Methodology

1. ✅ Grepped all services for `os.getenv` calls
2. ✅ Examined all `Settings` class definitions (BaseServiceSettings + service-specific)
3. ✅ Reviewed Alembic migration scripts
4. ✅ Checked scripts (seed.py, seed_min.py, smoke_test.py, events_tail.py)
5. ✅ Reviewed docker-compose.yml for environment overrides
6. ✅ Checked frontend (Next.js) for process.env usage

---

## Complete Environment Variable Inventory

### 1. AI Configuration

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `AI_MODE` | BaseServiceSettings (all services), shared_py.ai.client | Optional | `mock` | Values: `mock`, `aws`, `hybrid`. Mock mode requires no AWS credentials. |
| `AWS_REGION` | BaseServiceSettings, shared_py.ai.client | Optional | `us-east-1` | Required only when AI_MODE=aws or hybrid |
| `AWS_ACCESS_KEY_ID` | BaseServiceSettings | Optional | `""` (empty) | Required only when AI_MODE=aws or hybrid |
| `AWS_SECRET_ACCESS_KEY` | BaseServiceSettings | Optional | `""` (empty) | Required only when AI_MODE=aws or hybrid |
| `BEDROCK_MODEL_ID` | BaseServiceSettings, shared_py.ai.client | Optional | `anthropic.claude-3-haiku-20240307-v1:0` | Claude model for Bedrock reasoning |

### 2. Authentication & Security

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `JWT_SECRET` | User Service, Gateway | **Required** | `change-me-in-production-use-a-long-random-string` | MUST be identical for user service and gateway. Use long random string in production. |
| `JWT_ALGORITHM` | User Service, Gateway | Optional | `HS256` | Algorithm for JWT signing |
| `JWT_EXPIRE_MINUTES` | User Service | Optional | `1440` (24 hours) | Token expiration time |

### 3. Database Configuration

#### Postgres Infrastructure
| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `POSTGRES_HOST` | docker-compose.yml (metadata) | Optional | `localhost` | Not directly used by services (baked into DATABASE_URL_*) |
| `POSTGRES_PORT` | docker-compose.yml (metadata) | Optional | `5432` | Not directly used by services |
| `POSTGRES_USER` | docker-compose.yml, docker-compose postgres service | Optional | `slmai` | Postgres superuser |
| `POSTGRES_PASSWORD` | docker-compose.yml, docker-compose postgres service | Optional | `slmai_password` | Postgres superuser password |

#### Service Database URLs
Each service reads its database URL from `DATABASE_URL` env var (or service-specific `DATABASE_URL_*` for scripts):

| Variable | Used By | Required | Default | Format |
|----------|---------|----------|---------|--------|
| `DATABASE_URL` | Alembic env.py (all services) | **Required** | Varies per service | `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE` |
| `DATABASE_URL_GATEWAY` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_gateway` | Gateway service database (owns Return table) |
| `DATABASE_URL_USER` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_user` | User service database |
| `DATABASE_URL_GRADING` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_grading` | Grading service database |
| `DATABASE_URL_LIFECYCLE` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_lifecycle` | Lifecycle service database |
| `DATABASE_URL_PASSPORT` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_passport` | Passport service database |
| `DATABASE_URL_MATCHING` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_matching` | Matching service database |
| `DATABASE_URL_SUSTAINABILITY` | scripts/seed_min.py | Optional | `postgresql+asyncpg://slmai:slmai_password@localhost:5432/slmai_sustainability` | Sustainability service database |

**Note**: Services read `database_url` field from their Settings class. Scripts use `DATABASE_URL_*` naming. docker-compose.yml overrides with `DATABASE_URL` env var per service.

### 4. Event Bus (Redis)

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `REDIS_URL` | BaseServiceSettings (all services), scripts/events_tail.py, Gateway debug routes | **Required** | `redis://redis:6379/0` (Docker) or `redis://localhost:6379/0` (local) | Redis Streams for event choreography |

### 5. Object Storage (MinIO / S3)

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `S3_ENDPOINT_URL` | Gateway, Grading, shared_py.ai.client, scripts/seed_min.py | **Required** | `http://minio:9000` (Docker) or `http://localhost:9000` (local) | MinIO API endpoint |
| `S3_ACCESS_KEY` | Gateway, Grading, scripts/seed_min.py | **Required** | `minioadmin` | MinIO access key |
| `S3_SECRET_KEY` | Gateway, Grading, scripts/seed_min.py | **Required** | `minioadmin` | MinIO secret key |
| `S3_BUCKET` | Gateway, Grading, shared_py.ai.client, scripts/seed_min.py | **Required** | `slmai-media` | Bucket name for product images/videos |
| `S3_REGION` | Gateway | Optional | `us-east-1` | S3 region (for signature calculation) |

### 6. Service URLs (Gateway Routing)

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `USER_SERVICE_URL` | Gateway, Passport, Matching | **Required** | `http://user:8001` (Docker) or `http://localhost:8001` (local) | User service endpoint |
| `GRADING_SERVICE_URL` | Gateway, scripts/seed.py | **Required** | `http://grading:8002` (Docker) or `http://localhost:8002` (local) | Grading service endpoint |
| `LIFECYCLE_SERVICE_URL` | Gateway, scripts/seed.py | **Required** | `http://lifecycle:8003` (Docker) or `http://localhost:8003` (local) | Lifecycle service endpoint |
| `PASSPORT_SERVICE_URL` | Gateway, scripts/seed.py | **Required** | `http://passport:8004` (Docker) or `http://localhost:8004` (local) | Passport service endpoint |
| `MATCHING_SERVICE_URL` | Gateway, scripts/seed.py | **Required** | `http://matching:8005` (Docker) or `http://localhost:8005` (local) | Matching service endpoint |
| `SUSTAINABILITY_SERVICE_URL` | Gateway, scripts/seed.py | **Required** | `http://sustainability:8006` (Docker) or `http://localhost:8006` (local) | Sustainability service endpoint |

### 7. CORS Configuration

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `CORS_ORIGINS` | Gateway (BaseServiceSettings.cors_origins) | Optional | `http://localhost:3000` | Comma-separated list of allowed origins |

### 8. Frontend Configuration

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | apps/web/src/lib/api-client.ts | Optional | `http://localhost:8000` | Gateway API endpoint (exposed to browser) |
| `NEXT_PUBLIC_USE_MOCKS` | apps/web/src/lib/api-client.ts | Optional | `true` (not false) | Whether to use mock data in frontend |

### 9. Observability & Development

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `SERVICE_NAME` | BaseServiceSettings (each service) | Optional | Service-specific default | Service identity for logging |
| `LOG_LEVEL` | BaseServiceSettings (all services) | Optional | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

### 10. Matching Service Configuration

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `MATCH_RADIUS_KM` | Matching Service | Optional | `50.0` | Hyperlocal matching radius in kilometers |
| `MATCH_SCORE_THRESHOLD` | Matching Service | Optional | `0.4` | Minimum score for a match to be considered valid |

### 11. Script-Specific Variables

| Variable | Used By | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| `GATEWAY_URL` | scripts/smoke_test.py, scripts/seed.py | Optional | `http://localhost:8000` | Gateway base URL for scripts |
| `SERVICE_GATEWAY_URL` | scripts/smoke_test.py | Optional | `http://localhost:8000` | Direct gateway health check URL |
| `SERVICE_USER_URL` | scripts/smoke_test.py | Optional | `http://localhost:8001` | Direct user service health check URL |
| `SERVICE_GRADING_URL` | scripts/smoke_test.py | Optional | `http://localhost:8002` | Direct grading service health check URL |
| `SERVICE_LIFECYCLE_URL` | scripts/smoke_test.py | Optional | `http://localhost:8003` | Direct lifecycle service health check URL |
| `SERVICE_PASSPORT_URL` | scripts/smoke_test.py | Optional | `http://localhost:8004` | Direct passport service health check URL |
| `SERVICE_MATCHING_URL` | scripts/smoke_test.py | Optional | `http://localhost:8005` | Direct matching service health check URL |
| `SERVICE_SUSTAINABILITY_URL` | scripts/smoke_test.py | Optional | `http://localhost:8006` | Direct sustainability service health check URL |

---

## Summary by Service

### Gateway
- `database_url` (Settings)
- `jwt_secret`, `jwt_algorithm` (Settings)
- `user_service_url`, `grading_service_url`, `lifecycle_service_url`, `passport_service_url`, `matching_service_url`, `sustainability_service_url` (Settings)
- `s3_endpoint_url`, `s3_access_key`, `s3_secret_key`, `s3_bucket`, `s3_region` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### User Service
- `database_url` (Settings)
- `jwt_secret`, `jwt_algorithm`, `jwt_expire_minutes` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### Grading Service
- `database_url` (Settings)
- `s3_endpoint_url`, `s3_access_key`, `s3_secret_key`, `s3_bucket` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### Lifecycle Service
- `database_url` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### Passport Service
- `database_url` (Settings)
- `user_service_url` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### Matching Service
- `database_url` (Settings)
- `user_service_url` (Settings)
- `match_radius_km`, `match_score_threshold` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

### Sustainability Service
- `database_url` (Settings)
- `redis_url`, `ai_mode`, `cors_origins`, `service_name`, `log_level` (BaseServiceSettings)
- `aws_region`, `aws_access_key_id`, `aws_secret_access_key`, `bedrock_model_id` (BaseServiceSettings)

---

## Analysis: `.env.example` Completeness

### ✅ Already Documented in `.env.example`
- AI_MODE, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BEDROCK_MODEL_ID
- JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
- POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD
- DATABASE_URL_GATEWAY, DATABASE_URL_USER, DATABASE_URL_GRADING, DATABASE_URL_LIFECYCLE, DATABASE_URL_PASSPORT, DATABASE_URL_MATCHING, DATABASE_URL_SUSTAINABILITY
- REDIS_URL
- S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, S3_REGION
- USER_SERVICE_URL, GRADING_SERVICE_URL, LIFECYCLE_SERVICE_URL, PASSPORT_SERVICE_URL, MATCHING_SERVICE_URL, SUSTAINABILITY_SERVICE_URL
- CORS_ORIGINS
- NEXT_PUBLIC_API_BASE_URL

### ❌ Missing from `.env.example`
1. `SERVICE_NAME` — Used by BaseServiceSettings (optional, has defaults per service)
2. `LOG_LEVEL` — Used by BaseServiceSettings (optional, default: INFO)
3. `MATCH_RADIUS_KM` — Used by Matching Service (optional, default: 50.0)
4. `MATCH_SCORE_THRESHOLD` — Used by Matching Service (optional, default: 0.4)
5. `NEXT_PUBLIC_USE_MOCKS` — Used by frontend api-client (optional, default: true)
6. Script-specific URLs (`GATEWAY_URL`, `SERVICE_*_URL`) — Used by smoke_test.py and seed.py (optional, have defaults)

### 🔧 Recommendations

**HIGH PRIORITY — Add to `.env.example`:**
1. `LOG_LEVEL` — Common dev/production tuning knob
2. `MATCH_RADIUS_KM` — Matching business logic parameter
3. `MATCH_SCORE_THRESHOLD` — Matching business logic parameter
4. `NEXT_PUBLIC_USE_MOCKS` — Important for frontend development workflow

**MEDIUM PRIORITY — Consider adding:**
5. `SERVICE_NAME` — Useful for multi-instance deployments or observability
6. Script URLs (`GATEWAY_URL`, `SERVICE_*_URL`) — Useful if running scripts against non-default environments

**LOW PRIORITY — Can omit:**
- Individual service DATABASE_URL override (docker-compose.yml sets these explicitly)
- POSTGRES_HOST, POSTGRES_PORT — Metadata only, not directly consumed

---

## Validation

### Environment Variable Naming Conventions
✅ All Settings class fields use `snake_case`  
✅ Pydantic automatically maps from UPPER_CASE env vars  
✅ Example: `database_url` field reads from `DATABASE_URL` env var

### Docker vs Local Development
- **Docker Compose**: Uses service hostnames (`postgres`, `redis`, `minio`, `user`, etc.)
- **Local Dev**: Uses `localhost` for all services
- Both modes supported via `.env` configuration

### Required vs Optional
- **Truly Required** (services won't start without): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` (for Gateway/User)
- **Required for Feature** (services start but features fail): `S3_*` vars for media upload/grading
- **Optional with Defaults**: All others have sensible defaults

---

**Status**: Audit Complete  
**Next**: Update `.env.example` with missing variables (Task 3.2+)
