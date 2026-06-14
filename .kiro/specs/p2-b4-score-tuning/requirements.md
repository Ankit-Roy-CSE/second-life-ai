# Requirements Document

## Introduction

P2-B4 is the final AI-layer tuning task for Member B in the Amazon Second Life AI platform.
The goal is to make the value-recovery estimates and sustainability scores shown to judges
realistic, consistent, and defensible by:

1. Routing the real product price through the event saga so the Lifecycle Service no longer
   uses a hardcoded `value_estimate=100.0`.
2. Refining the mock decision table (`mock_decide_lifecycle`) with category-differentiated
   sustainability scores and tighter value-recovery multipliers.
3. Locking the golden-path demo constants so that `GOLDEN_PATH_VALUE_ESTIMATE=120.00`
   → Grade B → RESELL → `value_recovery=72.00` → `sustainability_score=80.0` always holds.
4. Adding or updating tests to cover the tuned values and the new event field.

All changes must be backward-compatible: no breaking changes to the `LifecycleDecision`
Pydantic schema, `AI_MODE=mock` must remain keyless, and existing consumers of
`ProductGraded` that omit `original_price_usd` must continue to work.

---

## Glossary

- **Lifecycle_Service**: The FastAPI microservice at `services/lifecycle/` that consumes
  `ProductGraded` events, calls the AI wrapper, and emits `LifecycleDecisionCreated`.
- **Mock_Client**: The deterministic AI stub in
  `packages/shared-py/shared_py/ai/mock.py`, active when `AI_MODE=mock`.
- **ProductGradedEventData**: The Pydantic model in
  `packages/shared-py/shared_py/events/schemas.py` that defines the payload of the
  `ProductGraded` Redis Streams event.
- **LifecycleDecision**: The Pydantic response model in
  `packages/shared-py/shared_py/ai/schemas.py` returned by `decide_lifecycle`.
- **value_estimate**: The USD price passed to `ai_client.decide_lifecycle()` and used by
  `mock_decide_lifecycle` to compute `value_recovery_estimate`.
- **value_recovery_estimate**: The estimated USD amount the platform can recover from a
  returned product; calculated as `value_estimate × grade_multiplier`.
- **sustainability_score**: A 0–100 score representing the environmental benefit of the
  chosen lifecycle action; stored in the `LifecycleDecision` record.
- **Golden_Path_Test**: A pinned regression test that asserts the exact chain
  `GOLDEN_PATH_VALUE_ESTIMATE=120.00` → Grade B → RESELL →
  `value_recovery=72.00` → `sustainability_score=80.0`.
- **original_price_usd**: The catalogue or purchase price of the product in USD, sourced
  from the product record and propagated via the `ProductGraded` event payload.
- **Lifecycle_Handler**: The event handler in
  `services/lifecycle/app/events/handlers.py` that consumes `ProductGraded` and invokes
  `LifecycleService.decide_lifecycle`.
- **Grade**: One of `A`, `B`, `C`, `D` representing product condition from best to worst.

---

## Requirements

---

### Requirement 1: Propagate Real Product Price via the `ProductGraded` Event

**User Story:** As a lifecycle decision engine, I want to receive the product's actual
purchase price alongside the grade, so that value-recovery estimates are based on real
product data rather than a hardcoded default.

#### Acceptance Criteria

1. THE `ProductGradedEventData` SHALL include an `original_price_usd` field of type
   `float | None` with a default of `None`, so that existing consumers that do not supply
   the field remain valid.

2. WHEN the Grading Service emits a `ProductGraded` event and the product's
   `original_price_usd` is known, THE Grading_Service SHALL populate
   `original_price_usd` in the `ProductGradedEventData` payload with that value.

3. IF a `ProductGraded` event is received by the `Lifecycle_Handler` with
   `original_price_usd` equal to `None` or absent, THEN THE `Lifecycle_Handler` SHALL
   use a fallback `value_estimate` of `100.0` USD.

4. WHEN a `ProductGraded` event is received by the `Lifecycle_Handler` with a non-`None`
   `original_price_usd`, THE `Lifecycle_Handler` SHALL pass that value as
   `value_estimate` to `LifecycleService.decide_lifecycle`.

5. THE `LifecycleDecision` Pydantic schema in `shared_py/ai/schemas.py` SHALL remain
   unchanged — no fields added, removed, or renamed — so that downstream consumers of
   `LifecycleDecisionCreated` require no migration.

---

### Requirement 2: Refine Mock Decision Table with Category-Differentiated Scores

**User Story:** As a demo presenter, I want the mock AI to produce sustainability scores
that reflect the product category and lifecycle action rather than flat per-grade constants,
so that the numbers shown to judges are defensible and internally consistent.

#### Acceptance Criteria

1. THE `Mock_Client` SHALL compute `sustainability_score` using a lookup table that
   varies by both `grade` and `product_category`, replacing the current
   grade-only flat scores.

2. WHEN `mock_decide_lifecycle` is called with `grade=Grade.A`, THE `Mock_Client`
   SHALL return a `sustainability_score` in the range `[82.0, 92.0]` for any
   supported `product_category`.

3. WHEN `mock_decide_lifecycle` is called with `grade=Grade.B` and the chosen
   action is `RESELL`, THE `Mock_Client` SHALL return a `sustainability_score` of
   exactly `80.0` for `product_category="electronics"`, preserving the golden-path
   constant.

4. WHEN `mock_decide_lifecycle` is called with `grade=Grade.C`, THE `Mock_Client`
   SHALL return a `sustainability_score` in the range `[60.0, 74.0]` for any
   supported `product_category`.

5. WHEN `mock_decide_lifecycle` is called with `grade=Grade.D`, THE `Mock_Client`
   SHALL return a `sustainability_score` in the range `[45.0, 60.0]` for any
   supported `product_category`.

6. FOR ALL combinations of `grade` in `{A, B, C, D}` and `product_category` in
   `{"electronics", "clothing", "furniture", "toys", "appliances", "books"}`,
   THE `Mock_Client` SHALL return a `sustainability_score` in the range `[0.0, 100.0]`.

7. WHEN the hyperlocal override fires (seed-based `grade in {A, B}` branch), THE
   `Mock_Client` SHALL apply the category-differentiated base score before adding the
   hyperlocal bonus, and SHALL cap the final `sustainability_score` at `100.0`.

---

### Requirement 3: Tighten Value-Recovery Multipliers

**User Story:** As a demo presenter, I want value-recovery estimates to be derived
from the product's real price using consistent per-grade multipliers, so that the
financial numbers are proportional and realistic across the demo narrative.

#### Acceptance Criteria

1. THE `Mock_Client` SHALL apply the following value-recovery multipliers when
   `mock_decide_lifecycle` selects `action=RESELL`:
   - `Grade.A` → multiplier in the range `[0.72, 0.78]`
   - `Grade.B` → multiplier of exactly `0.60` (preserves
     `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY = 120.00 × 0.60 = 72.00`)

2. THE `Mock_Client` SHALL apply the following value-recovery multipliers when
   `mock_decide_lifecycle` selects `action=REFURBISH`:
   - `Grade.B` (low-value branch) → multiplier in the range `[0.45, 0.55]`
   - `Grade.C` (high-value branch) → multiplier in the range `[0.35, 0.45]`

3. WHEN `mock_decide_lifecycle` selects `action=DONATE` or `action=RECYCLE`,
   THE `Mock_Client` SHALL apply a multiplier in the range `[0.03, 0.10]` to produce
   a non-zero but low `value_recovery_estimate`.

4. FOR ALL `grade` values and a given positive `value_estimate`, THE `Mock_Client`
   SHALL produce a `value_recovery_estimate` that satisfies
   `0.0 < value_recovery_estimate <= value_estimate`.

5. WHEN `value_estimate` is `0.0`, THE `Mock_Client` SHALL return
   `value_recovery_estimate = 0.0` without raising an exception.

---

### Requirement 4: Preserve Golden-Path Demo Constants

**User Story:** As a demo engineer, I want the golden-path constants in `client.py` to
match the actual mock output exactly, so that the seed script, integration tests, and
live demo all produce the same numbers without manual patching.

#### Acceptance Criteria

1. WHEN `mock_decide_lifecycle` is called with `grade=Grade.B`,
   `product_category="electronics"`, and `value_estimate=120.00`, THE `Mock_Client`
   SHALL return `action=RESELL`, `value_recovery_estimate=72.00`, and
   `sustainability_score=80.0` — matching `GOLDEN_PATH_EXPECTED_ACTION`,
   `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY`, and `GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE`
   defined in `client.py`.

2. THE `client.py` constants `GOLDEN_PATH_VALUE_ESTIMATE`, `GOLDEN_PATH_EXPECTED_GRADE`,
   `GOLDEN_PATH_EXPECTED_ACTION`, `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY`, and
   `GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE` SHALL remain syntactically present and
   semantically correct after any changes to `mock.py` or `client.py`.

3. THE Golden_Path_Test in the test suite SHALL assert all five golden-path output
   fields — `action`, `value_recovery_estimate`, `sustainability_score`, `confidence`,
   and that `rationale` is a non-empty string — for the golden-path inputs.

---

### Requirement 5: Test Coverage for Tuned Values

**User Story:** As a developer, I want automated tests that verify the tuned mock values
and the new event-schema field, so that any accidental regression in the demo numbers
is caught before the judges see it.

#### Acceptance Criteria

1. THE test suite in `packages/shared-py/tests/` SHALL include a property-based test
   that, for all `grade` in `{A, B, C, D}`, all `product_category` in
   `{"electronics", "clothing", "furniture", "toys", "appliances", "books"}`, and
   `value_estimate` in `(0.0, 10000.0]`, asserts that `mock_decide_lifecycle` returns a
   `LifecycleDecision` where `sustainability_score` is in `[0.0, 100.0]` and
   `0.0 <= value_recovery_estimate <= value_estimate`.

2. THE test suite SHALL include a test that deserializes a `ProductGraded` event payload
   that omits the `original_price_usd` field and asserts that
   `ProductGradedEventData.model_validate(payload).original_price_usd is None`.

3. THE test suite SHALL include a test that asserts the `Lifecycle_Handler` uses
   `value_estimate=100.0` when `original_price_usd` is `None` in the
   `ProductGradedEventData`.

4. THE test suite SHALL include the exact Golden_Path_Test described in Requirement 4
   AC 3, asserting `value_recovery_estimate == 72.00` and
   `sustainability_score == 80.0` (to two decimal places).

5. WHEN the test suite is run with `AI_MODE=mock` and no AWS credentials set, THE
   test suite SHALL pass all tests defined in this requirement without network access
   or AWS SDK initialization.

---

### Requirement 6: Backward-Compatible Event Schema Change

**User Story:** As a platform architect, I want the addition of `original_price_usd` to
`ProductGradedEventData` to be backward-compatible, so that existing event consumers
(passport service, any future replayed events) continue to work without schema migration.

#### Acceptance Criteria

1. THE `ProductGradedEventData` model SHALL use `original_price_usd: float | None =
   Field(default=None, ...)` so that Pydantic `model_validate` succeeds on any existing
   event dict that lacks the key.

2. WHEN the `Lifecycle_Handler` reads `data.original_price_usd` and the value is a
   positive float, THE `Lifecycle_Handler` SHALL use that float as `value_estimate`.

3. WHEN the `Lifecycle_Handler` reads `data.original_price_usd` and the value is `None`,
   zero, or negative, THE `Lifecycle_Handler` SHALL substitute `value_estimate=100.0` as
   the safe fallback.

4. THE `event_version` field in `EventEnvelope` for `ProductGraded` events emitted after
   this change SHALL remain `"1.0"` because the schema change is additive and
   backward-compatible.

5. THE passport service and any other existing consumers of `ProductGraded` events SHALL
   continue to function without code changes, because `original_price_usd` is an
   optional field they do not read.
