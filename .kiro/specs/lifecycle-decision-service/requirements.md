# Requirements Document

## Introduction

The Lifecycle Decision Service (P1-B2) is a FastAPI microservice that determines the optimal "second life" action for each returned product after it has been graded by the AI Grading Service. It consumes `ProductGraded` events, calls the AI decision engine, persists decisions, and emits `LifecycleDecisionCreated` events to drive the downstream saga (passport, matching).

## Glossary

- **Lifecycle_Service**: The Lifecycle Decision Service microservice running at port 8003
- **LifecycleDecision**: The persisted domain entity storing the AI-determined lifecycle action for a returned product
- **LifecycleAction**: Enum of possible actions: RESELL, REFURBISH, DONATE, RECYCLE, HYPERLOCAL
- **ProductGraded_Event**: Event emitted by the grading service after AI grading completes
- **LifecycleDecisionCreated_Event**: Event emitted by this service after a decision is persisted
- **AI_Client**: The shared AI wrapper (`shared_py.ai.ai_client`) used for lifecycle reasoning
- **Event_Consumer**: Background task that subscribes to Redis Streams for incoming events
- **Decision_Endpoint**: REST API endpoint exposing lifecycle decisions

## Requirements

### Requirement 1: Event Consumption

**User Story:** As the platform saga, I want the Lifecycle Service to consume ProductGraded events, so that lifecycle decisions are triggered automatically after grading.

#### Acceptance Criteria

1. WHEN a `ProductGraded` event is received, THE Lifecycle_Service SHALL extract the return_id, grade_id, and grade from the event payload
2. WHEN the Lifecycle_Service starts, THE Event_Consumer SHALL subscribe to the `slmai:events` Redis stream with consumer group `lifecycle`
3. WHEN the Lifecycle_Service shuts down, THE Event_Consumer SHALL stop gracefully without losing unacknowledged messages

### Requirement 2: AI Lifecycle Decision

**User Story:** As the platform, I want the service to call the AI decision engine, so that each returned product gets an optimal next-life action.

#### Acceptance Criteria

1. WHEN a `ProductGraded` event is processed, THE Lifecycle_Service SHALL call `ai_client.decide_lifecycle` with the grade, product_category, and value_estimate
2. THE Lifecycle_Service SHALL persist a LifecycleDecision record containing id, return_id, grade_id, action, rationale, value_recovery_estimate, sustainability_score, and created_at
3. WHILE `AI_MODE=mock` is configured, THE AI_Client SHALL return deterministic decisions without requiring AWS credentials

### Requirement 3: Idempotent Event Handling

**User Story:** As the platform, I want event handling to be idempotent, so that duplicate events do not create duplicate decisions.

#### Acceptance Criteria

1. WHEN a `ProductGraded` event is received for a return_id that already has a LifecycleDecision, THE Lifecycle_Service SHALL skip processing and return the existing decision
2. THE Lifecycle_Service SHALL enforce a unique constraint on the return_id column of the lifecycle_decisions table

### Requirement 4: Event Emission

**User Story:** As downstream services (passport, matching), I want the Lifecycle Service to emit a LifecycleDecisionCreated event, so that the saga continues.

#### Acceptance Criteria

1. WHEN a LifecycleDecision is successfully persisted, THE Lifecycle_Service SHALL emit a `LifecycleDecisionCreated` event to the Redis stream
2. THE LifecycleDecisionCreated_Event SHALL include return_id, decision_id, grade_id, action, rationale, value_recovery_estimate, and sustainability_score in its payload
3. THE LifecycleDecisionCreated_Event SHALL carry the same correlation_id as the triggering ProductGraded event

### Requirement 5: REST API Endpoints

**User Story:** As the API Gateway and admin users, I want REST endpoints to query lifecycle decisions, so that decision data is accessible for the UI and debugging.

#### Acceptance Criteria

1. WHEN a GET request is made to `/decisions/{return_id}`, THE Decision_Endpoint SHALL return the LifecycleDecision for that return_id with HTTP 200
2. IF no LifecycleDecision exists for the given return_id, THEN THE Decision_Endpoint SHALL return HTTP 404 with an error message
3. WHEN a GET request is made to `/decisions`, THE Decision_Endpoint SHALL return a paginated list of all decisions with total count
4. THE Decision_Endpoint SHALL accept `limit` (1–100, default 20) and `offset` (≥0, default 0) query parameters for pagination

### Requirement 6: Database Ownership

**User Story:** As the platform architect, I want the service to own its own database, so that service boundaries are maintained.

#### Acceptance Criteria

1. THE Lifecycle_Service SHALL use the `slmai_lifecycle` PostgreSQL database exclusively
2. THE Lifecycle_Service SHALL manage schema migrations via Alembic
3. THE Lifecycle_Service SHALL expose a readiness check at GET /ready that verifies database connectivity

### Requirement 7: Service Lifecycle

**User Story:** As the operations team, I want proper startup and shutdown handling, so that the service operates reliably.

#### Acceptance Criteria

1. WHEN the Lifecycle_Service starts, THE Lifecycle_Service SHALL initialize the database connection pool before accepting requests
2. WHEN the Lifecycle_Service shuts down, THE Lifecycle_Service SHALL dispose the database engine and cancel the event consumer task
3. THE Lifecycle_Service SHALL expose a health check at GET /health that returns HTTP 200
