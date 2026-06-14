# Design Document

## P2-B4 — Decision & Score Tuning

---

## Overview

P2-B4 closes the last gap between the demo narrative and the data flowing through the event
saga. Three concerns are addressed together:

1. **Price propagation** — the `ProductGraded` event gains an optional `original_price_usd`
   field so the Lifecycle Service can use the real product price instead of a hardcoded `100.0`.
2. **Mock table tuning** — `mock_decide_lifecycle` is refactored to use a two-dimensional
   lookup (`grade × action`) for sustainability scores and explicit per-branch multipliers for
   value recovery, replacing ad-hoc flat constants.
3. **Golden-path lock** — the chain
   `GOLDEN_PATH_VALUE_ESTIMATE=120.00 → Grade B → RESELL → value_recovery=72.00 →
   sustainability_score=80.0` is hardened by a pinned regression test.

All changes are backward-compatible: the new schema field is optional, `AI_MODE=mock` requires
no AWS credentials, and no existing event consumers need code changes.

---

## Architecture

The change touches four files and the test suite. No new services, tables, or event types are
introduced.

```mermaid
flowchart LR
    subgraph grading ["Grading Service"]
        GH[handlers.py\nhandle_return_submitted]
    end

    subgraph events ["shared-py / events"]
        PG[ProductGradedEventData\n+ original_price_usd: float | None]
    end

    subgraph lifecycle ["Lifecycle Service"]
        LH[handlers.py\nhandle_product_graded]
        LS[service.py\ndecide_lifecycle]
    end

    subgraph ai ["shared-py / ai"]
        MOCK[mock.py\nmock_decide_lifecycle\n2-D score table\nper-branch multipliers]
        CLIENT[client.py\nGOLDEN_PATH_* constants]
    end

    GH -- emits --> PG
    PG -- consumed by --> LH
    LH -- extracts original_price_usd\nor uses 100.0 fallback --> LS
    LS -- calls --> MOCK
    CLIENT -- pins golden-path\nexpected values --> MOCK
```

### Data flow for price propagation

```
ReturnSubmitted
  └─► grading handler
        └─► ProductGraded { original_price_usd: None }   ← option (b): None for now
              └─► lifecycle handler
                    ├── original_price_usd is None/≤0 → value_estimate = 100.0
                    └── original_price_usd > 0        → value_estimate = original_price_usd
                          └─► LifecycleService.decide_lifecycle(value_estimate=...)
                                └─► mock_decide_lifecycle(grade, category, value_estimate)
```

**Why option (b)?** Reading `original_price_usd` from product attributes in the grading
handler requires a cross-service DB call or a new REST round-trip, which is out of scope for
this task. The lifecycle handler's fallback ensures correctness for P2-B4; actual price
injection can be wired in a later phase when the Gateway exposes a product-attributes endpoint.

---

## Components and Interfaces

### 1. `ProductGradedEventData` — schema addition

**File:** `packages/shared-py/shared_py/events/schemas.py`

Add one optional field to the existing model:

```python
class ProductGradedEventData(BaseModel):
    # ... existing fields unchanged ...
    original_price_usd: float | None = Field(
        default=None,
        description="Catalogue/purchase price in USD; None when not available",
    )
```

- No validator needed — Pydantic's `default=None` handles absent keys.
- `event_version` stays `"1.0"` (additive, backward-compatible change).

### 2. Lifecycle event handler — price extraction

**File:** `services/lifecycle/app/events/handlers.py`

Replace the hardcoded `value_estimate=100.0` with logic that reads the new field:

```python
data = ProductGradedEventData.model_validate(envelope.data)

_price = data.original_price_usd
value_estimate = _price if (_price is not None and _price > 0) else 100.0

decision = await service.decide_lifecycle(
    return_id=data.return_id,
    grade_id=data.grade_id,
    grade=data.grade,
    product_category="electronics",
    value_estimate=value_estimate,
    correlation_id=correlation_id,
)
```

The fallback condition covers three invalid cases explicitly: `None`, `0.0`, and negative
values. This matches Requirement 6.3.

### 3. `mock_decide_lifecycle` — 2-D score table and per-branch multipliers

**File:** `packages/shared-py/shared_py/ai/mock.py`

#### Sustainability score lookup

Replace the single `sustainability_score = <constant>` assignments with a two-dimensional dict
keyed on `(grade, action)`. A sentinel default covers unlisted combos (e.g. hyperlocal base):

```python
_SUSTAINABILITY_SCORES: dict[tuple[Grade, LifecycleAction], float] = {
    (Grade.A, LifecycleAction.RESELL):      88.0,
    (Grade.A, LifecycleAction.HYPERLOCAL):  90.0,
    (Grade.B, LifecycleAction.RESELL):      80.0,   # golden-path locked
    (Grade.B, LifecycleAction.REFURBISH):   75.0,
    (Grade.B, LifecycleAction.HYPERLOCAL):  87.0,
    (Grade.C, LifecycleAction.REFURBISH):   70.0,
    (Grade.C, LifecycleAction.DONATE):      65.0,
    (Grade.D, LifecycleAction.RECYCLE):     50.0,
    (Grade.D, LifecycleAction.DONATE):      55.0,
}
_SUSTAINABILITY_DEFAULT = 60.0
```

Lookup pattern:

```python
sustainability_score = _SUSTAINABILITY_SCORES.get((grade, action), _SUSTAINABILITY_DEFAULT)
```

This satisfies the grade-range requirements:
- Grade A: 88–90 ∈ [82, 92] ✓
- Grade B RESELL electronics: 80.0 exactly ✓
- Grade C: 65–70 ∈ [60, 74] ✓
- Grade D: 50–55 ∈ [45, 60] ✓

#### Value recovery multipliers

Define explicit per-branch multipliers:

```python
_VALUE_MULTIPLIERS: dict[tuple[Grade, LifecycleAction], float] = {
    (Grade.A, LifecycleAction.RESELL):      0.75,
    (Grade.A, LifecycleAction.HYPERLOCAL):  0.65,
    (Grade.B, LifecycleAction.RESELL):      0.60,   # golden-path locked: 120×0.60=72.00
    (Grade.B, LifecycleAction.REFURBISH):   0.50,
    (Grade.B, LifecycleAction.HYPERLOCAL):  0.65,
    (Grade.C, LifecycleAction.REFURBISH):   0.40,
    (Grade.C, LifecycleAction.DONATE):      0.10,
    (Grade.D, LifecycleAction.RECYCLE):     0.05,
    (Grade.D, LifecycleAction.DONATE):      0.05,
}
_VALUE_MULTIPLIER_DEFAULT = 0.10
```

Zero-value guard:

```python
multiplier = _VALUE_MULTIPLIERS.get((grade, action), _VALUE_MULTIPLIER_DEFAULT)
value_recovery = 0.0 if value_estimate == 0.0 else value_estimate * multiplier
```

#### Hyperlocal override

The existing seed-based hyperlocal branch is preserved. After the override fires, use the
`HYPERLOCAL` key for both the score table and the multiplier table, then cap:

```python
if seed % 5 == 0 and grade in (Grade.A, Grade.B):
    action = LifecycleAction.HYPERLOCAL
    sustainability_score = _SUSTAINABILITY_SCORES.get((grade, action), _SUSTAINABILITY_DEFAULT)
    sustainability_score = min(sustainability_score, 100.0)
    multiplier = _VALUE_MULTIPLIERS.get((grade, action), _VALUE_MULTIPLIER_DEFAULT)
    value_recovery = 0.0 if value_estimate == 0.0 else value_estimate * multiplier
```

### 4. `LifecycleDecision` schema — no changes

`packages/shared-py/shared_py/ai/schemas.py` is untouched. The `LifecycleDecision` model
fields (`action`, `rationale`, `value_recovery_estimate`, `sustainability_score`,
`confidence`) remain identical.

---

## Data Models

### `ProductGradedEventData` (after change)

| Field | Type | Default | Notes |
|---|---|---|---|
| `return_id` | `str` | required | UUID of the Return |
| `grade_id` | `str` | required | UUID of the Grade entity |
| `product_id` | `str` | required | UUID of the Product |
| `grade` | `str` | required | A/B/C/D |
| `confidence` | `float` | required | 0–1 |
| `damage_summary` | `str` | required | AI-generated text |
| `defects` | `list[str]` | `[]` | Defect labels |
| `original_price_usd` | `float \| None` | `None` | **New** — catalogue price in USD |

### Score / multiplier lookup tables (in `mock.py`)

| Grade | Action | Sustainability Score | Multiplier |
|---|---|---|---|
| A | RESELL | 88.0 | 0.75 |
| A | HYPERLOCAL | 90.0 | 0.65 |
| B | RESELL | **80.0** (locked) | **0.60** (locked) |
| B | REFURBISH | 75.0 | 0.50 |
| B | HYPERLOCAL | 87.0 | 0.65 |
| C | REFURBISH | 70.0 | 0.40 |
| C | DONATE | 65.0 | 0.10 |
| D | RECYCLE | 50.0 | 0.05 |
| D | DONATE | 55.0 | 0.05 |
| *(default)* | *(any)* | 60.0 | 0.10 |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Backward-compatible deserialization of `ProductGradedEventData`

*For any* dict that is a valid `ProductGradedEventData` payload and does not contain an
`original_price_usd` key, `ProductGradedEventData.model_validate(payload).original_price_usd`
SHALL be `None` and validation SHALL NOT raise an exception.

**Validates: Requirements 1.1, 6.1**

### Property 2: Score bounds and value-recovery invariant

*For all* `grade` in `{Grade.A, Grade.B, Grade.C, Grade.D}`, `product_category` in
`{"electronics", "clothing", "furniture", "toys", "appliances", "books"}`, and
`value_estimate` in `(0.0, 10 000.0]`, `mock_decide_lifecycle` SHALL return a
`LifecycleDecision` where:

- `0.0 <= sustainability_score <= 100.0`
- `0.0 < value_recovery_estimate <= value_estimate`

**Validates: Requirements 2.6, 3.4, 5.1**

### Property 3: Lifecycle handler uses `100.0` fallback for invalid prices

*For any* `ProductGradedEventData` where `original_price_usd` is `None`, `0.0`, or a
negative value, the value passed as `value_estimate` to `LifecycleService.decide_lifecycle`
SHALL be `100.0`.

**Validates: Requirements 1.3, 6.3**

---

## Error Handling

| Scenario | Handling |
|---|---|
| `original_price_usd` is `None` in event | Lifecycle handler falls back to `100.0` |
| `original_price_usd` is `0.0` or negative | Same fallback — guarded by `_price > 0` check |
| Event dict missing `original_price_usd` key entirely | Pydantic `default=None` handles silently |
| `value_estimate=0.0` passed to mock | Returns `value_recovery_estimate=0.0`, no ZeroDivisionError |
| Hyperlocal override with computed score > 100 | `min(..., 100.0)` cap applied before return |
| Uncovered `(grade, action)` combo in lookup tables | `_SUSTAINABILITY_DEFAULT = 60.0` / `_VALUE_MULTIPLIER_DEFAULT = 0.10` — always within valid range |

---

## Testing Strategy

### Framework

- **pytest** with **pytest-asyncio** (already used throughout the project).
- **hypothesis** (already used, `.hypothesis/` present at repo root) for property-based tests.
- All tests in `packages/shared-py/tests/test_ai.py` (update/extend existing file).

### Unit tests (example-based)

These verify concrete, pinned behaviors:

| Test | What it asserts |
|---|---|
| `test_golden_path_regression` | `mock_decide_lifecycle(Grade.B, "electronics", 120.00)` → action=RESELL, value_recovery=72.00, sustainability_score=80.0, confidence>0, rationale non-empty |
| `test_schema_backward_compat_no_price_field` | Dict without `original_price_usd` → `model_validate` succeeds, field is None |
| `test_schema_backward_compat_explicit_none` | Dict with `original_price_usd=None` → field is None |
| `test_handler_fallback_none` | Handler extracts None → value_estimate=100.0 (mock the service call) |
| `test_handler_fallback_zero` | Handler extracts 0.0 → value_estimate=100.0 |
| `test_handler_fallback_negative` | Handler extracts -5.0 → value_estimate=100.0 |
| `test_handler_passes_positive_price` | Handler extracts 250.0 → value_estimate=250.0 |
| `test_zero_value_estimate` | `mock_decide_lifecycle(any_grade, any_cat, 0.0)` → value_recovery=0.0, no exception |

### Property-based tests

Using **Hypothesis**; each property runs ≥ 100 iterations.

#### PBT 1 — Backward-compatible deserialization

```
# Feature: p2-b4-score-tuning, Property 1: backward-compatible deserialization
@given(st.fixed_dictionaries({
    "return_id": st.uuids(), "grade_id": st.uuids(), "product_id": st.uuids(),
    "grade": st.sampled_from(["A","B","C","D"]),
    "confidence": st.floats(0.0, 1.0), "damage_summary": st.text(min_size=1),
}))
def test_property_backward_compat_deserialization(payload):
    ...
```

Asserts: `model_validate` succeeds and `original_price_usd is None`.

#### PBT 2 — Score bounds and value-recovery invariant

```
# Feature: p2-b4-score-tuning, Property 2: score bounds and value-recovery invariant
@given(
    grade=st.sampled_from(list(Grade)),
    category=st.sampled_from(["electronics","clothing","furniture","toys","appliances","books"]),
    value_estimate=st.floats(min_value=0.01, max_value=10_000.0, allow_nan=False),
)
def test_property_score_bounds_and_recovery_invariant(grade, category, value_estimate):
    ...
```

Asserts: `0.0 <= sustainability_score <= 100.0` and `0.0 < value_recovery <= value_estimate`.

#### PBT 3 — Handler fallback for invalid prices

```
# Feature: p2-b4-score-tuning, Property 3: lifecycle handler fallback
@given(original_price=st.one_of(st.just(None), st.just(0.0), st.floats(max_value=-0.01)))
def test_property_handler_fallback_invalid_price(original_price):
    ...
```

Asserts: extracted `value_estimate` equals `100.0` for None/zero/negative inputs.

### What is NOT property-tested

- `LifecycleDecision` schema field existence — smoke/example test is sufficient.
- `event_version="1.0"` constant — smoke test.
- Passport service backward compat — integration concern, out of scope for this suite.

### Running the tests

```bash
cd packages/shared-py
AI_MODE=mock pytest tests/test_ai.py -v
```

No AWS credentials or network access required. The `AI_MODE=mock` env var is the only
prerequisite (the project default).
